# ============================================================
# AI MATCHLAB — PROVIDER CLIENT
# Κεντρικός client για επικοινωνία με τον Worker
# ============================================================

import httpx
import asyncio
import os
from typing import Optional, Dict, Any


# ------------------------------------------------------------
# Ρυθμίσεις
# ------------------------------------------------------------

WORKER_URL = os.getenv("WORKER_URL", "").rstrip("/")
TIMEOUT = float(os.getenv("WORKER_TIMEOUT", 6.0))


class ProviderClient:
    """
    Unified client για όλα τα fetch:
    - JSON requests
    - HTML fetch (fixtures)
    - Error handling
    - Timeout management
    """

    def __init__(self):
        if not WORKER_URL:
            print("[ProviderClient] ⚠ WORKER_URL is missing in environment.")

        self.client = httpx.AsyncClient(timeout=TIMEOUT)

    # ------------------------------------------------------------
    # JSON GET
    # ------------------------------------------------------------
    async def get_json(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Παίρνει JSON από τον Worker: /api/...
        """
        url = f"{WORKER_URL}{path}"

        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            return resp.json()

        except httpx.TimeoutException:
            print(f"[ProviderClient] ⏳ Timeout on GET {url}")
            return None

        except httpx.HTTPError as e:
            print(f"[ProviderClient] ❌ HTTP error on GET {url}: {e}")
            return None

        except Exception as e:
            print(f"[ProviderClient] ⚠ Unexpected error on GET {url}: {e}")
            return None

    # ------------------------------------------------------------
    # HTML GET (fixtures, dashboards, κλπ)
    # ------------------------------------------------------------
    async def get_html(self, url: str) -> Optional[str]:
        """
        Παίρνει HTML από εξωτερικό URL (π.χ. fixtures).
        Δεν περνάει από WORKER_URL.
        """
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            return resp.text

        except httpx.TimeoutException:
            print(f"[ProviderClient] ⏳ Timeout on HTML fetch {url}")
            return None

        except httpx.HTTPError as e:
            print(f"[ProviderClient] ❌ HTTP error on HTML fetch {url}: {e}")
            return None

        except Exception as e:
            print(f"[ProviderClient] ⚠ Unexpected error HTML fetch {url}: {e}")
            return None

    # ------------------------------------------------------------
    async def close(self):
        """ Κλείνει το client σωστά """
        await self.client.aclose()


# ------------------------------------------------------------
# Singleton instance
# ------------------------------------------------------------
provider_client = ProviderClient()
