# ============================================================
# STOIXIMAN LIVE ODDS FETCHER v1.1
# ------------------------------------------------------------
# Παίρνει ζωντανά δεδομένα από Stoiximan FrontAPI (public)
# Προσθέτει source="Stoiximan" για SmartMoney Panel
# ============================================================

import httpx, json, asyncio, time

STOIXIMAN_FEED_URL = "https://api.stoiximan.gr/frontapi/v1/events"

async def fetch_stoiximan_odds(limit: int = 50):
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.get(STOIXIMAN_FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
            data = res.json()
            matches = []

            for event in data.get("data", [])[:limit]:
                league = event.get("competition", {}).get("name", "Unknown League")
                home = event.get("homeTeam", {}).get("name")
                away = event.get("awayTeam", {}).get("name")
                match_name = f"{home} - {away}"

                markets = event.get("markets", [])
                for m in markets:
                    name = m.get("name", "")
                    outcomes = m.get("selections", [])

                    # 1X2
                    if "1X2" in name or "Τελικό Αποτέλεσμα" in name:
                        for o in outcomes:
                            if o.get("name") == "1":
                                odd = float(o.get("price", 0))
                                matches.append({
                                    "source": "Stoiximan",
                                    "league": league,
                                    "match": match_name,
                                    "type": "1X2",
                                    "open": odd,
                                    "current": odd,
                                    "movement": 0.0,
                                })

                    # Over/Under 2.5
                    if "Over/Under" in name or "Σύνολο Γκολ" in name:
                        for o in outcomes:
                            if "Over 2.5" in o.get("name", ""):
                                odd = float(o.get("price", 0))
                                matches.append({
                                    "source": "Stoiximan",
                                    "league": league,
                                    "match": match_name,
                                    "type": "O/U 2.5",
                                    "open": odd,
                                    "current": odd,
                                    "movement": 0.0,
                                })

            return {"matches": matches, "timestamp": time.strftime("%H:%M:%S")}

    except Exception as e:
        print("[STOIXIMAN_FETCH] ⚠️", e)
        return {"matches": []}


if __name__ == "__main__":
    data = asyncio.run(fetch_stoiximan_odds())
    print(json.dumps(data, indent=2, ensure_ascii=False))
