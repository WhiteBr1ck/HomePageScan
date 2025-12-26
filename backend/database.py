from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, text, inspect
from sqlalchemy.future import select
from datetime import datetime

DATABASE_URL = "sqlite+aiosqlite:///./services.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

# Global app settings (site branding)
class AppSettings(Base):
    __tablename__ = "app_settings"
    id = Column(Integer, primary_key=True, index=True)
    site_title = Column(String, default="HomePageScan")
    site_icon_url = Column(String, nullable=True)
    view_mode = Column(String, default="grid")  # 'grid' or 'list'
    grid_size = Column(String, default="medium")  # 'small', 'medium', 'large'
    theme_mode = Column(String, default="auto")  # 'light', 'dark', 'auto'
    accent_color = Column(String, default="#3b82f6")  # Default blue-500
    default_sort_by = Column(String, default="custom")  # 'custom', 'name', or 'port'

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    # Remove site_title and site_icon_url from profile
    scan_target = Column(String, default="127.0.0.1")
    is_guest_default = Column(Boolean, default=False)
    
    services = relationship("Service", back_populates="profile", cascade="all, delete-orphan")

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=True) # Link to Profile
    
    ip = Column(String, index=True)
    port = Column(Integer, index=True)
    protocol = Column(String) # http/https
    
    # Auto-detected URL
    url = Column(String, index=True) 
    
    # Manually editable fields
    lan_url = Column(String, nullable=True) # Local Network URL
    wan_url = Column(String, nullable=True) # Public/WAN URL
    
    title = Column(String, default="")
    custom_name = Column(String, nullable=True)
    icon_url = Column(String, nullable=True)
    
    is_visible = Column(Boolean, default=True)
    is_manual_lock = Column(Boolean, default=False)
    
    last_scanned = Column(DateTime, default=datetime.utcnow)
    sort_order = Column(Integer, default=0)

    profile = relationship("Profile", back_populates="services")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Migration: Add new columns to app_settings if they don't exist
        def check_and_add_app_settings_columns(connection):
            inspector = inspect(connection)
            columns = [col['name'] for col in inspector.get_columns('app_settings')]

            migrations = {
                'default_sort_by': "VARCHAR DEFAULT 'custom'",
                'view_mode': "VARCHAR DEFAULT 'grid'",
                'grid_size': "VARCHAR DEFAULT 'medium'",
                'theme_mode': "VARCHAR DEFAULT 'auto'",
                'accent_color': "VARCHAR DEFAULT '#3b82f6'",
            }

            for col_name, col_type_default in migrations.items():
                if col_name not in columns:
                    try:
                        connection.execute(text(f"ALTER TABLE app_settings ADD COLUMN {col_name} {col_type_default}"))
                        print(f"✅ Migration: Added {col_name} column to app_settings")
                    except Exception as e:
                        print(f"⚠️ Migration failed for {col_name}: {e}")
            
        await conn.run_sync(check_and_add_app_settings_columns)

    async with AsyncSessionLocal() as session:
        # Create default app settings
        result = await session.execute(select(AppSettings))
        if not result.scalars().first():
            session.add(AppSettings(
                site_title="HomePageScan",
                site_icon_url=None,
                default_sort_by="custom",
                view_mode="grid",
                grid_size="medium",
                theme_mode="auto",
                accent_color="#3b82f6"
            ))
        
        # Create default user
        from auth import get_password_hash
        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalars().first():
            session.add(User(username="admin", hashed_password=get_password_hash("admin")))
        
        # Create default profile
        result = await session.execute(select(Profile).where(Profile.name == "Default"))
        if not result.scalars().first():
            session.add(Profile(
                name="Default", 
                scan_target="127.0.0.1",
                is_guest_default=True
            ))
            
        await session.commit()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
