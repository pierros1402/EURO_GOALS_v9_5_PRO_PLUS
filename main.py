# ============================================================
# AI MATCHLAB – FastAPI Backend (PREMIUM v0.9.3)
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, json, datetime as dt, httpx

print("=== AI MATCHLAB FASTAPI BACKEND (v1.0.0 / PREMIUM UI) ===")

# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

# Static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ------------------------------------------------------------
# WORKER URL
# ------------------------------------------------------------
WORKER_URL = "https://ai-matchlab-live-proxy.pierros1402.workers.dev"


# ============================================================
# ROUTES
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("matchlab.html", {"request": request})


@app.get("/matchlab", response_class=HTMLResponse)
async def matchlab(request: Request):
    return templates.TemplateResponse("matchlab.html", {"request": request})


# ---------------- LEGAL PAGES ----------------

@app.get("/legal/terms", response_class=HTMLResponse)
async def legal_terms(request: Request):
    return templates.TemplateResponse("legal/terms.html", {"request": request})

@app.get("/legal/privacy", response_class=HTMLResponse)
async def legal_privacy(request: Request):
    return templates.TemplateResponse("legal/privacy_policy.html", {"request": request})

@app.get("/legal/cookies", response_class=HTMLResponse)
async def legal_cookies(request: Request):
    return templates.TemplateResponse("legal/cookies_policy.html", {"request": request})

@app.get("/legal/responsible-gambling", response_class=HTMLResponse)
async def legal_rg(request: Request):
    return templates.TemplateResponse("legal/responsible_gambling.html", {"request": request})


# ---------------- HEALTH CHECK ----------------

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": dt.datetime.utcnow().isoformat()}


# ============================================================
# PROXY → WORKER ENDPOINTS
# ============================================================

async def fetch_worker(path: str):
    url = f"{WORKER_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e), "path": path}


@app.get("/ai/status")
async def worker_status():
    return await fetch_worker("/status")


@app.get("/ai/source-a/live")
async def worker_live():
    return await fetch_worker("/live")


@app.get("/ai/source-a/recent")
async def worker_recent():
    return await fetch_worker("/recent")


@app.get("/ai/source-a/upcoming")
async def worker_upcoming():
    return await fetch_worker("/upcoming")


# ============================================================
# SERVICE WORKER / MANIFEST (PWA SUPPORT)
# ============================================================

@app.get("/service-worker.js")
async def service_worker():
    filepath = os.path.join(BASE_DIR, "service-worker.js")
    return FileResponse(filepath, media_type="application/javascript")


@app.get("/manifest.json")
async def manifest():
    filepath = os.path.join(BASE_DIR, "manifest.json")
    return FileResponse(filepath, media_type="application/json")
