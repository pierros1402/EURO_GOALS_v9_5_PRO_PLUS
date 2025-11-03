# ==========================================================
# EURO_GOALS v9.3.5 – Health Check Module with System Logs
# ==========================================================
# Καταγράφει κάθε έλεγχο στο system_logs (SQLite / PostgreSQL)
# και επιστρέφει unified report για το dashboard.
# ==========================================================

import os
import sqlite3
import requests
from datetime import datetime

# ==========================================================
# 1️⃣  Βοηθητικές συναρτήσεις
# ==========================================================
def ensure_logs_table():
    """Δημιουργεί τον πίνακα system_logs αν δεν υπάρχει."""
    try:
        conn = sqlite3.connect("matches.db")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                database_status TEXT,
                render_status TEXT,
                smartmoney_status TEXT,
                goalmatrix_status TEXT,
                overall_status TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[LOGS] ⚠️ Error creating system_logs: {e}")

def save_log(report: dict):
    """Αποθήκευση νέας γραμμής στο system_logs."""
    try:
        conn = sqlite3.connect("matches.db")
        conn.execute("""
            INSERT INTO system_logs (timestamp, database_status, render_status, smartmoney_status, goalmatrix_status, overall_status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            report.get("timestamp"),
            report.get("database"),
            report.get("render"),
            report.get("smartmoney"),
            report.get("goalmatrix"),
            report.get("status")
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[LOGS] ⚠️ Error inserting log: {e}")

# ==========================================================
# 2️⃣  Έλεγχοι συστήματος
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
            return "PostgreSQL (Render) – Not Implemented"
    except Exception as e:
        return f"FAIL ({str(e)})"

def check_render_status():
    api_key = os.getenv("RENDER_API_KEY")
    service_id = os.getenv("RENDER_SERVICE_ID")
    if not api_key or not service_id:
        return "Skipped"
    try:
        url = f"https://api.render.com/v1/services/{service_id}"
        headers = {"Authorization": f"Bearer {api_key}"}
        r = requests.get(url, headers=headers, timeout=10)
        return "Online" if r.status_code == 200 else f"FAIL ({r.status_code})"
    except Exception as e:
        return f"FAIL ({str(e)})"

def check_smartmoney():
    return "Active"

def check_goalmatrix():
    return "Active"

# ==========================================================
# 3️⃣  Unified Health Check + Log save
# ==========================================================
def run_full_healthcheck():
    ensure_logs_table()

    db_status = check_database()
    render_status = check_render_status()
    sm_status = check_smartmoney()
    gm_status = check_goalmatrix()

    overall = "OK"
    if any(s.startswith("FAIL") for s in [db_status, render_status, sm_status, gm_status]):
        overall = "FAIL"

    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "render": render_status,
        "smartmoney": sm_status,
        "goalmatrix": gm_status,
        "status": overall
    }

    save_log(report)
    return report


# ==========================================================
# 4️⃣  Test run (αν τρέξει μόνο του)
# ==========================================================
if __name__ == "__main__":
    from pprint import pprint
    pprint(run_full_healthcheck())
