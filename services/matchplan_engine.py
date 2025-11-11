# ============================================================
# EURO_GOALS PRO+ — MATCHPLAN ENGINE (v9.6.9 Stable)
# ============================================================

import os, aiohttp, asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from services.leagues_list import LEAGUES

load_dotenv()
IS_DEV = os.getenv("IS_DEV", "false").lower() == "true"
SPORTMONKS_API_KEY = os.getenv("SPORTMONKS_API_KEY", "").strip()

async def fetch_json(session, url):
    try:
        async with session.get(url, timeout=20, ssl=not IS_DEV) as r:
            if r.status != 200:
                print(f"[MATCHPLAN] Bad response {r.status}: {url}")
                return {}
            return await r.json()
    except Exception as e:
        print(f"[MATCHPLAN] fetch error: {e}")
        return {}

async def get_from_sportmonks():
    results = []
    if not SPORTMONKS_API_KEY:
        return results

    today = datetime.utcnow().date()
    until = today + timedelta(days=7)
    url = (
        f"https://api.sportmonks.com/v3/football/fixtures/between/{today}/{until}"
        f"?api_token={SPORTMONKS_API_KEY}&include=participants;league;season"
    )
    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, url)
        items = data.get("data", [])
        for e in items:
            try:
                participants = e.get("participants", [])
                home = next((p.get("name") for p in participants if p.get("meta", {}).get("location")=="home"), None)
                away = next((p.get("name") for p in participants if p.get("meta", {}).get("location")=="away"), None)
                league_name = (e.get("league") or {}).get("name")
                start = e.get("starting_at") or {}
                date = (start.get("date") or "").split("T")[0] or e.get("date")
                results.append({
                    "league": league_name,
                    "home": home,
                    "away": away,
                    "date": date,
                    "status": e.get("status"),
                })
            except Exception:
                continue
    return results

async def get_matchplan_summary():
    data = await get_from_sportmonks()
    return {"timestamp": datetime.utcnow().isoformat(), "matches": data}

async def background_refresher():
    while True:
        try:
            await get_matchplan_summary()
            print("[MATCHPLAN] Background refresher active.")
        except Exception as e:
            print(f"[MATCHPLAN] refresher error: {e}")
        await asyncio.sleep(1800)
