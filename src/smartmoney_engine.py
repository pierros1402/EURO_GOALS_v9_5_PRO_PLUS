# ============================================================
# EURO_GOALS v9.5.5 PRO+ – SmartMoney Real Feed Engine
# Live connection to The Odds API (v4)
# ============================================================

import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# Environment Variables
# ============================================================
API_URL = os.getenv("SMARTMONEY_REALFEED_API_URL", "https://api.the-odds-api.com/v4/sports")
API_KEY = os.getenv("SMARTMONEY_REALFEED_API_KEY", "")
REFRESH_INTERVAL = int(os.getenv("SMARTMONEY_FEED_REFRESH", 60))

# ============================================================
# Supported Leagues (EU major)
# ============================================================
LEAGUES = {
    "soccer_epl": "Premier League (ENG)",
    "soccer_uefa_champs_league": "UEFA Champions League",
    "soccer_spain_la_liga": "La Liga (ESP)",
    "soccer_italy_serie_a": "Serie A (ITA)",
    "soccer_germany_bundesliga": "Bundesliga (GER)",
    "soccer_greece_super_league": "Super League (GRE)"
}

# ============================================================
# Core Fetch Function
# ============================================================
def fetch_odds_data():
    """Fetches live odds from The Odds API for all selected leagues."""
    data_summary = []

    for league_key, league_name in LEAGUES.items():
        try:
            url = f"{API_URL}/{league_key}/odds/?regions=eu&markets=h2h,spreads&oddsFormat=decimal&apiKey={API_KEY}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()

                # Extract bookmaker + odds summary
                for match in data:
                    home_team = match.get("home_team")
                    away_team = match.get("away_team")
                    bookmakers = match.get("bookmakers", [])

                    if not bookmakers:
                        continue

                    # Calculate movement index (SmartMoney logic)
                    avg_odds = []
                    for b in bookmakers:
                        for m in b.get("markets", []):
                            if m["key"] == "h2h":
                                outcomes = m.get("outcomes", [])
                                for o in outcomes:
                                    avg_odds.append(o.get("price", 0))

                    if avg_odds:
                        avg_price = round(sum(avg_odds) / len(avg_odds), 2)
                        data_summary.append({
                            "league": league_name,
                            "home": home_team,
                            "away": away_team,
                            "avg_odds": avg_price,
                            "bookmakers": len(bookmakers)
                        })

            else:
                print(f"[SmartMoney] ⚠️ League {league_name} – Error {response.status_code}")

        except Exception as e:
            print(f"[SmartMoney] ❌ {league_name} – {e}")

    return data_summary


# ============================================================
# CLI Diagnostic / Standalone Run
# ============================================================
if __name__ == "__main__":
    print("===============================================")
    print("💰 SMARTMONEY Real Feed Diagnostic (The Odds API)")
    print("===============================================\n")

    results = fetch_odds_data()
    for i, match in enumerate(results[:10]):  # Show first 10 for preview
        print(f"{i+1}. {match['league']}: {match['home']} vs {match['away']} → Avg Odds: {match['avg_odds']} ({match['bookmakers']} books)")

    print(f"\n✅ Total matches fetched: {len(results)}")
