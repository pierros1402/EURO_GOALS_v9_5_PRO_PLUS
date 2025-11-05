# app/routers/smartmoney.py
from fastapi import APIRouter
from app.services.smartmoney_engine import cache, refresh_smartmoney_once

router = APIRouter(prefix="/api/smartmoney", tags=["smartmoney"])

@router.get("/summary")
async def get_summary():
    if not cache.is_fresh:
        await refresh_smartmoney_once()
    return cache.get_summary()

@router.get("/alerts")
async def get_alerts():
    if not cache.is_fresh:
        await refresh_smartmoney_once()
    return {"items": cache.get_alerts()}

@router.get("/providers/health")
async def providers_health():
    if not cache.is_fresh:
        await refresh_smartmoney_once()
    s = cache.get_summary()
    return s.get("provider_health", {"odds": False, "depth": False})
