# ============================================================
# EURO_GOALS GOAL_MATRIX ENGINE — v9.7.4 REAL DATA CHAIN
# ============================================================

import os, time, math, requests
from .smartmoney_engine import get_odds_snapshot

WORKER_BASE = os.getenv("SMARTMONEY_WORKER_URL", "").rstrip("/")
REQUEST_TIMEOUT = float(os.getenv("SM_REQUEST_TIMEOUT", "8"))
CACHE_TTL_SEC = int(os.getenv("SM_CACHE_TTL", "15"))

_cache, _cache_ts = {}, {}

# ------------------------------------------------------------
# CACHE HELPERS
# ------------------------------------------------------------
def _cache_get(k, ttl=CACHE_TTL_SEC):
    ts = _cache_ts.get(k, 0)
    if time.time() - ts < ttl:
        return _cache.get(k)
    return None

def _cache_set(k, v):
    _cache[k], _cache_ts[k] = v, time.time()

def _get(url):
    r = requests.get(url, headers={"User-Agent": "EURO_GOALS/Goal_Matrix"}, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()

# ------------------------------------------------------------
# MAIN ENTRY
# ------------------------------------------------------------
def get_goal_matrix(match_id: str):
    """
    Fetch goal data directly from Worker (/goal_matrix),
    or compute locally from SmartMoney odds if not available.
    """
    key = f"gm:insights:{match_id}"
    cached = _cache_get(key)
    if cached:
        return cached

    data = None
    if WORKER_BASE:
        try:
            data = _get(f"{WORKER_BASE}/goal_matrix?match={match_id}")
        except Exception:
            data = None

    if data and isinstance(data, dict) and "xg_home" in data:
        result = {
            "xg_home": round(data.get("xg_home", 1.2), 2),
            "xg_away": round(data.get("xg_away", 1.1), 2),
            "likely_goals": data.get("likely_goals", "2-3"),
            "heatmap": data.get("heatmap", [])
        }
    else:
        # Fallback: local calculation from odds
        snap = get_odds_snapshot(match_id)
        odds = snap.get("unified", {})
        p1 = _inv(odds.get("1"))
        p2 = _inv(odds.get("2"))
        o25 = _num(odds.get("+2.5")) or 1.9
        mu = 0.8 + 3.2 * (1 / o25)
        xh = mu * (p1 / (p1 + p2 + 1e-6))
        xa = mu - xh
        likely = "0-2" if mu < 2.0 else ("2-3" if mu < 2.8 else "3-4+")
        result = {
            "xg_home": round(xh, 2),
            "xg_away": round(xa, 2),
            "likely_goals": likely,
            "heatmap": _build_heatmap(mu)
        }

    _cache_set(key, result)
    return result

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def _inv(o):
    try:
        return 1 / float(o)
    except:
        return 0.0

def _num(o):
    try:
        return float(o)
    except:
        return None

def _build_heatmap(mu):
    n = 10
    cells = [[0.05 for _ in range(n)] for _ in range(n)]
    boost = min(1.0, (mu - 1.8) / 2.2 + 0.3)
    cells[4][5] = min(1.0, 0.6 + 0.4 * boost)
    cells[5][5] = min(1.0, 0.55 + 0.45 * boost)
    cells[4][6] = min(1.0, 0.65 + 0.35 * boost)
    return cells

# ------------------------------------------------------------
# BACKWARD COMPATIBILITY
# ------------------------------------------------------------
# Παλιά έκδοση που χρησιμοποιούσε το όνομα get_goalmatrix_insights
get_goalmatrix_insights = get_goal_matrix
