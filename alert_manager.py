# ==============================================
# EURO_GOALS v9.4.0 – Alert Manager (Backend)
# ==============================================
import os
import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Boolean, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker

# ----------------------------------------------
# DB setup
# ----------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

def _make_engine(url: str):
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)

engine = _make_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

# ----------------------------------------------
# Model
# ----------------------------------------------
class Alert(Base):
    __tablename__ = "alert_history"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(64), index=True, nullable=False)           # SMART_MONEY_ALERT / GOAL_ALERT / HEALTH_ALERT / SYSTEM_EVENT
    message = Column(Text, nullable=False)
    meta = Column(Text, nullable=True)                               # JSON as text
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    is_read = Column(Boolean, default=False, index=True)

def init_db():
    Base.metadata.create_all(bind=engine)

# ----------------------------------------------
# Helpers
# ----------------------------------------------
VALID_TYPES = {"SMART_MONEY_ALERT", "GOAL_ALERT", "HEALTH_ALERT", "SYSTEM_EVENT"}

def _ensure_type(t: str) -> str:
    t = (t or "").strip().upper()
    if t not in VALID_TYPES:
        # Allow custom, but normalize
        return t or "SYSTEM_EVENT"
    return t

# ----------------------------------------------
# CRUD-like API
# ----------------------------------------------
def create_alert(alert_type: str, message: str, meta: Optional[dict] = None) -> int:
    """Insert new alert and return id."""
    with SessionLocal() as s:
        alert = Alert(
            type=_ensure_type(alert_type),
            message=message.strip(),
            meta=json.dumps(meta) if meta else None,
        )
        s.add(alert)
        s.commit()
        s.refresh(alert)
        return alert.id

def list_alerts(
    limit: int = 200,
    types: Optional[List[str]] = None,
    only_unread: bool = False,
    since_id: Optional[int] = None,
) -> List[dict]:
    with SessionLocal() as s:
        q = s.query(Alert)
        if types:
            norm = [_ensure_type(t) for t in types]
            q = q.filter(Alert.type.in_(norm))
        if only_unread:
            q = q.filter(Alert.is_read.is_(False))
        if since_id:
            q = q.filter(Alert.id > since_id)
        q = q.order_by(Alert.id.desc()).limit(max(1, min(limit, 1000)))
        rows = q.all()
        return [_serialize(a) for a in rows]

def latest_alert(since_id: Optional[int] = None) -> Optional[dict]:
    res = list_alerts(limit=1, since_id=since_id)
    return res[0] if res else None

def mark_read(ids: Optional[List[int]] = None, mark_all: bool = False) -> int:
    with SessionLocal() as s:
        q = s.query(Alert)
        if not mark_all and ids:
            q = q.filter(Alert.id.in_(ids))
        updated = q.update({"is_read": True})
        s.commit()
        return updated

def clear_all() -> int:
    with SessionLocal() as s:
        deleted = s.query(Alert).delete()
        s.commit()
        return deleted

def _serialize(a: Alert) -> dict:
    return {
        "id": a.id,
        "type": a.type,
        "message": a.message,
        "meta": json.loads(a.meta) if a.meta else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "is_read": bool(a.is_read),
    }
