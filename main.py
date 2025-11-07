import os
import time
import psutil
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

APP_VERSION = os.getenv("EURO_GOALS_VERSION", "v9.5.0 PRO+")
START_TS = time.time()

def env_bool(k, d=False):
    v = os.getenv(k)
    if v is None:
        return d
    return str(v).lower() in ("1", "true", "yes", "on")

STATE = {
    "smartmoney_on": env_bool("SMARTMONEY_ON", True),
    "goalmatrix_on": env_bool("GOALMATRIX_ON", True),
    "auto_refresh_on": env_bool("AUTO_REFRESH_ON", True),
    "refresh_secs": int(os.getenv("AUTO_REFRESH_SECS", "15"))
}

# Demo alert store
ALERTS = [
    {"id": 1, "time": "22:31:10", "type": "SmartMoney", "msg": "Unusual odds shift in Premier League (Chelsea - Arsenal)", "level": "high"},
    {"id": 2, "time": "22:34:55", "type": "GoalMatrix", "msg": "Over 2.5 probability > 78% (LaLiga)", "level": "medium"},
]

app = FastAPI(title="EURO_GOALS", version=APP_VERSION)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "APP_VERSION": APP_VERSION, "refresh_secs": STATE["refresh_secs"]}
    )

@app.get("/api/toggles")
async def toggles():
    return STATE

@app.post("/api/toggle/{name}")
async def toggle(name: str, value: bool | None = None, secs: int | None = None):
    name = name.lower()
    if name in ("smartmoney_on","goalmatrix_on","auto_refresh_on"):
        if value is None: raise HTTPException(400,"Missing ?value")
        STATE[name] = bool(value)
        return {"ok":True, name: STATE[name]}
    if name=="refresh_secs":
        if not secs or secs<5 or secs>300: raise HTTPException(400,"secs 5-300")
        STATE["refresh_secs"]=int(secs)
        return {"ok":True,"refresh_secs":STATE["refresh_secs"]}
    raise HTTPException(404,"Unknown toggle")

@app.get("/api/status")
async def status():
    uptime = int(time.time()-START_TS)
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    try: disk = psutil.disk_usage("/").percent
    except Exception: disk = 0
    services = {
        "render":"ok",
        "db":"ok",
        "apis":{"flashscore":"ok","sofascore":"ok","asianconnect":"ok"}
    }
    return {
        "ok":True,
        "version":APP_VERSION,
        "uptime_sec":uptime,
        "cpu":cpu,
        "ram":ram,
        "disk":disk,
        "state":STATE,
        "services":services,
        "last_refresh":time.strftime("%H:%M:%S")
    }

@app.get("/api/alerts_feed")
async def alerts_feed():
    """Simulated alerts feed endpoint."""
    # Future: Connect with SmartMoney Engine / GoalMatrix
    return {"ok": True, "count": len(ALERTS), "alerts": ALERTS}

@app.exception_handler(HTTPException)
async def err(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"ok": False, "error": exc.detail})
