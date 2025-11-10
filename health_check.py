# ============================================================
# EURO_GOALS v9.6.1 PRO+ — Unified Health Check Utility
# Ελέγχει τη διαθεσιμότητα όλων των API endpoints
# ============================================================

import asyncio
import httpx
import sys
import time

# 🔹 ΟΡΙΣΕ ΤΟ ΠΛΗΡΕΣ URL ΤΟΥ RENDER SERVICE Ή ΤΟΥ LOCALHOST
BASE_URL = "https://eurogoals-unified-pro954.onrender.com"
# BASE_URL = "http://127.0.0.1:8000"   # (για τοπική δοκιμή)

# 🔹 ΛΙΣΤΑ ENDPOINTS ΠΡΟΣ ΕΛΕΓΧΟ
ENDPOINTS = [
    "/", 
    "/api/smartmoney/summary",
    "/api/smartmoney/alerts",
    "/api/goalmatrix/summary",
    "/api/goalmatrix/alerts",
    "/api/heatmap/data",
    "/api/history",
    "/api/odds/data",
    "/api/odds/summary",
    "/system_status_page",
]


# ------------------------------------------------------------
# Έλεγχος κάθε endpoint
# ------------------------------------------------------------
async def check_endpoint(client, path):
    url = f"{BASE_URL}{path}"
    start = time.perf_counter()
    try:
        resp = await client.get(url, timeout=15)
        elapsed = (time.perf_counter() - start) * 1000
        status = resp.status_code
        if status == 200:
            result = "✅ OK"
        elif 300 <= status < 400:
            result = f"➡️ Redirect ({status})"
        elif 400 <= status < 500:
            result = f"⚠️ Client Error ({status})"
        else:
            result = f"❌ Server Error ({status})"
        print(f"{path:<35} {result:<25} {elapsed:6.1f} ms")
    except Exception as e:
        print(f"{path:<35} ❌ Exception: {e}")


# ------------------------------------------------------------
# Κεντρική ρουτίνα
# ------------------------------------------------------------
async def run_check():
    print("\n=== [EURO_GOALS] Unified Health Check v9.6.1 PRO+ ===")
    print(f"🌐 Target base: {BASE_URL}\n")
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[check_endpoint(client, ep) for ep in ENDPOINTS])
    print("\n✅ Completed health check.\n")


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    if "<to-url-tou-render-service>" in BASE_URL:
        print("❗ Πρέπει να ορίσεις το πλήρες URL του Render service πρώτα στο BASE_URL.")
        sys.exit(1)

    asyncio.run(run_check())
