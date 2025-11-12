# ============================================================
# EURO_GOALS v9.9.6 PRO+ — UNIFIED MAIN APP (Interactive Layer + Diagnostics)
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio, os, sys, time, datetime as dt, json
from dotenv import load_dotenv

# ------------------------------------------------------------
# LOAD ENV
# ------------------------------------------------------------
load_dotenv()
APP_VERSION = "9.9.6"
APP_NAME = os.getenv("APP_NAME", "EURO_GOALS PRO+")
INTERACTIVE_LAYER = os.getenv("INTERACTIVE_LAYER", "1") in ("1", "true", "True", "yes")
REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "10"))

# ------------------------------------------------------------
# STARTUP BANNER
# ------------------------------------------------------------
print("\n" + "=" * 66)
print(f"🚀 {APP_NAME} v{APP_VERSION} — Unified Application Startup")
print("=" * 66)
print(f"🧩 Interactive Layer: {'✅ ON' if INTERACTIVE_LAYER else '❌ OFF'}")
print(f"🔁 Refresh Interval : {REFRESH_SECONDS}s")
print(f"📦 Base Directory   : {os.path.basename(os.getcwd())}")
print("=" * 66 + "\n")

# ------------------------------------------------------------
# PATH FIX
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
SERVICES_DIR = os.path.join(BASE_DIR, "services")
if SERVICES_DIR not in sys.path:
    sys.path.append(SERVICES_DIR)

# ------------------------------------------------------------
# IMPORT ENGINES
# ------------------------------------------------------------
try:
    from services import history_engine, data_refresher
    print("✅ Engines imported successfully.")
except Exception as e:
    print("⚠️  Engine import failed:", e)

try:
    from services.dowjones_engine import DowJonesEngine
    print("✅ DowJonesEngine available.")
except Exception as e:
    print("⚠️  DowJonesEngine unavailable:", e)
    DowJonesEngine = None

try:
    from services.leagues_list import LEAGUES, EURO_COMPETITIONS
    print(f"✅ Leagues imported: {len(LEAGUES)} entries.")
except Exception as e:
    print("⚠️  Could not import leagues_list:", e)
    LEAGUES, EURO_COMPETITIONS = [], []

# ------------------------------------------------------------
# APP CONFIG
# ------------------------------------------------------------
app = FastAPI(title=APP_NAME, version=APP_VERSION)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ------------------------------------------------------------
# INITIALIZE ENGINES
# ------------------------------------------------------------
dowjones = None
if DowJonesEngine:
    try:
        dowjones = DowJonesEngine(refresh_seconds=REFRESH_SECONDS)
        print("✅ DowJonesEngine initialized.")
    except Exception as e:
        print("⚠️  DowJonesEngine init failed:", e)

# ------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main UI route — passes INTERACTIVE_LAYER flag to Jinja"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "INTERACTIVE_LAYER": INTERACTIVE_LAYER}
    )


@app.get("/health")
async def health_check():
    """System health endpoint"""
    return {
        "status": "ok",
        "version": APP_VERSION,
        "timestamp": dt.datetime.now().isoformat(),
        "interactive_layer": INTERACTIVE_LAYER,
        "refresh_seconds": REFRESH_SECONDS
    }


@app.get("/leagues", response_class=JSONResponse)
async def get_leagues():
    """Return league + competition list"""
    return {
        "status": "ok",
        "count": len(LEAGUES),
        "leagues": LEAGUES,
        "competitions": EURO_COMPETITIONS
    }


@app.get("/history_admin", response_class=HTMLResponse)
async def history_admin(request: Request, league: str = "football/england/premier-league"):
    """History Admin panel"""
    base = os.path.join("data", "history", league)
    standings_file = os.path.join(base, "standings", f"{dt.date.today().year}.json")
    fixtures_file = os.path.join(base, "seasons", f"{dt.date.today().year}.json")

    table, fixtures = [], []
    if os.path.exists(standings_file):
        try:
            table = json.load(open(standings_file, "r", encoding="utf-8"))["snapshots"][0]["table"]
        except Exception as e:
            print(f"⚠️  Could not read standings for {league}:", e)
    if os.path.exists(fixtures_file):
        try:
            fixtures = json.load(open(fixtures_file, "r", encoding="utf-8"))
        except Exception as e:
            print(f"⚠️  Could not read fixtures for {league}:", e)

    leagues = []
    root = os.path.join("data", "history")
    if os.path.exists(root):
        for path, dirs, files in os.walk(root):
            for d in dirs:
                if d not in ("standings", "seasons"):
                    rel = os.path.relpath(os.path.join(path, d), root)
                    leagues.append(rel.replace("\\", "/"))
    if not leagues and LEAGUES:
        leagues = [l["id"] for l in LEAGUES]

    return templates.TemplateResponse("history_admin.html", {
        "request": request,
        "leagues": sorted(set(leagues)),
        "current": league,
        "table": table,
        "fixtures": fixtures
    })


