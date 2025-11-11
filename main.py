# ============================================================
# EURO_GOALS v9.6.9 PRO+ — UNIFIED REAL DATA EDITION + SMARTMONEY ENGINE
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio, os, sys, time

print("=== [EURO_GOALS] Unified App v9.6.9 PRO+ — DEPLOY MODE ACTIVE ===")

# ------------------------------------------------------------
# PATH FIX
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
    standings_engine,
    smartmoney_engine  # ✅ ΝΕΟ MODULE
)
from services.smartmoney_router import router as smartmoney_router

# ------------------------------------------------------------
# FASTAPI APP
# ------------------------------------------------------------
app = FastAPI(title="EURO_GOALS PRO+ v9.6.9 Unified")

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ------------------------------------------------------------
# GLOBAL INFO
# ------------------------------------------------------------
APP_VERSION = "v9.6.9 PRO+"
RAW_PROXY = os.getenv("LIVE_PROXY_URL", "").strip()
LIVE_PROXY_URL = RAW_PROXY[:-5] if RAW_PROXY.endswith("/live") else RAW_PROXY
IS_DEV = os.getenv("IS_DEV", "false").lower() == "true"

print(f"[EURO_GOALS] ⚙️ Proxy: {LIVE_PROXY_URL or 'No proxy configured'} (raw={RAW_PROXY})")
print(f"[EURO_GOALS] ⚙️ Mode: {'DEV' if IS_DEV else 'PRODUCTION'}")

# ------------------------------------------------------------
# STARTUP EVENT
# ------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    print(f"=== [EURO_GOALS] 🚀 Starting App {APP_VERSION} ===")
    await asyncio.sleep(1)

    asyncio.create_task(history_engine.background_refresher())
    asyncio.create_task(matchplan_engine.background_refresher())
    asyncio.create_task(standings_engine.background_refresher())
    asyncio.create_task(smartmoney_engine.background_refresher())  # ✅ SmartMoney background task

    print("[EURO_GOALS] Background refreshers active.")
    print("===============================================")
    print("")

# ------------------------------------------------------------
# ROOT ENDPOINT
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "version": APP_VERSION})

# ------------------------------------------------------------
# SMARTMONEY PANELS
# ------------------------------------------------------------
@app.get("/smartmoney", response_class=HTMLResponse)
async def smartmoney_panel(request: Request):
    return templates.TemplateResponse("smartmoney_panel.html", {"request": request})

@app.get("/smartmoney/study", response_class=HTMLResponse)
async def smartmoney_study(request: Request):
    return templates.TemplateResponse("smartmoney_study.html", {"request": request})

# ------------------------------------------------------------
# API ROUTERS
# ------------------------------------------------------------
app.include_router(smartmoney_router, prefix="/api/smartmoney", tags=["smartmoney"])

# ------------------------------------------------------------
# HEALTH ENDPOINT
# ------------------------------------------------------------
@app.get("/api/system/check")
async def system_check():
    return JSONResponse({
        "status": "ok",
        "version": APP_VERSION,
        "proxy": LIVE_PROXY_URL or None,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "engines": {
            "history": "active",
            "matchplan": "active",
            "standings": "active",
            "smartmoney": "active"
        }
    })

# ------------------------------------------------------------
# HISTORY / MATCHPLAN / STANDINGS
# ------------------------------------------------------------
@app.get("/api/history")
async def get_history():
    data = await history_engine.get_history()
    return JSONResponse(data)

@app.get("/api/matchplan/summary")
async def get_matchplan_summary():
    data = await matchplan_engine.get_matchplan_summary()
    return JSONResponse(data)

@app.get("/api/standings/summary")
async def get_standings_summary():
    data = await standings_engine.get_standings()
    return JSONResponse(data)

# ------------------------------------------------------------
# MANUAL REFRESH
# ------------------------------------------------------------
@app.get("/api/system/refresh")
async def manual_refresh():
    await asyncio.gather(
        history_engine.get_history(),
        matchplan_engine.get_matchplan_summary(),
        standings_engine.get_standings(),
        smartmoney_engine.refresh_smartmoney_once()
    )
    return {"status": "refreshed", "time": time.strftime("%H:%M:%S")}

# ------------------------------------------------------------
# PWA / OFFLINE TEST
# ------------------------------------------------------------
@app.get("/offline", response_class=HTMLResponse)
async def offline_page(request: Request):
    return templates.TemplateResponse("offline.html", {"request": request})
