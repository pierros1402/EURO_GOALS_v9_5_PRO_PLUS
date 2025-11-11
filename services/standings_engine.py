# ============================================================
# EURO_GOALS PRO+ — STANDINGS ENGINE (v9.6.9, robust fix)
# ============================================================

import os
import asyncio
import aiohttp
from datetime import datetime
from urllib.parse import quote
from dotenv import load_dotenv
from services.leagues_list import LEAGUES

load_dotenv()

IS_DEV = os.getenv("IS_DEV", "false").lower() == "true"
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY", "").strip() or "1"
THESPORTSDB_BASE = os.getenv("THESPORTSDB_BASE", "https://www.thesportsdb.com/api/v1/json").rstrip("/")

def slug_to_name(slug: str) -> str:
    if not slug:
        return ""
    part = slug.split("/")[-1]
    name = part.replace("-", " ").title()
    return name

async def _fetch_json(session: aiohttp.ClientSession, url: str):
    try:
        async with session.get(url, timeout=20, ssl=not IS_DEV) as r:
            if r.status != 200:
                print(f"[STANDINGS] Non-200 ({r.status}) για {url}")
                return {}
            return await r.json()
    except Exception as e:
        print(f"[STANDINGS] fetch error: {e}  url={url}")
        return {}

async def _get_from_thesportsdb(session: aiohttp.ClientSession, league_name: str, season: str = "2024-2025"):
    safe_name = quote(league_name)
    urls = [
        f"{THESPORTSDB_BASE}/{THESPORTSDB_API_KEY}/lookuptable.php?l={safe_name}&s={quote(season)}",
        f"{THESPORTSDB_BASE}/{THESPORTSDB_API_KEY}/lookuptable.php?l={safe_name}&s=2023-2024",
    ]
    for u in urls:
        data = await _fetch_json(session, u)
        table = data.get("table") or data.get("Table") or []
        if table:
            return {"source": "thesportsdb", "data": table}
    return {}

async def get_standings():
    results = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for slug, meta in LEAGUES.items():
            league_name = (
                (meta.get("name") if isinstance(meta, dict) else None)
                or (meta.get("display_name") if isinstance(meta, dict) else None)
                or slug_to_name(slug)
            )

            async def load_one(sl=slug, lm=league_name):
                tsdb_data = await _get_from_thesportsdb(session, lm)
                return {"slug": sl, "league": lm, "standings": tsdb_data, "source": tsdb_data.get("source") or "thesportsdb"}

            tasks.append(load_one())

        items = await asyncio.gather(*tasks, return_exceptions=True)

    unified = []
    for it in items:
        if isinstance(it, Exception):
            print(f"[STANDINGS] task error: {it}")
            continue

        league = it.get("league")
        data = it.get("standings") or {}
        source = it.get("source")
        simplified = {
            "league": league,
            "source": source,
            "updated": datetime.utcnow().isoformat(),
            "raw": data.get("data") or data.get("table") or data,
        }
        unified.append(simplified)

    return {"timestamp": datetime.utcnow().isoformat(), "count": len(unified), "standings": unified}

async def background_refresher():
    while True:
        try:
            await get_standings()
            print("[STANDINGS] Background refresher active.")
        except Exception as e:
            print(f"[STANDINGS] refresher error: {e}")
        await asyncio.sleep(1800)
