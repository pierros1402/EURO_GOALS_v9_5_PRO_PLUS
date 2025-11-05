# ============================================================
# SMARTMONEY ENGINE v3.0 – EURO_GOALS v9.5.4 PRO+
# ============================================================
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SMARTMONEY_ENGINE_URL = os.getenv("SMARTMONEY_ENGINE_URL", "")
SMARTMONEY_API_KEY = os.getenv("SMARTMONEY_API_KEY", "")


# ------------------------------------------------------------
# Fetch SmartMoney Data
# ------------------------------------------------------------
def fetch_smartmoney_data():
    """Λήψη δεδομένων SmartMoney από τον απομακρυσμένο engine"""
    try:
        headers = {"Authorization": f"Bearer {SMARTMONEY_API_KEY}"}
        url = f"{SMARTMONEY_ENGINE_URL}/api/v1/status"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return {"error": True, "message": f"Bad status: {resp.status_code}"}
    except Exception as e:
        return {"error": True, "message": str(e)}


# ------------------------------------------------------------
# Update Local Cache / DB (placeholder για επόμενο στάδιο)
# ------------------------------------------------------------
def update_local_smartmoney():
    """Ενημέρωση τοπικής βάσης με τα τελευταία δεδομένα"""
    data = fetch_smartmoney_data()
    if data.get("error"):
        return {"status": "fail", "info": data.get("message")}
    # TODO: σύνδεση με SQLite / PostgreSQL
    return {"status": "ok", "info": "SmartMoney data refreshed"}
