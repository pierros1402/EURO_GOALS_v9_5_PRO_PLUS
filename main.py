# ============================================================
# EURO_GOALS PRO+ UNIFIED – MAIN ENTRY
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os, time

# ============================================================
# INITIAL SETUP
# ============================================================
load_dotenv()
app = FastAPI(title="EURO_GOALS PRO+ Unified", version="9.5.0")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
static_path = os.path.join(BASE_DIR, "static")

# Serve static files
app.mount("/static", StaticFiles(directory=static_path), name="static")

# ============================================================
# MAIN PAGE (UI)
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Load main dashboard"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "version": "v9.5.0 PRO+",
            "timestamp": time.strftime("%H:%M:%S")
        }
    )

# ============================================================
# HEALTH ENDPOINT (Render Health Check)
# ============================================================
@app.get("/render_health")
async def render_health():
    return {"status": "OK", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}

# ============================================================
# API ENDPOINTS (Sample placeholders)
# ============================================================
@app.get("/system_status_data")
async def system_status_data():
    return {"system": "EURO_GOALS", "status": "online"}

@app.get("/system_status_html", response_class=HTMLResponse)
async def system_status_html(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ============================================================
# STARTUP LOG
# ============================================================
@app.on_event("startup")
async def startup_event():
    print("[EURO_GOALS] 🚀 Starting unified service...")
    print("[EURO_GOALS] ✅ Templates & static routes active.")

