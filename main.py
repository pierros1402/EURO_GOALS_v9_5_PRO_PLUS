# ============================================================
# AI MatchLab v1.0.0 — EURO_GOALS PRO+ UNIFIED REALDATA MAIN
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
import datetime as dt
from typing import Optional, Dict, Any

# Optional httpx for Live Hub
try:
    import httpx
except ImportError:
    httpx = None

# ------------------------------------------------------------
# LOCAL IMPORTS (CONFIG)
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from config import (
    APP_NAME,
    APP_VERSION,
    APP_ENV,
    LIVE_HUB_URL,
    LIVE_HUB_TIMEOUT,
    logger,
)

print(f"=== [{APP_NAME}] {APP_VERSION} ACTIVE ===")

# ------------------------------------------------------------
# IMPORT ENGINES (safe fallbacks from services/)
# ------------------------------------------------------------
history_engine = None
matchplan_engine = None
standings_engine = None
smartmoney_engine = None
goalmatrix_engine = None
heatmap_engine = None

try:
    from services import history_engine as _h
    history_engine = _h
    logger.info("history_engine loaded OK")
except Exception:
    logger.warning("history_engine missing")

try:
    from services import matchplan_engine as _m
    matchplan_engine = _m
    logger.info("matchplan_engine loaded OK")
except Exception:
    logger.warning("matchplan_engine missing")

try:
    from services import standings_engine as _s
    standings_engine = _s
    logger.info("standings_engine loaded OK")
except Exception:
    logger.warning("standings_engine missing")

try:
    from services import smartmoney_engine as _sm
    smartmoney_engine = _sm
    logger.info("smartmoney_engine loaded OK")
except Exception:
    logger.warning("smartmoney_engine missing")

try:
    from services import goalmatrix_engine as _gm
    goalmatrix_engine = _gm
    logger.info("goalmatrix_engine loaded OK")
except Exception:
    logger.warning("goalmatrix_engine missing")

try:
    from services import heatmap_engine as _hm
    heatmap_engine = _hm
    logger.info("heatmap_engine loaded OK")
except Exception:
    logger.warning("heatmap_engine missing")

# ------------------------------------------------------------
# FASTAPI APP
# ------------------------------------------------------------
app = FastAPI(
    title=f"{APP_NAME} — EURO_GOALS PRO+ Unified Hub",
    version="1.0.0",
    description="Unified real-time European football data platform (AI MatchLab / EURO_GOALS PRO+).",
)

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ------------------------------------------------------------
# STARTUP / SHUTDOWN
# ------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 AI MatchLab starting...")
    if httpx is None:
        logger.error("httpx not installed; Live Hub disabled")
        app.state.http = None
    else:
        app.state.http = httpx.AsyncClient(timeout=LIVE_HUB_TIMEOUT)
        if LIVE_HUB_URL:
            logger.info(f"Live Hub client ready → {LIVE_HUB_URL}")
        else:
            logger.warning("Live Hub URL is empty; live endpoints will return not_configured")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 AI MatchLab shutting down...")
    if getattr(app.state, "http", None):
        try:
            await app.state.http.aclose()
        except Exception:
            pass

# ------------------------------------------------------------
# LIVE HUB CALLER
# ------------------------------------------------------------
async def call_live_hub(path: str, params: Optional[Dict[str, Any]] = None):
    """
    Generic proxy προς Live Hub (Betfair/feeds/κλπ),
    χωρίς να φαίνεται το όνομα του provider στο UI.
    """
    if not LIVE_HUB_URL:
        return {"ok": False, "error": "live_hub_not_configured", "data": None}

    if httpx is None:
        return {"ok": False, "error": "httpx_missing", "data": None}

    url = LIVE_HUB_URL.rstrip("/") + "/" + path.lstrip("/")
    client = app.state.http

    try:
        r = await client.get(url, params=params)
        r.raise_for_status()
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text}
        return {"ok": True, "data": data}
    except Exception as e:
        logger.warning(f"[LiveHub] request failed: {e}")
        return {
            "ok": False,
            "error": "request_failed",
            "details": str(e),
            "data": None,
        }

# ------------------------------------------------------------
# UI ROOT
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Κεντρικό UI (index.html) — AI MatchLab live dashboard.
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_version": APP_VERSION,
            "app_env": APP_ENV,
            "live_hub": bool(LIVE_HUB_URL),
            "ts": time.time(),
        },
    )

# ------------------------------------------------------------
# HEALTH
# ------------------------------------------------------------
@app.get("/health", response_class=JSONResponse)
async def health():
    return {
        "ok": True,
        "status": "alive",
        "version": APP_VERSION,
        "env": APP_ENV,
    }

