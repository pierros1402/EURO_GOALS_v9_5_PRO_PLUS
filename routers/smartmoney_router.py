from fastapi import APIRouter
import httpx, os

router = APIRouter(prefix="/api/smartmoney", tags=["SmartMoney"])

SMARTMONEY_ENGINE_URL = os.getenv("SMARTMONEY_ENGINE_URL", "https://smartmoney-engine-v1-0-0.onrender.com")

@router.get("/alerts")
async def get_smartmoney_alerts():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{SMARTMONEY_ENGINE_URL}/api/smartmoney/alerts")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "Engine responded with non-200", "status": response.status_code}
    except Exception as e:
        return {"error": str(e)}
