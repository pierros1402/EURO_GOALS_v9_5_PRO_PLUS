# ============================================================
# EURO_GOALS PRO+ – Alert Sound Test (MP3 / Windows)
# ------------------------------------------------------------
# Παίζει alert.mp3 χωρίς playsound, χρησιμοποιώντας το
# Windows Media Player backend μέσω 'os.startfile'.
# ============================================================

import os
import time
from pathlib import Path

# ------------------------------------------------------------
# Ρυθμίσεις
# ------------------------------------------------------------
ALERT_SOUND_PATH = os.getenv("ALERT_SOUND_PATH", "static/sounds/alert.mp3")
ALERT_SOUND_ENABLED = os.getenv("ALERT_SOUND_ENABLED", "true").lower() == "true"
SMARTMONEY_ALARM_DIFF = float(os.getenv("SMARTMONEY_ALARM_DIFF", "0.20"))

# Mock test odds
mock_odds_open = 2.10
mock_odds_now = 1.87
diff = round(abs(mock_odds_open - mock_odds_now), 2)

print("🎯 SMARTMONEY ALERT TEST – EURO_GOALS PRO+ v9.5.4 (MP3/Windows)")
print(f"➡️  ALERT_SOUND_PATH = {ALERT_SOUND_PATH}")
print(f"➡️  ALERT_SOUND_ENABLED = {ALERT_SOUND_ENABLED}")
print(f"➡️  Threshold = {SMARTMONEY_ALARM_DIFF}")
print(f"➡️  Mock odds diff = {diff}")

sound_file = Path(ALERT_SOUND_PATH)

if not sound_file.exists():
    print("❌ Το αρχείο alert.mp3 δεν βρέθηκε.")
    print("👉 Έλεγξε ότι υπάρχει στο: static/sounds/alert.mp3")
    raise SystemExit()

# ------------------------------------------------------------
# Έλεγχος και αναπαραγωγή
# ------------------------------------------------------------
if ALERT_SOUND_ENABLED and diff >= SMARTMONEY_ALARM_DIFF:
    print("🔔 Διαφορά ≥ threshold — παίζει alert ήχος...")
    try:
        # ανοίγει τον ήχο με το default media player (π.χ. Windows Media Player)
        os.startfile(str(sound_file))
        print("✅ Ήχος αναπαράχθηκε (Windows Media Player backend).")
    except Exception as e:
        print(f"⚠️ Σφάλμα κατά την αναπαραγωγή: {e}")
else:
    print("ℹ️ Δεν ενεργοποιήθηκε alert (diff < threshold ή ήχος απενεργοποιημένος).")

print("🧩 Τέλος δοκιμής.\n")
time.sleep(1)
