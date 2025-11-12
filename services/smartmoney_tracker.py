# ============================================================
# EURO_GOALS SMARTMONEY TRACKER — v9.7.7 PRO+
# Keep opening snapshot per match_id, compare with current odds,
# compute deltas and expose summary + top-moves.
# ============================================================

import time
from typing import Dict, List
from services.smartmoney_engine import get_odds_snapshot

# in-memory store (Render free: ok). If you want persistence -> add DB later.
_opening: Dict[str, Dict[str, float]] = {}   # match_id -> {market_key: opening_price}
_last: Dict[str, Dict] = {}                  # match_id -> {"time": "HH:MM:SS", "odds": {...}, "sources":[...]}
_moves: Dict[str, Dict[str, float]] = {}     # match_id -> {market_key: delta_pct}

WATCH_KEYS = ["1", "X", "2", "+2.5", "-2.5"]  # columns to show

def _pct(cur, base):
    try:
        cur = float(cur); base = float(base)
        if base == 0: return 0.0
        return round((cur - base) / base * 100.0, 2)
    except:
        return 0.0

def update_market(match_id: str):
    """Fetch current odds, store opening if first time, compute deltas."""
    snap = get_odds_snapshot(match_id)            # {"unified":{...}, "sources":[...]}
    cur = snap.get("unified", {}) or {}
    ts = time.strftime("%H:%M:%S")

    # first appearance -> freeze opening
    if match_id not in _opening:
        _opening[match_id] = {k: float(v) for k, v in cur.items() if _isnum(v)}

    # compute deltas vs opening
    base = _opening.get(match_id, {})
    movement = {}
    for k in set(list(base.keys()) + list(cur.keys())):
        if not k: continue
        movement[k] = _pct(cur.get(k), base.get(k, cur.get(k)))

    _last[match_id] = {"time": ts, "odds": cur, "sources": snap.get("sources", [])}
    _moves[match_id] = movement

    return {
        "match_id": match_id,
        "time": ts,
        "opening": base,
        "current": cur,
        "movement": movement,
        "sources": snap.get("sources", [])
    }

def get_tracker_summary():
    """Return compact list for dashboard (opening→current and delta)."""
    out = []
    for mid in list(_last.keys()):
        # refresh a bit when asked
        entry = update_market(mid)
        row = {
            "match_id": mid,
            "time": entry["time"],
            "sources": entry["sources"],
            "cols": {}
        }
        for k in WATCH_KEYS:
            o = entry["opening"].get(k)
            c = entry["current"].get(k)
            d = entry["movement"].get(k, 0.0)
            row["cols"][k] = {"open": o, "cur": c, "delta": d}
        out.append(row)
    return {"count": len(out), "rows": out}

def get_top_moves(limit=10):
    """Pick top matches by absolute delta on 1/X/2 (priority), then totals."""
    items = []
    for mid, mv in _moves.items():
        # focus on 1X2 primary; fallback to any key
        focus = [abs(mv.get("1", 0)), abs(mv.get("X", 0)), abs(mv.get("2", 0))]
        score = max(focus) if any(focus) else max([abs(mv.get(k, 0)) for k in WATCH_KEYS] or [0])
        items.append((score, mid))
    items.sort(reverse=True)
    top = []
    for score, mid in items[:limit]:
        row = {
            "match_id": mid,
            "score": score,
            "movement": {k: _moves[mid].get(k, 0.0) for k in WATCH_KEYS},
            "opening": _opening.get(mid, {}),
            "current": _last.get(mid, {}).get("odds", {}),
            "time": _last.get(mid, {}).get("time", ""),
            "sources": _last.get(mid, {}).get("sources", [])
        }
        top.append(row)
    return {"count": len(top), "top": top}

def _isnum(x):
    try:
        float(x); return True
    except:
        return False
