# ============================================================
# AI MATCHLAB — SMARTMONEY ENGINE
# Ελαφρύς εντοπισμός patterns & scoring
# ============================================================

from typing import Dict, Any, List, Optional
from .exchange_engine import exchange_engine


class SmartMoneyEngine:
    """
    Απλό αλλά αξιόπιστο SmartMoney scoring:
    - Έντονη διαφορά μεταξύ back & lay
    - Πίεση προς ένα selection
    - Spike στο matched volume
    """

    # ------------------------------------------------------------
    def analyze_market(self, raw_market: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Παίρνει raw exchange data, το κανονικοποιεί,
        και επιστρέφει SmartMoney insights.
        """

        market = exchange_engine.normalize_market(raw_market)
        if not market:
            return None

        runners = market["runners"]
        score = self.score_runners(runners)
        alerts = self.generate_alerts(score)

        return {
            "market_id": market["market_id"],
            "market_name": market["market_name"],
            "total_matched": market["total_matched"],
            "runners": runners,
            "smart_score": score,
            "alerts": alerts
        }

    # ------------------------------------------------------------
    def score_runners(self, runners: List[Dict[str, Any]]) -> int:
        """
        Υπολογισμός SmartMoney Score (0–100)
        Αξιολογεί πίεση, odds movement και σχετική ισορροπία.
        """

        back_pressure = 0
        lay_pressure = 0
        volatility = 0

        for r in runners:
            mv = r.get("movement", "none")

            if mv == "pressure_to_back":
                back_pressure += 1
            elif mv == "pressure_to_lay":
                lay_pressure += 1

            # Volatility indicator (αν back/lay απέχουν πολύ)
            bo = r.get("back_odds")
            lo = r.get("lay_odds")
            if bo and lo:
                diff = abs(bo - lo)
                if diff >= 0.5:
                    volatility += 1

        # Βασική λογική scoring:
        base = back_pressure + lay_pressure + volatility

        if base == 0:
            return 0

        # Scale to 0–100
        score = min(100, base * 10)
        return score

    # ------------------------------------------------------------
    def generate_alerts(self, score: int) -> List[str]:
        """
        Παράγει απλά alerts ανάλογα με το score.
        """

        alerts = []

        if score >= 70:
            alerts.append("possible_sharp_move")

        if score >= 40:
            alerts.append("increasing_pressure")

        if score >= 20:
            alerts.append("mild_activity")

        return alerts


# Singleton instance
smartmoney_engine = SmartMoneyEngine()
