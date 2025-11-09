# ============================================================
# EURO_GOALS v9.5.4 PRO+ UNIFIED MAIN APP
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
import time
import os
print("=== [EURO_GOALS] Unified App 9.5.4 PRO+ — FULL DEPLOY ACTIVE ===")

# ------------------------------------------------------------
# Εσωτερικές υπηρεσίες (Render + Local compatibility)
# ------------------------------------------------------------
try:
    from app.services import smartmoney_engine
except ModuleNotFoundError:
    from services import smartmoney_engine

# ------------------------------------------------------------
# Ρυθμίσεις εφαρμογής
# ------------------------------------------------------------
APP_VERSION = "9.5.4 PRO+"
app = FastAPI(title=f"EURO_GOALS {APP_VERSION}")

# ------------------------------------------------------------
# Στατικά αρχεία & templates
# ------------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ============================================================
# MAIN DASHBOARD
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "version": APP_VERSION}
    )

# ============================================================
# SMARTMONEY MONITOR PAGE
# ============================================================
@app.get("/smartmoney_monitor", response_class=HTMLResponse)
async def smartmoney_monitor(request: Request):
    """Σελίδα παρακολούθησης SmartMoney"""
    return templates.TemplateResponse(
        "smartmoney_monitor.html",
        {"request": request, "version": APP_VERSION}
    )

# ============================================================
# 🧠 SMARTMONEY API ENDPOINTS
# ============================================================

@app.get("/api/smartmoney/summary")
async def api_smartmoney_summary():
    """Επιστρέφει συνοπτικά στοιχεία SmartMoney"""
    return smartmoney_engine.cache.get_summary()

@app.get("/api/smartmoney/alerts")
async def api_smartmoney_alerts():
    """Επιστρέφει ενεργά alerts (πολλαπλές στοιχηματικές)"""
    return {"alerts": smartmoney_engine.cache.get_alerts()}

@app.get("/api/smartmoney_feed")
async def api_smartmoney_feed():
    """Feed για legacy ή νέα monitor views"""
    # επιστρέφει άμεσα λίστα (όχι {data: ...})
    return smartmoney_engine.cache.get_alerts()

# ============================================================
# HEALTH ENDPOINTS
# ============================================================
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "time": time.strftime("%H:%M:%S")
    }

@app.get("/system_status")
async def system_status():
    return {
        "version": APP_VERSION,
        "smartmoney_active": getattr(smartmoney_engine, "SMARTMONEY_ENABLED", True),
        "alerts": len(smartmoney_engine.cache.get_alerts())
    }

# ============================================================
# BACKGROUND TASK – SMARTMONEY REFRESHER
# ============================================================
@app.on_event("startup")
async def startup_event():
    print(f"[EURO_GOALS] 🚀 Εκκίνηση v{APP_VERSION}")
    try:
        asyncio.create_task(smartmoney_engine.background_refresher())
        print("💰 SMARTMONEY Engine background task started.")
    except Exception as e:
        print(f"[EURO_GOALS] ⚠️ Background init error: {e}")

# ============================================================
# DEBUG ROUTE — to verify correct instance
# ============================================================
@app.get("/__whoami")
def whoami():
    import os
    return {
        "version": APP_VERSION,
        "cwd": os.getcwd(),
        "templates_dir": os.path.abspath("templates"),
        "index_exists": os.path.exists("templates/index.html")
    }

# ============================================================
# LOCAL STARTUP
# ============================================================
if __name__ == "__main__":
    import uvicorn, os
    port = int(os.getenv("PORT", 8000))
    print(f"🏁 Running EURO_GOALS on 0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)

