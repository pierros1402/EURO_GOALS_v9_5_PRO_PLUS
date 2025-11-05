# ============================================================
# GOALMATRIX ENGINE v1.0.0
# ============================================================

import asyncio
import time
import httpx
from typing import List, Dict, Optional
from app.core.settings import settings


class GoalMatrixCache:
    def __init__(self):
        self._summary = {
            "enabled": True,
            "status": "Initializing",
            "last_updated_ts": 0,
            "total_matches": 0,
            "avg_goals": 0.0,
        }
        self._items: List[dict] = []
        self._ttl = 60

    @property
    def is_fresh(self) -> bool:
        return (time.time() - self._summary.get("last_updated_ts", 0)) < self._ttl

    def set(self, items: List[dict], status: str):
        avg_goals = 0.0
        if items:
            avg_goals = sum(i.get("expected_goals", 0.0) for i in items) / len(items)
        self._summary = {
            "enabled": True,
            "status": status,
            "last_updated_ts": int(time.time()),
            "total_matches": len(items),
            "avg_goals": round(avg_goals, 2),
        }
        self._items = items

    def get_summary(self) -> dict:
        return self._summary

    def get_items(self) -> List[dict]:
        return self._items


cache = GoalMatrixCache()


async def _fetch_data() -> Optional[dict]:
    """
    Dummy fetcher – εδώ θα συνδεθεί αργότερα με πραγματικό feed
    (π.χ. Sofascore / Football-Data.org / SportMonks)
    """
    await asyncio.sleep(0.5)
    # Mock data
    return {
        "matches": [
            {"match_id": 1001, "league": "Premier League", "home": "Arsenal", "away": "Chelsea", "xg_home": 1.9, "xg_away": 1.2},
            {"match_id": 1002, "league": "Serie A", "home": "Milan", "away": "Napoli", "xg_home": 1.4, "xg_away": 1.7},
            {"match_id": 1003, "league": "La Liga", "home": "Real Madrid", "away": "Barcelona", "xg_home": 2.1, "xg_away": 1.8},
        ]
    }


def _analyze_goals(raw_data: dict) -> List[dict]:
    items = []
    if not raw_data:
        return items

    for m in raw_data.get("matches", []):
        xg_home = float(m.get("xg_home", 0))
        xg_away = float(m.get("xg_away", 0))
        expected_goals = xg_home + xg_away
        tendency = "Over 2.5" if expected_goals >= 2.5 else "Under 2.5"
        items.append({
            "match_id": m["match_id"],
            "league": m["league"],
            "home": m["home"],
            "away": m["away"],
            "xg_home": xg_home,
            "xg_away": xg_away,
            "expected_goals": expected_goals,
            "tendency": tendency
        })
    return items


async def refresh_goalmatrix_once():
    try:
        data = await _fetch_data()
        items = _analyze_goals(data)
        status = "OK" if items else "No Data"
        cache.set(items, status)
    except Exception:
        cache.set([], "Failing")
    return cache.get_summary()


async def background_refresher():
    while True:
        await refresh_goalmatrix_once()
        await asyncio.sleep(60)
