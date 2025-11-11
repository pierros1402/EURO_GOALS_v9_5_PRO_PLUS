# ============================================================
# EURO_GOALS v9.7.2 PRO+ — UNIFIED MAIN (Refreshed Overlay Edition)
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os, sys, time

print("=== [EURO_GOALS] Unified App v9.7.2 PRO+ — Overlay Refreshed ===")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# ------------------------------------------------------------
# Try importing GoalMatrix + SmartMoney engines
# ------------------------------------------------------------
try:
    from services.goal_matrix_engine import get_goal_matrix, get_goalmatrix_insights
    from services.smartmoney_engine import get_odds_snapshot, get_smartmoney_signals
except Exception as e:
    print("[WARN] Overlay engines missing, using demo stubs:", e)

    def get_heatmap_for_match(match_id: str):
        n = 10
        cells = [[0.05 for _ in range(n)] for _ in range(n)]
        cells[4][6] = 0.85
        cells[5][5] = 0.72
        return {"match_id": match_id, "cells": cells}

    def get_goalmatrix_insights(match_id: str):
        return {"xg_home": 1.38, "xg_away": 1.12, "likely_goals": "2-3"}

    def get_odds_snapshot(match_id: str):
        return {"1": 2.15, "X": 3.25, "2": 3.30, "+2.5": 1.93, "-2.5": 1.88}

    def get_smartmoney_signals(match_id: str):
        return [
            {"type": "steam_move", "market": "+2.5", "dir": "down", "delta": -0.05},
            {"type": "sharp_action", "market": "1X", "dir": "up", "delta": +0.04},
        ]

# ------------------------------------------------------------
# FastAPI app setup
# ------------------------------------------------------------
app = FastAPI(title="EURO_GOALS PRO+ v9.7.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ------------------------------------------------------------
# Overlay in-memory state
# ------------------------------------------------------------
overlay_state = {
    "enabled": True,
    "opacity": 0.94,
    "compact": True,
    "hotkey": "KeyO"
}

# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "overlay": overlay_state})

@app.get("/overlay/state")
async def overlay_get_state():
    return overlay_state

@app.post("/overlay/toggle")
async def overlay_toggle():
    overlay_state["enabled"] = not overlay_state["enabled"]
    return overlay_state

@app.get("/overlay/match/{match_id}")
async def overlay_match_payload(match_id: str):
    try:
        heatmap = get_heatmap_for_match(match_id)
        insights = get_goalmatrix_insights(match_id)
        odds = get_odds_snapshot(match_id)
        signals = get_smartmoney_signals(match_id)
        return {
            "match_id": match_id,
            "goal_matrix": {"heatmap": heatmap, "insights": insights},
            "smartmoney": {"odds": odds, "signals": signals}
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/health")
async def health():
    return {"ok": True, "version": "9.7.2", "ts": int(time.time())}

@app.on_event("startup")
async def startup_event():
    print("[EURO_GOALS] 🚀 Startup complete (Overlay Refreshed)")

# ============================================================
# EURO_GOALS UNIFIED MAIN APP – v9.7.4 REAL DATA CHAIN
# ============================================================
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from services import smartmoney_engine, goal_matrix_engine

app = FastAPI(title="EURO_GOALS PRO+", version="9.7.4")

# ------------------------------------------------------------
# SMARTMONEY ENDPOINTS
# ------------------------------------------------------------
@app.get("/smartmoney/signals/{match_id}")
async def get_smartmoney_signals(match_id: str):
    data = smartmoney_engine.get_smartmoney_signals(match_id)
    return JSONResponse(content=data)

@app.get("/smartmoney/odds/{match_id}")
async def get_smartmoney_odds(match_id: str):
    data = smartmoney_engine.get_odds_snapshot(match_id)
    return JSONResponse(content=data)

# ------------------------------------------------------------
# GOAL_MATRIX ENDPOINT
# ------------------------------------------------------------
@app.get("/goal_matrix/{match_id}")
async def get_goal_matrix(match_id: str):
    data = goal_matrix_engine.get_goal_matrix(match_id)
    return JSONResponse(content=data)


