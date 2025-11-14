# ============================================================
# AI MATCHLAB — EXCHANGE ENGINE
# Επεξεργασία αγορών, odds και runners
# ============================================================

from typing import Dict, Any, List, Optional


class ExchangeEngine:
    """
    Ενοποιεί τα δεδομένα από τον Provider:
    - Κανονικοποίηση markets
    - Καθαρισμός odds
    - Εμπλουτισμός runners
    - Flags για movement
    """

    # ------------------------------------------------------------
    # Normalize exchange market data
    # ------------------------------------------------------------
    def normalize_market(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Παίρνει ένα raw exchange market JSON
        και επιστρέφει καθαρό, normalized object.
        """
        if not raw or "runners" not in raw:
            return None

        try:
            market = {
                "market_id": raw.get("marketId", ""),
                "market_name": raw.get("marketName", ""),
                "total_matched": raw.get("totalMatched", 0),
                "runners": self.normalize_runners(raw.get("runners", [])),
            }

            return market

        except Exception as e:
            print(f"[ExchangeEngine] ❌ normalize_market error: {e}")
            return None

    # ------------------------------------------------------------
    # Normalize runners / odds
    # ------------------------------------------------------------
    def normalize_runners(self, runners: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []

        for r in runners:
            try:
                back = r.get("ex", {}).get("availableToBack", [])
                lay = r.get("ex", {}).get("availableToLay", [])

                runner = {
                    "selection_id": r.get("selectionId"),
                    "name": r.get("runnerName"),
                    "status": r.get("status", "ACTIVE"),

                    "back_odds": back[0]["price"] if back else None,
                    "back_size": back[0]["size"] if back else None,

                    "lay_odds": lay[0]["price"] if lay else None,
                    "lay_size": lay[0]["size"] if lay else None,

                    "movement": self.detect_movement(back, lay)
                }

                out.append(runner)

            except Exception as e:
                print(f"[ExchangeEngine] ⚠ Error on runner normalize: {e}")

        return out

    # ------------------------------------------------------------
    # Movement detection
    # ------------------------------------------------------------
    def detect_movement(self, back: List[Dict[str, Any]], lay: List[Dict[str, Any]]) -> str:
        """
        Μικρή λογική για movement flag.
        Χρησιμοποιείται σαν input για GoalMatrix & SmartMoney.
        """
        try:
            if not back or not lay:
                return "none"

            b = back[0]["price"]
            l = lay[0]["price"]

            # Simple interpretation:
            if b < l:
                return "pressure_to_back"
            if l < b:
                return "pressure_to_lay"

        except:
            pass

        return "none"


# Singleton instance
exchange_engine = ExchangeEngine()
