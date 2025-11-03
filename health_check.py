# ==========================================================
# EURO_GOALS v9.3 – Health Check Module
# ==========================================================
# Ελέγχει:
# ✅ Σύνδεση με τη βάση δεδομένων
# ✅ Κατάσταση Render API (αν υπάρχουν env vars)
# ✅ Ενεργά modules SmartMoney & GoalMatrix (placeholder)
# ==========================================================

import os
import sqlite3
import requests
from datetime import datetime

# ==========================================================
# 1️⃣  Έλεγχος Database
# ==========================================================
def check_database():
    db_url = os.getenv("DATABASE_URL", "sqlite:///matches.db")
    try:
        if db_url.startswith("sqlite"):
            conn = sqlite3.connect("matches.db")
            conn.execute("SELECT 1")
            conn.close()
            return "OK"
        else:
            return "PostgreSQL (Render) – Not Implemented Yet"
    except Exception as e:
        return f"FAIL ({str(e)})"


# ==========================================================
# 2️⃣  Έλεγχος Render API
# ==========================================================
def check_render_status():
    api_key = os.getenv("RENDER_API_KEY")
    service_id = os.getenv("RENDER_SERVICE_ID")
    if not api_key or not service_id:
        return "Skipped (no API key/service id)"

    try:
        url = f"https://api.render.com/v1/services/{service_id}"
        headers = {"Authorization": f"Bearer {api_key}"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return "OK"
        else:
            return f"FAIL ({r.status_code})"
    except Exception as e:
        return f"FAIL ({str(e)})"


# ==========================================================
# 3️⃣  Placeholder Modules
# ==========================================================
def check_smartmoney():
    # Placeholder για μελλοντικό API
    return "Active"

def check_goalmatrix():
    # Placeholder για μελλοντικό API
    return "Active"


# ==========================================================
# 4️⃣  Συνδυαστικός έλεγχος – Δημιουργία αναφοράς
# ==========================================================
def run_full_healthcheck():
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "database": check_database(),
        "render": check_render_status(),
        "smartmoney": check_smartmoney(),
        "goalmatrix": check_goalmatrix(),
        "status": "OK"
    }


# ==========================================================
# 5️⃣  Αν τρέξει μόνο του (test mode)
# ==========================================================
if __name__ == "__main__":
    from pprint import pprint
    print("🔍 Running EURO_GOALS Health Check...\n")
    pprint(run_full_healthcheck())
