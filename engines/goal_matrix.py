from __future__ import annotations
from dataclasses import dataclass
from math import exp, factorial
from typing import Dict, List, Tuple

# ----------------------------
# Core Poisson helpers
# ----------------------------
def _poisson_p(k: int, lam: float) -> float:
    return (lam**k) * exp(-lam) / factorial(k)

def _sum_poisson_prob_up_to(max_goals: int, lam: float) -> float:
    return sum(_poisson_p(k, lam) for k in range(max_goals + 1))

# ----------------------------
# Public API
# ----------------------------
@dataclass
class GoalMatrixInput:
    home_avg: float  # expected goals for home
    away_avg: float  # expected goals for away
    over_line: float = 2.5  # default market line

@dataclass
class GoalMatrixResult:
    lambda_home: float
    lambda_away: float
    p_over: float
    p_under: float
    score_grid: List[Dict]  # [{"home":i,"away":j,"p":...}, ...]
    top_scores: List[Tuple[str, float]]  # [("1-1", 0.12), ...]

def compute_probabilities(inp: GoalMatrixInput) -> GoalMatrixResult:
    lam_h = max(0.01, float(inp.home_avg))
    lam_a = max(0.01, float(inp.away_avg))
    lam_tot = lam_h + lam_a

    # Grid up to 6 goals ανά ομάδα (τυπικά αρκετό)
    limit = 6
    grid = []
    for i in range(limit + 1):
        for j in range(limit + 1):
            p = _poisson_p(i, lam_h) * _poisson_p(j, lam_a)
            grid.append({"home": i, "away": j, "p": p})

    # P(Under n.5) = sum_{k=0..n} P(total_goals=k)
    under_cap = int(inp.over_line - 0.5)  # π.χ. line 2.5 -> 0..2
    # Υπολογίζουμε κατανομή συνόλου γκολ από τη σύγκλιση Poisson(lam_tot)
    p_under = _sum_poisson_prob_up_to(under_cap, lam_tot)
    p_over = 1.0 - p_under

    # Top scorelines
    top_scores = sorted(
        [(f"{g['home']}-{g['away']}", g["p"]) for g in grid],
        key=lambda x: x[1],
        reverse=True
    )[:5]

    return GoalMatrixResult(
        lambda_home=lam_h,
        lambda_away=lam_a,
        p_over=p_over,
        p_under=p_under,
        score_grid=grid,
        top_scores=top_scores,
    )

# ----------------------------
# Demo feed (placeholder)
# Θα συνδεθεί αργότερα στα πραγματικά feeds σου.
# ----------------------------
def demo_matches() -> List[Dict]:
    return [
        {
            "match_id": "EPL-2025-ARS-CHE",
            "league": "Premier League",
            "kickoff_utc": "2025-11-06T19:30:00Z",
            "home": "Arsenal",
            "away": "Chelsea",
            "home_avg": 1.62,
            "away_avg": 1.10,
            "over_line": 2.5,
        },
        {
            "match_id": "GRE-2025-PAO-PAOK",
            "league": "Super League Greece",
            "kickoff_utc": "2025-11-06T20:00:00Z",
            "home": "Panathinaikos",
            "away": "PAOK",
            "home_avg": 1.35,
            "away_avg": 1.20,
            "over_line": 2.25,
        },
    ]

def compute_for_demo_feed() -> List[Dict]:
    out = []
    for m in demo_matches():
        res = compute_probabilities(
            GoalMatrixInput(
                home_avg=m["home_avg"],
                away_avg=m["away_avg"],
                over_line=m["over_line"],
            )
        )
        out.append({
            **m,
            "p_over": res.p_over,
            "p_under": res.p_under,
            "top_scores": res.top_scores,
            "lambda_home": res.lambda_home,
            "lambda_away": res.lambda_away,
        })
    return out
