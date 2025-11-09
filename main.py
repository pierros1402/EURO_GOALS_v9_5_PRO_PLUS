# ============================================================
# EURO_GOALS v9.5.5 PRO+ UNIFIED EXPANSION — MAIN APP (FINAL)
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio, time, os

print("=== [EURO_GOALS] Unified App 9.5.5 PRO+ — FULL DEPLOY ACTIVE ===")

# ------------------------------------------------------------
# Προσπάθεια imports για Render + Local συμβατότητα
# ------------------------------------------------------------
def _try_import():
    try:
        # Render-style (όταν υπάρχει φάκελος app/)
        from app.services import smartmoney_engine, goalmatrix_engine, heatmap_engine, history_engine
        return smartmoney_engine, goalmatrix_engine, heatmap_engine, history_engine
    except ModuleNotFoundError:
        try:
            # Local-style
            from services import smartmoney_engine, goalmatrix_engine, heatmap_engine, history_engine
            return smartmoney_engine, goalmatrix_engine, heatmap_engine, history_engine
        except ModuleNotFoundError:
            return None

_imports = _try_import()

# ------------------------------------------------------------
# Engine Shims για ασφαλή εκκίνηση
# ------------------------------------------------------------
class _CacheShim:
    def __init__(self, name): self.name = name
    def get_summary(self): return {"engine": self.name, "summary": [], "ts": int(time.time())}
    def get_alerts(self): return []
    def get_data(self): return {"engine": self.name, "data": [], "ts": int(time.time())}
    def get_history(self): return {"engine": self.name, "history": [], "ts": int(time.time())}

class _EngineShim:
    def __init__(self, name):
        self.name = name
        self.cache = _CacheShim(name)
        self.ENABLED = True
    async def background_refresher(self):
        print(f"[EURO_GOALS] ({self.name}) shim refresher started.")
        while True:
            await asyncio.sleep(15)

if _imports is None:
    print("[EURO_GOALS] ⚠️ Services not found. Using Engine Shims.")
    smartmoney_engine = _EngineShim("smartmoney_engine")
    goal_matrix_engine = _EngineShim("goal_matrix_engine")
    heatmap_engine = _EngineShim("heatmap_engine")
    history_engine = _EngineShim("history_engine")
else:
    smartmoney_engine, goal_matrix_engine, heatmap_engine, history_engine = _imports

# ------------------------------------------------------------
# Ενιαία διεπαφή (προστασία)
# ------------------------------------------------------------
def _ensure_engine_iface(engine, name):
    if not hasattr(engine, "cache"): engine.cache = _CacheShim(name)
    for meth in ["get_summary","get_alerts","get_data","get_history"]:
        if not hasattr(engine.cache, meth):
            setattr(engine.cache, meth, lambda: {"engine": name})
    if not hasattr(engine, "background_refresher"):
        async def _noop(): 
            print(f"[EURO_GOALS] ({name}) bg shim running.")
            while True: await asyncio.sleep(15)
        engine.background_refresher = _noop
    if not hasattr(engine, "ENABLED"): engine.ENABLED = True

for eng, nm in [
    (smartmoney_engine,"smartmoney_engine"),
    (goal_matrix_engine,"goal_matrix_engine"),
    (heatmap_engine,"heatmap_engine"),
    (history_engine,"history_engine"),
]: _ensure_engine_iface(eng, nm)

# ------------------------------------------------------------
# FastAPI app & templates
# ------------------------------------------------------------
APP_VERSION = "9.5.5 PRO+ Unified Expansion"
app = FastAPI(title=f"EURO_GOALS {APP_VERSION}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ============================================================
# MAIN PAGES
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "version": APP_VERSION})

@app.get("/smartmoney_monitor", response_class=HTMLResponse)
async def smartmoney_monitor(request: Request):
    return templates.TemplateResponse("smartmoney_monitor.html", {"request": request, "version": APP_VERSION})

@app.get("/heatmap", response_class=HTMLResponse)
async def heatmap_page(request: Request):
    return templates.TemplateResponse("heatmap.html", {"request": request, "version": APP_VERSION})

