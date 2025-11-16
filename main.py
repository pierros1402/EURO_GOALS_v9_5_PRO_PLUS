# ============================================================
# AI MATCHLAB – UNIFIED FASTAPI BACKEND (v1.0.0)
# ============================================================

import os
import json
import httpx

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# ============================================================
# ENV SETUP
# ============================================================
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WORKER_URL = os.getenv(
    "AI_MATCHLAB_LIVE_WORKER",
    "https://ai-matchlab-live-proxy.pierros1402.workers.dev"
)

# ============================================================
# FASTAPI INIT
# ============================================================
app = FastAPI(title="AI MATCHLAB Backend")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


# ============================================================
# PWA (manifest.json & service-worker.js)
# 100% Correct Absolute Paths (Τέλος το corrupted binary!)
# ============================================================

@app.get("/manifest.json", include_in_schema=False)
def serve_manifest():
    return FileResponse(
        os.path.join(BASE_DIR, "manifest.json"),
        media_type="application/json"
    )


@app.get("/service-worker.js", include_in_schema=False)
def serve_sw():
    return FileResponse(
        os.path.join(BASE_DIR, "service-worker.js"),
        media_type="application/javascript"
    )


# ============================================================
# MAIN UI (MatchLab)
# ============================================================

@app.get("/", response_class=HTMLResponse)
def serve_ui(request: Request):
    return templates.TemplateResponse("matchlab.html", {"request": request})


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "AI MATCHLAB",
        "version": "v1.0.0",
        "worker_configured": WORKER_URL is not None
    }


# ============================================================
# WORKER STATUS ENDPOINT
# ============================================================

@app.get("/api/worker/status")
async def worker_status():
    url = f"{WORKER_URL}/status"
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(url)
            r.raise_for_status()

            try:
                data = r.json()
                return {
                    "ok": True,
                    "raw": data,
                    "target_url": url
                }
            except Exception:
                return {
                    "ok": False,
                    "error": "invalid_json",
                    "raw": r.text,
                    "target_url": url
                }

    except Exception as e:
        return {"ok": False, "error": str(e), "target_url": url}


# ============================================================
# LIVE FEED FOR UI (/api/source-a/live)
# ============================================================

@app.get("/api/source-a/live")
async def worker_live_feed():
    url = f"{WORKER_URL}/ai/source-a/live"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
            r.raise_for_status()

            try:
                parsed = r.json()
                return parsed

            except Exception:
                return {
                    "ok": False,
                    "error": "invalid_json",
                    "raw": r.text,
                    "target_url": url
                }

    except Exception as e:
        return {"ok": False, "error": str(e), "target_url": url}


# ============================================================
# START MESSAGE
# ============================================================

print("============================================================")
print(" AI MATCHLAB — FASTAPI BACKEND LOADED (v1.0.0)")
print(f" Environment: development")
print(f" Worker URL: {WORKER_URL}")
print("============================================================")
