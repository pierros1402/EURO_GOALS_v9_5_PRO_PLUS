# ============================================================
# EURO_GOALS v9.5.4 PRO+ – Unified Core + Engines + Monitor
# ============================================================
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, requests
from dotenv import load_dotenv

# ------------------------------------------------------------
# Imports from modules
# ------------------------------------------------------------
from src.smartmoney_engine import fetch_smartmoney_data, update_local_smartmoney
from src.goalmatrix_engine import fetch_goalmatrix_data, calculate_goal_probabilities
from src.monitor_engine import get_full_system_status
# =====================================================
# SMARTMONEY FEED ENDPOINT (The Odds API Integration)
# =====================================================
import os, requests
from fastapi import FastAPI
from fastapi.responses import JSONResponse

@app.get("/api/smartmoney_feed")
async def get_smartmoney_feed():
    api_key = os.getenv("SMARTMONEY_REALFEED_API_KEY")
    url = "https://api.the-odds-api.com/v4/sports/upcoming/odds"
    params = {"regions": "eu", "markets": "h2h", "apiKey": api_key}

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return JSONResponse(
                {"error": f"API responded {response.status_code}"}, status_code=500
            )

        raw = response.json()
        matches = []
        for item in raw[:15]:  # Limit results for performance
            if not item.get("bookmakers"): 
                continue
            first_bm = item["bookmakers"][0]
            first_market = first_bm["markets"][0] if first_bm["markets"] else {}
            outcomes = first_market.get("outcomes", [])
            home_price = outcomes[0]["price"] if len(outcomes) > 0 else "-"
            away_price = outcomes[1]["price"] if len(outcomes) > 1 else "-"

            matches.append({
                "league": item.get("sport_title", ""),
                "home_team": item.get("home_team", ""),
                "away_team": item.get("away_team", ""),
                "bookmaker": first_bm.get("title", ""),
                "market": first_market.get("key", ""),
                "home_price": home_price,
                "away_price": away_price,
                "last_update": first_bm.get("last_update", "")
            })

        return {"matches": matches}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ------------------------------------------------------------
# Load Environment
# ------------------------------------------------------------
load_dotenv()
RENDER_HEALTH_URL = os.getenv("RENDER_HEALTH_URL", "https://eurogoals-nextgen.onrender.com/health")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

# ------------------------------------------------------------
# Initialize App
# ------------------------------------------------------------
app = FastAPI(title="EURO_GOALS v9.5.4 PRO+", version="9.5.4")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ------------------------------------------------------------
# ROOT
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ------------------------------------------------------------
# MONITOR / HEALTH
# ------------------------------------------------------------
@app.get("/api/system/health", response_class=JSONResponse)
async def api_system_health():
    data = get_full_system_status()
    return data

# ------------------------------------------------------------
# SMARTMONEY ROUTES
# ------------------------------------------------------------
@app.get("/api/smartmoney/status", response_class=JSONResponse)
async def api_smartmoney_status():
    return fetch_smartmoney_data()

@app.post("/api/smartmoney/update", response_class=JSONResponse)
async def api_smartmoney_update():
    return update_local_smartmoney()

# ------------------------------------------------------------
# GOALMATRIX ROUTES
# ------------------------------------------------------------
@app.get("/api/goalmatrix/status", response_class=JSONResponse)
async def api_goalmatrix_status():
    return fetch_goalmatrix_data()

@app.get("/api/goalmatrix/probabilities", response_class=JSONResponse)
async def api_goalmatrix_probabilities():
    raw_data = fetch_goalmatrix_data()
    if raw_data.get("error"):
        return raw_data
    return calculate_goal_probabilities(raw_data)

# ------------------------------------------------------------
# STARTUP EVENT
# ------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    print("🚀 EURO_GOALS v9.5.4 PRO+ launched successfully")
    print("🩺 Starting Health Monitor v3...")
    status = get_full_system_status()
    print(status)
