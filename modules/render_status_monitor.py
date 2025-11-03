# ===============================================================
# EURO_GOALS – Render Status Monitor (Render-compatible version)
# ===============================================================
# Παρακολουθεί το Render service, την κατάσταση του API και τη βάση
# Δουλεύει σε server περιβάλλον (χωρίς win10toast / desktop alerts)
# ===============================================================

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# ---------------------------------------------------------------
# Φόρτωση μεταβλητών περιβάλλοντος
# ---------------------------------------------------------------
load_dotenv()

RENDER_API_KEY = os.getenv("RENDER_API_KEY")
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID")
RENDER_HEALTH_URL = os.getenv("RENDER_HEALTH_URL")

# ---------------------------------------------------------------
# Έλεγχος κατάστασης Render service
# ---------------------------------------------------------------
def get_render_status():
    """
    Ελέγχει την υγεία και το status του Render service.
    Επιστρέφει dictionary με τα αποτελέσματα.
    """
    status = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "render_api": "FAIL",
        "service_health": "FAIL",
        "summary": "❌ Προβλήματα επικοινωνίας με το Render."
    }

    try:
        # Έλεγχος Render health URL
        if RENDER_HEALTH_URL:
            res = requests.get(RENDER_HEALTH_URL, timeout=6)
            if res.status_code == 200:
                status["service_health"] = "OK"
            else:
                status["service_health"] = f"HTTP {res.status_code}"

        # Έλεγχος Render API
        if RENDER_API_KEY and RENDER_SERVICE_ID:
            api_url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}"
            headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
            res_api = requests.get(api_url, headers=headers, timeout=6)
            if res_api.status_code == 200:
                status["render_api"] = "OK"
            else:
                status["render_api"] = f"HTTP {res_api.status_code}"

        # Τελική σύνοψη
        if status["render_api"] == "OK" and status["service_health"] == "OK":
            status["summary"] = "✅ Όλα λειτουργούν κανονικά στο Render."
        elif "HTTP" in status["service_health"]:
            status["summary"] = "⚠️ Το Render service απαντά αλλά όχι κανονικά."
        else:
            status["summary"] = "❌ Αποτυχία επικοινωνίας με Render."

    except Exception as e:
        status["summary"] = f"⚠️ Σφάλμα κατά τον έλεγχο: {e}"

    return status


# ---------------------------------------------------------------
# Εκτέλεση αυτόνομη (αν τρέχει ως script)
# ---------------------------------------------------------------
if __name__ == "__main__":
    print("[EURO_GOALS] 🔍 Render Monitor Check Running...")
    result = get_render_status()
    for k, v in result.items():
        print(f"{k}: {v}")
