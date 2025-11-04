# ==============================================
# EURO_GOALS v9.4.4 PRO+ – Main Application
# Push Notifications + SmartMoney Heatmap + Mock APIs
# ==============================================

from fastapi import FastAPI, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime
import os, json, platform, threading

# Optional (for Push) – if not installed in local dev, keeps app alive
try:
    from pywebpush import webpush, WebPushException
    HAS_WEBPUSH = True
except Exception:
    HAS_WEBPUSH = False

# ------------------------------------------------
# 1) Env & basic config
# ------------------------------------------------
load_dotenv()

DATABASE_URL        = os.getenv("DATABASE_URL", "sqlite:///matches.db")
VAPID_PRIVATE_KEY   = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY    = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_EMAIL         = os.getenv("VAPID_EMAIL", "mailto:you@example.com")

# ------------------------------------------------
# 2) App, static & templates
# ------------------------------------------------
app = FastAPI(title="EURO_GOALS v9.4.4 PRO+")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# ------------------------------------------------
# 3) Pages
# ------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/smartmoney/heatmap", response_class=HTMLResponse)
def heatmap_page(request: Request):
    return templates.TemplateResponse("smartmoney_heatmap.html", {"request": request})

# (προηγούμενες σελίδες – αν τις χρειάζεσαι)
@app.get("/alert/history", response_class=HTMLResponse)
def alert_history(request: Request):
    return templates.TemplateResponse("alert_history.html", {"request": request})

@app.get("/smartmoney/logs", response_class=HTMLResponse)
def smartmoney_logs(request: Request):
    # Δείχνει log viewer αν υπάρχει logs/smartmoney_log.json
    try:
        log_path = "logs/smartmoney_log.json"
        logs = json.load(open(log_path, "r", encoding="utf-8")) if os.path.exists(log_path) else []
        return templates.TemplateResponse("smartmoney_logs.html", {"request": request, "logs": logs})
    except Exception as e:
        return HTMLResponse(f"<h3>Error reading logs: {e}</h3>")

# ------------------------------------------------
# 4) Health
# ------------------------------------------------
@app.get("/health", response_class=JSONResponse)
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "error": str(e)}

# ------------------------------------------------
# 5) Service Worker route (served from /service-worker.js)
# ------------------------------------------------
@app.get("/service-worker.js")
def sw():
    return FileResponse("static/service-worker.js", media_type="application/javascript")

# ------------------------------------------------
# 6) Browser Push endpoints (VAPID)
# ------------------------------------------------
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
    if not (HAS_WEBPUSH and VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY):
        return {"ok": False, "reason": "webpush_not_configured"}
    subs = json.load(open(PUSH_DB, "r", encoding="utf-8"))
    sent = 0
    for s in subs:
        try:
            webpush(
                subscription_info=s,
                data=json.dumps({
                    "title": "EURO_GOALS",
                    "body": "Test SmartMoney push",
                    "url": "/smartmoney/heatmap"
                }),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_EMAIL},
            )
            sent += 1
        except WebPushException as e:
            print("[PUSH] error:", e)
    return {"ok": True, "sent": sent}

# ------------------------------------------------
# 7) SmartMoney demo data (history + heatmap)
# ------------------------------------------------
@app.get("/smartmoney/history", response_class=JSONResponse)
def get_smartmoney_history(limit: int = 100):
    # Demo/mock – αντικαθίσταται με real aggregator
    sample = [{
        "ts_utc": datetime.utcnow().isoformat(),
        "home": "Chelsea", "away": "Arsenal",
        "bookmaker": "Pinnacle", "market": "1X2", "selection": "1",
        "old_price": 1.92, "new_price": 1.78, "change_pct": -0.072, "source": "TheOddsAPI"
    }]
    return {"items": sample[:limit]}

@app.get("/smartmoney/heatmap/data", response_class=JSONResponse)
def heatmap_data():
    """
    Επιστρέφει mock πλέγμα μεταβολών:
    - matches: λίστα αγώνων
    - bookmakers: λίστα books
    - matrix: map[match][bookmaker] -> drop_pct (-0.12 = -12%)
    """
    matches = [
        "Chelsea–Arsenal", "Bayern–Dortmund", "PAO–AEK", "Inter–Juve", "Real–Barca"
    ]
    bookmakers = ["Pinnacle", "Bet365", "Stoiximan", "Betano", "Unibet"]
    # demo τυχαίες πτώσεις
    import random
    matrix = {}
    for m in matches:
        row = {}
        for b in bookmakers:
            drop = round(random.uniform(-0.15, 0.05), 3)  # -15% … +5%
            row[b] = drop
        matrix[m] = row
    return {"matches": matches, "bookmakers": bookmakers, "matrix": matrix, "ts": datetime.utcnow().isoformat()}

# ------------------------------------------------
# 8) Mock routes (για να μην βλέπεις 404 από παλιό JS)
# ------------------------------------------------
@app.get("/smartmoney/events", response_class=JSONResponse)
def mock_events():
    return {"events": []}

@app.get("/api/alerts/latest", response_class=JSONResponse)
def mock_latest():
    return {"latest": None}

@app.get("/system_status_data", response_class=JSONResponse)
def mock_status():
    return {"database": "connected", "health": "ok", "smartmoney": "live", "render": "active", "timestamp": datetime.utcnow().isoformat()}

# ------------------------------------------------
# 9) Startup (logs)
# ------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("=============================================")
    print("🚀 EURO_GOALS v9.4.4 PRO+ starting …")
    print("🔔 Push:", "enabled" if (HAS_WEBPUSH and VAPID_PUBLIC_KEY) else "disabled")
    print("💰 SmartMoney heatmap endpoint ready.")
    print("=============================================")

# ------------------------------------------------
# 10) Local run
# ------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
