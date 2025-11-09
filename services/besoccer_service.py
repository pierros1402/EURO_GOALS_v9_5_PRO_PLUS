# ============================================================
# BeSoccer API Router
# ============================================================
from fastapi import APIRouter
import os, requests

router = APIRouter()
API_KEY = os.getenv("BESOCCER_API_KEY")
BASE_URL = os.getenv("BESOCCER_API_URL", "https://apiclient.besoccerapps.com/scripts/api/api.php")

@router.get("/matches")
def get_matches(competition: str = "premier-league", season: str = "2024"):
    """Ανάκτηση αγώνων από το BeSoccer API"""
    params = {
        "key": API_KEY,
        "tz": "Europe/Athens",
        "req": "matchs",
        "league": competition,
        "year": season,
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}
