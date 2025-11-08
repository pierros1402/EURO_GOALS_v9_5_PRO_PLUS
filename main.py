# ============================================================
# EURO_GOALS v9.5.0 PRO+ UNIFIED MAIN APP
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import time, os

# ------------------------------------------------------------
# Βασική ρύθμιση εφαρμογής
# ------------------------------------------------------------
APP_VERSION = "9.5.0 PRO+"
app = FastAPI(title=f"EURO_GOALS v{APP_VERSION}")

# ------------------------------------------------------------
# Σύνδεση φακέλων στατικών & templates
# ------------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ============================================================
# MAIN PAGE (Jinja2 template)
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "version": APP_VERSION,
            "timestamp": time.strftime("%H:%M:%S")
        }
    )

# ============================================================
# HEALTH ENDPOINT
# ============================================================

@app.get("/health")
async def render_health():
    """Render health check"""
    return {"status": "ok", "timestamp": time.strftime("%H:%M:%S")}

# ============================================================
# BACKUP STATUS ENDPOINT
# ============================================================

@app.get("/backup_status")
async def backup_status():
    """Backup readiness endpoint"""
    return JSONResponse({
        "backup_ready": True,
        "last_checked": time.strftime("%Y-%m-%d %H:%M:%S")
    })

# ============================================================
# SMARTMONEY MONITOR ENDPOINT
# ============================================================

@app.get("/smartmoney_monitor", response_class=HTMLResponse)
async def smartmoney_monitor(request: Request):
    """SmartMoney monitor page"""
    return templates.TemplateResponse(
        "smartmoney_monitor.html",
        {"request": request, "version": APP_VERSION}
    )

# ============================================================
# SYSTEM STATUS ENDPOINTS
# ============================================================

@app.get("/system_status_data")
async def system_status_data():
    """JSON system status"""
    return {
        "version": APP_VERSION,
        "status": "active",
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/system_status_html", response_class=HTMLResponse)
async def system_status_html(request: Request):
    """HTML Unified Dashboard"""
    return templates.TemplateResponse(
        "system_status_html.html",
        {"request": request, "version": APP_VERSION}
    )

# ============================================================
# Εκκίνηση εφαρμογής (Render)
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
