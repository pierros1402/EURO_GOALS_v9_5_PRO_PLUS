# ============================================================
# SMARTMONEY ENGINE v2.0 — EURO_GOALS PRO+ (Betfair Public via Worker)
# ============================================================
import os, time, asyncio
from typing import Any, Dict, List, Optional
import aiohttp

SMARTMONEY_ENABLED = os.getenv("SMARTMONEY_ENABLED", "true").lower() == "true"
SMARTMONEY_REFRESH_INTERVAL = int(os.getenv("SMARTMONEY_REFRESH_INTERVAL", "30"))
RAW_PROXY = os.getenv("SMARTMONEY_PROXY_URL", "").strip()
SMARTMONEY_PROXY_URL = RAW_PROXY[:-1] if RAW_PROXY.endswith("/") else RAW_PROXY

class _Cache:
    def __init__(self) -> None:
        self.summary: Dict[str, Any] = {
            "enabled": SMARTMONEY_ENABLED,
            "status": "Initializing",
            "count": 0,
            "last_updated_ts": 0,
            "proxy": SMARTMONEY_PROXY_URL or None,
        }
        self.alerts: List[Dict[str, Any]] = []
        self.markets: List[Dict[str, Any]] = []
        self.last_markets_ts: int = 0

    @property
    def is_fresh(self) -> bool:
        return (time.time() - self.summary.get("last_updated_ts", 0)) < SMARTMONEY_REFRESH_INTERVAL

cache = _Cache()

async def _fetch_json(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
    try:
        async with session.get(url, timeout=20) as r:
            if r.status != 200:
                print(f"[SMARTMONEY] HTTP {r.status} for {url}")
                return {}
            return await r.json()
    except Exception as e:
        print(f"[SMARTMONEY] fetch error: {e}")
        return {}

def _base() -> Optional[str]:
    return SMARTMONEY_PROXY_URL or None

async def fetch_markets(league: str = "") -> List[Dict[str, Any]]:
    if not _base():
        return []
    url = f"{_base()}/betfair/markets"
    if league:
        url += f"?league={league}"
    async with aiohttp.ClientSession() as session:
        data = await _fetch_json(session, url)
        items = data.get("markets") or data.get("data") or []
        cache.markets = items
        cache.last_markets_ts = int(time.time())
        return items

async def fetch_odds(market_id: str) -> Dict[str, Any]:
    if not _base():
        return {}
    url = f"{_base()}/betfair/odds?market={market_id}"
    async with aiohttp.ClientSession() as session:
        data = await _fetch_json(session, url)
        return data

async def fetch_trends(league: str = "") -> Dict[str, Any]:
    if not _base():
        return {}
    url = f"{_base()}/betfair/trends"
    if league:
        url += f"?league={league}"
    async with aiohttp.ClientSession() as session:
        data = await _fetch_json(session, url)
        return data

def _estimate_movement(runner: Dict[str, Any]) -> float:
    open_price = runner.get("open") or runner.get("openPrice")
    cur_price = runner.get("price") or runner.get("lastPriceTraded") or runner.get("current")
    if open_price and cur_price:
        try:
            return float(cur_price) - float(open_price)
        except Exception:
            return 0.0
    prices = runner.get("prices") or runner.get("ex", {}).get("availableToBack")
    if isinstance(prices, list) and len(prices) >= 2:
        try:
            return float(prices[0].get("price")) - float(prices[1].get("price"))
        except Exception:
            return 0.0
    return 0.0

async def refresh_smartmoney_once() -> None:
    if not SMARTMONEY_ENABLED:
        cache.summary["status"] = "Disabled"
        cache.summary["last_updated_ts"] = int(time.time())
        return
    if not _base():
        cache.summary["status"] = "NoProxy"
        cache.summary["last_updated_ts"] = int(time.time())
        return

    now = int(time.time())
    if now - cache.last_markets_ts > 120:
        await fetch_markets()

    sample = (cache.markets or [])[:12]
    alerts: List[Dict[str, Any]] = []

    async with aiohttp.ClientSession() as session:
        for m in sample:
            mid = m.get("marketId") or m.get("id")
            if not mid:
                continue
            data = await _fetch_json(session, f"{_base()}/betfair/odds?market={mid}")
            runners = data.get("runners") or []
            for r in runners:
                mv = _estimate_movement(r)
                if abs(mv) >= 0.15:
                    alerts.append({
                        "league": m.get("competition") or m.get("league"),
                        "market": m.get("marketName") or m.get("name") or "Unknown",
                        "event": m.get("eventName") or m.get("event") or "",
                        "runner": r.get("name") or r.get("runnerName") or "",
                        "movement": round(mv, 3),
                        "current": r.get("price") or r.get("lastPriceTraded"),
                        "open": r.get("open") or r.get("openPrice"),
                        "marketId": mid,
                        "ts": now,
                    })

    cache.alerts = alerts
    cache.summary.update({
        "enabled": SMARTMONEY_ENABLED,
        "status": "OK" if alerts else "Idle",
        "count": len(alerts),
        "last_updated_ts": int(time.time()),
        "proxy": _base(),
    })

async def get_summary():
    if not cache.is_fresh:
        await refresh_smartmoney_once()
    return cache.summary

async def get_alerts():
    if not cache.is_fresh:
        await refresh_smartmoney_once()
    return cache.alerts

async def get_markets_api(league: str = ""):
    return await fetch_markets(league)

async def get_odds_api(market: str):
    return await fetch_odds(market)

async def get_trends_api(league: str = ""):
    return await fetch_trends(league)

async def background_refresher():
    print("💰 SMARTMONEY ENGINE v2.0 ACTIVE (worker-proxy mode)")
    while True:
        try:
            await refresh_smartmoney_once()
        except Exception as e:
            print(f"[SMARTMONEY] refresher error: {e}")
        await asyncio.sleep(SMARTMONEY_REFRESH_INTERVAL)
