# ==============================================================
# EURO_GOALS v9.3 – Unified Monitor (Render + Local)
# ==============================================================
# Περιλαμβάνει:
# ✅ Health checks (Render + Unified)
# ✅ System Status API
# ✅ SmartMoney & GoalMatrix integration placeholders
# ✅ Auto-detection για SQLite / PostgreSQL
# ==============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import os
import sqlite3
from dotenv import load_dotenv

# ==============================================================
# 1️⃣  Βασική ρύθμιση εφαρμογής
# ==============================================================
load_dotenv()
app = FastAPI(title="EURO_GOALS v9.3 – Unified Monitor")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ==============================================================
# 2️⃣  Database setup (SQLite τοπικά ή PostgreSQL σε Render)
# ==============================================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

def get_db_connection():
    if DATABASE_URL.startswith("sqlite"):
        conn = sqlite3.connect("matches.db")
        return conn
    # PostgreSQL connection (placeholder για Render)
    return None

# ==============================================================
# 3️⃣  Import Health Check Module
# ==============================================================
from health_check import run_full_healthcheck

# ==============================================================
# 4️⃣  Root Route – Dashboard
# ==============================================================
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    """
    Αρχική σελίδα EURO_GOALS – δείχνει συνοπτικά τα panels.
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "version": "v9.3",
            "title": "EURO_GOALS – Unified Monitor"
        }
    )

# ==============================================================
# 5️⃣  Unified System Status Data (JSON)
# ==============================================================
@app.get("/system_status_data")
def system_status_data():
    """
    Επιστρέφει τρέχουσα κατάσταση όλων των components σε JSON.
    """
    report = run_full_healthcheck()
    return JSONResponse(content=report)

# ==============================================================
# 6️⃣  HEALTH ENDPOINTS (for Render + Unified Monitor)
# ==============================================================
@app.get("/health")
def health_status():
    """
    Επιστρέφει πλήρη αναφορά υγείας (System Status Panel).
    """
    try:
        report = run_full_healthcheck()
        return JSONResponse(content=report)
    except Exception as e:
        return JSONResponse(
            content={"status": "FAIL", "error": str(e)},
            status_code=500
        )

@app.get("/health_simple")
def health_simple():
    """
    Απλό endpoint για Render health check (HTTP 200 = OK).
    """
    return {"status": "ok"}

# ==============================================================
# 7️⃣  GoalMatrix API placeholder
# ==============================================================
@app.get("/goalmatrix_data")
def goalmatrix_data():
    """
    Επιστρέφει δοκιμαστικά δεδομένα GoalMatrix.
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "active",
        "source": "GoalMatrix",
        "message": "GoalMatrix endpoint operational"
    }

# ==============================================================
# 8️⃣  SmartMoney API placeholder
# ==============================================================
@app.get("/smartmoney_data")
def smartmoney_data():
    """
    Επιστρέφει δοκιμαστικά δεδομένα SmartMoney.
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "active",
        "source": "SmartMoney",
        "message": "SmartMoney module running"
    }

# ==============================================================
# 9️⃣  Static Pages Routes (System / SmartMoney / Matrix)
# ==============================================================
@app.get("/system_status", response_class=HTMLResponse)
def system_status_page(request: Request):
    return templates.TemplateResponse("system_status.html", {"request": request})

@app.get("/smartmoney", response_class=HTMLResponse)
def smartmoney_page(request: Request):
    return templates.TemplateResponse("smartmoney.html", {"request": request})

@app.get("/goalmatrix", response_class=HTMLResponse)
def goalmatrix_page(request: Request):
    return templates.TemplateResponse("goalmatrix.html", {"request": request})

# ==============================================================
# 🔟  Startup Event
# ==============================================================
@app.on_event("startup")
def startup_event():
    print(f"[EURO_GOALS] 🚀 v9.3 started at {datetime.utcnow().isoformat()}")
    print("[EURO_GOALS] ✅ Unified Monitoring initialized.")

# ==============================================================
# END OF FILE
# ==============================================================

