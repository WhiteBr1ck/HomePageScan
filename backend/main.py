from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, update
from database import get_db, init_db, Service, User, Profile, AppSettings
from schemas import (
    ServiceResponse, ServiceUpdate, ScanRequest, Token, UserLogin,
    ProfileCreate, ProfileResponse, ProfileUpdate,
    AppSettingsResponse, AppSettingsUpdate, ReorderRequest
)
from auth import verify_password, get_password_hash, create_access_token, get_current_user, get_current_user_optional
from scanner import run_scan_task, NMAP_BIN
import shutil 
import os
import logging
from typing import List, Optional
from pydantic import BaseModel
import asyncio
import json

app = FastAPI(title="HomePageScan API V2")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
os.makedirs("static/icons", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

import database

# Global scan status for SSE
scan_status = {
    "is_scanning": False,
    "target": "",
    "progress": 0,
    "logs": [],
    "completed": False
}

def add_scan_log(message: str):
    scan_status["logs"].append(message)
    if len(scan_status["logs"]) > 100:
        scan_status["logs"] = scan_status["logs"][-50:]

@app.on_event("startup")
async def on_startup():
    await init_db()
    async with database.AsyncSessionLocal() as db:
        # Default Admin - use ADMIN_PASSWORD from environment, fallback to 'admin'
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin")
        res = await db.execute(select(User).where(User.username == "admin"))
        existing_admin = res.scalars().first()
        if not existing_admin:
            db.add(User(username="admin", hashed_password=get_password_hash(admin_password)))
            logging.info(f"Created admin user with password from environment")
        
        # Default Profile
        res_prof = await db.execute(select(Profile).where(Profile.name == "Default"))
        if not res_prof.scalars().first():
            db.add(Profile(name="Default", site_title="HomePageScan", scan_target="127.0.0.1"))
            
        await db.commit()

@app.get("/")
def read_root():
    return {"message": "HomePageScan V2 API Running."}

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "nmap_found": bool(NMAP_BIN),
        "nmap_path": NMAP_BIN,
    }

