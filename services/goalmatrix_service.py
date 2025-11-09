# ============================================================
# GoalMatrix API Router – v1.1 Unified (EURO_GOALS PRO+)
# Συνδέεται με το goalmatrix_engine.py (cache + ανάλυση)
# Παρέχει:
#  - /api/goalmatrix/summary
#  - /api/goalmatrix/items
#  - /api/goalmatrix/feed   (PRO-friendly format)
#  - /api/goalmatrix/calc   (Poisson demo calc)
# ============================================================

from fastapi import APIRouter
from typing import List, Tuple
from . import goalmatrix_engine

router = APIRouter()

@router.get("/summary")
async def goalmatrix_summary():
    """Σύνοψη GoalMatrix από cache (status, total_matches, avg_goals, last_updated_ts)"""
    if goalmatrix_engine.cache.is_fresh:
        return goalmatrix_engine.cache.get_summary()
    await goalmatrix_engine.refresh_goalmatrix_once()
    return goalmatrix_engine.cache.get_summary()

@router.get("/items")
async def goalmatrix_items():
    """Ακατέργαστα items από το engine (league, home, away, xg_home, xg_away, expected_goals, tendency)"""
    if not goalmatrix_engine.cache.is_fresh:
        await goalmatrix_engine.refresh_goalmatrix_once()
    return {"items": goalmatrix_engine.cache.get_items()}

@router.get("/feed")
async def goalmatrix_feed():
    """
    PRO-friendly feed:
    Μετατρέπει τα engine items σε πεδία λ (lambda_home/away) + p_over/p_under + top_scores.
    NOTE: Εδώ χρησιμοποιούμε xG ως proxy για λ (ενδεικτικά).
    """
    if not goalmatrix_engine.cache.is_fresh:
        await goalmatrix_engine.refresh_goalmatrix_once()

    raw = goalmatrix_engine.cache.get_items()
    def approx_scores(lh: float, la: float) -> List[Tuple[str, float]]:
        # Απλός demo κατάλογος σκορ (ενδεικτικά ποσοστά που “κλείνουν” ≈ 40%)
        pairs = [("1-1", 0.12), ("2-1", 0.10), ("2-0", 0.08), ("1-0", 0.07), ("3-1", 0.05)]
        return pairs

    out = []
    for m in raw:
        lh = float(m.get("xg_home", 0.0))
        la = float(m.get("xg_away", 0.0))
        total = lh + la
        # χονδρική πιθανότητα over/under
        p_over = 0.65 if total >= 2.5 else (0.5 if total >= 2.2 else 0.35)
        p_under = 1.0 - p_over
        out.append({
            "league": m.get("league"),
            "home": m.get("home"),
            "away": m.get("away"),
            "lambda_home": round(lh, 3),
            "lambda_away": round(la, 3),
            "p_over": round(p_over, 3),
            "p_under": round(p_under, 3),
            "top_scores": approx_scores(lh, la),
        })

    return {
        "enabled": True,
        "refresh_sec": 20,
        "items": out
    }

@router.post("/calc")
async def goalmatrix_calc(payload: dict):
    """
    Απλός Poisson demo calculator για manual inputs.
    Περιμένει: home_avg, away_avg, over_line
    """
    try:
        home_avg = float(payload.get("home_avg", 1.5))
        away_avg = float(payload.get("away_avg", 1.2))
        over_line = float(payload.get("over_line", 2.5))
    except Exception:
        home_avg, away_avg, over_line = 1.5, 1.2, 2.5

    total = home_avg + away_avg
    p_over = 0.65 if total > over_line else (0.5 if total == over_line else 0.35)
    p_under = 1.0 - p_over
    top_scores = [("2-1", 0.15), ("1-1", 0.13), ("2-0", 0.12)]

    return {
        "enabled": True,
        "lambda_home": home_avg,
        "lambda_away": away_avg,
        "p_over": round(p_over, 3),
        "p_under": round(p_under, 3),
        "top_scores": top_scores
    }
