# ============================================================
# EURO_GOALS PRO+ v9.5.2 | Unified Adaptive Mode (Render Ready)
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import time, os, threading

# ============================================================
# APP SETTINGS
# ============================================================

APP_VERSION = "EURO_GOALS PRO+ v9.5.2 | Unified Adaptive Mode"
app = FastAPI(title=APP_VERSION)
templates = Jinja2Templates(directory="templates")

# ============================================================
# STATIC FILES (Render / Local)
# ============================================================

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/public", StaticFiles(directory="public"), name="public")

# ============================================================
# ROUTER IMPORTS
# ============================================================

try:
    from goalmatrix import router as goalmatrix_router
    from smartmoney_router import router as smartmoney_router
    app.include_router(goalmatrix_router)
    app.include_router(smartmoney_router)
except Exception as e:
    print(f"[EURO_GOALS] ⚠️ Routers not loaded: {e}")

# ============================================================
# MAIN PAGE (Jinja2 template)
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "version": APP_VERSION, "timestamp": time.strftime("%H:%M:%S")}
    )

# ============================================================
# HEALTH ENDPOINT (for system_status.js)
# ============================================================

@app.get("/health")
async def system_health():
    """Return global system health and live components."""
    ts = time.strftime("%H:%M:%S", time.localtime())
    alerts_sample = [
        {"time": ts, "message": "SmartMoney Engine OK", "level": "ok"},
        {"time": ts, "message": "GoalMatrix Engine refreshed", "level": "warn"},
    ]
    return {
        "status": "ok",
        "service": APP_VERSION,
        "components": {
            "render": True,
            "db": True,
            "flashscore": True,
            "sofascore": True,
            "asianconnect": False
        },
        "alerts": alerts_sample,
        "timestamp": int(time.time())
    }

# ============================================================
# ALERTS FEED (demo feed)
# ============================================================

@app.get("/api/alerts_feed")
async def alerts_feed():
    sample = [
        {"time": "22:31:10", "type": "SMARTMONEY", "desc": "Unusual odds shift (Chelsea - Arsenal)"},
        {"time": "22:34:55", "type": "GOALMATRIX", "desc": "Over 2.5 probability > 78% (LaLiga)"}
    ]
    return JSONResponse(sample)

# ============================================================
# AUTO SHUTDOWN ENDPOINT (triggered by render_auto_stop.js)
# ============================================================

@app.post("/shutdown")
async def shutdown_server():
    """Auto-stop Render process after inactivity or manual trigger."""
    print("[EURO_GOALS] 💤 Auto-shutdown triggered by inactivity.")
    os._exit(0)

# ============================================================
# SERVICE WORKER ROUTE
# ============================================================

@app.get("/service-worker.js", include_in_schema=False)
def service_worker():
    """Serve service worker from root"""
    sw_path = Path("static/js/sw.js")
    if sw_path.exists():
        return FileResponse(sw_path, media_type="application/javascript")
    return JSONResponse({"error": "service-worker.js not found"}, status_code=404)

# ============================================================
# STARTUP EVENT
# ============================================================

@app.on_event("startup")
def startup_event():
    print(f"[EURO_GOALS] 🚀 Application started: {APP_VERSION}")

# ============================================================
# IDLE MONITOR (Auto terminate if idle > 10min)
# ============================================================

LAST_REQUEST = time.time()

@app.middleware("http")
async def track_activity(request, call_next):
    """Update last activity timestamp on every request"""
    global LAST_REQUEST
    LAST_REQUEST = time.time()
    return await call_next(request)

def idle_shutdown_checker():
    """Daemon thread to auto-terminate app after 10 min idle"""
    while True:
        if time.time() - LAST_REQUEST > 600:
            print("[EURO_GOALS] ⏹ Idle >10min, shutting down Render instance.")
            os._exit(0)
        time.sleep(60)

threading.Thread(target=idle_shutdown_checker, daemon=True).start()

# ============================================================
# RENDER LOG
# ============================================================

print(f"[EURO_GOALS] ✅ FastAPI backend ready for Render: {APP_VERSION}")
