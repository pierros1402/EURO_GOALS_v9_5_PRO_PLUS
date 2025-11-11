# ============================================================
# SMARTMONEY SERVICE (optional external engine caller)
# ============================================================
import os
import aiohttp

SMARTMONEY_ENGINE_URL = os.getenv("SMARTMONEY_ENGINE_URL", "").rstrip("/")

async def _fetch_json(url: str):
    if not url:
        return {}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20) as r:
                if r.status != 200:
                    return {}
                return await r.json()
    except Exception:
        return {}

async def fetch_smartmoney_summary():
    return await _fetch_json(f"{SMARTMONEY_ENGINE_URL}/api/smartmoney/summary") if SMARTMONEY_ENGINE_URL else {}

async def fetch_smartmoney_alerts():
    return await _fetch_json(f"{SMARTMONEY_ENGINE_URL}/api/smartmoney/alerts") if SMARTMONEY_ENGINE_URL else {}
