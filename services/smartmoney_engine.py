# ============================================================
# EURO_GOALS SMARTMONEY ENGINE — v9.7.4 UNIFIED WORKER LINK
# ============================================================

import os, time, json, requests

WORKER_BASE = os.getenv("SMARTMONEY_WORKER_URL", "").rstrip("/")
REQUEST_TIMEOUT = float(os.getenv("SM_REQUEST_TIMEOUT", "8"))
CACHE_TTL_SEC = int(os.getenv("SM_CACHE_TTL", "15"))

_cache, _cache_ts = {}, {}

def _cache_get(k, ttl=CACHE_TTL_SEC):
    ts = _cache_ts.get(k, 0)
    if time.time() - ts < ttl:
        return _cache.get(k)
    return None

def _cache_set(k, v):
    _cache[k], _cache_ts[k] = v, time.time()

def _get(url):
    r = requests.get(url, headers={"User-Agent": "EURO_GOALS/SmartMoney"}, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()

# ------------------------------------------------------------
# Main Odds Aggregator (reads from unified Worker)
# ------------------------------------------------------------
def get_odds_snapshot(match_id: str):
    """
    Fetch odds from Cloudflare unified Worker (v4.0)
    Combines Betfair + Bet365 + Stoiximan + OPAP + GoalMatrix
    """
    key = f"sm:odds:{match_id}"
    cached = _cache_get(key)
    if cached:
        return cached

    if not WORKER_BASE:
        return {"error": "Worker URL missing"}

    # --- call each source from Worker ---
    sources = []
    endpoints = [
        f"{WORKER_BASE}/betfair/odds?market={match_id}",
        f"{WORKER_BASE}/bet365/odds?match={match_id}",
        f"{WORKER_BASE}/stoiximan/odds?match={match_id}",
        f"{WORKER_BASE}/opap/odds?match={match_id}"
    ]
    for url in endpoints:
        try:
            data = _get(url)
            if "odds" in data:
                src = data.get("source", url.split('/')[-2])
                sources.append({"source": src, "odds": data["odds"]})
        except Exception:
            continue

    # --- aggregate (median per market) ---
    buckets = {}
    for s in sources:
        for k, v in (s.get("odds") or {}).items():
            try:
                v = float(v)
                buckets.setdefault(k, []).append(v)
            except Exception:
                pass

    unified = {}
    for k, arr in buckets.items():
        arr = sorted(arr)
        mid = arr[len(arr)//2]
        unified[k] = round(mid, 3)

    result = {
        "unified": unified,
        "per_source": {s["source"]: s["odds"] for s in sources if "source" in s},
        "sources": [s["source"] for s in sources],
    }
    _cache_set(key, result)
    return result

# ------------------------------------------------------------
# SmartMoney signals (basic heuristics)
# ------------------------------------------------------------
def get_smartmoney_signals(match_id: str):
    snapshot = get_odds_snapshot(match_id)
    odds = snapshot.get("unified", {})
    signals = []

    if _lt(odds.get("1"), 2.0):
        signals.append({"type": "sharp_action", "market": "1", "dir": "down", "delta": -0.05})
    if _gt(odds.get("2"), 4.0):
        signals.append({"type": "steam_move", "market": "2", "dir": "up", "delta": +0.07})
    if odds.get("+2.5") and 1.60 <= float(odds["+2.5"]) <= 1.95:
        signals.append({"type": "total_goals_bias", "market": "+2.5", "dir": "down", "delta": -0.03})

    return signals

def _lt(x, thr): 
    try: return float(x) < thr
    except: return False

def _gt(x, thr): 
    try: return float(x) > thr
    except: return False
