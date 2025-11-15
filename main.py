# ============================================================
# AI MATCHLAB – MAIN APPLICATION (FULL PACKAGE)
# ============================================================

import os
import sys
import asyncio
from typing import Optional, Dict, Any

from dotenv import load_dotenv
load_dotenv()  # 👈 ΕΔΩ ΕΙΝΑΙ ΤΟ ΚΛΕΙΔΙ

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import httpx

print("=== [AI MATCHLAB] 🚀 Booting MAIN application... ===")

# ------------------------------------------------------------
# PATH / BASE CONFIG
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# ------------------------------------------------------------
# ENVIRONMENT VARIABLES
# ------------------------------------------------------------
# Βάλε εδώ το URL του Cloudflare Worker που έχουμε για AI MatchLab
# π.χ. https://ai-matchlab-worker.your-subdomain.workers.dev
WORKER_BASE_URL = os.getenv("AIMATCHLAB_WORKER_URL", "").strip()

if not WORKER_BASE_URL:
    print("[AI MATCHLAB] ⚠️ WARNING: AIMATCHLAB_WORKER_URL is not set!")
else:
    print(f"[AI MATCHLAB] ✅ Using Worker URL: {WORKER_BASE_URL}")

# Optional: Render environment / version info
APP_ENV = os.getenv("APP_ENV", "development")
APP_VERSION = os.getenv("AIMATCHLAB_VERSION", "v1.0.0")

print(f"[AI MATCHLAB] Environment: {APP_ENV} | Version: {APP_VERSION}")

# ------------------------------------------------------------
# FASTAPI APP
# ------------------------------------------------------------
app = FastAPI(
    title="AI MatchLab",
    description="AI MatchLab — Unified Betting Intelligence Workspace",
    version=APP_VERSION,
)

# ------------------------------------------------------------
# STATIC FILES & TEMPLATES
# ------------------------------------------------------------
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print(f"[AI MATCHLAB] ✅ Static mounted from: {STATIC_DIR}")
else:
    print(f"[AI MATCHLAB] ⚠️ Static directory not found: {STATIC_DIR}")

if not os.path.isdir(TEMPLATES_DIR):
    print(f"[AI MATCHLAB] ⚠️ Templates directory not found: {TEMPLATES_DIR}")

templates = Jinja2Templates(directory=TEMPLATES_DIR)


# ------------------------------------------------------------
# HELPER: CALL CLOUDFLARE WORKER
# ------------------------------------------------------------
async def call_worker(
    path: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0,
) -> Any:
    """
    Γενικός helper για να καλούμε τον Cloudflare Worker.
    Όλα τα data/feeds περνάνε από εκεί, χωρίς να φτιάχνουμε δικά μας APIs.
    """
    if not WORKER_BASE_URL:
        raise RuntimeError("AIMATCHLAB_WORKER_URL is not configured")

    # Φτιάχνουμε full URL: WORKER_BASE_URL + path
    base = WORKER_BASE_URL.rstrip("/")
    path = path.lstrip("/")
    url = f"{base}/{path}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            method_upper = method.upper()

            if method_upper == "GET":
                r = await client.get(url, params=params)
            elif method_upper == "POST":
                r = await client.post(url, params=params, json=json_body)
            elif method_upper == "PUT":
                r = await client.put(url, params=params, json=json_body)
            elif method_upper == "DELETE":
                r = await client.delete(url, params=params, json=json_body)
            else:
                raise ValueError(f"Unsupported method: {method}")

        if r.status_code >= 400:
            raise HTTPException(
                status_code=r.status_code,
                detail={"error": "Worker error", "body": r.text},
            )

        # Προσπαθούμε να γυρίσουμε JSON αν είναι
        try:
            return r.json()
        except Exception:
            # αλλιώς γυρνάμε raw text
            return r.text

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Worker request timed out",
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[AI MATCHLAB] ❌ Worker call failed: {e}")
        raise HTTPException(
            status_code=502,
            detail="Error communicating with AI MatchLab Worker",
        )


# ------------------------------------------------------------
# ROOT / MAIN UI
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Κεντρική σελίδα AI MatchLab.
    Εδώ θα φορτώνουμε το βασικό layout, panels, κ.λπ.
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_version": APP_VERSION,
            "app_env": APP_ENV,
            "worker_url_configured": bool(WORKER_BASE_URL),
        },
    )


# ------------------------------------------------------------
# OPTIONAL: Dedicated MatchLab Workspace Route
# (αν θέλεις ξεχωριστό template π.χ. matchlab.html)
# ------------------------------------------------------------
@app.get("/workspace", response_class=HTMLResponse)
async def workspace(request: Request):
    """
    Προαιρετικό route για AI MatchLab workspace.
    Αν δεν έχεις ακόμα matchlab.html, μπορείς να το δείχνεις ίδια με index.html.
    """
    template_name = "matchlab.html"
    template_path = os.path.join(TEMPLATES_DIR, template_name)

    if not os.path.isfile(template_path):
        # Αν δεν υπάρχει ακόμα matchlab.html, γύρνα index.html
        template_name = "index.html"

    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "app_version": APP_VERSION,
            "app_env": APP_ENV,
            "worker_url_configured": bool(WORKER_BASE_URL),
        },
    )


# ------------------------------------------------------------
# GENERIC PROXY API → WORKER
# ------------------------------------------------------------
@app.get("/api/worker/{subpath:path}")
async def api_worker_proxy(
    subpath: str,
    request: Request,
):
    """
    Generic GET proxy. Ό,τι στείλεις στο /api/worker/... προωθείται στο Worker.

    Παράδειγμα:
    Frontend → /api/worker/aimatchlab/feed?league=premier
    Worker   → {WORKER_BASE_URL}/aimatchlab/feed?league=premier
    """
    # Παίρνουμε τα query params
    params = dict(request.query_params)
    result = await call_worker(
        path=subpath,
        method="GET",
        params=params,
    )
    return JSONResponse(content=result)


@app.post("/api/worker/{subpath:path}")
async def api_worker_proxy_post(
    subpath: str,
    request: Request,
):
    """
    Generic POST proxy προς Worker (για configs, filters, κ.λπ. αν χρειαστούν).
    """
    params = dict(request.query_params)
    try:
        body = await request.json()
    except Exception:
        body = None

    result = await call_worker(
        path=subpath,
        method="POST",
        params=params,
        json_body=body,
    )
    if isinstance(result, (dict, list)):
        return JSONResponse(content=result)
    return JSONResponse(content={"result": result})


# ------------------------------------------------------------
# HEALTH CHECKS (Render κ.λπ.)
# ------------------------------------------------------------
@app.get("/health", response_class=JSONResponse)
async def health():
    """
    Απλό health check για Render / monitoring.
    """
    return {
        "status": "ok",
        "app": "AI MatchLab",
        "version": APP_VERSION,
        "env": APP_ENV,
        "worker_configured": bool(WORKER_BASE_URL),
    }


@app.get("/render-refresh", response_class=JSONResponse)
async def render_refresh():
    """
    Extra endpoint για manual ping από Render ή browser.
    """
    return {
        "status": "refresh-ok",
        "message": "AI MatchLab Render refresh endpoint is alive.",
    }


# ------------------------------------------------------------
# GLOBAL ERROR HANDLERS (OPTIONAL, LIGHT)
# ------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Μπορούμε να το κρατήσουμε απλό για αρχή
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    print(f"[AI MATCHLAB] ❌ Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error in AI MatchLab backend"},
    )


# ============================================================
# END OF FILE — AI MATCHLAB MAIN
# ============================================================
