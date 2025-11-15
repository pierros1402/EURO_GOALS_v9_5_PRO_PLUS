# ============================================================
# AI MATCHLAB — UNIFIED BACKEND
# FastAPI · Templates · Static Files · PWA endpoints
# ============================================================

import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

print("=== [AI MATCHLAB] Backend Boot ===")

# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# ------------------------------------------------------------
# APP INIT
# ------------------------------------------------------------
app = FastAPI()

# Static & Templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------

# HOME PAGE
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


# SIMPLE STATUS API (useful for health checks)
@app.get("/api/status")
async def api_status():
    return {
        "status": "AI MatchLab OK",
        "version": "0.1.0",
        "engine": "UI Skeleton Active"
    }


# ------------------------------------------------------------
# PWA HANDLERS
# ------------------------------------------------------------

# Service Worker
@app.get("/service-worker.js")
async def service_worker():
    sw_path = os.path.join(STATIC_DIR, "service-worker.js")
    return FileResponse(sw_path, media_type="application/javascript")


# Manifest.json
@app.get("/manifest.json")
async def manifest():
    manifest_path = os.path.join(STATIC_DIR, "manifest.json")
    return FileResponse(manifest_path, media_type="application/json")


# ------------------------------------------------------------
# ICONS HANDLER (for full PWA compatibility)
# ------------------------------------------------------------
@app.get("/icons/{filename}")
async def icons(filename: str):
    icons_dir = os.path.join(STATIC_DIR, "icons")
    file_path = os.path.join(icons_dir, filename)
    return FileResponse(file_path)


# ------------------------------------------------------------
# RUN MESSAGE
# ------------------------------------------------------------
print("=== [AI MATCHLAB] Backend Ready ===")
