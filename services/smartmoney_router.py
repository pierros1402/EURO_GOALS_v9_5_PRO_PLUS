# ============================================================
# SmartMoney API Router v2.0
# ============================================================
from fastapi import APIRouter, Query
from . import smartmoney_engine

router = APIRouter()

@router.get("/summary")
async def summary():
    return await smartmoney_engine.get_summary()

@router.get("/alerts")
async def alerts():
    return {"alerts": await smartmoney_engine.get_alerts()}

@router.get("/markets")
async def markets(league: str = Query("", description="optional league filter")):
    return {"markets": await smartmoney_engine.get_markets_api(league)}

@router.get("/odds")
async def odds(market: str = Query(..., description="Betfair market id")):
    return await smartmoney_engine.get_odds_api(market)

@router.get("/trends")
async def trends(league: str = Query("", description="optional league for trends")):
    return await smartmoney_engine.get_trends_api(league)
