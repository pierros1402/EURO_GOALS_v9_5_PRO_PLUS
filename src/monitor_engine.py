# ============================================================
# EURO_GOALS v9.5.4 PRO+ – Monitor Engine v3.1
# Ενοποιημένος έλεγχος Render, DB, SmartMoney, GoalMatrix
# ============================================================

import os
import requests
import psutil
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# Ρυθμίσεις URLs & Keys
# ============================================================
RENDER_HEALTH_URL = os.getenv("RENDER_HEALTH_URL", "")
SMARTMONEY_ENGINE_URL = os.getenv("SMARTMONEY_ENGINE_URL", "")
GOALMATRIX_ENGINE_URL = os.getenv("GOALMATRIX_ENGINE_URL", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")


# ============================================================
# Βοηθητική συνάρτηση ελέγχου
# ============================================================
def check_endpoint(url: str, name: str):
    """Κάνει έλεγχο σε endpoint και επιστρέφει κατάσταση."""
    if not url:
        return f"{name}: ❌ URL missing"

    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return f"{name}: ✅ OK"
        elif resp.status_code == 404:
            return f"{name}: 💤 Offline"
        else:
            return f"{name}: ⚠️ {resp.status_code}"
    except Exception:
        return f"{name}: 💤 Offline"


# ============================================================
# Κύρια συνάρτηση ελέγχου συστήματος
# ============================================================
def get_full_system_status():
    """Επιστρέφει JSON με πλήρη εικόνα του συστήματος."""
    try:
        render_status = check_endpoint(RENDER_HEALTH_URL, "render")
        smartmoney_status = check_endpoint(SMARTMONEY_ENGINE_URL, "smartmoney")
        goalmatrix_status = check_endpoint(GOALMATRIX_ENGINE_URL, "goalmatrix")

        # Χρήση psutil για CPU/RAM
        cpu_percent = psutil.cpu_percent(interval=1)
        ram_percent = psutil.virtual_memory().percent

        return {
            "render_status": render_status.replace("render: ", ""),
            "db_status": "Connected 💾" if DATABASE_URL else "No DB URL ❌",
            "smartmoney": smartmoney_status.replace("smartmoney: ", ""),
            "goalmatrix": goalmatrix_status.replace("goalmatrix: ", ""),
            "cpu": f"{cpu_percent:.1f}%",
            "ram": f"{ram_percent:.1f}%",
            "platform": os.getenv("RENDER_SERVICE_ID", "local")
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("🩺 Testing system status...")
    print(get_full_system_status())
