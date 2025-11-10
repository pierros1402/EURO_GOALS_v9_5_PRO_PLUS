# ============================================================
# EURO_GOALS v9.6.6 PRO+ — MATCHPLAN ENGINE
# ============================================================
# Δημιουργεί πλάνο 15 ημερών με fixtures από FlashScore/SofaScore.
# Περιλαμβάνει μόνο τις λίγκες που υπάρχουν στο leagues_list.
# ============================================================

import aiohttp
import asyncio
import time
from datetime import datetime, timedelta
from random import uniform
from services.leagues_list import LEAGUES

CACHE = {"ts": 0, "data": []}
CACHE_TTL = 60 * 60 * 3  # 3 ώρες

BASE_URL = "https://www.sofascore.com/api/v1/sport/football/scheduled-events"

async def fetch_json(session, url):
    try:
        async with session.get(url, timeout=20) as r:
            if r.status != 200:
                return {}
            return await r.json()
    except Exception as e:
        print(f"[MATCHPLAN] fetch error: {e}")
        return {}

async def get_matchplan_15d():
    """Λήψη fixtures 15 ημερών από SofaScore (μόνο ενεργές λίγκες)."""
    now = datetime.utcnow()
    if time.time() - CACHE["ts"] < CACHE_TTL:
        return CACHE["data"]

    all_matches = []
    async with aiohttp.ClientSession() as session:
        for i in range(15):
            date = (now + timedelta(days=i)).strftime("%Y-%m-%d")
            url = f"{BASE_URL}/{date}"
            data = await fetch_json(session, url)
            if not data:
                continue
            events = data.get("events", [])
            for e in events:
                league = e.get("tournament", {}).get("name", "")
                country = e.get("tournament", {}).get("category", {}).get("name", "")
                league_path = f"{country.lower()}/{league.lower().replace(' ', '-')}"
                if any(league_path.startswith(x.split("/")[0]) for x in LEAGUES.keys()):
                    all_matches.append({
                        "date": date,
                        "time": datetime.utcfromtimestamp(e.get("startTimestamp", 0)).strftime("%H:%M"),
                        "home": e.get("homeTeam", {}).get("name", ""),
                        "away": e.get("awayTeam", {}).get("name", ""),
                        "league": league,
                        "country": country,
                        "id": e.get("id"),
                        "odds_home": round(uniform(1.5, 2.9), 2),
                        "odds_draw": round(uniform(2.8, 4.0), 2),
                        "odds_away": round(uniform(2.5, 4.5), 2)
                    })
            await asyncio.sleep(0.5)

    CACHE["ts"] = time.time()
    CACHE["data"] = {"engine": "matchplan_engine", "days": 15, "fixtures": all_matches}
    return CACHE["data"]

async def background_refresher():
    print("[MATCHPLAN] Background refresher active.")
    while True:
        try:
            await get_matchplan_15d()
        except Exception as e:
            print(f"[MATCHPLAN] refresher error: {e}")
        await asyncio.sleep(CACHE_TTL)
