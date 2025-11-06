# ============================================================
# EURO_GOALS v9.5.4 PRO+ – GoalMatrix Feed ↔ DB
# ============================================================
import sqlite3
import math
from datetime import datetime
from fastapi import APIRouter
import os

router = APIRouter()

# ------------------------------------------------------------
# Correct absolute path to goalmatrix.db
# ------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "goalmatrix.db")

# -------------------------------------------------------------------
# Poisson-based probability helpers
# -------------------------------------------------------------------
def poisson_prob(lmbda, k):
    return (math.exp(-lmbda) * (lmbda**k)) / math.factorial(k)

def over_under_probability(l_home, l_away, line=2.5):
    p_under = 0.0
    for h in range(0, 10):
        for a in range(0, 10):
            if h + a <= line:
                p_under += poisson_prob(l_home, h) * poisson_prob(l_away, a)
    return 1 - p_under, p_under  # (p_over, p_under)

# -------------------------------------------------------------------
# Main feed
# -------------------------------------------------------------------
@router.get("/api/goalmatrix/feed")
def goalmatrix_feed():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM matches ORDER BY kickoff_utc ASC LIMIT 50"
    )
    rows = cur.fetchall()
    conn.close()

    items = []
    for r in rows:
        l_home, l_away = r["home_xg"], r["away_xg"]
        p_over, p_under = over_under_probability(l_home, l_away, r["over_line"])

        # Top scorelines
        scores = []
        for h in range(0, 5):
            for a in range(0, 5):
                prob = poisson_prob(l_home, h) * poisson_prob(l_away, a)
                scores.append((f"{h}-{a}", prob))
        scores.sort(key=lambda x: x[1], reverse=True)
        top_scores = scores[:3]

        items.append(
            {
                "league": r["league"],
                "home": r["home_team"],
                "away": r["away_team"],
                "lambda_home": round(l_home, 2),
                "lambda_away": round(l_away, 2),
                "p_over": round(p_over, 3),
                "p_under": round(p_under, 3),
                "top_scores": top_scores,
            }
        )

    return {
        "enabled": True,
        "refresh_sec": 20,
        "items": items,
        "updated": datetime.utcnow().isoformat(),
    }
