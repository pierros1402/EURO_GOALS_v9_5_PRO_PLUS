# ============================================================
# EURO_GOALS v9.5.0 PRO+ – Unified System + Render + SmartMoney + Backup
# ============================================================

from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import psutil
from datetime import datetime
from dotenv import load_dotenv

# ------------------------------------------------------------
# Load .env
# ------------------------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/matches.db")
RENDER_HEALTH_URL = os.getenv("RENDER_HEALTH_URL", "https://eurogoals-nextgen.onrender.com/health")

app = FastAPI(title="EURO_GOALS v9.5.0 PRO+", version="9.5.0 PRO+")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# Helper: System health check
# ------------------------------------------------------------
def get_system_health():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    return f"OK (CPU {cpu}%, RAM {ram}%, Disk {disk}%)"

# ------------------------------------------------------------
# System Endpoints
# ------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <h2>🏆 EURO_GOALS v9.5.0 PRO+ – API Interface</h2>
    <p>Available endpoints:</p>
    <ul>
      <li><a href="/system_status_data" target="_blank">/system_status_data</a> – JSON Unified Status</li>
      <li><a href="/system_status_html" target="_blank">/system_status_html</a> – HTML Unified Dashboard</li>
      <li><a href="/render_health" target="_blank">/render_health</a> – Render Health Check</li>
      <li><a href="/smartmoney_monitor" target="_blank">/smartmoney_monitor</a> – SmartMoney Monitor</li>
      <li><a href="/backup_status" target="_blank">/backup_status</a> – Backup Readiness</li>
    </ul>
    """

@app.get("/system_status_data", response_class=JSONResponse)
def system_status_data():
    data = {
        "DB": "Connected" if os.path.exists("data/matches.db") else "Fail",
        "Health": get_system_health(),
        "Render": "Inactive",
        "SmartMoney": "Live",
        "Backup": "Ready",
        "last_update": datetime.now().strftime("%H:%M:%S")
    }
    return data

@app.get("/system_status_html", response_class=HTMLResponse)
def system_status_html():
    data = system_status_data()
    html = f"""
    <h3>EURO_GOALS v9.5.0 PRO+ – System Status</h3>
    <ul>
      <li>DB: {data['DB']}</li>
      <li>Health: {data['Health']}</li>
      <li>Render: {data['Render']}</li>
      <li>SmartMoney: {data['SmartMoney']}</li>
      <li>Backup: {data['Backup']}</li>
      <li>Last Update: {data['last_update']}</li>
    </ul>
    """
    return HTMLResponse(content=html)

# ------------------------------------------------------------
# Render Health (Remote)
# ------------------------------------------------------------
@app.get("/render_health", response_class=JSONResponse)
def render_health():
    try:
        import requests
        r = requests.get(RENDER_HEALTH_URL, timeout=5)
        if r.status_code == 200:
            return {"Render": "Active", "status_code": 200}
        else:
            return {"Render": "Unstable", "status_code": r.status_code}
    except Exception as e:
        return {"Render": "Inactive", "error": str(e)}

# ------------------------------------------------------------
# SmartMoney Monitor (Placeholder)
# ------------------------------------------------------------
@app.get("/smartmoney_monitor", response_class=JSONResponse)
def smartmoney_monitor():
    # placeholder – ready for API integration
    return {
        "SmartMoney": "Live",
        "Monitored": ["Premier League", "La Liga", "Serie A", "Bundesliga", "Superleague Greece"],
        "last_refresh": datetime.now().strftime("%H:%M:%S")
    }

# ------------------------------------------------------------
# Backup Status (Local readiness check)
# ------------------------------------------------------------
@app.get("/backup_status", response_class=JSONResponse)
def backup_status():
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    files = os.listdir(backup_dir)
    return {
        "Backup": "Ready",
        "StoredFiles": len(files),
        "LastChecked": datetime.now().strftime("%H:%M:%S")
    }

# ------------------------------------------------------------
# Local test run
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
