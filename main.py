# ============================================================
# EURO_GOALS_UNIFIED v9.5.4 PRO+  (Docker / Render Compatible)
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path

# ============================================================
# App setup
# ============================================================
app = FastAPI(
    title="EURO_GOALS_UNIFIED v9.5.4 PRO+",
    version="9.5.4",
)

# ============================================================
# Directories
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# --- Render & Local Compatible Static Mount ---
if not STATIC_DIR.exists():
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ============================================================
# Root Endpoint
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    html_content = """
    <html>
        <head>
            <meta charset="utf-8">
            <title>🏆 EURO_GOALS v9.5.0 PRO+ – API Interface</title>
            <link rel="manifest" href="/static/manifest.json">
            <link rel="icon" href="/static/favicon.ico" type="image/x-icon">
            <script src="/static/service-worker.js"></script>
        </head>
        <body style="font-family:Arial; background:#fff; color:#000; margin:40px;">
            <h2>🏆 <b>EURO_GOALS v9.5.0 PRO+</b> – API Interface</h2>
            <p><b>Available endpoints:</b></p>
            <ul>
                <li><a href="/system_status_data">/system_status_data</a> – JSON Unified Status</li>
                <li><a href="/system_status_html">/system_status_html</a> – HTML Unified Dashboard</li>
                <li><a href="/render_health">/render_health</a> – Render Health Check</li>
                <li><a href="/smartmoney_monitor">/smartmoney_monitor</a> – SmartMoney Monitor</li>
                <li><a href="/backup_status">/backup_status</a> – Backup Readiness</li>
            </ul>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# ============================================================
# Example API endpoints (active ones)
# ============================================================
@app.get("/system_status_data")
async def system_status_data():
    return {
        "status": "✅ OK",
        "version": "9.5.4 PRO+",
        "environment": os.getenv("RENDER", "Local"),
    }

@app.get("/system_status_html", response_class=HTMLResponse)
async def system_status_html(request: Request):
    return templates.TemplateResponse("system_status.html", {"request": request})

@app.get("/render_health")
async def render_health():
    return {"health": "OK", "source": "Render Docker"}

@app.get("/smartmoney_monitor")
async def smartmoney_monitor():
    return {"smartmoney": "Monitoring active"}

@app.get("/backup_status")
async def backup_status():
    return {"backup": "Ready", "storage": "Google Drive / Local"}

# ============================================================
# Service Worker / Manifest / Favicon routes (explicit fallback)
# ============================================================
@app.get("/service-worker.js")
async def service_worker():
    path = STATIC_DIR / "service-worker.js"
    if path.exists():
        return HTMLResponse(path.read_text(), media_type="application/javascript")
    return JSONResponse({"error": "service-worker.js not found"}, status_code=404)

@app.get("/static/manifest.json")
async def manifest_json():
    path = STATIC_DIR / "manifest.json"
    if path.exists():
        return HTMLResponse(path.read_text(), media_type="application/json")
    return JSONResponse({"error": "manifest.json not found"}, status_code=404)

@app.get("/favicon.ico")
async def favicon():
    path = STATIC_DIR / "favicon.ico"
    if path.exists():
        return HTMLResponse(path.read_bytes(), media_type="image/x-icon")
    return JSONResponse({"error": "favicon.ico not found"}, status_code=404)

# ============================================================
# Startup Event
# ============================================================
@app.on_event("startup")
async def startup_event():
    print("🚀 EURO_GOALS v9.5.4 PRO+ started successfully!")

# ============================================================
# Run (local debug only)
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=True)
