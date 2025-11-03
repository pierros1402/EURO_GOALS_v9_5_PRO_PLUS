# ==============================================
# EURO_GOALS v9.4.1 – Main Application
# Dark UI + Notification Sync (Server-side)
# ==============================================
import os
from typing import Optional, List
from fastapi import FastAPI, Request, Query, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

from alert_manager import (
    init_db as init_alerts_db, create_alert, list_alerts,
    latest_alert, mark_read, clear_all
)
from settings_manager import (
    init_settings_db, get_settings, update_settings
)

load_dotenv()

app = FastAPI(title="EURO_GOALS v9.4.1")

# Static & templates
if not os.path.isdir("static"):
    os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# -------------------- Startup -------------------
@app.on_event("startup")
def _startup():
    init_alerts_db()
    init_settings_db()
    print("[EURO_GOALS] ✅ alert_history & user_settings ready")

# -------------------- Schemas -------------------
class AlertIn(BaseModel):
    type: str
    message: str
    meta: Optional[dict] = None

class MarkReadIn(BaseModel):
    ids: Optional[List[int]] = None
    all: Optional[bool] = False

class SettingsIn(BaseModel):
    notifications_enabled: Optional[bool] = None
    sound_enabled: Optional[bool] = None
    refresh_interval: Optional[int] = None

# -------------------- UI Routes -----------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    # Απλό home με link στο Alert Center + System Summary Bar
    html = """
    <!doctype html><html lang="en"><head>
      <meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
      <title>EURO_GOALS v9.4.1</title>
      <link rel="stylesheet" href="/static/css/alerts.css"/>
      <script defer src="/static/js/alerts.js"></script>
      <script defer src="/static/js/system_summary.js"></script>
    </head><body class="eg-dark">
      <div class="wrap">
        <div id="system-summary-bar"></div>
        <div class="hero">
          <h1>EURO_GOALS v9.4.1</h1>
          <p>Dark UI + Notifications (server-sync)</p>
          <p><a class="btn" href="/alert-center">Open Alert Center</a></p>
        </div>
      </div>
      <script>
        // Φορτώνουμε το System Summary Bar template
        fetch('/system-summary-partial').then(r=>r.text()).then(html=>{
          document.getElementById('system-summary-bar').innerHTML = html;
          window.EUROGOALS && EUROGOALS.Summary && EUROGOALS.Summary.init();
        });
        // Εκκίνηση polling alerts
        window.addEventListener('DOMContentLoaded',()=>{
          window.EUROGOALS && EUROGOALS.Alerts.startPolling();
        });
      </script>
    </body></html>
    """
    return HTMLResponse(html)

@app.get("/system-summary-partial", response_class=HTMLResponse)
def system_summary_partial(request: Request):
    return templates.TemplateResponse("system_summary_bar.html", {"request": request})

@app.get("/alert-center", response_class=HTMLResponse)
def alert_center(request: Request):
    return templates.TemplateResponse("alert_center.html", {"request": request})

# -------------------- API: Alerts ---------------
@app.post("/api/alerts/add")
def api_alert_add(alert: AlertIn):
    alert_id = create_alert(alert.type, alert.message, alert.meta)
    return {"ok": True, "id": alert_id}

@app.get("/api/alerts/list")
def api_alert_list(
    limit: int = Query(200, ge=1, le=1000),
    types: Optional[str] = Query(None),
    unread: bool = Query(False),
    since_id: Optional[int] = Query(None),
):
    tlist = [t.strip() for t in types.split(",")] if types else None
    data = list_alerts(limit=limit, types=tlist, only_unread=unread, since_id=since_id)
    return {"ok": True, "items": data}

@app.get("/api/alerts/latest")
def api_alert_latest(since_id: Optional[int] = Query(None)):
    data = latest_alert(since_id=since_id)
    return {"ok": True, "item": data}

@app.post("/api/alerts/mark-read")
def api_alert_mark_read(payload: MarkReadIn):
    count = mark_read(ids=payload.ids, mark_all=bool(payload.all))
    return {"ok": True, "updated": count}

@app.post("/api/alerts/clear")
def api_alert_clear():
    count = clear_all()
    return {"ok": True, "deleted": count}

@app.post("/api/alerts/demo-seed")
def api_demo_seed():
    demo = [
        ("SMART_MONEY_ALERT", "Chelsea vs Arsenal – Odd drop 1.92 → 1.78", {"book":"Pinnacle","market":"1X2","league":"EPL"}),
        ("GOAL_ALERT", "Borussia Dortmund 1–0 Bayern (23')", {"minute":23}),
        ("SYSTEM_EVENT", "Render deploy succeeded for EURO_GOALS v9.4.1", {"service":"Render"}),
        ("HEALTH_ALERT", "CPU spike detected on backend node", {"cpu":"92%"}),
    ]
    ids = []
    for t, m, meta in demo:
        ids.append(create_alert(t, m, meta))
    return {"ok": True, "inserted": ids}

# -------------------- API: Settings -------------
@app.get("/api/settings/get")
def api_settings_get():
    return {"ok": True, "settings": get_settings()}

@app.post("/api/settings/update")
def api_settings_update(payload: SettingsIn):
    changed = update_settings(
        notifications_enabled=payload.notifications_enabled,
        sound_enabled=payload.sound_enabled,
        refresh_interval=payload.refresh_interval
    )
    return {"ok": True, "settings": changed}
