import asyncio
import os
import shutil
import nmap
import httpx
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from urllib.parse import urljoin, urlparse
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal, Service
import logging
import subprocess
import aiofiles
from datetime import datetime
import re
import warnings

# Suppress BeautifulSoup warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def find_nmap_path():
    # 1. Check PATH
    path = shutil.which("nmap")
    if path:
        return path

    # 2. Check Common Paths
    common_paths = [
        r"C:\Program Files (x86)\Nmap\nmap.exe",
        r"C:\Program Files\Nmap\nmap.exe",
        r"D:\Program Files (x86)\Nmap\nmap.exe",
        r"D:\Program Files\Nmap\nmap.exe",
        r"D:\Tools\Nmap\nmap.exe"
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p
            
    # 3. Try 'where' command (Windows)
    try:
        output = subprocess.check_output(["where", "nmap"], encoding='utf-8', stderr=subprocess.DEVNULL)
        lines = output.strip().splitlines()
        if lines and os.path.exists(lines[0]):
            return lines[0]
    except Exception:
        pass

    return None

NMAP_BIN = find_nmap_path()
nm = None

if NMAP_BIN:
    logger.info(f"Nmap found at: {NMAP_BIN}")
    # We still initialize python-nmap just in case we need parsing utils, 
    # but we will primarily use subprocess for scanning now.
    try:
        nm = nmap.PortScanner(nmap_search_path=[NMAP_BIN, 'nmap'])
    except Exception:
        pass
else:
    logger.error("Nmap binary NOT found. Scans will fail.")

async def run_scan_task(target_ip: str, profile_id: int):
    # Import log function from main if possible, or just print to stdout
    # Since we are in a separate module, we can't easily import `add_scan_log` from main without circular import.
    # We will assume main.py is monkey-patching or we redesign slightly.
    # Ideally, main.py should pass a callback. But for now, let's just use a global queue or specialized logging.
    # BETTER APPROACH: We just process and let the background task finish, 
    # but to support REALTIME updates, we must communicate back to main.py.
    # Python modules are singletons. We can import `add_scan_log` inside the function if main is already loaded.
    
    from main import add_scan_log, scan_status
    
    logger.info(f"Starting scan for {target_ip} on Profile {profile_id}")
    
    if not NMAP_BIN:
        add_scan_log("Error: Nmap binary not found.")
        return

    # Construct Command: Scan top 2000 ports + standard service detection
    # -T4: Aggressive timing
    # --open: Only show open ports
    # -n: No DNS resolution (faster)
    cmd = [NMAP_BIN, target_ip, "-p", "1-65535", "-T4", "--open", "-n"]
    
    add_scan_log(f"Executing: {' '.join(cmd)}")
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Read output line by line
    discovered_ports = []
    
    # Simple regex to catch "Discovered open port 80/tcp on 192.168.1.1" (nmap output varies)
    # Standard nmap output for open ports often looks like: "80/tcp open http" in the table
    # OR if using -v, it says "Discovered open port..."
    
    # Let's read line by line
    while True:
        line_bytes = await process.stdout.readline()
        if not line_bytes:
            break
        line = line_bytes.decode('utf-8', errors='replace').strip()
        if not line:
            continue
            
        # Log interesting lines
        if "Discovered open port" in line:
            add_scan_log(line)
        elif "/tcp" in line and "open" in line:
            add_scan_log(f"Found: {line}")
            # Parse port: "80/tcp open http"
            parts = line.split('/')
            if parts[0].isdigit():
                port = int(parts[0])
                service_name = "unknown"
                if "open" in line:
                     # try to get service name from the right
                     remain = line.split("open")[-1].strip()
                     service_name = remain
                
                discovered_ports.append((port, service_name))

        # Update progress just to show activity
        if scan_status["progress"] < 90:
             scan_status["progress"] += 1

    await process.wait()
    
    if process.returncode != 0:
        stderr = await process.stderr.read()
        add_scan_log(f"Nmap exited with error: {stderr.decode()}")
    
    add_scan_log(f"Scan finished. Found {len(discovered_ports)} open ports.")
    scan_status["progress"] = 90
    
    # Process found ports
    async with AsyncSessionLocal() as db:
        for port, svc_name in discovered_ports:
             # Identify Web Services
            is_web = False
            scheme = "http"
            
            if 'http' in svc_name or port in [80, 8080, 8000, 3000, 5000, 8081]:
                is_web = True
                scheme = "http"
            elif 'https' in svc_name or 'ssl' in svc_name or port in [443, 8443]:
                is_web = True
                scheme = "https"
            
            # Heuristic: if unknown, try http check later? For now, be strict or generous.
            # Let's assume most open ports on home server might be web if not familiar
            if not is_web and port > 1000:
                 # Check if it speaks HTTP? 
                 # We will just try process_web_service which does a request check anyway.
                 is_web = True 
            
            if is_web:
                base_url = f"{scheme}://{target_ip}:{port}"
                add_scan_log(f"Probing {base_url}...")
                await process_web_service(db, target_ip, port, scheme, base_url, profile_id)

    scan_status["progress"] = 100

async def process_web_service(db: AsyncSession, ip: str, port: int, protocol: str, url: str, profile_id: int):
    # 1. Scrape Title and Icon
    title = ""
    icon_path = None
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=3.0) as client:
            resp = await client.get(url)
            
            # Stricter validation: Only accept if it's actually HTML content
            if resp.status_code >= 500:
                return  # Server error, skip
            
            content_type = resp.headers.get('content-type', '').lower()
            
            # Must be HTML or text/plain (some servers misconfigure this)
            if 'html' not in content_type and 'text' not in content_type:
                return
            
            # Parse and validate it's actually HTML
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Must have <html> tag or <title> tag to be considered valid web page
            if not soup.html and not soup.title:
                return
            
            # Extract title
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            
            # Try to find favicon
            icon_url = None
            icon_link = soup.find("link", rel=lambda x: x and 'icon' in x.lower())
            if icon_link and icon_link.get('href'):
                icon_url = urljoin(url, icon_link.get('href'))
            else:
                icon_url = urljoin(url, '/favicon.ico')
            
            if icon_url:
                icon_path = await download_icon(client, icon_url, ip, port)
            
    except Exception as e:
        # Not a web service or timeout
        return

    # 2. Database Upsert - SCOPED BY PROFILE
    result = await db.execute(select(Service).where(Service.ip == ip, Service.port == port, Service.profile_id == profile_id))
    existing_service = result.scalars().first()

    if existing_service:
        if not existing_service.is_manual_lock:
            existing_service.title = title or existing_service.title
            existing_service.protocol = protocol
            existing_service.url = url
            if icon_path:
                existing_service.icon_url = icon_path
            existing_service.last_scanned = datetime.utcnow()
    else:
        new_service = Service(
            profile_id=profile_id,
            ip=ip,
            port=port,
            protocol=protocol,
            url=url,
            lan_url=url, # Default LAN is detected IP
            wan_url=None,
            title=title or f"Port {port}",
            custom_name=None,
            icon_url=icon_path,
            is_visible=True,
            is_manual_lock=False
        )
        db.add(new_service)
    
    await db.commit()

async def download_icon(client: httpx.AsyncClient, url: str, ip: str, port: int) -> str:
    try:
        resp = await client.get(url)
        if resp.status_code == 200:
            filename = f"{ip}_{port}_{os.path.basename(urlparse(url).path) or 'favicon.ico'}"
            # Sanitize filename
            filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in '._-'])
            save_path = os.path.join("static", "icons", filename)
            
            async with aiofiles.open(save_path, 'wb') as f:
                await f.write(resp.content)
            
            return f"/static/icons/{filename}"
    except Exception:
        pass
    return None
