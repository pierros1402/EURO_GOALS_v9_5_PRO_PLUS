# ==============================================
# EURO_GOALS v9.4.1 – Settings Manager
# Server-side αποθήκευση ρυθμίσεων ειδοποιήσεων
# ==============================================
import os
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

def _make_engine(url: str):
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)

engine = _make_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(Integer, primary_key=True, index=True)
    notifications_enabled = Column(Boolean, default=False)
    sound_enabled = Column(Boolean, default=True)
    refresh_interval = Column(Integer, default=10)  # seconds

def init_settings_db():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as s:
        row = s.query(UserSettings).get(1)
        if not row:
            row = UserSettings(id=1, notifications_enabled=False, sound_enabled=True, refresh_interval=10)
            s.add(row); s.commit()

def get_settings() -> Dict[str, Any]:
    with SessionLocal() as s:
        row = s.query(UserSettings).get(1)
        if not row:
            row = UserSettings(id=1); s.add(row); s.commit()
        return {
            "notifications_enabled": bool(row.notifications_enabled),
            "sound_enabled": bool(row.sound_enabled),
            "refresh_interval": int(row.refresh_interval or 10),
        }

def update_settings(
    notifications_enabled: Optional[bool] = None,
    sound_enabled: Optional[bool] = None,
    refresh_interval: Optional[int] = None,
) -> Dict[str, Any]:
    with SessionLocal() as s:
        row = s.query(UserSettings).get(1)
        if not row:
            row = UserSettings(id=1); s.add(row)
        if notifications_enabled is not None:
            row.notifications_enabled = bool(notifications_enabled)
        if sound_enabled is not None:
            row.sound_enabled = bool(sound_enabled)
        if refresh_interval is not None:
            row.refresh_interval = int(max(5, min(60, refresh_interval)))
        s.commit()
        return {
            "notifications_enabled": bool(row.notifications_enabled),
            "sound_enabled": bool(row.sound_enabled),
            "refresh_interval": int(row.refresh_interval or 10),
        }
