# ============================================================
# OPAP / Πάμε Στοίχημα LIVE ODDS FETCHER v1.1
# ------------------------------------------------------------
# Παίρνει τιμές από το web API του pamestoixima.gr
# Προσθέτει source="OPAP"
# ============================================================

import httpx, json, asyncio, time

OPAP_FEED_URL = "https://www.pamestoixima.gr/web/services/odds"

async def fetch_opap_odds():
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.get(OPAP_FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
            data = res.json()

            matches = []
            for event in data.get("events", []):
                league = event.get("competition", {}).get("name", "Unknown League")
                match_name = f"{event.get('homeTeam', '')} - {event.get('awayTeam', '')}"

                markets = event.get("markets", [])
                for market in markets:
                    name = market.get("name", "")
                    outcomes = market.get("selections", [])

                    # 1X2
                    if name.lower() in ["1x2", "τελικό αποτέλεσμα"]:
                        for o in outcomes:
                            if o.get("name") == "1":
                                odd = float(o.get("price", 0))
                                matches.append({
                                    "source": "OPAP",
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
                                    "source": "OPAP",
                                    "league": league,
                                    "match": match_name,
                                    "type": "O/U 2.5",
                                    "open": odd,
                                    "current": odd,
                                    "movement": 0.0,
                                })

            return {"matches": matches, "timestamp": time.strftime("%H:%M:%S")}

    except Exception as e:
        print("[OPAP_FETCH] ⚠️", e)
        return {"matches": []}


if __name__ == "__main__":
    out = asyncio.run(fetch_opap_odds())
    print(json.dumps(out, indent=2, ensure_ascii=False))
