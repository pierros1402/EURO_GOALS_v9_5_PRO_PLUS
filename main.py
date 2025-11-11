# ============================================================
# EURO_GOALS v9.7.6 PRO+ — UNIFIED MAIN APP
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio, os, time, datetime

print("=== [EURO_GOALS] Unified App 9.7.6 PRO+ — LIVE SYSTEM ACTIVE ===")

# ------------------------------------------------------------
# PATHS / SETUP
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in os.sys.path:
    os.sys.path.append(BASE_DIR)

app = FastAPI(title="EURO_GOALS PRO+", version="9.7.6 PRO+")

# Static assets
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ------------------------------------------------------------
# ENGINES
# ------------------------------------------------------------
from services.smartmoney_engine import get_odds_snapshot, get_smartmoney_signals
from services.goal_matrix_engine import get_goal_matrix

# ------------------------------------------------------------
# ROOT STATUS PAGE
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home():
    now = datetime.datetime.now().strftime("%H:%M:%S")
    html = f"""
    <html>
      <head>
        <title>EURO_GOALS PRO+ v9.7.6 — Live System Status</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="/static/unified_theme.css">
        <style>
          .panel {{
            margin: 3rem auto;
            max-width: 640px;
            background: rgba(15,25,45,.85);
            border-radius: 18px;
            border: 1px solid #1a2a4a;
            box-shadow: 0 0 20px #0a84ff22;
            padding: 2rem;
            text-align: center;
          }}
          h1 {{ color: var(--accent); font-size: 1.8rem; margin-bottom: 0.5rem; }}
          h2 {{ color: var(--muted); font-weight: 400; margin-top: 0; }}
          .ok {{ color: var(--ok); }}
          .warn {{ color: var(--warn); }}
          .err {{ color: var(--err); }}
          .meta {{ color: var(--muted); font-size: 0.9rem; margin-top: 1rem; }}
          footer {{ text-align:center; margin-top:2rem; color:var(--muted); font-size:0.8rem; }}
        </style>
      </head>
      <body>
        <div class="panel">
          <h1>⚽ EURO_GOALS PRO+ v9.7.6</h1>
          <h2>Unified Data System — Live Monitor</h2>
          <p><b>SmartMoney Engine:</b> <span class="ok">Active</span></p>
          <p><b>GoalMatrix Engine:</b> <span class="ok">Synchronized</span></p>
          <p><b>Sources:</b> Betfair, Bet365, Stoiximan, OPAP</p>
          <p><b>Last Refresh:</b> {now}</p>
          <p class="meta">Cache TTL: 15s | Auto Refresh: 3min | Status: <b class="ok">Operational</b></p>
        </div>
        <footer>© EURO_GOALS Unified Engine | Live Node Ready</footer>
      </body>
    </html>
    """
    return HTMLResponse(content=html)

# ------------------------------------------------------------
# SMARTMONEY ENDPOINTS
# ------------------------------------------------------------
@app.get("/smartmoney/odds/{match_id}", response_class=JSONResponse)
async def odds_api(match_id: str):
    return get_odds_snapshot(match_id)

@app.get("/smartmoney/signals/{match_id}", response_class=JSONResponse)
async def signals_api(match_id: str):
    return get_smartmoney_signals(match_id)

# ------------------------------------------------------------
# GOALMATRIX ENDPOINTS
# ------------------------------------------------------------
@app.get("/goal_matrix/{match_id}", response_class=JSONResponse)
async def goal_matrix_api(match_id: str):
    return get_goal_matrix(match_id)

# ------------------------------------------------------------
# BACKGROUND REFRESHER
# ------------------------------------------------------------
async def periodic_refresher():
    while True:
        try:
            print("[EURO_GOALS] 🔄 Refresh cycle started")
            # εδώ μελλοντικά μπορείς να προσθέσεις fetch όλων των ενεργών αγώνων
            await asyncio.sleep(180)
        except Exception as e:
            print(f"[EURO_GOALS] ⚠️ Refresher error: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    print("[EURO_GOALS] 🚀 Starting Unified Engines...")
    asyncio.create_task(periodic_refresher())
    print("[EURO_GOALS] ✅ System initialized and live")

# ------------------------------------------------------------
# END OF FILE
# ============================================================
