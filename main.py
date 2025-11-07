# ============================================================
# EURO_GOALS v9.5.2 PRO+ | Smart Adaptive Mode (Compact Edition)
# Main Application File (FastAPI)
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import time, os

# ============================================================
# APP SETTINGS
# ============================================================

APP_VERSION = "EURO_GOALS v9.5.2 PRO+ | Smart Adaptive Mode"
app = FastAPI(title=APP_VERSION)
templates = Jinja2Templates(directory="templates")

# ============================================================
# STATIC FILES
# ============================================================
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============================================================
# ROUTES
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "version": APP_VERSION}
    )

# ------------------------------------------------------------
# SAMPLE API ENDPOINTS
# ------------------------------------------------------------

@app.get("/api/alerts_feed")
async def alerts_feed():
    """Demo alerts feed"""
    sample = [
        {"time": "22:31:10", "type": "SMARTMONEY", "desc": "Unusual odds shift (Chelsea - Arsenal)"},
        {"time": "22:34:55", "type": "GOALMATRIX", "desc": "Over 2.5 probability > 78% (LaLiga)"}
    ]
    return JSONResponse(sample)


@app.get("/health")
async def render_health_check():
    """Basic Render health check endpoint."""
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
        "timestamp": int(time.time())
    }

# ============================================================
# SHUTDOWN ENDPOINT (auto-stop από render_auto_stop.js)
# ============================================================

@app.post("/shutdown")
async def shutdown_server():
    """Auto-stop Render process after inactivity."""
    print("[EURO_GOALS] 💤 Auto-shutdown triggered by inactivity.")
    os._exit(0)

# ============================================================
# STARTUP MESSAGE
# ============================================================

@app.on_event("startup")
def startup_event():
    print(f"[EURO_GOALS] 🚀 Application started: {APP_VERSION}")

# ============================================================
# IDLE CHECKER (safety exit if Render keeps running forever)
# ============================================================

import threading

LAST_REQUEST = time.time()

@app.middleware("http")
async def track_activity(request, call_next):
    """Updates last activity timestamp on every request"""
    global LAST_REQUEST
    LAST_REQUEST = time.time()
    return await call_next(request)

def idle_shutdown_checker():
    """Daemon thread to auto-terminate app after 10 min idle"""
    while True:
        if time.time() - LAST_REQUEST > 600:  # 10 min inactivity
            print("[EURO_GOALS] ⏹ Idle >10 min, shutting down Render instance.")
            os._exit(0)
        time.sleep(60)

threading.Thread(target=idle_shutdown_checker, daemon=True).start()
