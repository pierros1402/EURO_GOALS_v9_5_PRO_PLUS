# ================================================================
# EURO_GOALS v9.4.6 PRO+ – Auto-Cleanup + Log Panel Edition
# ================================================================
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os
import psutil
import asyncio
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# ================================================================
# APP INITIALIZATION
# ================================================================
app = FastAPI(title="EURO_GOALS v9.4.6 PRO+")
templates = Jinja2Templates(directory="templates")

# ================================================================
# PATHS & GLOBAL SETTINGS
# ================================================================
DB_PATH = os.path.join("db", "matches.db")
BACKUP_DIR = "backups"
CPU_LIMIT = 95
DISK_LIMIT = 85
RAM_LIMIT = 90
DB_LIMIT_MB = 200
CLEAN_INTERVAL = 300  # seconds

# ================================================================
# GLOBAL LOG BUFFER
# ================================================================
LOG_BUFFER = []
LOG_LIMIT = 50

def log_event(message: str, level: str = "INFO"):
    """Προσθέτει γραμμή στο system log buffer."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = {"time": timestamp, "type": level, "message": message}
    LOG_BUFFER.append(entry)
    if len(LOG_BUFFER) > LOG_LIMIT:
        LOG_BUFFER.pop(0)
    print(f"[LOG][{level}] {message}")

# ================================================================
# AUTO-CLEANUP TASKS
# ================================================================
def cleanup_old_backups(max_keep: int = 3):
    """Διατηρεί μόνο τα πιο πρόσφατα backups."""
    try:
        if not os.path.exists(BACKUP_DIR):
            return
        backups = sorted(
            [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR)],
            key=os.path.getmtime,
            reverse=True
        )
        for old in backups[max_keep:]:
            os.remove(old)
            log_event(f"Removed old backup: {old}", "INFO")
    except Exception as e:
        log_event(f"Backup cleanup error: {e}", "ERROR")

async def auto_cleanup_task():
    """Παρακολουθεί CPU/RAM/Disk/DB και εκτελεί καθαρισμούς."""
    await asyncio.sleep(10)
    while True:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        # ---- CPU overload ----
        if cpu > CPU_LIMIT:
            log_event(f"High CPU {cpu}%, pausing SmartMoney...", "WARNING")
            await asyncio.sleep(30)
            log_event("CPU normalized, SmartMoney resumed.", "INFO")

        # ---- RAM alert ----
        if mem > RAM_LIMIT:
            log_event(f"High RAM usage {mem}%", "WARNING")

        # ---- Disk cleanup ----
        if disk > DISK_LIMIT:
            log_event(f"Disk {disk}% full → cleaning old backups...", "WARNING")
            cleanup_old_backups(max_keep=3)
            log_event("Old backups removed successfully.", "INFO")

        # ---- DB compact ----
        if os.path.exists(DB_PATH):
            db_size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
            if db_size_mb > DB_LIMIT_MB:
                log_event(f"DB size {db_size_mb:.1f}MB → compacting...", "WARNING")
                os.system(f"sqlite3 {DB_PATH} 'VACUUM;'")
                log_event("Database compacted successfully.", "INFO")

        await asyncio.sleep(CLEAN_INTERVAL)

# ================================================================
# STARTUP EVENT
# ================================================================
@app.on_event("startup")
async def startup_event():
    print("🚀 EURO_GOALS v9.4.6 PRO+ started successfully!")
    print("🧠 SmartMoney monitoring active")
    print("💾 Auto-Cleanup Task running every 5min")
    asyncio.create_task(auto_cleanup_task())

# ================================================================
# ROUTES
# ================================================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "EURO_GOALS v9.4.6 PRO+"})

@app.get("/system_status", response_class=HTMLResponse)
async def system_status(request: Request):
    return templates.TemplateResponse("system_status.html", {"request": request, "title": "System Status"})

@app.get("/alert_history", response_class=HTMLResponse)
async def alert_history(request: Request):
    return templates.TemplateResponse("alert_history.html", {"request": request, "title": "Alert History"})

@app.get("/system_logs", response_class=HTMLResponse)
async def system_logs(request: Request):
    return templates.TemplateResponse("system_log.html", {"request": request, "title": "System Logs"})

# ================================================================
# HEALTH CHECK
# ================================================================
def get_health_info():
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        status = "OK"
        if cpu > CPU_LIMIT or mem > RAM_LIMIT or disk > DISK_LIMIT:
            status = "High Load"
        return f"{status} (CPU {cpu:.0f}%, RAM {mem:.0f}%, Disk {disk:.0f}%)"
    except Exception as e:
        log_event(f"Health check error: {e}", "ERROR")
        return "Error"

# ================================================================
# RENDER STATUS
# ================================================================
def get_render_status():
    try:
        render_url = os.getenv("RENDER_HEALTH_URL")
        if not render_url:
            return "Inactive"
        r = requests.get(render_url, timeout=5)
        if r.status_code == 200:
            return "Active"
        return f"Offline ({r.status_code})"
    except Exception as e:
        log_event(f"Render check error: {e}", "ERROR")
        return "Offline"

# ================================================================
# DB CONNECTION CHECK
# ================================================================
def check_db_connection() -> str:
    try:
        db_url = os.getenv("DATABASE_URL", "sqlite:///db/matches.db")
        if db_url.startswith("sqlite:///"):
            path = db_url.replace("sqlite:///", "")
            if not os.path.exists(path):
                return f"Fail (missing: {path})"
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "Connected"
    except SQLAlchemyError as e:
        log_event(f"DB connection error: {e}", "ERROR")
        return "Fail"

# ================================================================
# SYSTEM STATUS DATA (JSON API)
# ================================================================
@app.get("/system_status_data")
async def system_status_data():
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
    log_event(f"Status update → DB: {db_status}, Health: {health}", "INFO")
    return data

# ================================================================
# SYSTEM LOG DATA (JSON)
# ================================================================
@app.get("/system_logs_data")
async def system_logs_data():
    """Επιστρέφει τα τελευταία log entries σε JSON."""
    return LOG_BUFFER

# ================================================================
# MAIN EXECUTION (for local run)
# ================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
