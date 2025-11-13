# ============================================================
# EURO_GOALS PRO+ v10.2.0 — UI + Advanced Betfair Engine
# - UI server (FastAPI)
# - SmartMoney & GoalMatrix engine πάνω από Cloudflare Worker
# - SmartMoney LOG (τελευταία alerts)
# - Flashscore fixtures proxy panel
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import os
import sys
import time
import asyncio
import datetime as dt
from typing import Any, Dict, List, Tuple

import httpx  # ΠΡΟΣΟΧΗ: να υπάρχει στο requirements.txt

print("=== [EURO_GOALS PRO+] v10.2.0 — UI + Advanced Engine ACTIVE ===")

# ------------------------------------------------------------
# SYSTEM PATH FIX
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# ------------------------------------------------------------
# CONFIG / ENV
# ------------------------------------------------------------
IS_RENDER = bool(os.getenv("RENDER", ""))

# Cloudflare Worker (raw data)
WORKER_BASE = os.getenv(
    "EG_WORKER_BASE",
    "https://eurogoals-live-proxy.pierros1402.workers.dev"
).rstrip("/")

SYSTEM_REFRESH_SECONDS = int(os.getenv("EG_SYSTEM_REFRESH", "10"))
BETFAIR_MARKET_LIMIT = int(os.getenv("EG_BF_MARKET_LIMIT", "10"))  # πόσα markets θα δουλεύουμε
FLASH_DEFAULT_LEAGUE = os.getenv(
    "EG_FS_DEFAULT_LEAGUE",
    "football/england/premier-league"
)

# ------------------------------------------------------------
# FASTAPI APP
# ------------------------------------------------------------
app = FastAPI(
    title="EURO_GOALS PRO+ v10.2.0 — UI + Engine",
    description="EURO_GOALS PRO+ — Unified UI + SmartMoney/GoalMatrix engine πάνω από τον Cloudflare Worker",
    version="10.2.0",
)

# Static / templates
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ------------------------------------------------------------
# IN-MEMORY STATE (SmartMoney log)
# ------------------------------------------------------------
SMARTMONEY_LOG: List[Dict[str, Any]] = []


# ============================================================
# HELPERS
# ============================================================

async def worker_get(path: str, params: Dict[str, Any] | None = None) -> Tuple[int, Dict[str, Any]]:
    """
    GET στο Cloudflare Worker και επιστρέφει (status_code, json_dict).
    """
    url = f"{WORKER_BASE}{path}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
        try:
            data = r.json()
        except Exception:
            data = {}
        return r.status_code, data
    except Exception as e:
        print(f"[EURO_GOALS] ⚠️ Worker JSON request failed: {e} (url={url})")
        return 0, {"error": str(e)}


async def worker_get_html(path: str, params: Dict[str, Any] | None = None) -> Tuple[int, str]:
    """
    GET στο Cloudflare Worker και επιστρέφει (status_code, html_text).
    Για Flashscore HTML passthrough.
    """
    url = f"{WORKER_BASE}{path}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
        return r.status_code, r.text
    except Exception as e:
        print(f"[EURO_GOALS] ⚠️ Worker HTML request failed: {e} (url={url})")
        return 0, f"<h3>Worker error: {e}</h3>"


def now_iso() -> str:
    return dt.datetime.utcnow().isoformat() + "Z"


def safe_float(x: Any) -> float | None:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


# ============================================================
# BETFAIR AGGREGATION HELPERS
# ============================================================

async def get_betfair_markets(limit: int = BETFAIR_MARKET_LIMIT) -> List[Dict[str, Any]]:
    """
    Παίρνει markets από τον Worker (/betfair/markets) με upper limit.
    """
    status, payload = await worker_get("/betfair/markets")
    if status != 200:
        print("[EURO_GOALS] ⚠️ Betfair markets error:", status, payload.get("error"))
        return []

    markets = payload.get("markets", [])
    if not isinstance(markets, list):
        return []
    return markets[:limit]


async def get_betfair_odds(market_id: str) -> Dict[str, Any]:
    """
    Παίρνει odds για ένα market από τον Worker (/betfair/odds?market=...).
    Επιστρέφει dict με runners.
    """
    status, payload = await worker_get("/betfair/odds", params={"market": market_id})
    if status != 200:
        return {"status": "error", "runners": [], "marketId": market_id}

    runners = payload.get("runners", [])
    if not isinstance(runners, list):
        runners = []
    return {"status": "ok", "runners": runners, "marketId": payload.get("marketId", market_id)}


