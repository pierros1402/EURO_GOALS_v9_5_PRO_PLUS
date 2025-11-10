# ============================================================
# EURO_GOALS — LIVE PROXY REFRESHER (v1.0.0 Stable)
# ============================================================
# Ανάκτηση real-time feed από Cloudflare Worker και caching
# ============================================================

import asyncio
import aiohttp
import time
import os

class LiveFeedCache:
    def __init__(self):
        self.data = {"status": "initializing", "matches": []}
        self.last_update = 0
        self.interval = 20  # refresh κάθε 20s
        self.proxy_url = os.getenv(
            "LIVE_PROXY_URL",
            "https://eurogoals-live-proxy.pierros1402.workers.dev/live"
        )

    async def refresh(self):
        """Fetch από τον Cloudflare Worker και αποθήκευση στην cache"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.proxy_url, timeout=6) as r:
                    if r.status == 200:
                        self.data = await r.json()
                        self.data["status"] = "online"
                        self.last_update = int(time.time())
                        print(f"[LIVE_PROXY] ✅ Updated {len(self.data.get('matches', []))} matches.")
                    else:
                        self.data = {"status": "error", "code": r.status, "matches": []}
                        print(f"[LIVE_PROXY] ⚠️ Worker returned status {r.status}")
        except Exception as e:
            self.data = {"status": "offline", "error": str(e), "matches": []}
            print(f"[LIVE_PROXY] ❌ Error: {e}")

    async def loop_refresh(self):
        """Επαναλαμβανόμενη διαδικασία refresh"""
        print(f"[LIVE_PROXY] 🔄 Auto-refresh active (interval {self.interval}s)")
        while True:
            await self.refresh()
            await asyncio.sleep(self.interval)

# Δημιουργία shared instance για χρήση στο main.py
live_feed_cache = LiveFeedCache()