# --- Auth ---
@app.post("/api/login", response_model=Token)
async def login(form_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/users")
async def create_user(form_data: UserLogin, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.add(User(username=form_data.username, hashed_password=get_password_hash(form_data.password)))
    await db.commit()
    return {"message": "User created"}

# --- Password Change ---
class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@app.post("/api/users/password")
async def change_password(data: PasswordChange, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    current_user.hashed_password = get_password_hash(data.new_password)
    await db.commit()
    return {"message": "Password changed successfully"}

# --- Profiles ---
@app.get("/api/profiles", response_model=List[ProfileResponse])
async def get_profiles(db: AsyncSession = Depends(get_db), user: Optional[User] = Depends(get_current_user_optional)):
    # If not authenticated, return only guest default profile
    if not user:
        result = await db.execute(select(Profile).where(Profile.is_guest_default == True))
        profiles = result.scalars().all()
        return profiles if profiles else []
    
    # If authenticated, return all profiles
    result = await db.execute(select(Profile))
    return result.scalars().all()

@app.post("/api/profiles", response_model=ProfileResponse)
async def create_profile(profile: ProfileCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    new_prof = Profile(name=profile.name, site_title=profile.site_title, site_icon_url=profile.site_icon_url, scan_target=profile.scan_target)
    db.add(new_prof)
    await db.commit()
    await db.refresh(new_prof)
    return new_prof

@app.put("/api/profiles/{profile_id}", response_model=ProfileResponse)
async def update_profile(profile_id: int, profile: ProfileUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    res = await db.execute(select(Profile).where(Profile.id == profile_id))
    prof = res.scalars().first()
    if not prof: raise HTTPException(404, "Profile not found")
    
    if profile.name: prof.name = profile.name
    if profile.scan_target: prof.scan_target = profile.scan_target
    
    await db.commit()
    await db.refresh(prof)
    return prof

@app.delete("/api/profiles/{profile_id}")
async def delete_profile(profile_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    res = await db.execute(select(Profile).where(Profile.id == profile_id))
    prof = res.scalars().first()
    if not prof: raise HTTPException(404, "Profile not found")
    if prof.name == "Default": raise HTTPException(400, "Cannot delete default profile")
    
    await db.delete(prof)
    await db.commit()
    return {"message": "Profile deleted"}

@app.post("/api/profiles/{profile_id}/set-guest-default")
async def set_guest_default(profile_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    # Unset all other profiles
    await db.execute(update(Profile).values(is_guest_default=False))
    
    # Set the specified profile as guest default
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    
    profile.is_guest_default = True
    await db.commit()
    return {"message": f"Profile '{profile.name}' set as guest default"}

# --- App Settings ---
@app.get("/api/settings", response_model=AppSettingsResponse)
async def get_app_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AppSettings))
    settings = result.scalars().first()
    if not settings:
        # Create default if not exists
        settings = AppSettings(site_title="HomePageScan")
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings

@app.put("/api/settings", response_model=AppSettingsResponse)
async def update_app_settings(updates: AppSettingsUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(AppSettings))
    settings = result.scalars().first()
    if not settings:
        settings = AppSettings()
        db.add(settings)
    
    if updates.site_title is not None:
        settings.site_title = updates.site_title
    if updates.site_icon_url is not None:
        settings.site_icon_url = updates.site_icon_url if updates.site_icon_url else None
    if updates.view_mode is not None:
        settings.view_mode = updates.view_mode
    if updates.grid_size is not None:
        settings.grid_size = updates.grid_size
    if updates.theme_mode is not None:
        settings.theme_mode = updates.theme_mode
    if updates.accent_color is not None:
        settings.accent_color = updates.accent_color
    if updates.default_sort_by is not None:
        settings.default_sort_by = updates.default_sort_by
    
    await db.commit()
    await db.refresh(settings)
    return settings


# --- Services ---
@app.get("/api/services", response_model=List[ServiceResponse])
async def read_services(profile_id: int = 1, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Service)
        .where(Service.profile_id == profile_id)
        .where(Service.is_visible == True)
        .order_by(Service.sort_order.desc(), Service.port.asc())
    )
    return result.scalars().all()

@app.post("/api/services/{service_id}")
async def update_service(
    service_id: int, 
    service_update: ServiceUpdate, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if service_update.custom_name is not None:
        service.custom_name = service_update.custom_name
    if service_update.icon_url is not None:
        service.icon_url = service_update.icon_url
    if service_update.is_visible is not None:
        service.is_visible = service_update.is_visible
    if service_update.lan_url is not None:
        service.lan_url = service_update.lan_url
    if service_update.wan_url is not None:
        service.wan_url = service_update.wan_url
    if service_update.sort_order is not None:
        service.sort_order = service_update.sort_order
    
    service.is_manual_lock = True
    
    await db.commit()
    await db.refresh(service)
    return service

@app.delete("/api/services/{service_id}")
async def delete_service(service_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    await db.delete(service)
    await db.commit()
    return {"message": "Deleted"}

@app.post("/api/reorder-services")
async def reorder_services(request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Reorder services. Accepts any JSON format and extracts ordered_ids
    """
    try:
        body = await request.json()
        print(f"DEBUG: Raw request body: {body}")
        print(f"DEBUG: Body type: {type(body)}")
        
        # Handle both array and object formats
        if isinstance(body, list):
            ordered_ids = body
            print(f"DEBUG: Received as array: {ordered_ids}")
        elif isinstance(body, dict):
            ordered_ids = body.get("ordered_ids", [])
            print(f"DEBUG: Received as object, extracted: {ordered_ids}")
        else:
            print(f"DEBUG: Unexpected body type!")
            raise HTTPException(400, f"Invalid request format: {type(body)}")
        
        if not ordered_ids:
            raise HTTPException(400, "ordered_ids is required")
        
        total = len(ordered_ids)
        for index, svc_id in enumerate(ordered_ids):
            new_order = total - index
            stmt = update(Service).where(Service.id == svc_id).values(sort_order=new_order)
            await db.execute(stmt)
            
        await db.commit()
        return {"message": "Reordered successfully", "count": len(ordered_ids)}
    except Exception as e:
        print(f"DEBUG: Error occurred: {e}")
        raise HTTPException(500, f"Reorder failed: {str(e)}")

# --- Manual Service Add ---
@app.post("/api/services/manual")
async def add_service_manual(data: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    from datetime import datetime
    new_service = Service(
        profile_id=data.get('profile_id', 1),
        ip=data.get('ip', '0.0.0.0'),
        port=data.get('port', 80),
        protocol=data.get('protocol', 'http'),
        url=data.get('url', ''),
        lan_url=data.get('lan_url'),
        wan_url=data.get('wan_url'),
        title=data.get('title', 'Manual Service'),
        custom_name=data.get('custom_name'),
        icon_url=None,
        is_visible=True,
        is_manual_lock=True,
        last_scanned=datetime.utcnow(),
        sort_order=100
    )
    db.add(new_service)
    await db.commit()
    await db.refresh(new_service)
    return new_service

# --- Scan with SSE Progress ---
@app.post("/api/scan")
async def trigger_scan(
    scan_req: ScanRequest, 
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    global scan_status
    scan_status = {
        "is_scanning": True,
        "target": scan_req.target_ip,
        "progress": 0,
        "logs": [f"Starting scan for {scan_req.target_ip}..."],
        "completed": False
    }
    background_tasks.add_task(run_scan_with_status, scan_req.target_ip, scan_req.profile_id)
    return {"message": f"Scan started for {scan_req.target_ip}"}

async def run_scan_with_status(target_ip: str, profile_id: int):
    global scan_status
    try:
        add_scan_log(f"Initializing Nmap scan on {target_ip}...")
        scan_status["progress"] = 5
        
        await run_scan_task(target_ip, profile_id)
        
        scan_status["progress"] = 100
        add_scan_log("Scan completed successfully!")
    except Exception as e:
        add_scan_log(f"Scan error: {str(e)}")
    finally:
        scan_status["is_scanning"] = False
        scan_status["completed"] = True

@app.get("/api/scan/status")
async def get_scan_status():
    return scan_status

@app.get("/api/scan/stream")
async def scan_stream():
    async def event_generator():
        while True:
            data = json.dumps(scan_status)
            yield f"data: {data}\n\n"
            if scan_status["completed"] and not scan_status["is_scanning"]:
                break
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# --- Upload ---
@app.post("/api/upload")
async def upload_icon(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    file_location = f"static/icons/{file.filename}"
    with open(file_location, "wb+") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"url": f"/static/icons/{file.filename}"}