def summarize_market_for_goal_matrix(market: Dict[str, Any], runners: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Παράγει μία γραμμή για το GoalMatrix panel από ένα Betfair market.
      - league: competition.name
      - match: eventName
      - initial_odds / current_odds: απόδοση φαβορί (min lastPriceTraded)
      - movement: placeholder "—" (δεν έχουμε ιστορικό ακόμα)
    """
    league = (market.get("competition") or {}).get("name") or ""
    match = market.get("eventName") or market.get("marketName") or "—"

    best_price = None
    for r in runners:
        lp = safe_float(r.get("lastPriceTraded"))
        if lp is None or lp <= 1.01:
            continue
        if best_price is None or lp < best_price:
            best_price = lp

    if best_price is None:
        initial_odds = None
        current_odds = None
        movement = "—"
    else:
        initial_odds = best_price
        current_odds = best_price
        movement = "—"

    return {
        "league": league,
        "match": match,
        "initial_odds": initial_odds,
        "current_odds": current_odds,
        "movement": movement,
    }


def summarize_market_for_smartmoney(market: Dict[str, Any], runners: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Πρώτη advanced εκδοχή SmartMoney signal πάνω σε Betfair:
      - χρησιμοποιεί το φαβορί (min lastPriceTraded)
      - αν η απόδοση του φαβορί < 1.80 -> 1 alert
      - αλλιώς 0 alerts
    """
    league = (market.get("competition") or {}).get("name") or ""
    match = market.get("eventName") or market.get("marketName") or "—"

    best_price = None
    for r in runners:
        lp = safe_float(r.get("lastPriceTraded"))
        if lp is None or lp <= 1.01:
            continue
        if best_price is None or lp < best_price:
            best_price = lp

    if best_price is None:
        odds = None
        alerts = 0
    else:
        odds = best_price
        alerts = 1 if best_price < 1.80 else 0

    return {
        "league": league,
        "match": match,
        "odds": odds,
        "change": "—",
        "alerts": alerts,
    }


def append_smartmoney_log(items: List[Dict[str, Any]], updated: str) -> None:
    """
    Κρατάμε τα τελευταία ~50 SmartMoney alerts σε in-memory log.
    Κάθε φορά που /api/smartmoney/summary βρίσκει alerts, τα περνάει εδώ.
    """
    global SMARTMONEY_LOG
    for row in items:
        if (row.get("alerts") or 0) > 0:
            SMARTMONEY_LOG.append(
                {
                    "ts": updated,
                    "league": row.get("league"),
                    "match": row.get("match"),
                    "odds": row.get("odds"),
                }
            )
    # κρατάμε μόνο τα τελευταία 50
    SMARTMONEY_LOG = SMARTMONEY_LOG[-50:]


# ============================================================
# ROUTES — PAGES
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Κεντρικό Unified Dashboard UI
    (χρησιμοποιεί index.html + partials που έχεις ήδη).
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "is_render": IS_RENDER,
            "fs_default_league": FLASH_DEFAULT_LEAGUE,
        },
    )


# ============================================================
# ROUTES — HEALTH
# ============================================================

@app.get("/health", response_class=JSONResponse)
async def health():
    """
    Απλό health check για Render + Worker reachability.
    """
    worker_status, worker_payload = await worker_get("/")
    return JSONResponse(
        {
            "status": "ok",
            "timestamp": now_iso(),
            "env": "render" if IS_RENDER else "local",
            "worker": {
                "base": WORKER_BASE,
                "http_status": worker_status,
                "payload_status": worker_payload.get("status", None),
                "version": worker_payload.get("version", None),
            },
        }
    )


# ============================================================
# ROUTES — API / JSON για το UI (goal_smart_refresh.js)
# ============================================================

@app.get("/api/system/status", response_class=JSONResponse)
async def api_system_status():
    """
    Ενιαίο status endpoint που περιμένει το goal_smart_refresh.js.
    """

    worker_status, worker_payload = await worker_get("/")

    ok = worker_status == 200 and not worker_payload.get("error")
    base_status = "ok" if ok else f"error: http={worker_status} err={worker_payload.get('error')}"

    engines = {
        "dowjones": base_status,
        "smartmoney": base_status,
        "goalmatrix": base_status,
    }

    return JSONResponse(
        {
            "status": "ok" if ok else "degraded",
            "timestamp": now_iso(),
            "engines": engines,
            "alerts": {
                # τα actual alerts έρχονται από το /api/smartmoney/summary,
                # εδώ κρατάμε μόνο placeholder για το summary bar
                "smartmoney": 0,
                "goalmatrix": 0,
            },
            "worker": {
                "base": WORKER_BASE,
                "http_status": worker_status,
                "version": worker_payload.get("version", None),
                "endpoints": worker_payload.get("endpoints", []),
            },
        }
    )


