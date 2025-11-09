# ============================================================
# BET365 LIVE ODDS FETCHER v1.2
# ------------------------------------------------------------
# Παίρνει live Over/Under και 1X2 αποδόσεις χωρίς επίσημο API
# Επιστρέφει unified JSON για SmartMoney Engine
# ============================================================

import httpx, re, json, asyncio

BET365_FEED_URL = "https://www.bet365.com/inplayapi/sports/1/"

async def fetch_bet365_odds():
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.get(BET365_FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
            text = res.text

            m = re.search(r"(?<=JSON.parse\\\(')(.*?)(?='\\\))", text)
            if not m:
                return {"matches": []}

            data_raw = json.loads(m.group(1).encode().decode("unicode_escape"))
            matches = []

            for comp in data_raw.get("CL", []):
                league = comp.get("NA", "Unknown League")
                for match in comp.get("EV", []):
                    name = match.get("NA", "")
                    markets = match.get("MA", [])
                    over25_open = over25_now = None
                    home_open = home_now = None

                    for market in markets:
                        if "Over/Under 2.5" in market.get("NA", ""):
                            for outcome in market.get("PA", []):
                                if outcome.get("NA") == "Over 2.5":
                                    over25_open = float(outcome.get("OD", 0))
                                    over25_now = float(outcome.get("FI", outcome.get("OD", 0)))
                        if "Full Time Result" in market.get("NA", ""):
                            for outcome in market.get("PA", []):
                                if outcome.get("NA") == "Home":
                                    home_open = float(outcome.get("OD", 0))
                                    home_now = float(outcome.get("FI", outcome.get("OD", 0)))

                    if over25_open and over25_now:
                        movement = round(over25_open - over25_now, 2)
                        matches.append({
                            "source": "Bet365",
                            "league": league,
                            "match": name,
                            "type": "O/U 2.5",
                            "open": over25_open,
                            "current": over25_now,
                            "movement": movement,
                        })
                    elif home_open and home_now:
                        movement = round(home_open - home_now, 2)
                        matches.append({
                            "source": "Bet365",
                            "league": league,
                            "match": name,
                            "type": "1X2",
                            "open": home_open,
                            "current": home_now,
                            "movement": movement,
                        })

            return {"matches": matches}

    except Exception as e:
        print("[BET365_FETCH] ⚠️", e)
        return {"matches": []}


if __name__ == "__main__":
    data = asyncio.run(fetch_bet365_odds())
    print(json.dumps(data, indent=2, ensure_ascii=False))
