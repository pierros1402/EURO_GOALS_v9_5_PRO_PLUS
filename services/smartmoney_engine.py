# ============================================================
# SMARTMONEY ENGINE v9.9.11 — No-Fail Auto-Retry Edition
# ============================================================

import asyncio, time, random
from functools import wraps

class SmartMoneyEngine:
    def __init__(self):
        self.last_snapshot = None
        self.last_signals = []
        print("[SmartMoneyEngine] ✅ Initialized (Auto-Retry Mode)")

    # === Auto-Retry Decorator ===
    def safe_retry(max_retries=3, delay=2):
        def decorator(func):
            @wraps(func)
            async def wrapper(self, *args, **kwargs):
                for attempt in range(1, max_retries + 1):
                    try:
                        result = await func(self, *args, **kwargs)
                        return result
                    except Exception as e:
                        print(f"[SmartMoneyEngine] ⚠️ Attempt {attempt} failed: {e}")
                        if attempt < max_retries:
                            await asyncio.sleep(delay)
                        else:
                            if self.last_snapshot:
                                print("[SmartMoneyEngine] 🧠 Returning cached snapshot.")
                                return self.last_snapshot
                            return {"status": "error", "message": str(e)}
            return wrapper
        return decorator

    # === Core Functions ===
    @safe_retry(max_retries=3, delay=2)
    async def get_odds_snapshot(self, match_id="default"):
        """Simulate pulling odds snapshot from live or API."""
        # example of random API noise
        if random.random() < 0.2:
            raise Exception("Temporary odds fetch error.")
        snapshot = {
            "match_id": match_id,
            "timestamp": time.time(),
            "odds": {
                "home": round(random.uniform(1.5, 2.5), 2),
                "draw": round(random.uniform(2.5, 3.5), 2),
                "away": round(random.uniform(2.0, 3.5), 2)
            }
        }
        self.last_snapshot = snapshot
        return snapshot

    @safe_retry(max_retries=3, delay=2)
    async def get_smartmoney_signals(self, match_id="default"):
        """Simulate SmartMoney pattern recognition."""
        if random.random() < 0.2:
            raise Exception("Signal generation timeout.")
        signals = [
            {"team": "Home", "trend": "SharpDrop", "confidence": random.randint(60, 95)},
            {"team": "Away", "trend": "HeavyBetting", "confidence": random.randint(50, 85)},
        ]
        self.last_signals = signals
        return signals

# === Singleton instance ===
engine = SmartMoneyEngine()

async def get_odds_snapshot(match_id="default"):
    return await engine.get_odds_snapshot(match_id)

async def get_smartmoney_signals(match_id="default"):
    return await engine.get_smartmoney_signals(match_id)
