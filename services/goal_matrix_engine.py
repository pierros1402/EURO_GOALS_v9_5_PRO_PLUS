# ============================================================
# EURO_GOALS — GOAL MATRIX ENGINE v9.8.0 PRO+
# ============================================================
# Λειτουργία:
# 1) Αν υπάρχει Cloudflare Worker → /goal_matrix?match={match_id}
# 2) Αλλιώς fallback: υπολογισμός xG/heatmap από ενοποιημένα odds
#    του SmartMoney Engine (χωρίς να εκτίθενται οι πραγματικές πηγές).
# ============================================================

from __future__ import annotations
import os, time, math, requests
from typing import Dict, Any, List

# SmartMoney snapshot (ενιαία odds από Worker)
from .smartmoney_engine import get_odds_snapshot

# -------------------------
# Config (ENV)
# -------------------------
WORKER_BASE: str = os.getenv("SMARTMONEY_WORKER_URL", "").rstrip("/")
REQUEST_TIMEOUT: float = float(os.getenv("SM_REQUEST_TIMEOUT", "8"))
CACHE_TTL_SEC: int = int(os.getenv("SM_CACHE_TTL", "15"))

# optional: map match_id -> external market id (αν θέλεις custom mapping)
# π.χ. SM_MARKET_MAP_JSON='{"12345":"1.2345678"}'
import json
MARKET_MAP: Dict[str, str] = {}
try:
    _m = os.getenv("SM_MARKET_MAP_JSON", "")
    if _m and _m.strip():
        MARKET_MAP = json.loads(_m)
except Exception:
    MARKET_MAP = {}

# -------------------------
# Internal cache
# -------------------------
_cache: Dict[str, Any] = {}
_cache_ts: Dict[str, float] = {}

def _cache_get(k: str, ttl: int = CACHE_TTL_SEC):
    ts = _cache_ts.get(k, 0.0)
    if time.time() - ts < ttl:
        return _cache.get(k)
    return None

def _cache_set(k: str, v: Any):
    _cache[k] = v
    _cache_ts[k] = time.time()

# -------------------------
# HTTP helper
# -------------------------
def _get_json(url: str) -> Dict[str, Any]:
    r = requests.get(url, headers={"User-Agent": "EURO_GOALS/GoalMatrix"}, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()

# ============================================================
# PUBLIC API
# ============================================================
def get_goal_matrix(match_id: str) -> Dict[str, Any]:
    """
    Επιστρέφει:
      {
        "xg_home": float,
        "xg_away": float,
        "likely_goals": "0-2" | "2-3" | "3-4+",
        "heatmap": [[float]*10]*10
      }
    Πρώτα δοκιμάζει Worker (/goal_matrix?match=). Αν δεν απαντήσει,
    κάνει fallback σε τοπικό υπολογισμό από τα unified odds.
    """
    key = f"gm:insights:{match_id}"
    cached = _cache_get(key)
    if cached is not None:
        return cached

    # --- 1) Προσπάθεια μέσω Worker (αν έχεις υλοποιήσει το endpoint)
    if WORKER_BASE:
        try:
            ext_id = MARKET_MAP.get(match_id, match_id)
            data = _get_json(f"{WORKER_BASE}/goal_matrix?match={ext_id}")
            # Αν ο Worker δώσει έγκυρο payload, το χρησιμοποιούμε ως έχει
            if isinstance(data, dict) and "xg_home" in data and "xg_away" in data:
                result = {
                    "xg_home": round(float(data.get("xg_home", 1.2)), 2),
                    "xg_away": round(float(data.get("xg_away", 1.1)), 2),
                    "likely_goals": str(data.get("likely_goals", "2-3")),
                    "heatmap": data.get("heatmap") or _default_heatmap(),
                }
                _cache_set(key, result)
                return result
        except Exception:
            # σιωπηρό fallback
            pass

    # --- 2) Fallback: υπολογισμός από SmartMoney unified odds
    snap = get_odds_snapshot(match_id)
    odds = snap.get("unified", {})

    # Εκτίμηση “expected total goals” (μ) από την αγορά Over/Under 2.5
    # Χρησιμοποιούμε μια ομαλή προσέγγιση: μ ≈ 0.8 + 3.2*(1/odds_o25)
    o25 = _num(odds.get("+2.5")) or 1.85  # default τιμή αν λείπει
    mu = 0.8 + 3.2 * (1.0 / o25)

    # Κατανομή μ μεταξύ home/away με βάση τις τιμές 1/2 (πιθανότητες νίκης)
    p1 = _inv(odds.get("1"))  # περίπου πιθανότητα νίκης του γηπεδούχου
    p2 = _inv(odds.get("2"))
    den = max(p1 + p2, 1e-6)
    xg_home = mu * (p1 / den)
    xg_away = mu - xg_home

    likely = "0-2" if mu < 2.0 else ("2-3" if mu < 2.8 else "3-4+")

    result = {
        "xg_home": round(xg_home, 2),
        "xg_away": round(xg_away, 2),
        "likely_goals": likely,
        "heatmap": _build_heatmap(mu, xg_home, xg_away),
    }
    _cache_set(key, result)
    return result

# ============================================================
# HELPERS
# ============================================================
def _inv(o) -> float:
    try:
        return 1.0 / float(o)
    except Exception:
        return 0.0

def _num(o) -> float | None:
    try:
        return float(o)
    except Exception:
        return None

def _default_heatmap(n: int = 10) -> List[List[float]]:
    # σταθερό χαμηλό pattern
    return [[0.05 for _ in range(n)] for _ in range(n)]

def _build_heatmap(mu: float, xh: float, xa: float, n: int = 10) -> List[List[float]]:
    """
    Απλό heatmap (10x10) με ενίσχυση κεντρικών “κελιών” όταν ανεβαίνει το μ.
    Δεν είναι pitch map — λειτουργεί ως compact intensity grid για UI χρωματισμό.
    """
    cells = _default_heatmap(n)
    # βασική ενίσχυση γύρω από (4,5), (5,5), (4,6) ως “high-prob” περιοχές
    boost = min(1.0, max(0.0, (mu - 1.8) / 2.2 + 0.3))
    cells[4][5] = min(1.0, 0.6 + 0.4 * boost)
    cells[5][5] = min(1.0, 0.55 + 0.45 * boost)
    cells[4][6] = min(1.0, 0.65 + 0.35 * boost)

    # μικρή προσαρμογή υπέρ της ομάδας με υψηλότερο xG
    side_bias = 0.02 * (xh - xa)
    cells[4][5] = _clip01(cells[4][5] + side_bias)
    cells[5][5] = _clip01(cells[5][5] + side_bias * 0.7)

    return cells

def _clip01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)
