# ============================================================
# MONITOR ENGINE v3 – EURO_GOALS v9.5.4 PRO+
# ============================================================
import os
import requests
import sqlite3
import platform
import psutil
from dotenv import load_dotenv

load_dotenv()

RENDER_HEALTH_URL = os.getenv("RENDER_HEALTH_URL", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")
SMARTMONEY_ENGINE_URL = os.getenv("SMARTMONEY_ENGINE_URL", "")
GOALMATRIX_API_URL = os.getenv("GOALMATRIX_API_URL", "")


# ------------------------------------------------------------
# Render Health
# ------------------------------------------------------------
def check_render_health():
    try:
        r = requests.get(RENDER_HEALTH_URL, timeout=5)
        return {"render_status": "Online ✅", "code": r.status_code}
    except Exception as e:
        return {"render_status": f"Offline ⚠️ ({e})", "code": None}


# ------------------------------------------------------------
# Database Health
# ------------------------------------------------------------
def check_database_health():
    try:
        if DATABASE_URL.startswith("sqlite"):
            db_path = DATABASE_URL.replace("sqlite:///", "")
            conn = sqlite3.connect(db_path)
            conn.execute("SELECT 1")
            conn.close()
            return {"db_status": "Connected 💾"}
        else:
            return {"db_status": "External DB (not tested)"}
    except Exception as e:
        return {"db_status": f"Error ❌ ({e})"}


# ------------------------------------------------------------
# API Engines Health (SmartMoney + GoalMatrix)
# ------------------------------------------------------------
def check_api_health():
    results = {}
    try:
        sm = requests.get(f"{SMARTMONEY_ENGINE_URL}/health", timeout=4)
        results["smartmoney"] = "OK ✅" if sm.status_code == 200 else f"⚠️ {sm.status_code}"
    except Exception:
        results["smartmoney"] = "Offline ❌"

    try:
        gm = requests.get(f"{GOALMATRIX_API_URL}/health", timeout=4)
        results["goalmatrix"] = "OK ✅" if gm.status_code == 200 else f"⚠️ {gm.status_code}"
    except Exception:
        results["goalmatrix"] = "Offline ❌"

    return results


# ------------------------------------------------------------
# System Metrics (CPU / RAM)
# ------------------------------------------------------------
def check_system_metrics():
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        return {"cpu": f"{cpu}%", "ram": f"{ram}%"}
    except Exception as e:
        return {"cpu": "N/A", "ram": "N/A", "error": str(e)}


# ------------------------------------------------------------
# Unified Monitor Summary
# ------------------------------------------------------------
def get_full_system_status():
    data = {}
    data.update(check_render_health())
    data.update(check_database_health())
    data.update(check_api_health())
    data.update(check_system_metrics())
    data["platform"] = platform.node()
    return data
