import asyncio
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.templating import Jinja2Templates

from app.core.settings import settings
from app.routers.smartmoney import router as smartmoney_router
from app.routers.goalmatrix import router as goalmatrix_router
from app.services.smartmoney_engine import background_refresher as smartmoney_refresher
from app.services.goalmatrix_engine import background_refresher as goalmatrix_refresher

app = FastAPI(title=settings.APP_NAME)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(smartmoney_router)
app.include_router(goalmatrix_router)

@app.get("/health")
async def health():
    return {"ok": True, "app": settings.APP_NAME}

@app.get("/", response_class=HTMLResponse)
async def unified_dashboard(request: Request):
    return templates.TemplateResponse("unified_dashboard.html", {"request": request})

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(smartmoney_refresher())
    asyncio.create_task(goalmatrix_refresher())
