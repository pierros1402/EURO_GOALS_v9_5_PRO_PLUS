# ============================================================
# EURO_GOALS_UNIFIED v9.5.x — Main Application
# Full Integration: SmartMoney Engine v1.0.0
# ============================================================

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers import smartmoney_router
import os

# ------------------------------------------------------------
# APP CONFIGURATION
# ------------------------------------------------------------
app = FastAPI(title="EURO_GOALS_UNIFIED", version="9.5.x")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "..", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "..", "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ------------------------------------------------------------
# INCLUDE ROUTERS
# ------------------------------------------------------------
app.include_router(smartmoney_router.router)

# ------------------------------------------------------------
# ROOT ROUTE
# ------------------------------------------------------------
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ------------------------------------------------------------
# HEALTH CHECK
# ------------------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "OK", "app": "EURO_GOALS_UNIFIED", "smartmoney": "connected"}

# ------------------------------------------------------------
# STARTUP EVENT
# ------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    print("🚀 EURO_GOALS_UNIFIED started successfully.")
    print("🔗 SmartMoney Engine connected:", os.getenv("SMARTMONEY_ENGINE_URL", "not set"))

# ============================================================
# END OF FILE
# ============================================================
