# ============================================================
# AI MATCHLAB — MAIN BACKEND (FastAPI)
# Unified UI Loader + Status Routes
# ============================================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import datetime as dt

# ------------------------------------------------------------
# APP INIT
# ------------------------------------------------------------
app = FastAPI(title="AI MATCHLAB Backend")

# ------------------------------------------------------------
# STATIC & TEMPLATES
# ------------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ============================================================
# SYSTEM ROUTES
# ============================================================

@app.get("/status", response_class=JSONResponse)
async def status():
    return {
        "ok": True,
        "service": "AI MATCHLAB FastAPI Backend",
        "version": "v3",
        "timestamp": dt.datetime.utcnow().isoformat() + "Z",
    }


@app.get("/api/health", response_class=JSONResponse)
async def health():
    return {"status": "healthy", "timestamp": dt.datetime.utcnow().isoformat()}


# ============================================================
# PRETTY ROUTES → φορτώνουν το index.html με συγκεκριμένο tab
# ============================================================

@app.get("/live", response_class=HTMLResponse)
async def live_tab(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "default_view": "live"})

@app.get("/scores", response_class=HTMLResponse)
async def scores_tab(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "default_view": "scores"})

@app.get("/standings", response_class=HTMLResponse)
async def standings_tab(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "default_view": "standings"})

@app.get("/leagues", response_class=HTMLResponse)
async def leagues_tab(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "default_view": "leagues"})

@app.get("/teams", response_class=HTMLResponse)
async def teams_tab(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "default_view": "teams"})

@app.get("/ai", response_class=HTMLResponse)
async def ai_tab(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "default_view": "ai"})

@app.get("/goalmatrix", response_class=HTMLResponse)
async def goalmatrix_tab(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "default_view": "goalmatrix"})

@app.get("/smartmoney", response_class=HTMLResponse)
async def smartmoney_tab(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "default_view": "smartmoney"})

@app.get("/about", response_class=HTMLResponse)
async def about_tab(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "default_view": "about"})

# ============================================================
# OPTIONAL API ROUTES (placeholders for future AI modules)
# ============================================================

@app.get("/api/ping")
async def ping():
    return {"ok": True, "pong": True}


@app.get("/api/time")
async def time_now():
    return {"utc": dt.datetime.utcnow().isoformat() + "Z"}


# ============================================================
# LOCAL DEV RUNNER
# ============================================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
