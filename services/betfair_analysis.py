# ============================================================
# EURO_GOALS — BETFAIR ANALYSIS ENGINE v9.7.7 PRO+
# Tracks Betfair market snapshots (in-memory), computes trend
# and exposes "hot markets" by absolute movement.
# ============================================================

import os, time, requests
from collections import deque
from typing import Dict, List

WORKER_BASE = (os.getenv("SMARTMONEY_WORKER_URL", "") or "").rstrip("/")

# store last N points per marketId (simple in-mem ring buffer)
MAX_POINTS = 60  # ~20min if we sample ανά 20s στο UI ή ~3min στο loop
_history: Dict[str, deque] = {}
# shape of point: {"ts": 1700000000, "runners": {name: lastPriceTraded}}

def _now() -> int:
    return int(time.time())

def _fetch_odds(market_id: str):
    if not WORKER_BASE:
        return {}
    try:
        r = requests.get(f"{WORKER_BASE}/betfair/odds?market={market_id}", timeout=10)
        if not r.ok:
            return {}
        j = r.json()
        out = {}
        for x in j.get("runners", []):
            name = (x.get("name") or "").strip()
            if name:
                out[name] = x.get("lastPriceTraded")
        return {"marketId": market_id, "runners": out, "ts": _now()}
    except Exception:
        return {}

def update_market(market_id: str):
    """Pull a fresh snapshot from Worker and append to history."""
    snap = _fetch_odds(market_id)
    if not snap:
        return {"marketId": market_id, "ok": False}
    dq = _history.setdefault(market_id, deque(maxlen=MAX_POINTS))
    dq.append(snap)
    return {"marketId": market_id, "ok": True, "ts": snap["ts"]}

def get_markets_list() -> List[Dict]:
    """Fetch list of available Betfair markets from Worker."""
    if not WORKER_BASE:
        return []
    try:
        r = requests.get(f"{WORKER_BASE}/betfair/markets", timeout=10)
        if not r.ok:
            return []
        data = r.json()
        return data.get("markets", [])
    except Exception:
        return []

def _delta_pct(cur, old) -> float:
    try:
        cur = float(cur); old = float(old)
        if old == 0: return 0.0
        return round((cur - old) / old * 100.0, 2)
    except Exception:
        return 0.0

def _last_two(dq: deque):
    if len(dq) < 2:
        return None, None
    return dq[-2], dq[-1]

def _first_last(dq: deque):
    if len(dq) < 2:
        return None, None
    return dq[0], dq[-1]

def get_market_view(market_id: str):
    """Return current view + short-term & long-term deltas per runner."""
    dq = _history.get(market_id, deque())
    prev, last = _last_two(dq)
    first, _ = _first_last(dq)
    runners = (last or {}).get("runners", {})
    rows = []
    for name, cur in runners.items():
        short = _delta_pct(cur, (prev or {"runners": {}})["runners"].get(name, cur))
        long = _delta_pct(cur, (first or {"runners": {}})["runners"].get(name, cur))
        rows.append({
            "runner": name,
            "current": cur,
            "delta_short": short,   # % vs previous point
            "delta_long": long      # % vs first point in buffer
        })
    return {
        "marketId": market_id,
        "points": len(dq),
        "updated": (last or {}).get("ts"),
        "rows": rows
    }

def get_hot_markets(limit=10):
    """Rank markets by max |long delta| across runners."""
    scores = []
    for mid, dq in _history.items():
        first, last = _first_last(dq)
        if not (first and last): 
            continue
        max_abs = 0.0
        for name, cur in (last.get("runners") or {}).items():
            base = (first.get("runners") or {}).get(name, cur)
            d = abs(_delta_pct(cur, base))
            if d > max_abs:
                max_abs = d
        scores.append((max_abs, mid))
    scores.sort(reverse=True)
    top = []
    for s, mid in scores[:limit]:
        top.append({"marketId": mid, "score": s})
    return {"count": len(top), "top": top}
