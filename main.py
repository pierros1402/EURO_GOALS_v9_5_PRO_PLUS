# ============================================================
# EURO_GOALS v9.6.8 PRO+ — UNIFIED MATCHPLAN + STANDINGS SYSTEM + PWA Health Check
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio, os, sys, time, requests

print("=== [EURO_GOALS] Unified App 9.6.8 PRO+ — AUTO-REFRESH PWA ACTIVE ===")

# ------------------------------------------------------------
# SYSTEM PATH FIX
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# ------------------------------------------------------------
# IMPORT ENGINES
# ------------------------------------------------------------
from services import (
    history_engine,
    matchplan_engine,
    standings_engine
)
from services.leagues_list import LEAGUES, EURO_COMPETITIONS

# ------------------------------------------------------------
# OPTIONAL LIVE PROXY (Cloudflare)
# ------------------------------------------------------------
LIVE_PROXY_URL = os.getenv("LIVE_PROXY_URL", "https://eurogoals-live-proxy.pierros1402.workers.dev/live")

def get_live_data():
    """Retrieve unified live feed from Cloudflare Worker"""
    try:
        r = requests.get(LIVE_PROXY_URL, timeout=6)
        return r.json() if r.status_code == 200 else {"status": "error", "code": r.status_code}
    except Exception as e:
        return {"status": "offline", "error": str(e)}

# ------------------------------------------------------------
# FASTAPI APP SETUP
# ------------------------------------------------------------
APP_VERSION = "9.6.8 PRO+ — Auto-Refresh PWA"
app = FastAPI(title=f"EURO_GOALS {APP_VERSION}")

STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ------------------------------------------------------------
# MAIN PAGES
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "version": APP_VERSION})

@app.get("/plan", response_class=HTMLResponse)
async def plan_page(request: Request):
    return templates.TemplateResponse("plan.html", {"request": request, "version": APP_VERSION})

@app.get("/standings", response_class=HTMLResponse)
async def standings_page(request: Request):
    return templates.TemplateResponse("standings_panel.html", {"request": request, "version": APP_VERSION})

@app.get("/history_unified", response_class=HTMLResponse)
async def history_page(request: Request):
    return templates.TemplateResponse("history_unified.html", {"request": request, "version": APP_VERSION})

# ------------------------------------------------------------
# ✅ PWA HEALTH CHECK PAGE
# ------------------------------------------------------------
@app.get("/pwa_health_check", response_class=HTMLResponse)
async def pwa_health_check(request: Request):
    return templates.TemplateResponse("pwa_health_check.html", {"request": request, "version": APP_VERSION})

# ------------------------------------------------------------
# API ENDPOINTS
# ------------------------------------------------------------
@app.get("/api/live")
async def api_live_proxy():
    return JSONResponse(get_live_data())

@app.get("/api/history")
async def api_history(source: str = "flashscore"):
    return await history_engine.get_history(source)

@app.get("/api/matchplan")
async def api_matchplan():
    return await matchplan_engine.get_matchplan_15d()

@app.get("/api/standings")
async def api_standings():
    return await standings_engine.get_standings()

@app.get("/api/leagues")
async def api_leagues():
    """Επιστρέφει τη λίστα όλων των λιγκών και διοργανώσεων."""
    return {
        "version": APP_VERSION,
        "total_leagues": len(LEAGUES),
        "total_competitions": len(EURO_COMPETITIONS),
        "leagues": LEAGUES,
        "euro_competitions": EURO_COMPETITIONS
    }

# ------------------------------------------------------------
# SYSTEM CHECK ENDPOINT
# ------------------------------------------------------------
@app.get("/api/system/check", response_class=JSONResponse)
async def api_system_check():
    data = {
        "version": APP_VERSION,
        "timestamp": int(time.time()),
        "status": "online",
        "engines": {
            "history_engine": "ok",
            "matchplan_engine": "ok",
            "standings_engine": "ok"
        }
    }
    return data

# ------------------------------------------------------------
# STARTUP EVENTS
# ------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    print(f"[EURO_GOALS] 🚀 App v{APP_VERSION} launched")
    try:
        asyncio.create_task(history_engine.background_refresher())
        asyncio.create_task(matchplan_engine.background_refresher())
        asyncio.create_task(standings_engine.background_refresher())
    except Exception as e:
        print(f"[EURO_GOALS] ⚠️ Startup refresher error: {e}")

# ------------------------------------------------------------
# LOCAL RUN (for manual testing)
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
