# ============================================================
# EURO_GOALS v9.5.3 PRO+ Smart Monitor
# Main Application File (FastAPI)
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import time

# ============================================================
# APP SETTINGS
# ============================================================

APP_VERSION = "EURO_GOALS v9.5.2 PRO+ Smart Monitor"
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

# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/api/alerts_feed")
async def alerts_feed():
    """Placeholder alerts feed."""
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
# STARTUP MESSAGE
# ============================================================
@app.on_event("startup")
def startup_event():
    print(f"[EURO_GOALS] 🚀 Application started: {APP_VERSION}")
