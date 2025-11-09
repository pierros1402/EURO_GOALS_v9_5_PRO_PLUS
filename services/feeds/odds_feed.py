# ============================================================
# SMARTMONEY FEED AGGREGATOR v1.0.0
# Ενοποιεί odds από Bet365, Stoiximan, Πάμε Στοίχημα (ΟΠΑΠ)
# ============================================================

import httpx
import asyncio
import os

BET365_ENABLED = os.getenv("BET365_ENABLED", "true").lower() == "true"
STOIXIMAN_ENABLED = os.getenv("STOIXIMAN_ENABLED", "true").lower() == "true"
PAMESTOIXIMA_ENABLED = os.getenv("PAMESTOIXIMA_ENABLED", "true").lower() == "true"

BET365_API_URL = os.getenv("BET365_API_URL", "https://bet365-api.example.com/v1/soccer/today")
BET365_API_KEY = os.getenv("BET365_API_KEY", "your_bet365_key")

STOIXIMAN_API_URL = os.getenv("STOIXIMAN_API_URL", "https://api.stoiximan.gr/frontapi/v1/events")
PAMESTOIXIMA_API_URL = os.getenv("PAMESTOIXIMA_API_URL", "https://www.pamestoixima.gr/web/services/odds")


async def fetch_bet365():
    if not BET365_ENABLED:
        return []
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(BET365_API_URL, headers={"X-API-Key": BET365_API_KEY})
            r.raise_for_status()
            data = r.json()
            out = []
            for ev in data.get("events", []):
                out.append({
                    "source": "bet365",
                    "match": f"{ev.get('home')} - {ev.get('away')}",
                    "league": ev.get("league"),
                    "odds_open": ev.get("odds_open", {}),
                    "odds_now": ev.get("odds_now", {}),
                })
            return out
    except Exception as e:
        print("[Bet365] ⚠️", e)
        return []


async def fetch_stoiximan():
    if not STOIXIMAN_ENABLED:
        return []
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(STOIXIMAN_API_URL)
            r.raise_for_status()
            data = r.json()
            out = []
            for ev in data.get("events", []):
                # Προσαρμογή όπου χρειάζεται ανά δομή
                league = (ev.get("competition") or {}).get("name")
                name = ev.get("name") or f"{ev.get('homeTeam','?')} - {ev.get('awayTeam','?')}"
                # Παράδειγμα: παίρνουμε 1Χ2 από το πρώτο market (προσαρμόζεται)
                markets = ev.get("markets") or []
                if not markets:
                    continue
                sels = markets[0].get("selections") or []
                if len(sels) < 3:
                    continue
                out.append({
                    "source": "stoiximan",
                    "match": name,
                    "league": league,
                    "odds_open": {
                        "home": float(sels[0].get("price", 0)),
                        "draw": float(sels[1].get("price", 0)),
                        "away": float(sels[2].get("price", 0)),
                    },
                    "odds_now": {
                        "home": float(sels[0].get("price", 0)),
                        "draw": float(sels[1].get("price", 0)),
                        "away": float(sels[2].get("price", 0)),
                    },
                })
            return out
    except Exception as e:
        print("[Stoiximan] ⚠️", e)
        return []


async def fetch_pamestoixima():
    if not PAMESTOIXIMA_ENABLED:
        return []
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(PAMESTOIXIMA_API_URL)
            r.raise_for_status()
            data = r.json()
            out = []
            for event in data.get("events", []):
                home = event.get("homeTeam")
                away = event.get("awayTeam")
                league = event.get("sportName") or event.get("competitionName")
                markets = event.get("markets") or []
                if not markets:
                    continue
                sels = markets[0].get("selections") or []
                if len(sels) < 3:
                    continue
                out.append({
                    "source": "opap",
                    "match": f"{home} - {away}",
                    "league": league,
                    "odds_open": {
                        "home": float(sels[0].get("price", 0)),
                        "draw": float(sels[1].get("price", 0)),
                        "away": float(sels[2].get("price", 0)),
                    },
                    "odds_now": {
                        "home": float(sels[0].get("price", 0)),
                        "draw": float(sels[1].get("price", 0)),
                        "away": float(sels[2].get("price", 0)),
                    },
                })
            return out
    except Exception as e:
        print("[OPAP] ⚠️", e)
        return []


async def get_all_odds():
    tasks = []
    tasks.append(fetch_bet365())
    tasks.append(fetch_stoiximan())
    tasks.append(fetch_pamestoixima())

    results = await asyncio.gather(*tasks, return_exceptions=True)
    merged = []
    for res in results:
        if isinstance(res, list):
            merged.extend(res)
    return merged
