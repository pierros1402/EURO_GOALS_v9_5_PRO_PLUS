# ============================================================
# EURO_GOALS PRO+ v9.9.13 PRO+ — UNIFIED MAIN APPLICATION
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio, os, sys, time, datetime as dt, json

print("=== [EURO_GOALS PRO+] v9.9.13 — FULL REAL DATA + LEAGUES + DOW JONES ACTIVE ===")

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
    data_refresher,
)

# ------------------------------------------------------------
# IMPORT DOW JONES ENGINE
# ------------------------------------------------------------
try:
    from services.dowjones_engine import DowJonesEngine
except Exception as e:
    print(f"[EURO_GOALS] ⚠️ DowJonesEngine unavailable: {e}")
    DowJonesEngine = None

# ------------------------------------------------------------
# IMPORT LEAGUE LIST
# ------------------------------------------------------------
try:
    from services.leagues_list import LEAGUES, EURO_COMPETITIONS
except Exception as e:
    print(f"[EURO_GOALS] ⚠️ Could not import leagues_list: {e}")
    LEAGUES, EURO_COMPETITIONS = [], []

# ------------------------------------------------------------
# APP CONFIG / FLAGS
# ------------------------------------------------------------
IS_RENDER = bool(os.getenv("RENDER", ""))
refresh_seconds = int(os.getenv("EG_REFRESH_INTERVAL", "180"))

# Unified system status cache
system_status = {
    "dowjones": {"status": "idle", "last_update": None},
    "history": {"status": "idle", "last_update": None},
    "data_refresher": {"status": "idle", "last_update": None},
}

# ============================================================
# FASTAPI APP SETUP
# ============================================================
app = FastAPI(
    title="EURO_GOALS PRO+ v9.9.13",
    description="Unified EURO_GOALS PRO+ — Real data + Leagues + DowJones Engine",
    version="9.9.13",
)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ============================================================
# STARTUP / BACKGROUND TASKS
# ============================================================

async def dowjones_refresher_loop(engine: DowJonesEngine, seconds: int):
    """Background loop for DowJones live data."""
    print("[EURO_GOALS] 🔁 Starting DowJones refresher loop...")
    while True:
        try:
            await engine.refresh()
            system_status["dowjones"]["status"] = "ok"
            system_status["dowjones"]["last_update"] = dt.datetime.utcnow().isoformat()
        except Exception as e:
            system_status["dowjones"]["status"] = f"error: {e}"
            print("[EURO_GOALS][DowJonesEngine] Error in refresher:", e)
        await asyncio.sleep(seconds)


async def history_refresher_loop():
    """Background loop for Flashscore history refresh."""
    print("[EURO_GOALS] 🔁 Starting History refresher loop...")
    while True:
        try:
            history_engine.refresh_history()
            system_status["history"]["status"] = "ok"
            system_status["history"]["last_update"] = dt.datetime.utcnow().isoformat()
        except Exception as e:
            system_status["history"]["status"] = f"error: {e}"
            print("[EURO_GOALS][HistoryEngine] Error in refresher:", e)
        await asyncio.sleep(refresh_seconds)


async def data_refresher_loop():
    """Background loop for generic data refresher (fixtures / standings etc)."""
    if not hasattr(data_refresher, "run"):
        print("[EURO_GOALS] ℹ️ data_refresher has no .run() method — skipped.")
        return
    print("[EURO_GOALS] 🔁 Starting DataRefresher loop...")
    while True:
        try:
            await data_refresher.run()
            system_status["data_refresher"]["status"] = "ok"
            system_status["data_refresher"]["last_update"] = dt.datetime.utcnow().isoformat()
        except Exception as e:
            system_status["data_refresher"]["status"] = f"error: {e}"
            print("[EURO_GOALS][DataRefresher] Error in refresher:", e)
        await asyncio.sleep(refresh_seconds)


@app.on_event("startup")
async def startup_event():
    """Initialize engines + background tasks."""
    print("============================================================")
    print(" EURO_GOALS PRO+ v9.9.13 — Unified Application Startup")
    print("============================================================")
    print(f" Base Directory : {os.path.basename(BASE_DIR) or BASE_DIR}")
    print(f" Running on     : {'Render' if IS_RENDER else 'Local / Dev'}")
    print(f" Refresh cycle  : {refresh_seconds}s")
    print("============================================================")

    # DowJones init
    dow = None
    if DowJonesEngine:
        try:
            dow = DowJonesEngine(refresh_seconds=refresh_seconds)
            system_status["dowjones"]["status"] = "initialized"
            print("[EURO_GOALS] ✅ DowJonesEngine initialized.")
        except Exception as e:
            system_status["dowjones"]["status"] = f"error: {e}"
            print("[EURO_GOALS] ❌ Failed to initialize DowJonesEngine:", e)
            dow = None
    else:
        print("[EURO_GOALS] ⚠️ DowJonesEngine class not available.")

    # History init (no heavy init, just flag)
    system_status["history"]["status"] = "ready"
    print("[EURO_GOALS] ✅ History Engine ready.")

    # Data refresher init
    system_status["data_refresher"]["status"] = "ready"
    print("[EURO_GOALS] ✅ DataRefresher ready.")

    # Background tasks
    loop = asyncio.get_event_loop()
    if dow:
        loop.create_task(dowjones_refresher_loop(dow, refresh_seconds))
    loop.create_task(history_refresher_loop())
    loop.create_task(data_refresher_loop())

    print("[EURO_GOALS] 🚀 All systems active — startup complete.")


# ============================================================
# ROUTES — PAGES
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main unified dashboard."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "is_render": IS_RENDER,
        },
    )


@app.get("/history-admin", response_class=HTMLResponse)
async def history_admin(request: Request):
    """History admin / viewer."""
    history_data = history_engine.get_history_summary() if hasattr(history_engine, "get_history_summary") else {}
    return templates.TemplateResponse(
        "history_admin.html",
        {
            "request": request,
            "history": history_data,
        },
    )


# ============================================================
# ROUTES — API / JSON
# ============================================================

@app.get("/health", response_class=JSONResponse)
async def health():
    """Simple health check."""
    return JSONResponse(
        {
            "status": "ok",
            "timestamp": dt.datetime.utcnow().isoformat(),
            "system": system_status,
        }
    )


@app.get("/leagues", response_class=JSONResponse)
async def get_leagues():
    """Expose leagues list / euro competitions."""
    return JSONResponse(
        {
            "leagues": LEAGUES,
            "euro_competitions": EURO_COMPETITIONS,
            "count": len(LEAGUES),
        }
    )


@app.get("/api/dowjones/live", response_class=JSONResponse)
async def dowjones_live():
    """Expose current DowJones snapshot from engine."""
    if not DowJonesEngine or not hasattr(DowJonesEngine, "get_snapshot"):
        return JSONResponse({"error": "DowJonesEngine not available"}, status_code=503)

    try:
        snapshot = DowJonesEngine.get_snapshot()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    return JSONResponse({"data": snapshot, "ts": int(time.time())})


@app.get("/api/system/status/unified", response_class=JSONResponse)
async def unified_system_status():
    """Unified system status for top dashboard."""
    return JSONResponse(
        {
            "status": "ok",
            "ts": int(time.time()),
            "env": "render" if IS_RENDER else "local",
            "components": system_status,
        }
    )


# ============================================================
# GLOBAL EXCEPTION HANDLER (OPTIONAL SIMPLE LOGGING)
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("[EURO_GOALS] ❌ Exception:", repr(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


# ============================================================
# LOCAL DEV ENTRY POINT
# ============================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=not IS_RENDER,
    )
