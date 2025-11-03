# ==============================================================
# EURO_GOALS v9.3.5 – Unified Monitor + System Logs Endpoint
# ==============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import os, sqlite3
from dotenv import load_dotenv
from health_check import run_full_healthcheck, ensure_logs_table

load_dotenv()
app = FastAPI(title="EURO_GOALS v9.3.5 – Unified Monitor")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# ==============================================================
# 1️⃣  Root + System Pages
# ==============================================================
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "version": "v9.3.5"})

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
# 2️⃣  API Endpoints
# ==============================================================
@app.get("/system_status_data")
def system_status_data():
    report = run_full_healthcheck()
    return JSONResponse(content=report)

@app.get("/system_logs")
def get_system_logs():
    """Επιστρέφει τις τελευταίες 20 εγγραφές από το system_logs."""
    ensure_logs_table()
    try:
        conn = sqlite3.connect("matches.db")
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT 20").fetchall()
        data = [dict(r) for r in rows]
        conn.close()
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/health_simple")
def health_simple():
    return {"status": "ok"}

# ==============================================================
# 3️⃣  Startup Event
# ==============================================================
@app.on_event("startup")
def startup_event():
    print(f"[EURO_GOALS] 🚀 v9.3.5 started at {datetime.utcnow().isoformat()}")
    ensure_logs_table()
    print("[EURO_GOALS] ✅ System Logs table ready.")
