# ============================================================
# GOALMATRIX ENGINE v2.0 – EURO_GOALS v9.5.4 PRO+
# ============================================================
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOALMATRIX_API_URL = os.getenv("GOALMATRIX_API_URL", "")
GOALMATRIX_API_KEY = os.getenv("GOALMATRIX_API_KEY", "")


# ------------------------------------------------------------
# Fetch GoalMatrix Data
# ------------------------------------------------------------
def fetch_goalmatrix_data():
    """Λήψη δεδομένων GoalMatrix από remote API ή local engine"""
    try:
        headers = {"Authorization": f"Bearer {GOALMATRIX_API_KEY}"}
        url = f"{GOALMATRIX_API_URL}/api/v1/matrix"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return {"error": True, "message": f"Bad status: {resp.status_code}"}
    except Exception as e:
        return {"error": True, "message": str(e)}


# ------------------------------------------------------------
# Calculate Goal Probabilities (demo version)
# ------------------------------------------------------------
def calculate_goal_probabilities(data):
    """Υπολογίζει ενδεικτικά ποσοστά για Over/Under 2.5"""
    try:
        if not data or "matches" not in data:
            return {"error": True, "message": "No data for GoalMatrix"}
        results = []
        for m in data["matches"]:
            goals_avg = (m.get("home_goals_avg", 1.2) + m.get("away_goals_avg", 1.0)) / 2
            over25 = round(min(0.95, goals_avg / 2.5), 2)
            under25 = round(1 - over25, 2)
            results.append({
                "match": m.get("match_name", "Unknown"),
                "over25": over25,
                "under25": under25
            })
        return {"status": "ok", "data": results}
    except Exception as e:
        return {"error": True, "message": str(e)}
