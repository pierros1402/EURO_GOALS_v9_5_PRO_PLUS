# ==============================================
# EURO_GOALS v9.4.0 – Main Application
# Alert & Notification System (Unified Root Version)
# ==============================================
import os
from typing import Optional, List
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

# Εισάγουμε από τη ρίζα (όχι app πλέον)
from alert_manager import (
    init_db, create_alert, list_alerts,
    latest_alert, mark_read, clear_all
)

load_dotenv()

# ----------------------------------------------
# FastAPI setup
# ----------------------------------------------
app = FastAPI(title="EURO_GOALS v9.4.0")

# Static & templates
if not os.path.isdir("static"):
    os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS για desktop/mobile πρόσβαση
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------
# Startup event
# ----------------------------------------------
@app.on_event("startup")
def _on_startup():
    init_db()
    print("[EURO_GOALS] ✅ alert_history initialized")


# ----------------------------------------------
# Schemas
# ----------------------------------------------
class AlertIn(BaseModel):
    type: str
    message: str
    meta: Optional[dict] = None


class MarkReadIn(BaseModel):
    ids: Optional[List[int]] = None
    all: Optional[bool] = False


# ----------------------------------------------
# Root route
# ----------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    html = """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>EURO_GOALS v9.4.0</title>
      <script defer src="/static/js/alerts.js"></script>
      <link rel="stylesheet" href="/static/css/alerts.css" />
      <style>
        body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;padding:24px}
        a.btn{display:inline-block;padding:10px 14px;border-radius:10px;text-decoration:none;border:1px solid #ddd}
      </style>
    </head>
    <body>
      <h1>EURO_GOALS v9.4.0</h1>
      <p>Alert & Notification System ενεργό.</p>
      <p><a class="btn" href="/alert-center">Open Alert Center</a></p>
      <p><label><input type="checkbox" id="notif-toggle"/> Enable Browser Notifications</label></p>
      <script>
        const key='eu_notifications_enabled';
        const toggle=document.getElementById('notif-toggle');
        toggle.checked=localStorage.getItem(key)==='1';
        toggle.addEventListener('change',()=>{
          localStorage.setItem(key,toggle.checked?'1':'0');
          if(toggle.checked){
            window.EUROGOALS && EUROGOALS.Alerts.requestPermission();
          }
        });
        window.addEventListener('DOMContentLoaded',()=>{
          window.EUROGOALS && EUROGOALS.Alerts.startPolling();
        });
      </script>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ----------------------------------------------
# Alert Center UI
# ----------------------------------------------
@app.get("/alert-center", response_class=HTMLResponse)
def alert_center(request: Request):
    try:
        return templates.TemplateResponse("alert_center.html", {"request": request})
    except Exception as e:
        return HTMLResponse(f"<h1>Error loading alert_center.html</h1><pre>{e}</pre>", status_code=500)


# ----------------------------------------------
# API – Alerts
# ----------------------------------------------
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


# ----------------------------------------------
# Demo seed – δημιουργεί 4 δοκιμαστικά alerts
# ----------------------------------------------
@app.post("/api/alerts/demo-seed")
def api_demo_seed():
    demo = [
        ("SMART_MONEY_ALERT", "Chelsea vs Arsenal – Odd drop 1.92 → 1.78", {"book":"Pinnacle","market":"1X2","league":"EPL"}),
        ("GOAL_ALERT", "Borussia Dortmund 1–0 Bayern (23')", {"minute":23}),
        ("SYSTEM_EVENT", "Render deploy succeeded for EURO_GOALS v9.4.0", {"service":"Render"}),
        ("HEALTH_ALERT", "CPU spike detected on backend node", {"cpu":"92%"}),
    ]
    ids = []
    for t, m, meta in demo:
        ids.append(create_alert(t, m, meta))
    return {"ok": True, "inserted": ids}


# ----------------------------------------------
# 404 fallback
# ----------------------------------------------
@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse({"error": "Not Found"}, status_code=404)
