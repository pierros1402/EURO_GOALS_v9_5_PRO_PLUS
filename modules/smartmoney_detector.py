# =========================================================
# MODULE: smartmoney_detector.py – EURO_GOALS v9.3.2
# =========================================================
# Εικονικό module για Smart Money Detection
# Προσομοιώνει δεδομένα για σκοπούς test & summary bar.
# =========================================================

from datetime import datetime
import random

def detect_smart_money():
    """
    Επιστρέφει τυχαία προσομοιωμένα αποτελέσματα για ανίχνευση
    "Smart Money" μεταβολών αποδόσεων.
    """
    print("[SMART MONEY] 🔍 Checking market movements...")

    # Προσομοίωση λίστας ύποπτων αγώνων
    sample = [
        {"league": "Premier League", "match": "Chelsea vs Arsenal", "movement": "1.92 → 1.78", "timestamp": datetime.now().strftime("%H:%M:%S")},
        {"league": "Serie A", "match": "Milan vs Napoli", "movement": "2.15 → 1.98", "timestamp": datetime.now().strftime("%H:%M:%S")},
        {"league": "La Liga", "match": "Real Madrid vs Betis", "movement": "1.70 → 1.60", "timestamp": datetime.now().strftime("%H:%M:%S")}
    ]

    # 50% πιθανότητα να μην υπάρχει κίνηση
    if random.choice([True, False]):
        print("[SMART MONEY] ✅ Detected 3 suspicious matches.")
        return sample
    else:
        print("[SMART MONEY] ℹ️ No suspicious activity.")
        return []
