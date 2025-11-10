# ============================================================
# EURO_GOALS v9.6.6 PRO+ — HISTORY ENGINE (FlashScore + SofaScore)
# ============================================================

import aiohttp
import asyncio
import time
import json
from bs4 import BeautifulSoup
from services.leagues_list import LEAGUES

CACHE = {"flashscore": {"ts": 0, "data": []}, "sofascore": {"ts": 0, "data": []}}
CACHE_TTL = 60 * 60 * 6  # 6 ώρες
YEARS_BACK = 10

async def fetch_html(session, url):
    try:
        async with session.get(url, timeout=20) as r:
            return await r.text()
    except:
        return ""

async def fetch_json(session, url):
    try:
        async with session.get(url, timeout=20) as r:
            return await r.text()
    except:
        return "{}"

def parse_flashscore(html):
    soup = BeautifulSoup(html, "html.parser")
    matches = []
    for row in soup.select(".event__match"):
        home = row.select_one(".event__participant--home")
        away = row.select_one(".event__participant--away")
        score_home = row.select_one(".event__score--home")
        score_away = row.select_one(".event__score--away")
        date = row.get("data-date", "")
        league = row.get("data-league", "")
        if home and away and score_home and score_away:
            matches.append({
                "league": league or "Unknown",
                "date": date,
                "home_team": home.text.strip(),
                "away_team": away.text.strip(),
                "score": f"{score_home.text.strip()} - {score_away.text.strip()}",
                "source": "flashscore"
            })
    return matches

def parse_sofascore(json_text):
    try:
        data = json.loads(json_text)
    except:
        return []
    results = []
    for e in data.get("events", []):
        results.append({
            "league": e.get("tournament", {}).get("name", ""),
            "date": e.get("startTimestamp", ""),
            "home_team": e.get("homeTeam", {}).get("name", ""),
            "away_team": e.get("awayTeam", {}).get("name", ""),
            "score": f"{e.get('homeScore', {}).get('current', '-')} - {e.get('awayScore', {}).get('current', '-')}",
            "source": "sofascore"
        })
    return results

async def get_flashscore_history():
    if time.time() - CACHE["flashscore"]["ts"] < CACHE_TTL:
        return CACHE["flashscore"]["data"]

    base_url = "https://www.flashscore.com/football/"
    all_data = []
    async with aiohttp.ClientSession() as session:
        for path in LEAGUES.keys():
            for year_offset in range(YEARS_BACK):
                season_year = 2025 - year_offset
                url = f"{base_url}{path}-{season_year}-{season_year+1}/results/"
                html = await fetch_html(session, url)
                all_data.extend(parse_flashscore(html))
                await asyncio.sleep(0.4)
    CACHE["flashscore"] = {"ts": time.time(), "data": all_data}
    return all_data

async def get_sofascore_history():
    if time.time() - CACHE["sofascore"]["ts"] < CACHE_TTL:
        return CACHE["sofascore"]["data"]

    urls = [
        "https://www.sofascore.com/api/v1/unique-tournament/17/season/52036/events",
        "https://www.sofascore.com/api/v1/unique-tournament/8/season/52030/events"
    ]
    results = []
    async with aiohttp.ClientSession() as session:
        for url in urls:
            txt = await fetch_json(session, url)
            results.extend(parse_sofascore(txt))
            await asyncio.sleep(0.4)
    CACHE["sofascore"] = {"ts": time.time(), "data": results}
    return results

async def get_history(source="flashscore"):
    flash_data, sofa_data = [], []
    if source == "flashscore":
        flash_data = await get_flashscore_history()
        data = flash_data
    elif source == "sofascore":
        sofa_data = await get_sofascore_history()
        data = sofa_data
    else:
        flash_data = await get_flashscore_history()
        sofa_data = await get_sofascore_history()
        data = flash_data + sofa_data
    data.sort(key=lambda x: x.get("date", ""), reverse=True)
    data = data[:2000]
    return {"engine": "history_engine", "source": source, "history": data}

async def background_refresher():
    print("[HISTORY] Background refresher active.")
    while True:
        try:
            await get_flashscore_history()
            await get_sofascore_history()
        except Exception as e:
            print(f"[HISTORY] refresher error: {e}")
        await asyncio.sleep(CACHE_TTL)
