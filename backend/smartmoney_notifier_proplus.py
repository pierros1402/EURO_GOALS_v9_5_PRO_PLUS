# ============================================================
# EURO_GOALS v9.4.2 PRO+ – SmartMoney Local Notifier (Real APIs)
# ============================================================

import os
import time
import json
import threading
import requests
from datetime import datetime
from dotenv import load_dotenv

# Προαιρετικά modules για Windows notifications
try:
    from win10toast import ToastNotifier
    import playsound
    WINDOWS = True
except ImportError:
    WINDOWS = False

load_dotenv()

# ============================================================
# CONFIG
# ============================================================
THEODDSAPI_KEY = os.getenv("THEODDSAPI_KEY")
SPORTMONKS_API_KEY = os.getenv("SPORTMONKS_API_KEY")
REFRESH_INTERVAL = int(os.getenv("SMARTMONEY_PRO_REFRESH", 60))
ALERT_THRESHOLD = float(os.getenv("SMARTMONEY_PRO_ALERT_THRESHOLD", 0.05))
SOUND_FILE = "static/sounds/smartmoney_alert.mp3"

# Ενεργοποίηση τοπικού notifier στα Windows
notifier = ToastNotifier() if WINDOWS else None
last_prices = {}   # cache για προηγούμενες τιμές

# ============================================================
# Ειδοποίηση (toast + ήχος)
# ============================================================
def show_notification(title, msg):
    if WINDOWS and notifier:
        try:
            notifier.show_toast(title, msg, duration=6, threaded=True)
            if os.path.exists(SOUND_FILE):
                playsound.playsound(SOUND_FILE, block=False)
        except Exception as e:
            print("[NOTIFIER] ⚠️ Error:", e)
    else:
        print(f"🔔 {title}: {msg}")

# ============================================================
# Λήψη αποδόσεων από TheOddsAPI
# ============================================================
def get_odds_theoddsapi():
    try:
        url = (
            f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds"
            f"/?apiKey={THEODDSAPI_KEY}&regions=eu&markets=h2h"
        )
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            print("[TheOddsAPI] Error:", r.status_code, r.text[:80])
    except Exception as e:
        print("[TheOddsAPI] Exception:", e)
    return []

# ============================================================
# Λήψη αποδόσεων από SportMonks (π.χ. live matches)
# ============================================================
def get_odds_sportmonks():
    try:
        url = (
            f"https://api.sportmonks.com/v3/football/odds/inplay"
            f"?api_token={SPORTMONKS_API_KEY}&bookmakers=2,3,4"
        )
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json().get("data", [])
    except Exception as e:
        print("[SportMonks] Exception:", e)
    return []

# ============================================================
# Κύρια λογική SmartMoney – Ανίχνευση μεταβολών
# ============================================================
def detect_smartmoney():
    global last_prices
    theodds_data = get_odds_theoddsapi()
    sportmonks_data = get_odds_sportmonks()

    alerts = []
    now = datetime.utcnow().strftime("%H:%M:%S")

    # ----------------- TheOddsAPI -----------------
    for match in theodds_data:
        home = match.get("home_team", "")
        away = match.get("away_team", "")
        teams = f"{home} vs {away}"

        for bookmaker in match.get("bookmakers", []):
            bm = bookmaker.get("title")
            for market in bookmaker.get("markets", []):
                for outcome in market.get("outcomes", []):
                    sel = outcome.get("name")
                    price = float(outcome.get("price", 0))
                    key = f"{teams}_{bm}_{sel}"

                    if key in last_prices:
                        old = last_prices[key]
                        if old == 0:
                            continue
                        change = (price - old) / old
                        if abs(change) >= ALERT_THRESHOLD:
                            msg = f"{teams} ({bm}) {sel} {old:.2f}→{price:.2f} ({change*100:.1f}%)"
                            alerts.append(msg)
                            log_smartmoney_event(msg)
                            show_notification("💰 SmartMoney Alert", msg)
                    last_prices[key] = price

    # ----------------- SportMonks -----------------
    for m in sportmonks_data:
        fixture = m.get("fixture", {}).get("name", "")
        bookmaker = m.get("bookmaker", {}).get("name", "")
        odds = m.get("odds", [])
        for o in odds:
            market = o.get("label")
            sel = o.get("name")
            price = float(o.get("value", 0))
            key = f"{fixture}_{bookmaker}_{sel}"
            if key in last_prices:
                old = last_prices[key]
                change = (price - old) / old if old else 0
                if abs(change) >= ALERT_THRESHOLD:
                    msg = f"{fixture} ({bookmaker}) {sel} {old:.2f}→{price:.2f} ({change*100:.1f}%)"
                    alerts.append(msg)
                    show_notification("💰 SmartMoney Alert", msg)
            last_prices[key] = price

    if alerts:
        print(f"[SmartMoney PRO+] [{now}] {len(alerts)} alerts detected.")
    else:
        print(f"[SmartMoney PRO+] [{now}] No major movements.")
    return alerts

# ============================================================
# Επαναλαμβανόμενος βρόχος
# ============================================================
def smartmoney_loop():
    print("[SmartMoney PRO+] 🔁 Monitoring (Real APIs) started...")
    while True:
        try:
            detect_smartmoney()
        except Exception as e:
            print("[SmartMoney PRO+] Loop Error:", e)
        time.sleep(REFRESH_INTERVAL)

# ============================================================
# Εκκίνηση σε thread
# ============================================================
def start_local_notifier():
    t = threading.Thread(target=smartmoney_loop, daemon=True)
    t.start()
    print("[SmartMoney PRO+] ✅ Local notifier (Real APIs) running in background.")

# ============================================================
# Χειροκίνητη εκκίνηση (αν τρέχει standalone)
# ============================================================
if __name__ == "__main__":
    start_local_notifier()
    while True:
        time.sleep(10)
# ------------------------------------------------------------
# Καταγραφή alert σε τοπικό JSON (για προβολή στο UI)
# ------------------------------------------------------------
def log_smartmoney_event(msg):
    try:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "smartmoney_log.json")

        # φόρτωση παλιού αρχείου
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []

        # νέα εγγραφή
        data.insert(0, {
            "timestamp": datetime.utcnow().isoformat(),
            "message": msg
        })

        # διατήρηση μόνο των 200 τελευταίων
        data = data[:200]

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[SmartMoney LOG] Error:", e)

