# ============================================================
# EURO_GOALS PRO+ — HISTORY ENGINE (v9.6.9 Unified Edition)
# ============================================================
# Συνδέεται με Cloudflare Worker v2.1:
#  - /thesportsdb/history?league=<slug>
#  - /flashscore/history?url=...
# ============================================================

import os, asyncio, aiohttp
from datetime import datetime
from dotenv import load_dotenv
from services.leagues_list import LEAGUES

load_dotenv()

WORKER_BASE_RAW = os.getenv("LIVE_PROXY_URL", "").rstrip("/")
WORKER_BASE = WORKER_BASE_RAW[:-5] if WORKER_BASE_RAW.endswith("/live") else WORKER_BASE_RAW
IS_DEV = os.getenv("IS_DEV", "false").lower() == "true"

async def _fetch_json(session, url):
    try:
        async with session.get(url, timeout=20, ssl=not IS_DEV) as r:
            if r.status != 200:
                print(f"[HISTORY] Non-200 ({r.status}) για {url}")
                return {}
            return await r.json()
    except Exception as e:
        print(f"[HISTORY] Error στο fetch για {url}: {e}")
        return {}

async def get_history():
    if not WORKER_BASE:
        return {"timestamp": datetime.utcnow().isoformat(), "history": [], "note": "LIVE_PROXY_URL missing"}

    history = []
    async with aiohttp.ClientSession() as session:
        jobs = []
        for slug, meta in LEAGUES.items():
            url = f"{WORKER_BASE}/thesportsdb/history?league={slug}"
            jobs.append(_fetch_json(session, url))

        flashscore_url = os.getenv("FLASHCORE_URL", "").strip()
        if flashscore_url:
            jobs.append(_fetch_json(session, f"{WORKER_BASE}/flashscore/history?url={flashscore_url}"))

        results = await asyncio.gather(*jobs, return_exceptions=False)

        for res in results:
            if not res or not isinstance(res, dict): 
                continue
            league = res.get("league")
            for m in res.get("matches", []):
                history.append({
                    "league": league or m.get("league"),
                    "date": m.get("date"),
                    "home": m.get("home"),
                    "away": m.get("away"),
                    "score": m.get("score"),
                    "id": m.get("id"),
                })

    history.sort(key=lambda x: (x.get("date") or ""), reverse=True)
    return {"timestamp": datetime.utcnow().isoformat(), "total": len(history), "history": history}

async def background_refresher():
    while True:
        try:
            await get_history()
            print("[HISTORY] Background refresher active ✅")
        except Exception as e:
            print(f"[HISTORY] refresher error: {e}")
        await asyncio.sleep(1800)
