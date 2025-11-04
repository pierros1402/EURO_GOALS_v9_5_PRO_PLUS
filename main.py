# ===============================================================
# EURO_GOALS v9.4.4 PRO+ — Main Application (FULL)
# ===============================================================

import os
import io
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, List

import pandas as pd
import requests
import httpx

from fastapi import FastAPI, Request, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from dotenv import load_dotenv
from pywebpush import webpush, WebPushException

# Local modules (δίπλα στο main.py)
from database import SessionLocal, engine, Base
from models import SmartMoneyAlert, PushSubscription

# ===============================================================
# ENV / CONFIG
# ===============================================================

load_dotenv()

def _clean(v: str) -> str:
    return (v or "").strip().strip("'").strip('"')

APP_NAME = os.getenv("APP_NAME", "EURO_GOALS v9.4.4 PRO+")
PUSH_ENABLED = os.getenv("PUSH_ENABLED", "false").lower() == "true"

VAPID_PUBLIC_KEY  = _clean(os.getenv("VAPID_PUBLIC_KEY", ""))
VAPID_PRIVATE_KEY = _clean(os.getenv("VAPID_PRIVATE_KEY", ""))
VAPID_CONTACT     = _clean(os.getenv("VAPID_CONTACT") or os.getenv("VAPID_EMAIL") or "mailto:admin@eurogoals.local")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

RENDER_API_KEY     = os.getenv("RENDER_API_KEY", "")
RENDER_SERVICE_ID  = os.getenv("RENDER_SERVICE_ID", "")
RENDER_HEALTH_URL  = os.getenv("RENDER_HEALTH_URL", "")

SMARTMONEY_INTERVAL_SEC = int(os.getenv("SMARTMONEY_REFRESH_INTERVAL", "60"))
SMARTMONEY_THRESHOLD    = float(os.getenv("SMARTMONEY_THRESHOLD", "0.20"))

AUDIO_ALERTS = os.getenv("AUDIO_ALERTS", "false").lower() == "true"

# ===============================================================
# APP INIT
# ===============================================================

Base.metadata.create_all(bind=engine)

