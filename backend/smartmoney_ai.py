# ============================================================
# EURO_GOALS v9.4.3 PRO+ – SmartMoney AI Analyzer
# ============================================================

from typing import List, Dict

# Βάρη ανά bookmaker (ενδεικτικά)
BOOKMAKER_WEIGHTS = {
    "pinnacle": 1.00,
    "bet365": 0.95,
    "betano": 0.85,
    "stoiximan": 0.85,
    "unibet": 0.80,
    "others": 0.75,
}

def _bm_weight(name: str) -> float:
    if not name:
        return BOOKMAKER_WEIGHTS["others"]
    key = name.strip().lower()
    return BOOKMAKER_WEIGHTS.get(key, BOOKMAKER_WEIGHTS["others"])

def score_alert(a: Dict) -> Dict:
    """
    Δίνει score σε ένα alert:
    - βασίζεται στο abs(change_pct) * bookmaker_weight
    - κατηγορίες: STRONG / MEDIUM / WATCH
    """
    cp = abs(float(a.get("change_pct") or 0.0))
    bm = a.get("bookmaker") or ""
    w = _bm_weight(bm)
    raw = cp * w

    if raw >= 0.10: label = "STRONG"
    elif raw >= 0.06: label = "MEDIUM"
    else: label = "WATCH"

    return {
        "match": f"{a.get('home','')} vs {a.get('away','')}".strip(),
        "bookmaker": bm,
        "market": a.get("market"),
        "selection": a.get("selection"),
        "old": a.get("old_price"),
        "new": a.get("new_price"),
        "change_pct": cp,
        "score": round(raw, 4),
        "tier": label,
        "source": a.get("source", "-"),
        "ts_utc": a.get("ts_utc")
    }

def analyze_alerts(alerts: List[Dict], top_n: int = 10) -> List[Dict]:
    scored = [score_alert(a) for a in alerts if a.get("change_pct") not in (None, "")]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]
