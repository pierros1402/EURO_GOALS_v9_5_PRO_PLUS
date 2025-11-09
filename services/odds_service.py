# ============================================================
# TheOdds API Router
# ============================================================
from fastapi import APIRouter
import os, requests

router = APIRouter()
API_KEY = os.getenv("THEODDS_API_KEY")
BASE_URL = os.getenv("THEODDS_API_URL", "https://api.the-odds-api.com/v4/sports")

@router.get("/live")
def get_live_odds(sport: str = "soccer_epl"):
    """Ζωντανές αποδόσεις από το TheOdds API"""
    url = f"{BASE_URL}/{sport}/odds"
    params = {"apiKey": API_KEY, "regions": "eu", "markets": "h2h,totals"}
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}
