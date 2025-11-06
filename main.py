# ============================================================
# EURO_GOALS v9.5.4 PRO+ — Main Application (Unified Engine)
# ============================================================
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from dotenv import load_dotenv
import os

# ------------------------------------------------------------
# Load environment variables
# ------------------------------------------------------------
load_dotenv()

GM_ENABLED = os.getenv("GM_ENABLED", "false").lower() == "true"
GM_REFRESH_SEC = int(os.getenv("GM_REFRESH_SEC", "20"))

# ------------------------------------------------------------
# App setup
# ------------------------------------------------------------
app = FastAPI(title="EURO_GOALS_UNIFIED v9.5.4 PRO+", version="9.5.4")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ------------------------------------------------------------
# Routers import
# ------------------------------------------------------------
from feeds.goal_matrix_feed import router as goalmatrix_router

# ------------------------------------------------------------
# Include routers
# ------------------------------------------------------------
app.include_router(goalmatrix_router)

# ------------------------------------------------------------
# Root route (Dashboard)
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    context = {
        "request": request,
        "GM_ENABLED": GM_ENABLED,
        "GM_REFRESH_SEC": GM_REFRESH_SEC,
    }
    return templates.TemplateResponse("index.html", context)

# ------------------------------------------------------------
# Healthcheck
# ------------------------------------------------------------
@app.get("/health", response_class=JSONResponse)
async def health_check():
    return {
        "status": "OK",
        "timestamp": datetime.utcnow().isoformat(),
        "goal_matrix_enabled": GM_ENABLED,
        "goal_matrix_refresh": GM_REFRESH_SEC,
    }

# ------------------------------------------------------------
# GoalMatrix calc endpoint (manual input from UI)
# ------------------------------------------------------------
import math
from pydantic import BaseModel

class GoalMatrixInput(BaseModel):
    home_avg: float
    away_avg: float
    over_line: float

def poisson_prob(lmbda, k):
    return (math.exp(-lmbda) * (lmbda**k)) / math.factorial(k)

@app.post("/api/goalmatrix/calc")
async def calc_goal_matrix(data: GoalMatrixInput):
    if not GM_ENABLED:
        return {"enabled": False}

    l_home = data.home_avg
    l_away = data.away_avg
    line = data.over_line

    # Over/Under probabilities
    p_under = 0.0
    for h in range(0, 10):
        for a in range(0, 10):
            if h + a <= line:
                p_under += poisson_prob(l_home, h) * poisson_prob(l_away, a)
    p_over = 1 - p_under

    # Top scores
    scores = []
    for h in range(0, 5):
        for a in range(0, 5):
            prob = poisson_prob(l_home, h) * poisson_prob(l_away, a)
            scores.append((f"{h}-{a}", prob))
    scores.sort(key=lambda x: x[1], reverse=True)
    top_scores = scores[:3]

    return {
        "enabled": True,
        "lambda_home": l_home,
        "lambda_away": l_away,
        "p_over": p_over,
        "p_under": p_under,
        "top_scores": top_scores,
    }

# ------------------------------------------------------------
# Run (only local)
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
