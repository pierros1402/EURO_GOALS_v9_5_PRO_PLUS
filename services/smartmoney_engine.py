# app/services/smartmoney_engine.py
import asyncio
import time
from typing import Dict, List, Optional, Tuple
import httpx
from .typing import JSONLike if False else dict  # hint only
from app.core.settings import settings

class SmartMoneyCache:
    def __init__(self):
        self._alerts: List[dict] = []
        self._summary: dict = {
            "enabled": settings.SMARTMONEY_ENABLED,
            "provider_health": {"odds": False, "depth": False},
            "last_updated_ts": 0,
            "status": "Initializing",
            "count": 0,
        }
        self._ttl = settings.SMARTMONEY_CACHE_TTL

    @property
    def is_fresh(self) -> bool:
        return (time.time() - self._summary.get("last_updated_ts", 0)) <= self._ttl

    def set(self, alerts: List[dict], provider_health: Dict[str, bool], status: str):
        self._alerts = alerts
        self._summary = {
            "enabled": settings.SMARTMONEY_ENABLED,
            "provider_health": provider_health,
            "last_updated_ts": int(time.time()),
            "status": status,
            "count": len(alerts),
        }

    def get_alerts(self) -> List[dict]:
        return self._alerts

    def get_summary(self) -> dict:
        return self._summary

cache = SmartMoneyCache()

async def _probe_provider(client: httpx.AsyncClient, url: Optional[str], key: Optional[str]) -> Tuple[bool, Optional[dict]]:
    if not url:
        return False, None
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    try:
        r = await client.get(str(url), headers=headers, timeout=10)
        ok = r.status_code == 200
        data = r.json() if ok else None
        return ok, data
    except Exception:
        return False, None

def _compute_signals(odds_data: Optional[dict], depth_data: Optional[dict]) -> List[dict]:
    """
    Ενδεικτικός αλγόριθμος: ενώνει odds movement + market depth
    και παράγει alerts με weight (Money Flow Index proxy).
    """
    if not odds_data and not depth_data:
        return []

    matches = {}

    # Normalize odds_data
    if odds_data and isinstance(odds_data, dict):
        for item in odds_data.get("matches", []):
            mid = str(item.get("match_id"))
            matches.setdefault(mid, {}).update({
                "home": item.get("home"),
                "away": item.get("away"),
                "league": item.get("league"),
                "kickoff": item.get("kickoff"),
                "odds_open": item.get("odds_open"),
                "odds_now": item.get("odds_now"),
            })

    # Normalize depth_data
    if depth_data and isinstance(depth_data, dict):
        for item in depth_data.get("markets", []):
            mid = str(item.get("match_id"))
            mkt = {
                "back_volume": item.get("back_volume", 0.0),
                "lay_volume": item.get("lay_volume", 0.0),
                "last_5m_delta": item.get("last_5m_delta", 0.0),
            }
            matches.setdefault(mid, {}).update(mkt)

    alerts = []
    for mid, m in matches.items():
        open_odds = (m.get("odds_open") or {}).get("over25")
        now_odds  = (m.get("odds_now") or {}).get("over25")
        if not open_odds or not now_odds:
            # try 1X2 as fallback
            open_odds = (m.get("odds_open") or {}).get("home")
            now_odds  = (m.get("odds_now") or {}).get("home")

        if not open_odds or not now_odds:
            continue

        movement = (open_odds - now_odds) if isinstance(open_odds, (int,float)) and isinstance(now_odds,(int,float)) else 0.0
        flow = float(m.get("back_volume", 0.0)) - float(m.get("lay_volume", 0.0))
        last5 = float(m.get("last_5m_delta", 0.0))

        # Simple score (you θα το βελτιώσεις με τα πραγματικά πεδία σου)
        score = (movement * 10) + (flow * 0.001) + (last5 * 2)

        if score >= 1.5:  # threshold demo
            alerts.append({
                "match_id": mid,
                "home": m.get("home"),
                "away": m.get("away"),
                "league": m.get("league"),
                "kickoff": m.get("kickoff"),
                "movement": round(movement, 3),
                "money_flow": round(flow, 2),
                "last5m": round(last5, 3),
                "score": round(score, 3),
                "signal": "STRONG" if score >= 3.0 else "MEDIUM",
            })

    # Sort by score desc
    alerts.sort(key=lambda x: x["score"], reverse=True)
    return alerts

async def refresh_smartmoney_once() -> dict:
    if not settings.SMARTMONEY_ENABLED:
        cache.set([], {"odds": False, "depth": False}, status="Disabled")
        return cache.get_summary()

    async with httpx.AsyncClient() as client:
        odds_ok, odds_data = await _probe_provider(
            client, settings.PROVIDER_ODDS_API_URL, settings.PROVIDER_ODDS_API_KEY
        )
        depth_ok, depth_data = await _probe_provider(
            client, settings.PROVIDER_MARKET_DEPTH_API_URL, settings.PROVIDER_MARKET_DEPTH_API_KEY
        )

    alerts = _compute_signals(odds_data, depth_data)
    status = "OK" if (odds_ok or depth_ok) else "Degraded" if (odds_ok != depth_ok) else "Failing"  # both False -> Failing
    cache.set(alerts, {"odds": odds_ok, "depth": depth_ok}, status=status)
    return cache.get_summary()

async def background_refresher():
    # idempotent loop
    while True:
        try:
            await refresh_smartmoney_once()
        except Exception:
            cache.set([], {"odds": False, "depth": False}, status="Failing")
        await asyncio.sleep(max(10, settings.SMARTMONEY_REFRESH_INTERVAL))
