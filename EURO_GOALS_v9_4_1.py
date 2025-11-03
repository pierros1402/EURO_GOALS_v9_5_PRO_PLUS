# ================================================================
# EURO_GOALS v9.4.2 – FastAPI Backend (SmartMoney Auto-Notifier PRO)
# ================================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# ------------------------------------------------
# Load .env variables
# ------------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

# ------------------------------------------------
# Database setup
# ------------------------------------------------
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

# ------------------------------------------------
# FastAPI app
# ------------------------------------------------
app = FastAPI(title="EURO_GOALS v9.4.2 – SmartMoney Auto-Notifier PRO")

# Static files & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ------------------------------------------------
# Routers & Modules
# ------------------------------------------------
from backend.smartmoney_notifier import start as start_smartmoney
from backend.smartmoney_router import router as smartmoney_router

# Include SmartMoney router
app.include_router(smartmoney_router)

# ------------------------------------------------
# Basic Routes
# ------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Αρχική σελίδα EURO_GOALS"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/alert_history", response_class=HTMLResponse)
def alert_history(request: Request):
    """Πλήρες ιστορικό ειδοποιήσεων (SmartMoney, Goals, System)"""
    return templates.TemplateResponse("alert_history.html", {"request": request})

@app.get("/health", response_class=JSONResponse)
def health_check():
    """Health endpoint για Render monitoring"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "details": str(e)}

# ------------------------------------------------
# Startup event
# ------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("🚀 [EURO_GOALS] Εκκίνηση εφαρμογής v9.4.2 …")
    # Start SmartMoney Auto-Notifier PRO background thread
    start_smartmoney()
    print("💰 [SmartMoney] Auto-Notifier PRO ενεργοποιήθηκε.")
    print("✅ Σύστημα έτοιμο.\n")

# ------------------------------------------------
# Optional fallback route
# ------------------------------------------------
@app.exception_handler(404)
def not_found(request: Request, exc):
    return templates.TemplateResponse(
        "index.html", {"request": request, "error": "Page not found"}, status_code=404
    )

# ------------------------------------------------
# Entry point (local run)
# ------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
