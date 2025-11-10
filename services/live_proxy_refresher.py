# ============================================================
# EURO_GOALS v9.6.1 PRO+ — Live Proxy Refresher
# ============================================================

import asyncio
import aiohttp
import os
import time

LIVE_PROXY_URL = os.getenv("LIVE_PROXY_URL", "https://eurogoals-live-proxy.pierros1402.workers.dev/live")

class LiveFeedCache:
    """Απλό cache αντικείμενο για αποθήκευση των τελευταίων live δεδομένων"""
    def __init__(self):
        self.last_update = 0
        self.data = {"status": "initializing", "matches": []}

    async def refresh(self):
        """Ανανεώνει τα δεδομένα από τον Cloudflare Worker"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(LIVE_PROXY_URL, timeout=10) as resp:
                    if resp.status == 200:
                        json_data = await resp.json()
                        self.data = json_data
                        self.last_update = int(time.time())
                        print(f"[LIVE_PROXY] ✅ Updated {len(json_data.get('matches', []))} matches")
                    else:
                        print(f"[LIVE_PROXY] ⚠️ HTTP {resp.status}")
            except Exception as e:
                print(f"[LIVE_PROXY] ❌ Error fetching: {e}")

    async def loop_refresh(self, interval=20):
        """Ατέρμων βρόχος ανανέωσης κάθε X δευτερόλεπτα"""
        while True:
            await self.refresh()
            await asyncio.sleep(interval)

# Δημιουργία global αντικειμένου cache
live_feed_cache = LiveFeedCache()
