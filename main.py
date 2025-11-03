# ============================================================
# EURO_GOALS v9.4.3 PRO+ – Main Application
# Push (VAPID) + AI Analyzer + Mini Charts
# ============================================================

from fastapi import FastAPI, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime
from pywebpush import webpush, WebPushException
import os, threading, json, platform

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_EMAIL = os.getenv("VAPID_EMAIL", "mailto:you@example.com")

app = FastAPI(title="EURO_GOALS v9.4.3 PRO+")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# ------------------------ PAGES ------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/alert_history", response_class=HTMLResponse)
def alert_history(request: Request):
    return templates.TemplateResponse("alert_history.html", {"request": request})

@app.get("/smartmoney/logs", response_class=HTMLResponse)
def smartmoney_logs(request: Request):
    try:
        log_path = "logs/smartmoney_log.json"
        logs = json.load(open(log_path, "r", encoding="utf-8")) if os.path.exists(log_path) else []
        return templates.TemplateResponse("smartmoney_logs.html", {"request": request, "logs": logs})
    except Exception as e:
        return HTMLResponse(f"<h3>Error reading logs: {e}</h3>")

# Serve service worker at scope "/"
@app.get("/sw.js")
def sw():
    return FileResponse("static/js/sw.js", media_type="application/javascript")

# ------------------------ HEALTH ------------------------
@app.get("/health", response_class=JSONResponse)
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "error": str(e)}

# ------------------------ SMARTMONEY (demo JSON for UI) ------------------------
@app.get("/smartmoney/history", response_class=JSONResponse)
def get_smartmoney_history(limit: int = 100):
    """
    Demo JSON. Στην παραγωγή αντικαθίσταται από πραγματικά alerts (DB ή in-memory).
    """
    sample = [{
        "ts_utc": datetime.utcnow().isoformat(),
        "home": "Chelsea", "away": "Arsenal",
        "bookmaker": "Pinnacle", "market": "1X2", "selection": "1",
        "old_price": 1.92, "new_price": 1.78, "change_pct": -0.072, "source": "TheOddsAPI"
    }]
    return {"items": sample[:limit]}

# ------------------------ AI ANALYZER ------------------------
from backend.smartmoney_ai import analyze_alerts

@app.post("/smartmoney/analyze", response_class=JSONResponse)
def smartmoney_analyze(payload: dict = Body(...)):
    alerts = payload.get("alerts", [])
    top = int(payload.get("top", 10))
    result = analyze_alerts(alerts, top_n=top)
    return {"items": result}

# ------------------------ LOCAL NOTIFIER STARTUP ------------------------
def start_local_notifier():
    try:
        if platform.system().lower() != "windows":
            print("[SmartMoney PRO+] Local notifier skipped (non-Windows).")
            return
        from backend.smartmoney_notifier_proplus import start_local_notifier as run_notifier
        t = threading.Thread(target=run_notifier, daemon=True)
        t.start()
        print("[SmartMoney PRO+] ✅ Local notifier (Real APIs) started.")
    except Exception as e:
        print("[SmartMoney PRO+] ⚠️ Failed to start local notifier:", e)

# ------------------------ PUSH ENDPOINTS ------------------------
PUSH_DB = "data/push_subs.json"
os.makedirs("data", exist_ok=True)
if not os.path.exists(PUSH_DB):
    json.dump([], open(PUSH_DB, "w", encoding="utf-8"))

@app.get("/push/public_key", response_class=JSONResponse)
def push_public_key():
    return {"publicKey": VAPID_PUBLIC_KEY}

@app.post("/push/subscribe", response_class=JSONResponse)
def push_subscribe(payload: dict = Body(...)):
    subs = json.load(open(PUSH_DB, "r", encoding="utf-8"))
    # avoid duplicates
    if payload not in subs:
        subs.append(payload)
        json.dump(subs, open(PUSH_DB, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return {"ok": True, "count": len(subs)}

@app.post("/push/test", response_class=JSONResponse)
def push_test():
    subs = json.load(open(PUSH_DB, "r", encoding="utf-8"))
    vapid_claims = {"sub": VAPID_EMAIL}
    sent = 0
    for s in subs:
        try:
            webpush(
                subscription_info=s,
                data=json.dumps({"title": "EURO_GOALS", "body": "Test SmartMoney push", "url": "/smartmoney/logs"}),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=vapid_claims,
            )
            sent += 1
        except WebPushException as e:
            print("[PUSH] Error:", e)
    return {"ok": True, "sent": sent}

# ------------------------ STARTUP ------------------------
@app.on_event("startup")
def startup_event():
    print("💡 [EURO_GOALS] v9.4.3 PRO+ start …")
    start_local_notifier()
    print("💰 [SmartMoney] PRO+ active.")
    print("✅ Ready.")

# ------------------------ DEV RUN ------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
