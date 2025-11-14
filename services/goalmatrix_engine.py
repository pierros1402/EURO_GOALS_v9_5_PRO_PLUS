# ============================================================
# AI MATCHLAB — GOALMATRIX ENGINE
# Ανάλυση odds movement & market pressure για GoalMatrix
# ============================================================

from typing import Dict, Any, List, Optional
from .exchange_engine import exchange_engine


class GoalMatrixEngine:
    """
    Απλό αλλά σταθερό AI logic για GoalMatrix:
    - Αναλύει movement από exchange_engine
    - Προσδιορίζει direction: positive / negative / neutral
    - Υπολογίζει μικρά indicators (pressure, stability)
    """

    # ------------------------------------------------------------
    def analyze_market(self, raw_market: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """ 
        Παίρνει ένα raw market JSON και επιστρέφει
        compact GoalMatrix structured object.
        """

        market = exchange_engine.normalize_market(raw_market)
        if not market:
            return None

        runners = market.get("runners", [])
        indicators = self.generate_indicators(runners)

        return {
            "market_id": market["market_id"],
            "market_name": market["market_name"],
            "total_matched": market["total_matched"],
            "runners": runners,
            "indicators": indicators
        }

    # ------------------------------------------------------------
    def generate_indicators(self, runners: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Δημιουργεί συνοπτικούς δείκτες για το GoalMatrix panel.
        Απλό, γρήγορο, χωρίς περίπλοκο AI (για v1).
        """

        back_pressure = 0
        lay_pressure = 0

        for r in runners:
            mv = r.get("movement", "none")

            if mv == "pressure_to_back":
                back_pressure += 1
            elif mv == "pressure_to_lay":
                lay_pressure += 1

        indicator = "neutral"

        if back_pressure > lay_pressure:
            indicator = "positive"
        elif lay_pressure > back_pressure:
            indicator = "negative"

        return {
            "positive_pressure": back_pressure,
            "negative_pressure": lay_pressure,
            "direction": indicator,
            "confidence": self.compute_confidence(back_pressure, lay_pressure)
        }

    # ------------------------------------------------------------
    def compute_confidence(self, pos: int, neg: int) -> float:
        """
        Confidence score (0.0 – 1.0)
        Πολύ απλό: pos+neg = συνολική ένταση movement.
        """

        total = pos + neg
        if total == 0:
            return 0.0

        ratio = abs(pos - neg) / total
        return round(ratio, 2)


# Singleton instance
goalmatrix_engine = GoalMatrixEngine()