@app.get("/history_unified", response_class=HTMLResponse)
async def history_page(request: Request):
    return templates.TemplateResponse("history_unified.html", {"request": request, "version": APP_VERSION})

@app.get("/system_status_page", response_class=HTMLResponse)
async def system_status_page(request: Request):
    return templates.TemplateResponse("system_status.html", {"request": request, "version": APP_VERSION})

# ============================================================
# API ENDPOINTS
# ============================================================
# 🧠 SMARTMONEY
@app.get("/api/smartmoney/summary")
async def api_sm_summary(): return smartmoney_engine.cache.get_summary()

@app.get("/api/smartmoney/alerts")
async def api_sm_alerts(): return {"alerts": smartmoney_engine.cache.get_alerts()}

# 🎯 GOALMATRIX
@app.get("/api/goalmatrix/summary")
async def api_gm_summary(): return goal_matrix_engine.cache.get_summary()

@app.get("/api/goalmatrix/alerts")
async def api_gm_alerts(): return {"alerts": goal_matrix_engine.cache.get_alerts()}
@app.get("/api/goalmatrix/items")
async def api_gm_items():
    # Dummy data για εμφάνιση στο panel (θα αντικατασταθεί με real GoalMatrix data)
    sample_items = [
        {
            "league": "Premier League",
            "home": "Arsenal",
            "away": "Liverpool",
            "xg_home": 1.9,
            "xg_away": 1.2,
            "expected_goals": 3.1,
            "tendency": "Over 2.5"
        },
        {
            "league": "Serie A",
            "home": "Inter",
            "away": "Napoli",
            "xg_home": 1.4,
            "xg_away": 1.1,
            "expected_goals": 2.5,
            "tendency": "Balanced"
        }
    ]
    return {"items": sample_items, "ts": int(time.time())}
# 🔥 HEATMAP
@app.get("/api/heatmap/data")
async def api_heatmap_data(): return heatmap_engine.cache.get_data()

# 🕓 ΙΣΤΟΡΙΚΑ (FlashScore + SofaScore)
@app.get("/api/history")
async def api_history(source: str = "flashscore"):
    return await history_engine.get_history(source)

# ============================================================
# HEALTH / STATUS
# ============================================================
@app.get("/system_status")
async def system_status():
    def safe_len(data, key): 
        try:
            return len(data.get(key, [])) if isinstance(data, dict) else 0
        except Exception:
            return 0

    return {
        "version": APP_VERSION,
        "engines": {
            "smartmoney": {
                "active": getattr(smartmoney_engine, "ENABLED", True),
                "alerts": safe_len(smartmoney_engine.cache.get_summary(), "summary")
            },
            "goalmatrix": {
                "active": getattr(goal_matrix_engine, "ENABLED", True),
                "alerts": safe_len(goal_matrix_engine.cache.get_summary(), "summary")
            },
            "heatmap": {
                "active": getattr(heatmap_engine, "ENABLED", True),
                "items": safe_len(heatmap_engine.cache.get_data(), "data")
            },
            "history": {
                "active": getattr(history_engine, "ENABLED", True),
                "history_items": safe_len(history_engine.cache.get_history(), "history")
            }
        },
        "ts": int(time.time())
    }

# ============================================================
# STARTUP
# ============================================================
@app.on_event("startup")
async def startup_event():
    print(f"[EURO_GOALS] 🚀 Εκκίνηση v{APP_VERSION}")
    async def _safe(name, func):
        try:
            asyncio.create_task(func())
            print(f"✅ {name} background task started.")
        except Exception as e:
            print(f"⚠️ {name} init error: {e}")

    await _safe("SMARTMONEY", smartmoney_engine.background_refresher)
    await _safe("GOALMATRIX", goal_matrix_engine.background_refresher)
    await _safe("HEATMAP", heatmap_engine.background_refresher)
    await _safe("HISTORY", history_engine.background_refresher)

# ============================================================
# LOCAL STARTUP
# ============================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🏁 Running EURO_GOALS on 0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)
