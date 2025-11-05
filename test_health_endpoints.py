# ============================================================
# EURO_GOALS v9.5.4 PRO+ – Health Diagnostics Tool
# Ελέγχει τα endpoints των Render / SmartMoney / GoalMatrix
# ============================================================

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# Ενδεικτικά URLs από .env
# ============================================================
RENDER_HEALTH_URL = os.getenv("RENDER_HEALTH_URL", "")
SMARTMONEY_ENGINE_URL = os.getenv("SMARTMONEY_ENGINE_URL", "")
GOALMATRIX_ENGINE_URL = os.getenv("GOALMATRIX_ENGINE_URL", "")

# ============================================================
# Συνάρτηση ελέγχου ενός URL
# ============================================================
def test_endpoint(name: str, url: str):
    if not url:
        return f"{name}: ❌ No URL defined in environment"
    try:
        resp = requests.get(url, timeout=5)
        return f"{name}: {resp.status_code} ({resp.reason})"
    except requests.exceptions.ConnectTimeout:
        return f"{name}: ⏱️ Timeout (no response)"
    except requests.exceptions.ConnectionError:
        return f"{name}: 🚫 Connection error"
    except Exception as e:
        return f"{name}: ❌ {str(e)}"


# ============================================================
# Κύρια εκτέλεση
# ============================================================
if __name__ == "__main__":
    print("===============================================")
    print("🔍 EURO_GOALS Health Diagnostics v9.5.4 PRO+")
    print("===============================================\n")

    urls = {
        "Render Health URL": RENDER_HEALTH_URL,
        "SmartMoney Engine": SMARTMONEY_ENGINE_URL,
        "GoalMatrix Engine": GOALMATRIX_ENGINE_URL,
    }

    for name, url in urls.items():
        print(test_endpoint(name, url))

    print("\n✅ Diagnostics completed.\n")