app = FastAPI(title=APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ===============================================================
# DB DEPENDENCY + FALLBACK PROBES
# ===============================================================

def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    except SQLAlchemyError as e:
        # Fallback σφάλμα DB (αν remote σκάσει, έχουμε ήδη sqlite default)
        print(f"[DB][ERR] {e}")
        raise HTTPException(status_code=500, detail="Database connection error")
    finally:
        if db:
            db.close()

def db_ok() -> bool:
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print("[DB][ERR] health:", e)
        return False

# ===============================================================
# UTILS
# ===============================================================

def playsound_safe():
    """Παίζει ήχο ειδοποίησης αν ενεργοποιηθεί στα env."""
    if not AUDIO_ALERTS:
        return
    try:
        from playsound import playsound
        sound = os.path.join("static", "sounds", "notify.mp3")
        if os.path.exists(sound):
            threading.Thread(target=playsound, args=(sound,), daemon=True).start()
    except Exception as e:
        print("[AUDIO][WARN]", e)

def now_utc():
    return datetime.utcnow()

# ===============================================================
# PAGES
# ===============================================================

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/heatmap", response_class=HTMLResponse)
def heatmap_page(request: Request):
    return templates.TemplateResponse("heatmap.html", {"request": request})

@app.get("/alerts", response_class=HTMLResponse)
def alerts_page(request: Request):
    return templates.TemplateResponse("alert_history.html", {"request": request})

# ===============================================================
# HEALTH + SYSTEM STATUS
# ===============================================================

@app.get("/health")
def health():
    return {
        "ok": True,
        "ts": now_utc().isoformat() + "Z",
        "db": db_ok(),
        "push_enabled": PUSH_ENABLED,
        "auto_interval": SMARTMONEY_INTERVAL_SEC,
        "render_health": RENDER_HEALTH_URL or None
    }

# system_summary_bar endpoints (χρησιμοποιούνται από /static/js/system_summary.js)
@app.get("/status/health")
def status_health():
    return {"ok": True, "ts": now_utc().isoformat() + "Z"}

@app.get("/status/auto")
def status_auto():
    return {"interval": SMARTMONEY_INTERVAL_SEC, "enabled": True}

@app.get("/status/smartmoney")
def status_smartmoney(db: Session = Depends(get_db)):
    # τελευταία 5 alerts
    last = db.query(SmartMoneyAlert).order_by(SmartMoneyAlert.id.desc()).limit(5).all()
    return {"recent": len(last), "threshold": SMARTMONEY_THRESHOLD}

@app.get("/status/render")
def status_render():
    if not RENDER_HEALTH_URL:
        return {"ok": None}
    try:
        r = requests.get(RENDER_HEALTH_URL, timeout=5)
        return {"ok": r.ok, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/status/push")
def status_push():
    return {"enabled": PUSH_ENABLED, "has_keys": bool(VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY)}

# ===============================================================
# SMARTMONEY — API
# ===============================================================

def _fake_smartmoney_scan() -> List[dict]:
    """
    Demo scanner – αντικατέστησέ το με πραγματικά odds/feeds.
    Επιστρέφει λίστα από "ευρήματα" όταν παρατηρείται μεταβολή > threshold.
    """
    # Παράγει τυχαία ένα alert ανά ~2-3 κύκλους:
    import random
    if random.random() < 0.35:
        minute = random.randint(0, 95)
        delta = round(random.uniform(SMARTMONEY_THRESHOLD, SMARTMONEY_THRESHOLD + 0.25), 3)
        return [{
            "match_id": f"M-{100 + random.randint(1, 50)}",
            "league": "DEMO",
            "team": "TeamA",
            "event_time": now_utc() - timedelta(minutes=random.randint(0, 60)),
            "minute": minute,
            "delta_odds": delta,
            "intensity": round(1.0 + delta, 3)
        }]
    return []

def _store_alerts(db: Session, alerts: List[dict]) -> int:
    cnt = 0
    for a in alerts:
        obj = SmartMoneyAlert(
            match_id=a["match_id"],
            league=a["league"],
            team=a["team"],
            event_time=a["event_time"],
            minute=a["minute"],
            delta_odds=a["delta_odds"],
            intensity=a["intensity"],
        )
        db.add(obj)
        cnt += 1
    db.commit()
    return cnt

def _push_alert(title: str, body: str, url: str = "/heatmap"):
    if not PUSH_ENABLED or not (VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY and VAPID_CONTACT):
        return
    data = {"title": title, "body": body, "url": url, "tag": "eurogoals"}
    # στέλνουμε σε όλους τους εγγεγραμμένους
    db = SessionLocal()
    subs = db.query(PushSubscription).all()
    for s in subs:
        try:
            sub_info = {"endpoint": s.endpoint, "keys": {"p256dh": s.p256dh, "auth": s.auth}}
            webpush(
                subscription_info=sub_info,
                data=json.dumps(data),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_CONTACT},
            )
        except WebPushException as e:
            resp = getattr(e, "response", None)
            print(f"[PUSH][ERR] {e} | {resp and resp.text}")
    db.close()

# background loop
_bg_stop = False

def _smartmoney_loop():
    global _bg_stop
    print(f"[SMARTMONEY] loop started (interval={SMARTMONEY_INTERVAL_SEC}s, threshold={SMARTMONEY_THRESHOLD})")
    while not _bg_stop:
        try:
            findings = _fake_smartmoney_scan()
            if findings:
                db = SessionLocal()
                saved = _store_alerts(db, findings)
                db.close()
                msg = f"{saved} SmartMoney alert(s) stored"
                print("[SMARTMONEY]", msg)
                playsound_safe()
                _push_alert("SmartMoney Alert", msg, "/heatmap")
        except Exception as e:
            print("[SMARTMONEY][ERR]", e)
        time.sleep(SMARTMONEY_INTERVAL_SEC)

# ===============================================================
# ALERT HISTORY (filter + refresh)
# ===============================================================

@app.get("/api/alerts")
def api_alerts(
    days: int = Query(2, ge=1, le=30),
    league: Optional[str] = None,
    team: Optional[str] = None,
    db: Session = Depends(get_db),
):
    since = now_utc() - timedelta(days=days)
    q = db.query(SmartMoneyAlert).filter(SmartMoneyAlert.event_time >= since)
    if league:
        q = q.filter(SmartMoneyAlert.league == league)
    if team:
        q = q.filter(SmartMoneyAlert.team == team)
    rows = q.order_by(SmartMoneyAlert.event_time.desc()).limit(500).all()

    def _row(a: SmartMoneyAlert):
        return {
            "id": a.id,
            "match_id": a.match_id,
            "league": a.league,
            "team": a.team,
            "event_time": a.event_time.isoformat() if a.event_time else None,
            "minute": a.minute,
            "delta_odds": a.delta_odds,
            "intensity": a.intensity,
        }
    return {"alerts": [_row(r) for r in rows]}

# ===============================================================
# HEATMAP DATA (για /static/js/heatmap.js)
# ===============================================================

@app.get("/api/heatmap_data")
def api_heatmap_data(days: int = 2, bucket: int = 5, db: Session = Depends(get_db)):
    since = now_utc() - timedelta(days=days)
    alerts = db.query(SmartMoneyAlert).filter(SmartMoneyAlert.event_time >= since).all()

    # φτιάχνουμε 96 buckets (0..95) λεπτών
    minutes = list(range(0, 96))
    match_ids = sorted({a.match_id for a in alerts})

    index = {(a.match_id, min(95, (a.minute or 0))): (a.intensity or 0.0) for a in alerts}
    matrix = [[round(index.get((mid, m), 0.0), 3) for m in minutes] for mid in match_ids]

    return {
        "x": minutes,
        "y": match_ids,
        "z": matrix,
        "meta": {"since": since.isoformat() + "Z", "alerts": len(alerts)},
    }

# ===============================================================
# PUSH — PUBLIC KEY / SUBSCRIBE / SEND TEST
# ===============================================================

@app.get("/push/public_key")
def push_public_key():
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=400, detail="Missing VAPID public key")
    return {"publicKey": VAPID_PUBLIC_KEY}

