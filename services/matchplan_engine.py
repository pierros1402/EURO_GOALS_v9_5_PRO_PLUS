# ============================================================
# EURO_GOALS PRO+ — MATCHPLAN ENGINE (v9.6.9 + SmartMoney Link)
# ============================================================
import os, asyncio, aiohttp, re, unicodedata
from datetime import datetime, timedelta
from dotenv import load_dotenv
from services.leagues_list import LEAGUES
from services import smartmoney_engine

load_dotenv()
IS_DEV = os.getenv("IS_DEV", "false").lower() == "true"
SPORTMONKS_API_KEY = os.getenv("SPORTMONKS_API_KEY", "").strip()

def _norm(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

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
                    "league": league_name, "home": home, "away": away,
                    "date": date, "status": e.get("status"),
                })
            except Exception:
                continue
    return results

def _best_price_from_runner(r):
    ex = r.get("ex") or {}
    atb = ex.get("availableToBack") or []
    if isinstance(atb, list) and atb:
        return atb[0].get("price")
    return r.get("lastPriceTraded") or r.get("price")

def _attach_odds(market_data):
    out = {}
    for r in (market_data.get("runners") or []):
        name = r.get("name") or r.get("runnerName") or ""
        out[name] = _best_price_from_runner(r)
    return out

def _match_market(fixt, markets):
    h, a = _norm(fixt.get("home")), _norm(fixt.get("away"))
    if not h or not a:
        return None
    for m in markets:
        ev = _norm(m.get("eventName") or m.get("event") or "")
        comp = _norm(m.get("competition") or m.get("league") or "")
        if h in ev and a in ev:
            return m
        if (h in ev or a in ev) and (comp and comp in _norm(fixt.get("league") or "")):
            return m
    return None

async def enrich_with_smartmoney(fixtures):
    markets = await smartmoney_engine.get_markets_api(league="")
    enriched = []
    for fx in fixtures:
        mkt = _match_market(fx, markets) if markets else None
        if mkt:
            odds_payload = await smartmoney_engine.get_odds_api(mkt.get("marketId") or mkt.get("id"))
            odds = _attach_odds(odds_payload)
            fx_enriched = dict(fx)
            fx_enriched.update({
                "marketId": mkt.get("marketId") or mkt.get("id"),
                "marketName": mkt.get("marketName") or mkt.get("name"),
                "odds": odds,
            })
            enriched.append(fx_enriched)
        else:
            enriched.append(fx)
    return enriched

async def get_matchplan_summary():
    data = await get_from_sportmonks()
    return {"timestamp": datetime.utcnow().isoformat(), "matches": data}

async def get_matchplan_enriched():
    base = await get_from_sportmonks()
    enriched = await enrich_with_smartmoney(base)
    return {"timestamp": datetime.utcnow().isoformat(), "matches": enriched}

async def background_refresher():
    while True:
        try:
            await get_matchplan_summary()
            print("[MATCHPLAN] Background refresher active.")
        except Exception as e:
            print(f"[MATCHPLAN] refresher error: {e}")
        await asyncio.sleep(1800)
