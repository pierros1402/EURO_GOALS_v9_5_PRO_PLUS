# ============================================================
# AI MatchLab v1.1.0 — Unified RealData Hub
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import asyncio
import os
import sys
import time
import json
import logging
import datetime as dt
from typing import Optional, Dict, Any

# Optional httpx for Live Hub
try:
    import httpx
except ImportError:
    httpx = None

print("=== [AI MatchLab] Unified Hub v1.1.0 starting... ===")

# ------------------------------------------------------------
# SYSTEM PATH FIX
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# ------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[AI_MATCHLAB] %(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("aimatchlab")

# ------------------------------------------------------------
# IMPORT ENGINES (safe fallbacks)
# ------------------------------------------------------------
def try_import_engine(name):
    try:
        mod = __import__(f"services.{name}", fromlist=["*"])
        logger.info(f"{name} loaded OK")
        return mod
    except:
        logger.warning(f"{name} missing")
        return None

history_engine      = try_import_engine("history_engine")
matchplan_engine    = try_import_engine("matchplan_engine")
standings_engine    = try_import_engine("standings_engine")
smartmoney_engine   = try_import_engine("smartmoney_engine")
goalmatrix_engine   = try_import_engine("goalmatrix_engine")
heatmap_engine      = try_import_engine("heatmap_engine")

# ------------------------------------------------------------
# ENVIRONMENT CONFIG
# ------------------------------------------------------------
APP_VERSION = "AI MatchLab v1.1.0 — Unified RealData Hub"
APP_ENV = os.getenv("AI_MATCHLAB_ENV", "production")

LIVE_HUB_URL = os.getenv("AI_MATCHLAB_LIVE_HUB_URL", "").strip()
LIVE_HUB_TIMEOUT = float(os.getenv("AI_MATCHLAB_LIVE_HUB_TIMEOUT", "4.0"))

# ------------------------------------------------------------
# FASTAPI APP
# ------------------------------------------------------------
app = FastAPI(
    title="AI MatchLab — Unified Hub",
    version="1.1.0",
    description="Unified real-time football intelligence hub"
)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ------------------------------------------------------------
# STARTUP / SHUTDOWN
# ------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 AI MatchLab starting...")
    if httpx:
        app.state.http = httpx.AsyncClient(timeout=LIVE_HUB_TIMEOUT)
        logger.info("Live Hub client ready")
    else:
        app.state.http = None
        logger.error("httpx missing — Live Hub disabled")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 AI MatchLab shutting down...")
    if getattr(app.state, "http", None):
        try:
            await app.state.http.aclose()
        except:
            pass

# ------------------------------------------------------------
# LIVE HUB CALLER
# ------------------------------------------------------------
async def call_live_hub(path: str, params: Optional[Dict[str, Any]] = None):
    if not LIVE_HUB_URL:
        return {"ok": False, "error": "live_hub_not_configured", "data": None}

    if httpx is None:
        return {"ok": False, "error": "httpx_missing", "data": None}

    url = LIVE_HUB_URL.rstrip("/") + "/" + path.lstrip("/")
    client = app.state.http

    try:
        start = time.perf_counter()
        r = await client.get(url, params=params)
        duration = round((time.perf_counter() - start) * 1000, 1)

        r.raise_for_status()

        try:
            data = r.json()
        except:
            data = {"raw": r.text}

        return {"ok": True, "ms": duration, "data": data}

    except Exception as e:
        logger.warning(f"[LiveHub] request failed: {e}")
        return {"ok": False, "error": str(e), "data": None}

# ------------------------------------------------------------
# UI ROOT
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_version": APP_VERSION,
            "app_env": APP_ENV,
            "live_hub": bool(LIVE_HUB_URL),
            "ts": time.time()
        }
    )

# ------------------------------------------------------------
# NEW: SYSTEM STATUS ENDPOINT (B1)
# ------------------------------------------------------------
@app.get("/api/system/status", response_class=JSONResponse)
async def system_status():

    # ping Live Hub
    live_hub_info = {"configured": bool(LIVE_HUB_URL), "ok": False, "ping": None}
    if LIVE_HUB_URL and httpx:
        ping = await call_live_hub("health")
        live_hub_info["ok"] = ping.get("ok", False)
        live_hub_info["ping"] = ping.get("ms", None)

    engines = {
        "history": bool(history_engine),
        "matchplan": bool(matchplan_engine),
        "standings": bool(standings_engine),
        "smartmoney": bool(smartmoney_engine),
        "goalmatrix": bool(goalmatrix_engine),
        "heatmap": bool(heatmap_engine),
    }

    return {
        "ok": True,
        "version": APP_VERSION,
        "env": APP_ENV,
        "timestamp": dt.datetime.utcnow().isoformat(),
        "live_hub": live_hub_info,
        "engines": engines,
    }

# ------------------------------------------------------------
# LIVE ENDPOINTS
# ------------------------------------------------------------
@app.get("/api/live/overview", response_class=JSONResponse)
async def live_overview(league: Optional[str] = None):
    params = {"league": league} if league else None
    return await call_live_hub("live/overview", params)

@app.get("/api/live/match/{match_id}", response_class=JSONResponse)
async def live_match(match_id: str):
    return await call_live_hub(f"live/match/{match_id}")
