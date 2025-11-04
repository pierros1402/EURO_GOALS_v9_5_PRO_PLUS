# ==============================================
# EURO_GOALS v9.4.4 PRO+ — Push + SmartMoney Heatmap
# ==============================================
import os
import json
from datetime import datetime, timedelta
from typing import List

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from dotenv import load_dotenv

from pywebpush import webpush, WebPushException

# --------------------------------------------------
# ENV & APP
# --------------------------------------------------
load_dotenv()
PUSH_ENABLED = os.getenv("PUSH_ENABLED", "false").lower() == "true"
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_CONTACT = os.getenv("VAPID_CONTACT", "mailto:admin@eurogoals.local")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

app = FastAPI(title="EURO_GOALS v9.4.4 PRO+")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# --------------------------------------------------
# DATABASE
# --------------------------------------------------
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------------------------------------------
# MODELS
# --------------------------------------------------
class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    id = Column(Integer, primary_key=True)
    endpoint = Column(Text, unique=True, nullable=False)
    p256dh = Column(String(255), nullable=False)
    auth = Column(String(255), nullable=False)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SmartMoneyAlert(Base):
    __tablename__ = "smartmoney_alerts"
    id = Column(Integer, primary_key=True)
    match_id = Column(String(64), index=True)
    league = Column(String(128))
    team = Column(String(128), nullable=True)
    event_time = Column(DateTime, default=datetime.utcnow, index=True)
    minute = Column(Integer, nullable=True)
    delta_odds = Column(Float, nullable=True)
    intensity = Column(Float, nullable=True)


Base.metadata.create_all(bind=engine)

# --------------------------------------------------
# ROUTES
# --------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "vapid_public": VAPID_PUBLIC_KEY, "push_enabled": PUSH_ENABLED},
    )


@app.get("/heatmap", response_class=HTMLResponse)
async def heatmap_page(request: Request):
    return templates.TemplateResponse("heatmap.html", {"request": request})


@app.get("/status/push")
async def status_push(db: Session = Depends(get_db)):
    subs = db.query(PushSubscription).count()
    return {"enabled": PUSH_ENABLED, "subscriptions": subs, "vapid_public": bool(VAPID_PUBLIC_KEY)}


@app.get("/status/heatmap")
async def status_heatmap(db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=1)
    cnt = db.query(SmartMoneyAlert).filter(SmartMoneyAlert.event_time >= since).count()
    return {"last24h_alerts": cnt}


@app.post("/push/subscribe")
async def push_subscribe(payload: dict, request: Request, db: Session = Depends(get_db)):
    if not PUSH_ENABLED:
        raise HTTPException(status_code=400, detail="Push disabled")

    endpoint = payload.get("endpoint")
    keys = payload.get("keys", {})
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")
    ua = request.headers.get("User-Agent", "-")

    if not endpoint or not p256dh or not auth:
        raise HTTPException(status_code=400, detail="Invalid payload")

    existing = db.query(PushSubscription).filter(PushSubscription.endpoint == endpoint).first()
    if existing:
        existing.p256dh = p256dh
        existing.auth = auth
        existing.user_agent = ua
    else:
        db.add(PushSubscription(endpoint=endpoint, p256dh=p256dh, auth=auth, user_agent=ua))
    db.commit()
    return {"ok": True}


@app.post("/send_push")
async def send_push(payload: dict, db: Session = Depends(get_db)):
    if not PUSH_ENABLED:
        raise HTTPException(status_code=400, detail="Push disabled")
    if not (VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY):
        raise HTTPException(status_code=400, detail="Missing VAPID keys")

    title = payload.get("title", "EURO_GOALS")
    body = payload.get("body", "")
    url = payload.get("url", "/")
    tag = payload.get("tag", "eurogoals")

    data = {"title": title, "body": body, "url": url, "tag": tag}
    vapid = {
        "vapid_private_key": VAPID_PRIVATE_KEY,
        "vapid_claims": {"sub": VAPID_CONTACT},
    }

    errors = 0
    subs = db.query(PushSubscription).all()
    for s in subs:
        try:
            sub_info = {"endpoint": s.endpoint, "keys": {"p256dh": s.p256dh, "auth": s.auth}}
            webpush(subscription_info=sub_info, data=json.dumps(data), **vapid)
        except WebPushException:
            errors += 1
    return {"sent": len(subs) - errors, "errors": errors, "total": len(subs)}


@app.get("/api/heatmap_data")
async def api_heatmap_data(db: Session = Depends(get_db), days: int = 2, bucket: int = 5):
    since = datetime.utcnow() - timedelta(days=days)
    alerts = db.query(SmartMoneyAlert).filter(SmartMoneyAlert.event_time >= since).all()

    heat_index = {}

    def bucketize_minute(a: SmartMoneyAlert) -> int:
        if a.minute is not None:
            return max(0, min(95, a.minute))
        t = a.event_time or datetime.utcnow()
        return (t.hour * 60 + t.minute) % 96

    for a in alerts:
        key = (a.match_id or "-"), bucketize_minute(a)
        weight = a.intensity if a.intensity else (abs(a.delta_odds) if a.delta_odds else 1.0)
        heat_index[key] = heat_index.get(key, 0.0) + float(weight)

    match_ids = sorted(list({k[0] for k in heat_index.keys()}))
    minutes = list(range(0, 96))
    matrix = [[round(heat_index.get((mid, m), 0.0), 3) for m in minutes] for mid in match_ids]

    return {
        "x": minutes,
        "y": match_ids,
        "z": matrix,
        "meta": {"since": since.isoformat() + "Z", "alerts": len(alerts)},
    }


@app.get("/health")
async def health():
    return {"ok": True, "ts": datetime.utcnow().isoformat() + "Z"}
from fastapi.responses import FileResponse
import os

@app.get("/health")
async def health():
    return {"ok": True, "ts": datetime.utcnow().isoformat() + "Z"}

@app.get("/service-worker.js")
async def service_worker():
    file_path = os.path.join("static", "service-worker.js")
    return FileResponse(file_path, media_type="application/javascript")
