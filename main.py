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

# Static & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ------------------------------------------------
# Routers
# ------------------------------------------------
from backend.smartmoney_notifier import start as start_smartmoney
from backend.smartmoney_router import router as smartmoney_router
app.include_router(smartmoney_router)

# ------------------------------------------------
# Routes
# ------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/alert_history", response_class=HTMLResponse)
def alert_history(request: Request):
    return templates.TemplateResponse("alert_history.html", {"request": request})

@app.get("/health", response_class=JSONResponse)
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "details": str(e)}

# ------------------------------------------------
# Startup
# ------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("🚀 [EURO_GOALS] Εκκίνηση v9.4.2 …")
    start_smartmoney()
    print("💰 [SmartMoney] Auto-Notifier PRO ενεργοποιήθηκε.")
    print("✅ Σύστημα έτοιμο.\n")

# ------------------------------------------------
# Fallback 404
# ------------------------------------------------
@app.exception_handler(404)
def not_found(request: Request, exc):
    return templates.TemplateResponse(
        "index.html", {"request": request, "error": "Page not found"}, status_code=404
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
