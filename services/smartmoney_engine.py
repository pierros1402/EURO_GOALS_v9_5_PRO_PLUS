# ============================================================
# SMARTMONEY ENGINE v1.0.1 — EURO_GOALS PRO+ Unified
# Multi-source odds (Bet365, Stoiximan, OPAP)
# ============================================================

import os
import time
import random
import asyncio

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
SMARTMONEY_ENABLED = os.getenv("SMARTMONEY_ENABLED", "true").lower() == "true"
SMARTMONEY_ALARM_DIFF = float(os.getenv("SMARTMONEY_ALARM_DIFF", "0.20"))
SMARTMONEY_REFRESH_INTERVAL = int(os.getenv("SMARTMONEY_REFRESH_INTERVAL", "30"))

# ------------------------------------------------------------
# CACHE CLASS
# ------------------------------------------------------------
class SmartMoneyCache:
    def __init__(self):
        self.summary = {
            "enabled": SMARTMONEY_ENABLED,
            "status": "Initializing",
            "count": 0,
            "last_updated_ts": 0
        }
        self.alerts = []

    # --------------------------------------------------------
    # Core methods
    # --------------------------------------------------------
    def get_summary(self):
        return self.summary

    def get_alerts(self):
        return self.alerts

    def get_data(self):
        """Generic data accessor for compatibility"""
        return {"summary": self.summary, "alerts": self.alerts}


# ------------------------------------------------------------
# GLOBAL CACHE INSTANCE
# ------------------------------------------------------------
cache = SmartMoneyCache()

# ------------------------------------------------------------
# BACKGROUND REFRESHER (Simulated until real API integration)
# ------------------------------------------------------------
async def background_refresher():
    """Fake background task — replace with real API polling."""
    if not SMARTMONEY_ENABLED:
        print("⚠️ SMARTMONEY ENGINE DISABLED")
        return

    print("💰 SMARTMONEY ENGINE ACTIVE (looping)...")

    while True:
        await asyncio.sleep(SMARTMONEY_REFRESH_INTERVAL)

        sample_sources = ["Bet365", "Stoiximan", "OPAP"]
        sample_matches = [
            ("Arsenal", "Chelsea"),
            ("PAOK", "Olympiacos"),
            ("Real Madrid", "Barcelona"),
            ("Manchester Utd", "Liverpool")
        ]

        alerts = []
        for src, (home, away) in zip(sample_sources, sample_matches):
            open_odds = round(random.uniform(1.60, 2.20), 2)
            cur_odds = round(open_odds + random.uniform(-0.35, 0.35), 2)
            movement = round(cur_odds - open_odds, 2)

            if abs(movement) >= SMARTMONEY_ALARM_DIFF:
                alerts.append({
                    "source": src,
                    "league": random.choice(["Premier League", "Super League", "La Liga"]),
                    "match": f"{home} - {away}",
                    "market": "1X2",
                    "open": open_odds,
                    "current": cur_odds,
                    "movement": movement,
                    "timestamp": time.strftime("%H:%M:%S")
                })

        cache.alerts = alerts
        cache.summary = {
            "enabled": SMARTMONEY_ENABLED,
            "status": "OK" if alerts else "Idle",
            "count": len(alerts),
            "last_updated_ts": int(time.time())
        }

        print(f"[SMARTMONEY] Refreshed {len(alerts)} alerts at {time.strftime('%H:%M:%S')}")

# ------------------------------------------------------------
# API-LIKE ACCESSORS (Async wrappers)
# ------------------------------------------------------------
async def get_summary():
    return cache.get_summary()

async def get_alerts():
    return cache.get_alerts()

async def get_data():
    return cache.get_data()
