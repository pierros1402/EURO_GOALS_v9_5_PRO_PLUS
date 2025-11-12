# ============================================================
# EURO_GOALS SMARTMONEY ENGINE — v9.8.0 PRO+ UNIFIED SOURCE MASK
# Sources: Betfair (masked as SRC01), Bet365, Stoiximan, OPAP
# Normalizes odds and exposes a unified snapshot per match_id
# ============================================================

import os, time, math, json, requests

# -------------------------
# Config (Render ENV)
# -------------------------
WORKER_BASE           = os.getenv("SMARTMONEY_WORKER_URL", "").rstrip("/")
BET365_API_URL        = os.getenv("BET365_API_URL", "").rstrip("/")
STOIXIMAN_API_URL     = os.getenv("STOIXIMAN_API_URL", "").rstrip("/")
OPAP_API_URL          = os.getenv("OPAP_API_URL", "").rstrip("/")
REQUEST_TIMEOUT       = float(os.getenv("SM_REQUEST_TIMEOUT", "8"))
CACHE_TTL_SEC         = int(os.getenv("SM_CACHE_TTL", "15"))

# Optional mapping of match_id -> marketId (for Betfair)
MAP_MARKET_JSON = os.getenv("SM_MARKET_MAP_JSON", "")
MARKET_MAP = {}
try:
    if MAP_MARKET_JSON.strip():
        MARKET_MAP = json.loads(MAP_MARKET_JSON)
except Exception:
    MARKET_MAP = {}

_cache = {}
_cache_ts = {}

def _cache_get(key, ttl=CACHE_TTL_SEC):
    ts = _cache_ts.get(key, 0)
    if time.time() - ts < ttl:
        return _cache.get(key)
    return None

def _cache_set(key, val):
    _cache[key] = val
    _cache_ts[key] = time.time()

def _get(url):
    r = requests.get(url, headers={"User-Agent": "EURO_GOALS/SmartMoney"}, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()

# ------------------------------------------------------------
# INTERNAL SOURCE MASK
# ------------------------------------------------------------
SOURCE_MAP = {
    "betfair": "SRC01",       # internal hidden feed
    "flashscore": "SRC02",    # reserved hidden feed
    "sofascore": "SRC02",     # reserved hidden feed
    "bet365": "Bet365",
    "stoiximan": "Stoiximan",
    "opap": "OPAP"
}

def mask_source(name: str) -> str:
    return SOURCE_MAP.get(str(name).lower(), "FeedX")

# ------------------------------------------------------------
# ADAPTERS
# ------------------------------------------------------------
def _betfair_odds(match_id: str):
    """Pull runners/odds from Cloudflare Worker (public Betfair)."""
    if not WORKER_BASE:
        return {}
    market_id = MARKET_MAP.get(match_id, match_id)
    url = f"{WORKER_BASE}/betfair/odds?market={market_id}"
    try:
        data = _get(url)
        runners = data.get("runners", [])
        out = {}
        for r in runners:
            name = (r.get("name") or "").strip()
            price = r.get("lastPriceTraded")
            if name and price:
                out[name] = float(price)
        return {"source": "betfair", "odds": out}
    except Exception:
        return {}

def _bet365_odds(match_id: str):
    if not BET365_API_URL:
        return {}
    url = f"{BET365_API_URL}/odds?match={match_id}"
    try:
        data = _get(url)
        odds = data.get("odds", {})
        return {"source": "bet365", "odds": _stringify_keys(odds)}
    except Exception:
        return {}

def _stoiximan_odds(match_id: str):
    if not STOIXIMAN_API_URL:
        return {}
    url = f"{STOIXIMAN_API_URL}/odds?match={match_id}"
    try:
        data = _get(url)
        odds = data.get("odds", {})
        return {"source": "stoiximan", "odds": _stringify_keys(odds)}
    except Exception:
        return {}

def _opap_odds(match_id: str):
    if not OPAP_API_URL:
        return {}
    url = f"{OPAP_API_URL}/odds?match={match_id}"
    try:
        data = _get(url)
        odds = data.get("odds", {})
        return {"source": "opap", "odds": _stringify_keys(odds)}
    except Exception:
        return {}

def _stringify_keys(d):
    return {str(k): v for k, v in d.items()} if isinstance(d, dict) else {}

# ------------------------------------------------------------
# PUBLIC API
# ------------------------------------------------------------
def get_odds_snapshot(match_id: str):
    """
    Returns unified odds dict by market key (1, X, 2, +2.5, -2.5, BTTS, etc.)
    merged across sources with median aggregation.
    """
    key = f"sm:odds:{match_id}"
    cached = _cache_get(key)
    if cached:
        return cached

    sources = []
    bf = _betfair_odds(match_id)
    if bf: sources.append(bf)
    b365 = _bet365_odds(match_id)
    if b365: sources.append(b365)
    stx = _stoiximan_odds(match_id)
    if stx: sources.append(stx)
    opap = _opap_odds(match_id)
    if opap: sources.append(opap)

    # unify by market key
    buckets = {}
    for s in sources:
        for k, v in (s.get("odds") or {}).items():
            try:
                v = float(v)
            except Exception:
                continue
            buckets.setdefault(k, []).append(v)

    unified = {}
    for k, arr in buckets.items():
        arr = sorted(arr)
        mid = arr[len(arr)//2]  # median
        unified[k] = round(mid, 3)

    out = {
        "unified": unified,
        "per_source": { mask_source(s["source"]): s["odds"] for s in sources if "source" in s },
        "sources": [mask_source(s.get("source")) for s in sources]
    }
    _cache_set(key, out)
    return out

# ------------------------------------------------------------
# SMARTMONEY SIGNALS
# ------------------------------------------------------------
def get_smartmoney_signals(match_id: str):
    snapshot = get_odds_snapshot(match_id)
    odds = snapshot.get("unified", {})
    sig = []

    if _lt(odds.get("1"), 2.0):
        sig.append({"type": "sharp_action", "market": "1", "dir": "down", "delta": -0.05})
    if _gt(odds.get("2"), 4.0):
        sig.append({"type": "steam_move", "market": "2", "dir": "up", "delta": +0.07})
    if odds.get("+2.5") and 1.60 <= float(odds["+2.5"]) <= 1.95:
        sig.append({"type": "total_goals_bias", "market": "+2.5", "dir": "down", "delta": -0.03})

    return sig

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def _lt(x, thr):
    try: return float(x) < thr
    except: return False

def _gt(x, thr):
    try: return float(x) > thr
    except: return False