# ------------------------------------------------------------
# DOW JONES ROUTES
# ------------------------------------------------------------
@app.get("/dowjones", response_class=HTMLResponse)
async def dowjones_page(request: Request):
    """DowJones full-page panel"""
    ui_cfg = {
        "app_name": f"{APP_NAME} v{APP_VERSION}",
        "refresh_seconds": REFRESH_SECONDS,
        "countries": os.getenv("DJ_COUNTRIES", "").split(",") if os.getenv("DJ_COUNTRIES") else [],
        "leagues": os.getenv("DJ_LEAGUES", "").split(",") if os.getenv("DJ_LEAGUES") else [],
    }
    return templates.TemplateResponse("dowjones.html", {"request": request, "ui": ui_cfg})


@app.get("/api/dowjones/live")
async def api_dowjones_live():
    return JSONResponse(dowjones.snapshot() if dowjones else {"rows": [], "mock": True, "tick": 0})


@app.get("/api/dowjones/config")
async def api_dowjones_config():
    return dowjones.public_config() if dowjones else {}


@app.get("/api/dowjones/health")
async def api_dowjones_health():
    return dowjones.health() if dowjones else {"mock": True}

# ------------------------------------------------------------
# SMARTMONEY & GOALMATRIX SUMMARY ENDPOINTS
# ------------------------------------------------------------
from services import smartmoney_engine, goal_matrix_engine

@app.get("/api/smartmoney/summary")
async def api_smartmoney_summary(match_id: str = "default"):
    """Returns unified SmartMoney odds & signals"""
    try:
        data = smartmoney_engine.get_odds_snapshot(match_id)
        signals = smartmoney_engine.get_smartmoney_signals(match_id)
        return {"status": "ok", "match_id": match_id, "snapshot": data, "signals": signals}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/goal_matrix/summary")
async def api_goal_matrix_summary(match_id: str = "default"):
    """Returns GoalMatrix expected goals and heatmap"""
    try:
        data = goal_matrix_engine.get_goal_matrix(match_id)
        return {"status": "ok", "match_id": match_id, "matrix": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ------------------------------------------------------------
# UNIFIED SYSTEM STATUS API
# ------------------------------------------------------------
from services import dowjones_engine, smartmoney_engine, goal_matrix_engine, history_engine
import datetime as dt

@app.get("/api/system/status")
async def api_system_status():
    """Unified system health snapshot for all engines"""
    now = dt.datetime.now().isoformat()
    engines = {
        "dowjones": "ok",
        "smartmoney": "ok",
        "goalmatrix": "ok",
        "history": "ok"
    }
    alerts = {"smartmoney": 0, "goalmatrix": 0}

    try:
        sm_data = await smartmoney_engine.get_smartmoney_signals("default")
        alerts["smartmoney"] = len(sm_data) if isinstance(sm_data, list) else 0
    except Exception as e:
        engines["smartmoney"] = f"error: {e}"

    try:
        gm_data = goal_matrix_engine.get_goal_matrix("default")
        alerts["goalmatrix"] = len(gm_data.get("alerts", [])) if isinstance(gm_data, dict) else 0
    except Exception as e:
        engines["goalmatrix"] = f"error: {e}"

    return {
        "status": "ok",
        "timestamp": now,
        "engines": engines,
        "last_refresh": now,
        "alerts": alerts
    }

# ------------------------------------------------------------
# STARTUP EVENT
# ------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    print("⚙️  Starting system engines...")

    # History Engine
    if hasattr(history_engine, "init"):
        try:
            await history_engine.init()
            print("✅ History Engine initialized.")
        except Exception as e:
            print("⚠️  History Engine init failed:", e)

    # Data Refresher
    try:
        asyncio.create_task(data_refresher.start_background_refresh())
        print("✅ Data Refresher started.")
    except Exception as e:
        print("⚠️  Data Refresher failed:", e)

    # DowJones Engine
    if dowjones:
        try:
            await dowjones.start()

            async def refresher():
                while True:
                    try:
                        await dowjones.refresh()
                    except Exception as e:
                        print("⚠️  DowJones refresh error:", e)
                    await asyncio.sleep(dowjones.refresh_seconds)

            asyncio.create_task(refresher())
            print("✅ DowJones Engine started.")
        except Exception as e:
            print("⚠️  DowJones start failed:", e)

    # Interactive Layer check
    if INTERACTIVE_LAYER:
        print("🎨 Interactive Layer: ENABLED")
    else:
        print("🎨 Interactive Layer: DISABLED")

    print("🚀 All systems active — startup complete.\n")


# ------------------------------------------------------------
# ERROR HANDLER
# ------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("❌ Exception:", exc)
    return JSONResponse(status_code=500, content={"error": str(exc)})


# ------------------------------------------------------------
# LOCAL RUN
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
