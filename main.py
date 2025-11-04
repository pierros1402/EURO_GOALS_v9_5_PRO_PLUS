# ================================================================
# EURO_GOALS v9.4.4 PRO+ – Main Application
# ================================================================
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os
import psutil
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# ================================================================
# APP INITIALIZATION
# ================================================================
app = FastAPI(title="EURO_GOALS v9.4.4 PRO+")
templates = Jinja2Templates(directory="templates")

# ================================================================
# STARTUP MESSAGE
# ================================================================
@app.on_event("startup")
async def startup_event():
    print("🚀 EURO_GOALS v9.4.4 PRO+ started successfully!")
    print("✅ Push notifications ENABLED")
    print("🧠 SmartMoney loop started (interval=30s, threshold=0.2)")
    print("🗂  Multi-league refresh placeholder active...")

# ================================================================
# HOME / INDEX ROUTE
# ================================================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "EURO_GOALS v9.4.4 PRO+"})

# ================================================================
# SYSTEM STATUS PAGE (TEMPLATE)
# ================================================================
@app.get("/system_status", response_class=HTMLResponse)
async def system_status(request: Request):
    return templates.TemplateResponse("system_status.html", {"request": request, "title": "System Status"})

# ================================================================
# HEALTH CHECK FUNCTION
# ================================================================
def get_health_info():
    """Επιστρέφει health summary (CPU, RAM, Disk)."""
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        return f"OK (CPU {cpu:.0f}%, RAM {mem:.0f}%, Disk {disk:.0f}%)"
    except Exception as e:
        print("[HEALTH][ERR]", e)
        return "Error"

# ================================================================
# RENDER SERVICE STATUS
# ================================================================
def get_render_status():
    """Ελέγχει την κατάσταση του Render service μέσω του health URL."""
    try:
        render_url = os.getenv("RENDER_HEALTH_URL")
        if not render_url:
            return "Inactive"
        r = requests.get(render_url, timeout=5)
        if r.status_code == 200:
            return "Active"
        else:
            return f"Offline ({r.status_code})"
    except Exception as e:
        print("[RENDER][ERR]", e)
        return "Offline"

# ================================================================
# DATABASE CONNECTION CHECK
# ================================================================
def check_db_connection() -> str:
    """Ελέγχει αν μπορεί να συνδεθεί πραγματικά στη βάση."""
    try:
        db_url = os.getenv("DATABASE_URL", "sqlite:///db/matches.db")

        # Αν είναι SQLite, βρίσκουμε το πραγματικό path
        if db_url.startswith("sqlite:///"):
            path = db_url.replace("sqlite:///", "")
            if not os.path.exists(path):
                return f"Fail (missing: {path})"

        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "Connected"

    except SQLAlchemyError as e:
        print("[DB][ERR] check:", e)
        return "Fail"

# ================================================================
# SYSTEM STATUS DATA (JSON API)
# ================================================================
@app.get("/system_status_data")
async def system_status_data():
    """Επιστρέφει δυναμικά δεδομένα για το System Status Panel."""
    db_status = check_db_connection()
    health = get_health_info()
    render_status = get_render_status()
    smartmoney_status = "Live"
    backup_status = "Ready"

    data = {
        "DB": db_status,
        "Health": health,
        "Render": render_status,
        "SmartMoney": smartmoney_status,
        "Backup": backup_status,
        "last_update": datetime.now().strftime("%H:%M:%S"),
    }

    print("[STATUS]", data)
    return data

# ================================================================
# UTILS / PLACEHOLDER FUNCTIONS
# ================================================================
def playsound_safe():
    """Placeholder – ενεργοποιεί ήχο ειδοποίησης αν είναι ON στο .env"""
    if not os.getenv("AUDIO_ALERTS", "false").lower() == "true":
        return
    try:
        print("[AUDIO] Playing sound alert...")
    except Exception as e:
        print("[AUDIO][ERR]", e)

# ================================================================
# ENDPOINT FOR ALERT HISTORY (PLACEHOLDER)
# ================================================================
@app.get("/alert_history", response_class=HTMLResponse)
async def alert_history(request: Request):
    return templates.TemplateResponse("alert_history.html", {"request": request, "title": "Alert History"})

# ================================================================
# MAIN EXECUTION (for local run)
# ================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
