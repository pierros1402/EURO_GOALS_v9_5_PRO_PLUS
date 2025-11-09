# ============================================================
# EURO_GOALS PRO+ – Auto SmartMoney Alert Monitor (Windows)
# ------------------------------------------------------------
# Ελέγχει αυτόματα mock odds κάθε 20s και παίζει alert.mp3
# αν διαφορά ≥ SMARTMONEY_ALARM_DIFF.
# ============================================================

import os
import random
import time
from pathlib import Path

ALERT_SOUND_PATH = os.getenv("ALERT_SOUND_PATH", "static/sounds/alert.mp3")
ALERT_SOUND_ENABLED = os.getenv("ALERT_SOUND_ENABLED", "true").lower() == "true"
SMARTMONEY_ALARM_DIFF = float(os.getenv("SMARTMONEY_ALARM_DIFF", "0.20"))
REFRESH_INTERVAL = 20  # seconds

sound_file = Path(ALERT_SOUND_PATH)
if not sound_file.exists():
    print("❌ Το αρχείο alert.mp3 δεν βρέθηκε.")
    raise SystemExit()

print("🎯 EURO_GOALS PRO+ SmartMoney Auto Monitor (Windows)")
print(f"➡️ Threshold = {SMARTMONEY_ALARM_DIFF}")
print(f"➡️ Refresh κάθε {REFRESH_INTERVAL} δευτ.\n")

# Προσομοίωση αποδόσεων (θα αντικατασταθεί από πραγματικά δεδομένα)
odds_open = 2.10

while True:
    odds_now = round(odds_open + random.uniform(-0.4, 0.4), 2)
    diff = abs(odds_open - odds_now)

    print(f"[{time.strftime('%H:%M:%S')}] ➡️ Odds open={odds_open:.2f} now={odds_now:.2f} | diff={diff:.2f}", end="")

    if ALERT_SOUND_ENABLED and diff >= SMARTMONEY_ALARM_DIFF:
        print("  🔔 ALERT TRIGGERED!")
        os.startfile(str(sound_file))
    else:
        print("  ✅ OK")

    time.sleep(REFRESH_INTERVAL)
