# ============================================================
# EURO_GOALS v9.6.2 PRO+ — UNIFIED LIVE PROXY INTEGRATION
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio, os, sys, time, requests

print("=== [EURO_GOALS] Unified App 9.6.2 PRO+ — LIVE PROXY ENABLED ===")

# ------------------------------------------------------------
# SYSTEM PATH FIX
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# ------------------------------------------------------------
# GLOBAL LIVE PROXY ENDPOINT (Cloudflare Worker)
# ------------------------------------------------------------
LIVE_PROXY_URL = os.getenv("LIVE_PROXY_URL", "https://eurogoals-live.worker.dev/live")

def get_live_data():
    """Pulls unified live data feed from Cloudflare Worker"""
    try:
        r = requests.get(LIVE_PROXY_URL, timeout=6)
        if r.status_code == 200:
            return r.json()
        else:
            return {"status": "error", "msg": f"Worker returned {r.status_code}"}
    except Exception as e:
        return {"status": "offline", "error": str(e)}

# ============================================================
# ENGINE SHIMS (Fallback για μη διαθέσιμα modules)
# ============================================================
class _CacheShim:
    def __init__(self, name): self.name = name
    def get_summary(self): return {"engine": self.name, "status": "ok", "summary": []}
    def get_alerts(self):  return {"engine": self.name, "alerts": []}
    def get_data(self):    return {"engine": self.name, "data": []}
    def get_history(self): return {"engine": self.name, "history": []}

class _EngineShim:
    def __init__(self, name):
        self.name = name
        self.cache = _CacheShim(name)
        self.ENABLED = False
    async def get_summary(self): return self.cache.get_summary()
    async def get_alerts(self):  return self.cache.get_alerts()
    async def get_data(self):    return self.cache.get_data()
    async def get_history(self, source="flashscore"): return self.cache.get_history()
    async def get_odds_data(self): return self.cache.get_data()
    async def get_odds_summary(self): return self.cache.get_summary()
    async def background_refresher(self):
        print(f"[EURO_GOALS] ({self.name}) background shim running.")
        while True:
            await asyncio.sleep(30)

# ============================================================
# ENGINE IMPORT HELPER
# ============================================================
def _try_import():
    try:
        from services import (
            smartmoney_engine,
            goal_matrix_engine,
            history_engine,
            odds_unified_engine
        )
        try:
            from services import heatmap_engine
        except ImportError:
            heatmap_engine = _EngineShim("heatmap_engine")
        return smartmoney_engine, goal_matrix_engine, history_engine, odds_unified_engine, heatmap_engine
    except ImportError as e:
        print(f"[EURO_GOALS] ⚠️ Import error: {e}")
        return None

# ============================================================
# LOAD ENGINES
# ============================================================
_imports = _try_import()
if _imports is None:
    print("[EURO_GOALS] ⚠️ Services not found. Using Engine Shims.")
    smartmoney_engine  = _EngineShim("smartmoney_engine")
    goal_matrix_engine = _EngineShim("goal_matrix_engine")
    history_engine     = _EngineShim("history_engine")
    odds_unified_engine = _EngineShim("odds_unified_engine")
    heatmap_engine     = _EngineShim("heatmap_engine")
else:
    smartmoney_engine, goal_matrix_engine, history_engine, odds_unified_engine, heatmap_engine = _imports

# ============================================================
# FASTAPI APP
# ============================================================
APP_VERSION = "9.6.2 PRO+ Live Proxy Integration"
app = FastAPI(title=f"EURO_GOALS {APP_VERSION}")

STATIC_DIR    = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ============================================================
# PAGES
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

@app.get("/alert_center", response_class=HTMLResponse)
async def alert_center(request: Request):
    return templates.TemplateResponse("alert_center.html", {"request": request, "version": APP_VERSION})

# ============================================================
# API ENDPOINTS
# ============================================================
@app.get("/api/live")
async def api_live_proxy():
    """Returns unified live data directly from Cloudflare Worker"""
    return JSONResponse(get_live_data())

@app.get("/api/smartmoney/summary")
async def api_sm_summary(): return await smartmoney_engine.get_summary()

@app.get("/api/smartmoney/alerts")
async def api_sm_alerts(): return {"alerts": await smartmoney_engine.get_alerts()}

@app.get("/api/goalmatrix/summary")
async def api_gm_summary(): return await goal_matrix_engine.get_summary()

@app.get("/api/goalmatrix/alerts")
async def api_gm_alerts(): return {"alerts": await goal_matrix_engine.get_alerts()}

@app.get("/api/heatmap/data")
async def api_heatmap_data(): return await heatmap_engine.get_data()

@app.get("/api/history")
async def api_history(source: str = "flashscore"): return await history_engine.get_history(source)

@app.get("/api/odds/data")
async def api_odds_data(): return await odds_unified_engine.get_odds_data()

@app.get("/api/odds/summary")
async def api_odds_summary():
    try:
        return await odds_unified_engine.get_summary()
    except TypeError:
        return odds_unified_engine.get_summary()

# ============================================================
# SYSTEM CHECK
# ============================================================
@app.get("/api/system/check", response_class=JSONResponse)
async def api_system_check():
    engines = {}
    async def safe_call(name, func):
        try:
            result = func
            if asyncio.iscoroutine(result):
                result = await result
            engines[name] = result
        except Exception as e:
            engines[name] = {"error": str(e)}
    await safe_call("smartmoney", smartmoney_engine.get_summary())
    await safe_call("goalmatrix", goal_matrix_engine.get_summary())
    await safe_call("heatmap", heatmap_engine.get_summary())
    await safe_call("history", history_engine.get_summary())
    await safe_call("odds_unified", odds_unified_engine.get_summary())

    return {
        "version": APP_VERSION,
        "status": "online",
        "proxy_url": LIVE_PROXY_URL,
        "timestamp": int(time.time()),
        "engines": engines
    }

# ============================================================
# STARTUP TASKS
# ============================================================
@app.on_event("startup")
async def startup_event():
    print(f"[EURO_GOALS] 🚀 Εκκίνηση v{APP_VERSION}")
    print(f"[EURO_GOALS] 🌍 Using LIVE PROXY URL: {LIVE_PROXY_URL}")
    async def _safe(name, func):
        try:
            asyncio.create_task(func())
            print(f"✅ {name} background task started.")
        except Exception as e:
            print(f"⚠️ {name} init error: {e}")
    await _safe("SMARTMONEY", smartmoney_engine.background_refresher)
    await _safe("GOALMATRIX", goal_matrix_engine.background_refresher)
    await _safe("HEATMAP",    heatmap_engine.background_refresher)
    await _safe("HISTORY",    history_engine.background_refresher)
    await _safe("ODDS",       odds_unified_engine.background_refresher)

# ============================================================
# LOCAL RUN
# ============================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🏁 Running EURO_GOALS on 0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
