from fastapi import APIRouter
import httpx, os

router = APIRouter(prefix="/api/smartmoney", tags=["SmartMoney"])

SMARTMONEY_ENGINE_URL = os.getenv("SMARTMONEY_ENGINE_URL", "https://smartmoney-engine-v1-0-0.onrender.com")

@router.get("/alerts")
async def get_smartmoney_alerts():
    """Fetch live SmartMoney alerts from external engine"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{SMARTMONEY_ENGINE_URL}/api/smartmoney/alerts")
            if response.status_code == 200:
                return response.json()
            else:
                return {"alerts": [], "status": response.status_code, "error": "Non-200 from engine"}
    except Exception as e:
        return {"alerts": [], "error": str(e)}
