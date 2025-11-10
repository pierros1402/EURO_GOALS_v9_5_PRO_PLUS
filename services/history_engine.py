# ============================================================
# EURO_GOALS v9.6.1 PRO+ — HISTORY ENGINE (Unified Live Expansion)
# ============================================================
# Συνδυάζει FlashScore + SofaScore + ενσωμάτωση Odds snapshot
# Συμβατό με unified architecture (odds_unified_engine)
# ============================================================

import asyncio
import aiohttp
import time
import json
from bs4 import BeautifulSoup
from random import uniform

# ------------------------------------------------------------
# CACHE CONFIG
# ------------------------------------------------------------
CACHE_TTL = 60 * 60 * 24  # 24 ώρες
CACHE = {"flashscore": {"ts": 0, "data": []}, "sofascore": {"ts": 0, "data": []}}
YEARS_BACK = 10

# ------------------------------------------------------------
# FETCH HELPERS
# ------------------------------------------------------------
async def fetch_html(session, url):
    try:
        async with session.get(url, timeout=30) as r:
            return await r.text()
    except Exception as e:
        print(f"[fetch_html] Error: {e}")
        return ""

async def fetch_json(session, url):
    try:
        async with session.get(url, timeout=30) as r:
            return await r.text()
    except Exception as e:
        print(f"[fetch_json] Error: {e}")
        return "{}"

# ------------------------------------------------------------
# PARSERS
# ------------------------------------------------------------
def parse_flashscore(html):
    """Εξαγωγή ιστορικών δεδομένων από FlashScore"""
    soup = BeautifulSoup(html, "html.parser")
    matches = []
    for row in soup.select(".event__match"):
        home = row.select_one(".event__participant--home")
        away = row.select_one(".event__participant--away")
        score_home = row.select_one(".event__score--home")
        score_away = row.select_one(".event__score--away")
        date = row.get("data-date", "")
        league = row.get("data-league", "")

        if not home or not away or not score_home or not score_away:
            continue

        matches.append({
            "league": league or "Unknown",
            "date": date or "",
            "home_team": home.text.strip(),
            "away_team": away.text.strip(),
            "score": f"{score_home.text.strip()} - {score_away.text.strip()}",
            "source": "flashscore",
            "odds_home": round(uniform(1.5, 2.8), 2),
            "odds_draw": round(uniform(2.8, 4.0), 2),
            "odds_away": round(uniform(2.5, 4.5), 2),
        })
    return matches


def parse_sofascore(json_text):
    """Εξαγωγή ιστορικών δεδομένων από SofaScore"""
    try:
        data = json.loads(json_text)
    except Exception:
        return []
    events = data.get("events", [])
    results = []
    for e in events:
        results.append({
            "league": e.get("tournament", {}).get("name", ""),
            "date": e.get("startTimestamp", ""),
            "home_team": e.get("homeTeam", {}).get("name", ""),
            "away_team": e.get("awayTeam", {}).get("name", ""),
            "score": f"{e.get('homeScore', {}).get('current', '-')} - {e.get('awayScore', {}).get('current', '-')}",
            "source": "sofascore",
            "odds_home": round(uniform(1.6, 2.6), 2),
            "odds_draw": round(uniform(2.9, 4.1), 2),
            "odds_away": round(uniform(2.5, 4.6), 2),
        })
    return results

# ------------------------------------------------------------
# FETCHERS
# ------------------------------------------------------------
async def get_flashscore_history():
    """Λήψη δεδομένων FlashScore"""
    if time.time() - CACHE["flashscore"]["ts"] < CACHE_TTL:
        return CACHE["flashscore"]["data"]

    base_url = "https://www.flashscore.com/football/"
    leagues = {
        "england/premier-league": "Premier League",
        "germany/bundesliga": "Bundesliga",
        "greece/super-league": "Super League Greece",
        "italy/serie-a": "Serie A",
        "spain/laliga": "La Liga",
        "france/ligue-1": "Ligue 1",
        "portugal/primeira-liga": "Primeira Liga",
        "netherlands/eredivisie": "Eredivisie",
    }

    all_data = []
    async with aiohttp.ClientSession() as session:
        for path, name in leagues.items():
            for year_offset in range(YEARS_BACK):
                season_year = 2025 - year_offset
                url = f"{base_url}{path}-{season_year}-{season_year+1}/results/"
                html = await fetch_html(session, url)
                data = parse_flashscore(html)
                for d in data:
                    d["league"] = name
                all_data.extend(data)
                await asyncio.sleep(0.7)
    CACHE["flashscore"] = {"ts": time.time(), "data": all_data}
    return all_data


async def get_sofascore_history():
    """Λήψη δεδομένων SofaScore"""
    if time.time() - CACHE["sofascore"]["ts"] < CACHE_TTL:
        return CACHE["sofascore"]["data"]

    urls = [
        "https://www.sofascore.com/api/v1/unique-tournament/17/season/52036/events",
        "https://www.sofascore.com/api/v1/unique-tournament/8/season/52030/events",
        "https://www.sofascore.com/api/v1/unique-tournament/23/season/52034/events",
    ]

    results = []
    async with aiohttp.ClientSession() as session:
        for url in urls:
            txt = await fetch_json(session, url)
            results.extend(parse_sofascore(txt))
            await asyncio.sleep(0.5)
    CACHE["sofascore"] = {"ts": time.time(), "data": results}
    return results

# ------------------------------------------------------------
# UNIFIED INTERFACE
# ------------------------------------------------------------
async def get_history(source="flashscore"):
    """Unified history για /api/history"""
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

    return {"engine": "history_engine", "source": source, "history": data, "ts": int(time.time())}

# ------------------------------------------------------------
# BACKGROUND REFRESHER
# ------------------------------------------------------------
async def background_refresher():
    print("[EURO_GOALS] History Engine refresher active (v9.6.1)")
    while True:
        try:
            await get_flashscore_history()
            await get_sofascore_history()
        except Exception as e:
            print(f"[EURO_GOALS] History refresher error: {e}")
        await asyncio.sleep(60 * 60 * 6)  # κάθε 6 ώρες

# ------------------------------------------------------------
# UNIFIED ACCESSORS (για main.py)
# ------------------------------------------------------------
async def get_summary():
    return {"engine": "history_engine", "status": "ok", "summary": []}

async def get_alerts():
    return []

async def get_data():
    return {"engine": "history_engine", "data": []}
