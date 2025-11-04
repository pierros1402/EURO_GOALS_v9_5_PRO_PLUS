# ================================================================
# EURO_GOALS v9.5.0 PRO+ – Unified Responsive Edition
# ================================================================
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os
import psutil
import asyncio
import requests
import shutil
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# ================================================================
# APP INIT
# ================================================================
app = FastAPI(title="EURO_GOALS v9.5.0 PRO+")
templates = Jinja2Templates(directory="templates")

# ================================================================
# GLOBAL PATHS & LIMITS
# ================================================================
DB_PATH = os.path.join("db", "matches.db")
BACKUP_DIR = "backups"
CPU_LIMIT, DISK_LIMIT, RAM_LIMIT = 95, 85, 90
DB_LIMIT_MB, CLEAN_INTERVAL = 200, 300

# ================================================================
# LOG BUFFER
# ================================================================
LOG_BUFFER, LOG_LIMIT = [], 50
def log_event(msg, lvl="INFO"):
    t = datetime.now().strftime("%H:%M:%S")
    entry = {"time": t, "type": lvl, "message": msg}
    LOG_BUFFER.append(entry)
    if len(LOG_BUFFER) > LOG_LIMIT:
        LOG_BUFFER.pop(0)
    print(f"[LOG][{lvl}] {msg}")

# ================================================================
# BACKUP MANAGEMENT
# ================================================================
def make_backup():
    """Δημιουργεί νέο backup DB"""
    try:
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        ts = datetime.now().strftime("%Y_%m_%d_%H_%M")
        bfile = os.path.join(BACKUP_DIR, f"EURO_GOALS_BACKUP_{ts}.db")
        shutil.copy(DB_PATH, bfile)
        log_event(f"Backup created: {bfile}", "INFO")
        return True
    except Exception as e:
        log_event(f"Backup failed: {e}", "ERROR")
        return False

def cleanup_old_backups(max_keep=5):
    try:
        if not os.path.exists(BACKUP_DIR): return
        files = sorted(
            [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR)],
            key=os.path.getmtime,
            reverse=True)
        for old in files[max_keep:]:
            os.remove(old)
            log_event(f"Removed old backup: {old}", "INFO")
    except Exception as e:
        log_event(f"Cleanup failed: {e}", "ERROR")

# ================================================================
# AUTO-CLEANUP BACKGROUND TASK
# ================================================================
async def auto_cleanup_task():
    await asyncio.sleep(10)
    while True:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        if cpu > CPU_LIMIT:
            log_event(f"High CPU {cpu}%", "WARNING")
            await asyncio.sleep(20)
        if mem > RAM_LIMIT:
            log_event(f"High RAM {mem}%", "WARNING")
        if disk > DISK_LIMIT:
            log_event(f"Disk {disk}% → cleanup backups", "WARNING")
            cleanup_old_backups()
        if os.path.exists(DB_PATH):
            size = os.path.getsize(DB_PATH)/(1024*1024)
            if size > DB_LIMIT_MB:
                log_event(f"DB {size:.1f}MB → compacting", "WARNING")
                os.system(f"sqlite3 {DB_PATH} 'VACUUM;'")
        await asyncio.sleep(CLEAN_INTERVAL)

# ================================================================
# STARTUP EVENT
# ================================================================
@app.on_event("startup")
async def startup_event():
    print("🚀 EURO_GOALS v9.5.0 PRO+ launched")
    asyncio.create_task(auto_cleanup_task())
    log_event("System initialized", "INFO")

# ================================================================
# HEALTH / DB / RENDER STATUS
# ================================================================
def get_health_info():
    try:
        cpu, mem, disk = psutil.cpu_percent(0.5), psutil.virtual_memory().percent, psutil.disk_usage("/").percent
        s = "OK" if cpu<CPU_LIMIT and mem<RAM_LIMIT and disk<DISK_LIMIT else "High Load"
        return f"{s} (CPU {cpu:.0f}%, RAM {mem:.0f}%, Disk {disk:.0f}%)"
    except Exception as e:
        log_event(f"Health err: {e}", "ERROR")
        return "Error"

def check_db_connection():
    try:
        db_url = os.getenv("DATABASE_URL", "sqlite:///db/matches.db")
        if db_url.startswith("sqlite:///"):
            path = db_url.replace("sqlite:///", "")
            if not os.path.exists(path):
                return "Fail (missing)"
        e = create_engine(db_url)
        with e.connect() as c: c.execute(text("SELECT 1"))
        return "Connected"
    except SQLAlchemyError as e:
        log_event(f"DB conn err: {e}", "ERROR")
        return "Fail"

def get_render_status():
    try:
        url = os.getenv("RENDER_HEALTH_URL")
        if not url: return "Inactive"
        r = requests.get(url, timeout=5)
        return "Active" if r.status_code==200 else f"Offline ({r.status_code})"
    except Exception as e:
        log_event(f"Render err: {e}", "ERROR")
        return "Offline"

# ================================================================
# ROUTES – UI
# ================================================================
@app.get("/", response_class=HTMLResponse)
async def home(req: Request):
    return templates.TemplateResponse("system_status.html", {"request": req, "title": "EURO_GOALS v9.5.0 PRO+"})

@app.get("/system_status", response_class=HTMLResponse)
async def sys_status(req: Request):
    return templates.TemplateResponse("system_status.html", {"request": req, "title": "System Status"})

@app.get("/system_logs", response_class=HTMLResponse)
async def sys_logs(req: Request):
    return templates.TemplateResponse("system_log.html", {"request": req, "title": "System Logs"})

@app.get("/control_panel", response_class=HTMLResponse)
async def ctrl_panel(req: Request):
    return templates.TemplateResponse("control_panel.html", {"request": req, "title": "Control Dashboard"})

# ================================================================
# ROUTES – JSON APIs
# ================================================================
@app.get("/system_status_data")
async def sys_status_data():
    d = {
        "DB": check_db_connection(),
        "Health": get_health_info(),
        "Render": get_render_status(),
        "SmartMoney": "Live",
        "Backup": "Ready",
        "last_update": datetime.now().strftime("%H:%M:%S"),
    }
    log_event(f"Status → {d['DB']}, {d['Health']}", "INFO")
    return JSONResponse(d)

@app.get("/system_logs_data")
async def sys_logs_data():
    return JSONResponse(LOG_BUFFER)

@app.post("/manual_backup")
async def manual_backup():
    ok = make_backup()
    cleanup_old_backups()
    return {"result": "success" if ok else "fail"}

@app.post("/clear_logs")
async def clear_logs():
    LOG_BUFFER.clear()
    log_event("System logs cleared manually", "INFO")
    return {"result": "cleared"}

# ================================================================
# LOCAL RUN
# ================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
