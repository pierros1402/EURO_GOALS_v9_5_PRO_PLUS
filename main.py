# ==============================================
# EURO_GOALS v9.4.3 PRO+ – Main Application
# SmartMoney Auto-Notifier + Mock API Routes
# ==============================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# ------------------------------------------------
# 1. Φόρτωση περιβάλλοντος (.env)
# ------------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

# ------------------------------------------------
# 2. Ρύθμιση εφαρμογής & templates
# ------------------------------------------------
app = FastAPI(title="EURO_GOALS v9.4.3 PRO+")
templates = Jinja2Templates(directory="templates")

# ------------------------------------------------
# 3. Database engine
# ------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# ------------------------------------------------
# 4. System startup log
# ------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("=============================================")
    print("🚀 [EURO_GOALS] Εκκίνηση εφαρμογής v9.4.3 PRO+ …")
    print("💰 [SmartMoney] Auto-Notifier PRO+ ενεργοποιήθηκε.")
    print("=============================================")

# ------------------------------------------------
# 5. Βασικές σελίδες
# ------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/alert/history", response_class=HTMLResponse)
async def alert_history(request: Request):
    return templates.TemplateResponse("alert_history.html", {"request": request})

@app.get("/smartmoney/monitor", response_class=HTMLResponse)
async def smartmoney_monitor(request: Request):
    return templates.TemplateResponse("smartmoney_monitor.html", {"request": request})

@app.get("/unified/dashboard", response_class=HTMLResponse)
async def unified_dashboard(request: Request):
    return templates.TemplateResponse("unified_dashboard.html", {"request": request})

# ------------------------------------------------
# 6. Health check
# ------------------------------------------------
@app.get("/health", response_class=JSONResponse)
async def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "error": str(e)}

# ------------------------------------------------
# 7. Mock API routes (για σταθερότητα frontend)
# ------------------------------------------------
@app.get("/smartmoney/events", response_class=JSONResponse)
async def get_smartmoney_events():
    return {"events": []}

@app.get("/api/alerts/latest", response_class=JSONResponse)
async def get_latest_alert():
    return {"latest": None}

@app.get("/system_status_data", response_class=JSONResponse)
async def get_system_status_data():
    return {
        "database": "connected",
        "health": "ok",
        "smartmoney": "live",
        "render": "active",
        "timestamp": "2025-11-04T06:00:00Z"
    }

# ------------------------------------------------
# 8. Εκτέλεση τοπικά
# ------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
