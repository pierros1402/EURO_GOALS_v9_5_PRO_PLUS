# ============================================================
# SmartMoney API Router – συνδέεται με smartmoney_engine
# ============================================================
from fastapi import APIRouter
from . import smartmoney_engine

router = APIRouter()

@router.get("/summary")
async def smartmoney_summary():
    """Επιστρέφει σύνοψη SmartMoney"""
    if smartmoney_engine.cache.is_fresh:
        return smartmoney_engine.cache.get_summary()
    await smartmoney_engine.refresh_smartmoney_once()
    return smartmoney_engine.cache.get_summary()

@router.get("/alerts")
async def smartmoney_alerts():
    """Επιστρέφει λίστα SmartMoney alerts"""
    if not smartmoney_engine.cache.is_fresh:
        await smartmoney_engine.refresh_smartmoney_once()
    return {"alerts": smartmoney_engine.cache.get_alerts()}