@app.post("/push/subscribe")
async def push_subscribe(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    endpoint = data.get("endpoint")
    keys = data.get("keys", {})
    if not endpoint or "p256dh" not in keys or "auth" not in keys:
        raise HTTPException(status_code=400, detail="Invalid subscription")
    exists = db.query(PushSubscription).filter(PushSubscription.endpoint == endpoint).first()
    if not exists:
        db.add(PushSubscription(endpoint=endpoint, p256dh=keys["p256dh"], auth=keys["auth"]))
        db.commit()
    return {"ok": True}

@app.post("/send_push")
async def send_push(payload: dict, db: Session = Depends(get_db)):
    if not PUSH_ENABLED:
        raise HTTPException(status_code=400, detail="Push disabled")
    if not (VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY and VAPID_CONTACT):
        raise HTTPException(status_code=400, detail="Missing VAPID config")

    title = payload.get("title", "EURO_GOALS")
    body  = payload.get("body", "")
    url   = payload.get("url", "/")
    data  = {"title": title, "body": body, "url": url, "tag": "eurogoals"}

    subs = db.query(PushSubscription).all()
    sent = 0
    errors = 0
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
            print(f"[PUSH][ERR] {e} | {resp and resp.text}")
    return {"sent": sent, "errors": errors, "total": len(subs)}

# ===============================================================
# BACKUP MANAGER (manual + monthly)
# ===============================================================

BACKUP_DIR = os.path.join("backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

def _backup_filename(ts: datetime = None) -> str:
    ts = ts or now_utc()
    return os.path.join(BACKUP_DIR, f"EURO_GOALS_BACKUP_{ts:%Y_%m}.sql")

def _sqlite_dump() -> bytes:
    # μόνο για sqlite dump (για Postgres θα έβαζες pg_dump)
    import sqlite3
    if not DATABASE_URL.startswith("sqlite"):
        # απλό JSON export για demo
        db = SessionLocal()
        rows = db.query(SmartMoneyAlert).limit(10000).all()
        db.close()
        buf = io.StringIO()
        json.dump([{"id": r.id, "match_id": r.match_id} for r in rows], buf)
        return buf.getvalue().encode("utf-8")

    path = DATABASE_URL.replace("sqlite:///", "")
    con = sqlite3.connect(path)
    buf = io.StringIO()
    for line in con.iterdump():
        buf.write(f"{line}\n")
    con.close()
    return buf.getvalue().encode("utf-8")

@app.post("/backup/trigger")
def backup_trigger():
    try:
        data = _sqlite_dump()
        fname = _backup_filename()
        with open(fname, "wb") as f:
            f.write(data)
        return {"ok": True, "file": fname, "size": len(data)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/backup/download")
def backup_download():
    fname = _backup_filename()
    if not os.path.exists(fname):
        raise HTTPException(status_code=404, detail="no backup for current month")
    return FileResponse(fname, media_type="application/sql", filename=os.path.basename(fname))

def _monthly_backup_daemon():
    while True:
        try:
            # τρέχει κάθε μέρα στις 02:05 UTC και κρατά τον τρέχοντα μήνα
            now = now_utc()
            if now.hour == 2 and now.minute == 5:
                print("[BACKUP] running monthly backup...")
                backup_trigger()
                time.sleep(70)  # μην ξανατρέξει στο ίδιο λεπτό
        except Exception as e:
            print("[BACKUP][ERR]", e)
        time.sleep(30)

# ===============================================================
# AUTO-REFRESH / RENDER MONITOR (βοηθητικά)
# ===============================================================

@app.get("/render/health")
def render_health():
    if not RENDER_HEALTH_URL:
        return {"ok": None}
    try:
        r = requests.get(RENDER_HEALTH_URL, timeout=5)
        return {"ok": r.ok, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ===============================================================
# STARTUP
# ===============================================================

@app.on_event("startup")
def startup_event():
    print("🚀 EURO_GOALS v9.4.4 PRO+ started successfully")
    print(f"💬 Push notifications {'ENABLED' if PUSH_ENABLED else 'DISABLED'}")
    # background loops
    threading.Thread(target=_smartmoney_loop, daemon=True).start()
    threading.Thread(target=_monthly_backup_daemon, daemon=True).start()
    # εδώ hook για multi-league refresh στο startup (placeholder)
    try:
        print("[STARTUP] multi-league refresh… (placeholder)")
    except Exception as e:
        print("[STARTUP][ERR] multi-league:", e)

# ===============================================================
# SHUTDOWN
# ===============================================================

@app.on_event("shutdown")
def on_shutdown():
    global _bg_stop
    _bg_stop = True
    print("👋 shutdown requested")
