# ===============================================================
# EURO_GOALS v9.4.4 PRO+  —  Main Application
# ===============================================================

import os
import json
import pandas as pd
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from pywebpush import webpush, WebPushException

from database import SessionLocal, engine, Base
from models import PushSubscription

# ===============================================================
# INITIALIZATION
# ===============================================================

load_dotenv()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="EURO_GOALS v9.4.4 PRO+")

# Static & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ---------------------------------------------------------------
# Helper: καθαρισμός env strings
# ---------------------------------------------------------------
def _clean(v: str) -> str:
    return (v or "").strip().strip("'").strip('"')

# ---------------------------------------------------------------
# Load ENV variables
# ---------------------------------------------------------------
PUSH_ENABLED = os.getenv("PUSH_ENABLED", "false").lower() == "true"
VAPID_PUBLIC_KEY = _clean(os.getenv("VAPID_PUBLIC_KEY"))
VAPID_PRIVATE_KEY = _clean(os.getenv("VAPID_PRIVATE_KEY"))
VAPID_CONTACT = _clean(
    os.getenv("VAPID_CONTACT")
    or os.getenv("VAPID_EMAIL")
    or "mailto:admin@eurogoals.local"
)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

# ---------------------------------------------------------------
# CORS (αν χρειαστεί να κάνεις fetch από άλλες πηγές)
# ---------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------
# Database Dependency
# ---------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===============================================================
# ROUTES – CORE
# ===============================================================

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
def health():
    return {"status": "OK", "push_enabled": PUSH_ENABLED}

# ===============================================================
# ROUTES – PUSH NOTIFICATIONS
# ===============================================================

@app.get("/push/public_key")
def push_public_key():
    """Στέλνει το public VAPID key στον browser"""
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=400, detail="Missing VAPID public key")
    return {"publicKey": VAPID_PUBLIC_KEY}


@app.post("/push/subscribe")
async def push_subscribe(request: Request, db: Session = Depends(get_db)):
    """Αποθηκεύει το subscription του browser"""
    data = await request.json()
    endpoint = data.get("endpoint")
    keys = data.get("keys", {})

    if not endpoint or "p256dh" not in keys or "auth" not in keys:
        raise HTTPException(status_code=400, detail="Invalid subscription")

    # Έλεγχος αν υπάρχει ήδη
    existing = db.query(PushSubscription).filter(PushSubscription.endpoint == endpoint).first()
    if not existing:
        sub = PushSubscription(endpoint=endpoint, p256dh=keys["p256dh"], auth=keys["auth"])
        db.add(sub)
        db.commit()

    print("[PUSH] ✅ Subscription saved")
    return {"ok": True}


@app.post("/send_push")
async def send_push(payload: dict, db: Session = Depends(get_db)):
    """Αποστολή push σε όλους τους εγγεγραμμένους browsers"""
    if not PUSH_ENABLED:
        raise HTTPException(status_code=400, detail="Push disabled")
    if not (VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY and VAPID_CONTACT):
        raise HTTPException(status_code=400, detail="Missing VAPID config")

    title = payload.get("title", "EURO_GOALS")
    body = payload.get("body", "")
    url = payload.get("url", "/")
    tag = payload.get("tag", "eurogoals")

    data = {"title": title, "body": body, "url": url, "tag": tag}

    subs = db.query(PushSubscription).all()
    sent, errors = 0, 0

    for s in subs:
        try:
            sub_info = {"endpoint": s.endpoint, "keys": {"p256dh": s.p256dh, "auth": s.auth}}
            webpush(
                subscription_info=sub_info,
                data=json.dumps(data),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_CONTACT},
            )
            sent += 1
        except WebPushException as e:
            errors += 1
            resp = getattr(e, "response", None)
            try:
                print(f"[PUSH][ERR] {e} | resp={resp and resp.text}")
            except Exception:
                print(f"[PUSH][ERR] {e}")

    print(f"[PUSH] ✅ Sent={sent}, Errors={errors}, Total={len(subs)}")
    return {"sent": sent, "errors": errors, "total": len(subs)}

# ===============================================================
# STARTUP LOG
# ===============================================================
@app.on_event("startup")
def startup_event():
    print("🚀 EURO_GOALS v9.4.4 PRO+ started successfully")
    if PUSH_ENABLED:
        print("💬 Push notifications ENABLED")
    else:
        print("💬 Push notifications DISABLED")

# ===============================================================
# END OF FILE
# ===============================================================