@app.get("/api/goal_matrix/summary", response_class=JSONResponse)
async def api_goal_matrix_summary():
    """
    Advanced GoalMatrix summary:
      - Παίρνει Betfair markets από τον Worker
      - Για κάθε market παίρνει runners/odds
      - Φτιάχνει πίνακα:
        league, match, initial_odds, current_odds, movement
    """

    markets = await get_betfair_markets(BETFAIR_MARKET_LIMIT)

    # ❗ Αν δεν βρούμε markets, ΔΕΝ ρίχνουμε 503.
    # Γυρίζουμε 200 με status="ok" και κενή λίστα,
    # ώστε το UI να γράφει "Δεν βρέθηκαν δεδομένα" χωρίς κόκκινο ERROR.
    if not markets:
        return JSONResponse(
            {
                "status": "ok",
                "updated": now_iso(),
                "total": 0,
                "items": [],
            }
        )

    tasks = []
    for m in markets:
        mid = m.get("id") or m.get("marketId")
        if not mid:
            continue
        tasks.append(get_betfair_odds(str(mid)))

    odds_results = await asyncio.gather(*tasks, return_exceptions=True)

    items: List[Dict[str, Any]] = []
    for market, res in zip(markets, odds_results):
        if isinstance(res, Exception):
            runners = []
        else:
            runners = res.get("runners", [])
        row = summarize_market_for_goal_matrix(market, runners)
        items.append(row)

    return JSONResponse(
        {
            "status": "ok",
            "updated": now_iso(),
            "total": len(items),
            "items": items,
        }
    )


@app.get("/api/smartmoney/summary", response_class=JSONResponse)
async def api_smartmoney_summary():
    """
    Advanced SmartMoney summary:
      - Χρησιμοποιεί τα ίδια Betfair markets
      - Δείχνει για κάθε match:
          league, match, odds(φαβορί), change(placeholder), alerts(0/1)
      - Alerts: 1 όταν το φαβορί έχει απόδοση < 1.80
      - Κρατά log των alerts (last 50) στο SMARTMONEY_LOG
    """

    markets = await get_betfair_markets(BETFAIR_MARKET_LIMIT)

    # ❗ Όπως και στο GoalMatrix, αν δεν υπάρχουν markets,
    # δεν στέλνουμε 503 αλλά "άδειο" OK.
    if not markets:
        updated = now_iso()
        return JSONResponse(
            {
                "status": "ok",
                "updated": updated,
                "total": 0,
                "alerts": 0,
                "items": [],
            }
        )

    tasks = []
    for m in markets:
        mid = m.get("id") or m.get("marketId")
        if not mid:
            continue
        tasks.append(get_betfair_odds(str(mid)))

    odds_results = await asyncio.gather(*tasks, return_exceptions=True)

    items: List[Dict[str, Any]] = []
    for market, res in zip(markets, odds_results):
        if isinstance(res, Exception):
            runners = []
        else:
            runners = res.get("runners", [])
        row = summarize_market_for_smartmoney(market, runners)
        items.append(row)

    total_alerts = sum(1 for r in items if (r.get("alerts") or 0) > 0)

    updated = now_iso()
    append_smartmoney_log(items, updated)

    return JSONResponse(
        {
            "status": "ok",
            "updated": updated,
            "total": len(items),
            "alerts": total_alerts,
            "items": items,
        }
    )


@app.get("/api/smartmoney/log", response_class=JSONResponse)
async def api_smartmoney_log():
    """
    Επιστρέφει τα τελευταία SmartMoney alerts (max 10) για το Log panel.
    """
    # τελευταία 10, με reverse (πιο πρόσφατο πρώτο)
    last_items = SMARTMONEY_LOG[-10:][::-1]
    return JSONResponse(
        {
            "updated": now_iso(),
            "items": last_items,
        }
    )


# ------------------------------------------------------------
# OPTIONAL: Alias για συμβατότητα με παλιό endpoint
# ------------------------------------------------------------
@app.get("/api/system/status/unified", response_class=JSONResponse)
async def api_system_status_unified_alias():
    """
    Alias ώστε αν κάπου χρησιμοποιούσαμε /api/system/status/unified,
    να παίρνει την ίδια απάντηση με /api/system/status.
    """
    return await api_system_status()


# ============================================================
# FLASHSCORE FIXTURES PROXY
# ============================================================

@app.get("/fs/fixtures_proxy", response_class=HTMLResponse)
async def fs_fixtures_proxy(league: str = FLASH_DEFAULT_LEAGUE):
    """
    Proxy για Flashscore fixtures μέσω Worker.
    Χρησιμοποιείται από το Flashscore panel (select + button).
    """
    status, html = await worker_get_html("/flashscore/fixtures", params={"league": league})
    if status != 200:
        return HTMLResponse(
            f"<h3>Flashscore error (status={status})</h3>",
            status_code=502,
        )
    return HTMLResponse(html)


# ============================================================
# GLOBAL EXCEPTION HANDLER (LOG)
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
