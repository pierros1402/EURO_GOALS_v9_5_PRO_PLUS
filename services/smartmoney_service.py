# ============================================================
# SMARTMONEY SERVICE – Connector to external SmartMoney Engine
# ============================================================
import httpx, os, asyncio

SMARTMONEY_ENGINE_URL = os.getenv("SMARTMONEY_ENGINE_URL", "https://smartmoney-engine-v1-0-0.onrender.com")

async def fetch_smartmoney_summary():
    """Λήψη συνοπτικών στοιχείων SmartMoney"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(f"{SMARTMONEY_ENGINE_URL}/api/smartmoney/summary")
            if res.status_code == 200:
                return res.json()
    except Exception as e:
        print(f"[SMARTMONEY] ⚠️ {e}")
    return None

async def fetch_smartmoney_alerts():
    """Λήψη ενεργών alerts"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(f"{SMARTMONEY_ENGINE_URL}/api/smartmoney/alerts")
            if res.status_code == 200:
                return res.json()
    except Exception as e:
        print(f"[SMARTMONEY] ⚠️ {e}")
    return []
