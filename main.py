import os
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

APP_VERSION = os.getenv("EURO_GOALS_VERSION", "v9.5.0 PRO+")
START_TS = time.time()

# ----------------------------
# In-memory UI toggles (server-side truth)
# ----------------------------
def env_bool(key: str, default: bool) -> bool:
    v = os.getenv(key)
    if v is None: 
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")

STATE = {
    "smartmoney_on": env_bool("SMARTMONEY_ON", True),
    "goalmatrix_on": env_bool("GOALMATRIX_ON", True),
    "auto_refresh_on": env_bool("AUTO_REFRESH_ON", True),
    "refresh_secs": int(os.getenv("AUTO_REFRESH_SECS", "15")),
}

# ----------------------------
# FastAPI app
# ----------------------------
app = FastAPI(title="EURO_GOALS", version=APP_VERSION)

# Static & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    ctx = {
        "request": request,
        "APP_VERSION": APP_VERSION,
        "refresh_secs": STATE["refresh_secs"],
    }
    return templates.TemplateResponse("index.html", ctx)


# ----------------------------
# Lightweight status endpoints
# ----------------------------
@app.get("/api/ping")
async def ping():
    return {"ok": True, "version": APP_VERSION, "uptime_sec": int(time.time() - START_TS)}

@app.get("/api/toggles")
async def get_toggles():
    return {
        "smartmoney_on": STATE["smartmoney_on"],
        "goalmatrix_on": STATE["goalmatrix_on"],
        "auto_refresh_on": STATE["auto_refresh_on"],
        "refresh_secs": STATE["refresh_secs"],
    }

@app.post("/api/toggle/{name}")
async def set_toggle(name: str, value: bool | None = None, secs: int | None = None):
    name = name.lower()
    if name in ("smartmoney_on", "goalmatrix_on", "auto_refresh_on"):
        if value is None:
            raise HTTPException(400, "Provide ?value=true|false")
        STATE[name] = bool(value)
        return {"ok": True, name: STATE[name]}
    if name == "refresh_secs":
        if secs is None or secs < 5 or secs > 300:
            raise HTTPException(400, "Provide ?secs=5..300")
        STATE["refresh_secs"] = int(secs)
        return {"ok": True, "refresh_secs": STATE["refresh_secs"]}
    raise HTTPException(404, "Unknown toggle")

@app.get("/api/status")
async def status():
    # Σε αυτή την έκδοση κρατάμε deterministic statuses (χωρίς εξωτερικά calls)
    uptime = int(time.time() - START_TS)
    services = {
        "render_health": "ok",   # hook για μελλοντικό http check
        "db": "ok",              # hook για πραγματικό DB check
        "apis": {
            "flashscore": "ok",
            "sofascore": "ok",
            "asianconnect": "ok"
        }
    }
    return {
        "ok": True,
        "version": APP_VERSION,
        "uptime_sec": uptime,
        "state": STATE,
        "services": services
    }


# ----------------------------
# Error handlers (clean JSON)
# ----------------------------
@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"ok": False, "error": exc.detail})
