# ============================================================
# EURO_GOALS v9.6.6 PRO+ — STANDINGS ENGINE
# ============================================================
# Συνδυάζει SportMonks + TheSportsDB (fallback)
# ============================================================

import aiohttp
import asyncio
import os
import time
from services.leagues_list import LEAGUES

CACHE = {"ts": 0, "data": []}
CACHE_TTL = 60 * 60 * 6  # 6 ώρες

SPORTMONKS_API_KEY = os.getenv("SPORTMONKS_API_KEY", "")
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY", "")

async def fetch_json(session, url):
    try:
        async with session.get(url, timeout=25) as r:
            if r.status != 200:
                return {}
            return await r.json()
    except Exception as e:
        print(f"[STANDINGS] fetch error: {e}")
        return {}

async def get_from_sportmonks():
    """Πλήρη standings από SportMonks"""
    results = []
    base_url = f"https://api.sportmonks.com/v3/football/standings?api_token={SPORTMONKS_API_KEY}"
    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, base_url)
        for item in data.get("data", []):
            league_name = item.get("name", "Unknown")
            table = item.get("standings", [])
            for team in table:
                results.append({
                    "league": league_name,
                    "team": team.get("team", {}).get("name", ""),
                    "position": team.get("position"),
                    "points": team.get("overall", {}).get("points"),
                    "played": team.get("overall", {}).get("games_played"),
                    "won": team.get("overall", {}).get("won"),
                    "drawn": team.get("overall", {}).get("drawn"),
                    "lost": team.get("overall", {}).get("lost"),
                    "goals_for": team.get("overall", {}).get("goals_scored"),
                    "goals_against": team.get("overall", {}).get("goals_against"),
                    "goal_diff": team.get("overall", {}).get("goal_difference"),
                    "form": team.get("recent_form", "")
                })
        return results

async def get_from_thesportsdb():
    """Fallback standings από TheSportsDB"""
    results = []
    async with aiohttp.ClientSession() as session:
        for league in LEAGUES.values():
            url = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_API_KEY}/lookuptable.php?l={league.replace(' ', '%20')}&s=2024-2025"
            data = await fetch_json(session, url)
            table = data.get("table", [])
            for t in table:
                results.append({
                    "league": league,
                    "team": t.get("strTeam", ""),
                    "position": t.get("intRank"),
                    "played": t.get("intPlayed"),
                    "points": t.get("intPoints"),
                    "won": t.get("intWin"),
                    "drawn": t.get("intDraw"),
                    "lost": t.get("intLoss")
                })
            await asyncio.sleep(0.5)
    return results

async def get_standings():
    """Unified standings με προτεραιότητα SportMonks"""
    if time.time() - CACHE["ts"] < CACHE_TTL:
        return CACHE["data"]

    data = []
    if SPORTMONKS_API_KEY:
        try:
            data = await get_from_sportmonks()
        except Exception as e:
            print(f"[STANDINGS] SportMonks error: {e}")

    if not data and THESPORTSDB_API_KEY:
        print("[STANDINGS] Falling back to TheSportsDB...")
        data = await get_from_thesportsdb()

    CACHE["ts"] = time.time()
    CACHE["data"] = {"engine": "standings_engine", "count": len(data), "standings": data}
    return CACHE["data"]

async def background_refresher():
    print("[STANDINGS] Background refresher active.")
    while True:
        try:
            await get_standings()
        except Exception as e:
            print(f"[STANDINGS] refresher error: {e}")
        await asyncio.sleep(CACHE_TTL)