@app.get("/api/system/health", response_class=JSONResponse)
async def system_health():
    return {
        "ok": True,
        "version": APP_VERSION,
        "env": APP_ENV,
        "live_hub": bool(LIVE_HUB_URL),
        "engines": {
            "history": bool(history_engine),
            "matchplan": bool(matchplan_engine),
            "standings": bool(standings_engine),
            "smartmoney": bool(smartmoney_engine),
            "goalmatrix": bool(goalmatrix_engine),
            "heatmap": bool(heatmap_engine),
        },
    }

# ------------------------------------------------------------
# LIVE
# ------------------------------------------------------------
@app.get("/api/live/overview", response_class=JSONResponse)
async def live_overview(league: Optional[str] = None):
    params = {"league": league} if league else None
    return await call_live_hub("live/overview", params)

@app.get("/api/live/match/{match_id}", response_class=JSONResponse)
async def live_match(match_id: str):
    return await call_live_hub(f"live/match/{match_id}")

# ------------------------------------------------------------
# HISTORY
# ------------------------------------------------------------
@app.get("/api/history/{competition}", response_class=JSONResponse)
async def history(competition: str):
    if not history_engine:
        return {"ok": False, "error": "history_engine_missing"}

    try:
        fn = getattr(history_engine, "get_competition_history", None)
        if fn is None:
            return {"ok": False, "error": "get_competition_history_not_found"}

        if asyncio.iscoroutinefunction(fn):
            data = await fn(competition)
        else:
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(
                None, fn, competition
            )
        return {"ok": True, "data": data}
    except Exception as e:
        logger.exception("history endpoint failed")
        return {"ok": False, "error": str(e)}

# ------------------------------------------------------------
# MATCHPLAN
# ------------------------------------------------------------
@app.get("/api/matchplan/today", response_class=JSONResponse)
async def matchplan_today():
    if not matchplan_engine:
        return {"ok": False, "error": "matchplan_engine_missing"}

    try:
        fn = getattr(matchplan_engine, "get_today_matchplan", None)
        if fn is None:
            return {"ok": False, "error": "get_today_matchplan_not_found"}

        if asyncio.iscoroutinefunction(fn):
            data = await fn()
        else:
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, fn)
        return {"ok": True, "data": data}
    except Exception as e:
        logger.exception("matchplan endpoint failed")
        return {"ok": False, "error": str(e)}

# ------------------------------------------------------------
# STANDINGS
# ------------------------------------------------------------
@app.get("/api/standings/{league}", response_class=JSONResponse)
async def standings(league: str):
    if not standings_engine:
        return {"ok": False, "error": "standings_engine_missing"}

    try:
        fn = getattr(standings_engine, "get_standings", None)
        if fn is None:
            return {"ok": False, "error": "get_standings_not_found"}

        if asyncio.iscoroutinefunction(fn):
            data = await fn(league)
        else:
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, fn, league)
        return {"ok": True, "data": data}
    except Exception as e:
        logger.exception("standings endpoint failed")
        return {"ok": False, "error": str(e)}

# ------------------------------------------------------------
# SMARTMONEY
# ------------------------------------------------------------
@app.get("/api/smartmoney/overview", response_class=JSONResponse)
async def smartmoney():
    if not smartmoney_engine:
        return {"ok": False, "error": "smartmoney_engine_missing"}

    try:
        fn = getattr(smartmoney_engine, "get_overview", None)
        if fn is None:
            return {"ok": False, "error": "get_overview_not_found"}

        if asyncio.iscoroutinefunction(fn):
            data = await fn()
        else:
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, fn)
        return {"ok": True, "data": data}
    except Exception as e:
        logger.exception("smartmoney endpoint failed")
        return {"ok": False, "error": str(e)}

# ------------------------------------------------------------
# GOALMATRIX
# ------------------------------------------------------------
@app.get("/api/goalmatrix/overview", response_class=JSONResponse)
async def goalmatrix():
    if not goalmatrix_engine:
        return {"ok": False, "error": "goalmatrix_engine_missing"}

    try:
        fn = getattr(goalmatrix_engine, "get_overview", None)
        if fn is None:
            return {"ok": False, "error": "get_overview_not_found"}

        if asyncio.iscoroutinefunction(fn):
            data = await fn()
        else:
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, fn)
        return {"ok": True, "data": data}
    except Exception as e:
        logger.exception("goalmatrix endpoint failed")
        return {"ok": False, "error": str(e)}

# ------------------------------------------------------------
# HEATMAP
# ------------------------------------------------------------
@app.get("/api/heatmap/overview", response_class=JSONResponse)
async def heatmap():
    if not heatmap_engine:
        return {"ok": False, "error": "heatmap_engine_missing"}

    try:
        fn = getattr(heatmap_engine, "get_overview", None)
        if fn is None:
            return {"ok": False, "error": "get_overview_not_found"}

        if asyncio.iscoroutinefunction(fn):
            data = await fn()
        else:
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, fn)
        return {"ok": True, "data": data}
    except Exception as e:
        logger.exception("heatmap endpoint failed")
        return {"ok": False, "error": str(e)}
