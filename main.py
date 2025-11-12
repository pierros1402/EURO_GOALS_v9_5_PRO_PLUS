# ============================================================
# EURO_GOALS v9.8.8 PRO+ — UNIFIED MAIN APP (+ Betfair Dow Jones)
# ============================================================
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio, os, sys, time, datetime as dt, json

print("=== [EURO_GOALS PRO+] v9.8.8 — FULL REAL DATA + LEAGUES + DOW JONES ACTIVE ===")

# ------------------------------------------------------------
# SYSTEM PATH FIX
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# ------------------------------------------------------------
# IMPORT ENGINES (existing)
# ------------------------------------------------------------
from services import (
    history_engine,
    data_refresher
)

# ------------------------------------------------------------
# IMPORT DOW JONES ENGINE (new)
# ------------------------------------------------------------
try:
    from services.dowjones_engine import DowJonesEngine
except Exception as e:
    print("[EURO_GOALS] ⚠️ DowJonesEngine unavailable:", e)
    DowJonesEngine = None

# ------------------------------------------------------------
# IMPORT LEAGUE LIST
# ------------------------------------------------------------
try:
    from leagues_list import LEAGUES, EURO_COMPETITIONS
except Exception as e:
    print("[EURO_GOALS] ⚠️ Could not import leagues_list:", e)
    LEAGUES, EURO_COMPETITIONS = [], []

# ------------------------------------------------------------
# APP CONFIG
# ------------------------------------------------------------
app = FastAPI(title=os.getenv("APP_NAME", "EURO_GOALS PRO+"), version="9.8.8")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ------------------------------------------------------------
# ENGINE INSTANCES
# ------------------------------------------------------------
refresh_seconds = int(os.getenv("REFRESH_SECONDS", "10"))
dowjones = DowJonesEngine(refresh_seconds=refresh_seconds) if DowJonesEngine else None

# ------------------------------------------------------------
# BASIC ROUTES
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "9.8.8", "timestamp": dt.datetime.now().isoformat()}

# ------------------------------------------------------------
# LEAGUES ROUTE
# ------------------------------------------------------------
@app.get("/leagues", response_class=JSONResponse)
async def get_leagues():
    return {
        "status": "ok",
        "count": len(LEAGUES),
        "leagues": LEAGUES,
        "competitions": EURO_COMPETITIONS
    }

# ------------------------------------------------------------
# HISTORY ADMIN VIEW (unchanged)
# ------------------------------------------------------------
@app.get("/history_admin", response_class=HTMLResponse)
async def history_admin(request: Request, league: str = "football/england/premier-league"):
    base = os.path.join("data", "history", league)
    standings_file = os.path.join(base, "standings", f"{dt.date.today().year}.json")
    fixtures_file = os.path.join(base, "seasons", f"{dt.date.today().year}.json")

    table, fixtures = [], []
    if os.path.exists(standings_file):
        try:
            table = json.load(open(standings_file, "r", encoding="utf-8"))["snapshots"][0]["table"]
        except Exception as e:
            print(f"[EURO_GOALS] ⚠️ Could not read standings for {league}:", e)
    if os.path.exists(fixtures_file):
        try:
            fixtures = json.load(open(fixtures_file, "r", encoding="utf-8"))
        except Exception as e:
            print(f"[EURO_GOALS] ⚠️ Could not read fixtures for {league}:", e)

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
# DOW JONES PANEL (new)
# ------------------------------------------------------------
@app.get("/dowjones", response_class=HTMLResponse)
async def dowjones_page(request: Request):
    ui_cfg = {
        "app_name": os.getenv("APP_NAME", "EURO_GOALS PRO+ v9.8.8"),
        "refresh_seconds": refresh_seconds,
        "countries": os.getenv("DJ_COUNTRIES", "").split(",") if os.getenv("DJ_COUNTRIES") else [],
        "leagues": os.getenv("DJ_LEAGUES", "").split(",") if os.getenv("DJ_LEAGUES") else [],
    }
    return templates.TemplateResponse("dowjones.html", {"request": request, "ui": ui_cfg})

@app.get("/api/dowjones/live")
async def api_dowjones_live():
    return JSONResponse(dowjones.snapshot() if dowjones else {"rows": [], "mock": True, "tick": 0, "ts": int(time.time())})

@app.get("/api/dowjones/config")
async def api_dowjones_config():
    return dowjones.public_config() if dowjones else {}

@app.get("/api/dowjones/health")
async def api_dowjones_health():
    return dowjones.health() if dowjones else {"mock": True}

# ------------------------------------------------------------
# STARTUP EVENT
# ------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    print("[EURO_GOALS] 🚀 Starting engines...")

    # History Engine
    print("[EURO_GOALS] 📚 History Engine starting...")
    if hasattr(history_engine, "init"):
        try:
            await history_engine.init()
            print("[EURO_GOALS] ✅ History Engine initialized.")
        except Exception as e:
            print("[EURO_GOALS] ⚠️ History Engine init failed:", e)
    else:
        print("[EURO_GOALS] ℹ️ History Engine has no init() method — skipped.")

    # Data Refresher
    print("[EURO_GOALS] 🔁 Data Refresher starting...")
    try:
        asyncio.create_task(data_refresher.start_background_refresh())
        print("[EURO_GOALS] ✅ Data Refresher launched.")
    except Exception as e:
        print("[EURO_GOALS] ⚠️ Data Refresher start failed:", e)

    # Dow Jones refresher loop
    if dowjones:
        print("[EURO_GOALS] 📈 Dow Jones Engine starting...")
        try:
            await dowjones.start()
            async def refresher():
                while True:
                    try:
                        await dowjones.refresh()
                    except Exception as e:
                        print("[EURO_GOALS][dowjones.refresh]", repr(e))
                    await asyncio.sleep(dowjones.refresh_seconds)
            asyncio.create_task(refresher())
            print("[EURO_GOALS] ✅ Dow Jones refresher launched.")
        except Exception as e:
            print("[EURO_GOALS] ⚠️ Dow Jones start failed:", e)

    print("[EURO_GOALS] ✅ Startup complete — Engines Active")

# ------------------------------------------------------------
# GLOBAL ERROR HANDLER
# ------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("[EURO_GOALS] ❌ Exception:", exc)
    return JSONResponse(status_code=500, content={"error": str(exc)})

# ============================================================
# LOCAL RUN
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
