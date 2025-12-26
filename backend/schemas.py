from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

# --- Profile ---
class ProfileBase(BaseModel):
    name: str
    scan_target: Optional[str] = "127.0.0.1"

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    scan_target: Optional[str] = None

class ProfileResponse(ProfileBase):
    id: int
    is_guest_default: bool = False
    class Config:
        from_attributes = True

# --- Service ---
class ServiceBase(BaseModel):
    custom_name: Optional[str] = None
    icon_url: Optional[str] = None
    is_visible: Optional[bool] = True
    lan_url: Optional[str] = None
    wan_url: Optional[str] = None
    sort_order: Optional[int] = 0

class ServiceUpdate(ServiceBase):
    pass

class ServiceResponse(ServiceBase):
    id: int
    profile_id: Optional[int]
    ip: str
    port: int
    protocol: str
    url: str # Original Detected URL
    title: str
    last_scanned: datetime
    
    class Config:
        from_attributes = True

class ScanRequest(BaseModel):
    target_ip: str
    profile_id: int

# --- Reorder ---
class ReorderRequest(BaseModel):
    ordered_ids: List[int]

# --- AppSettings ---
class AppSettingsBase(BaseModel):
    site_title: str = "HomePageScan"
    site_icon_url: Optional[str] = None
    default_sort_by: str = "custom"

class AppSettingsResponse(BaseModel):
    id: int
    site_title: str
    site_icon_url: Optional[str] = None
    view_mode: str = "grid"
    grid_size: str = "medium"
    theme_mode: str = "auto"
    accent_color: str = "#3b82f6"
    default_sort_by: str = "custom"
    
    class Config:
        from_attributes = True

class AppSettingsUpdate(BaseModel):
    site_title: Optional[str] = None
    site_icon_url: Optional[str] = None
    view_mode: Optional[str] = None
    grid_size: Optional[str] = None
    theme_mode: Optional[str] = None
    accent_color: Optional[str] = None
    default_sort_by: Optional[str] = None
