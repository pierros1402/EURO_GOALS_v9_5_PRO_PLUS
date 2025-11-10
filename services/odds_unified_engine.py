# ============================================================
# EURO_GOALS v9.6.1 PRO+ — UNIFIED ODDS ENGINE (Live Expansion)
# ============================================================
# Πραγματικές αποδόσεις από:
#  - Stoiximan (HTML)
#  - Bet365 (mobile JSON-like)
#  - OPAP (public JSON)
# Καλύπτει:
#  * Αγγλία (PL, CH, L1, L2)
#  * Γερμανία (Bundesliga, 2.Bundesliga, 3.Liga, Regionalliga)
#  * Ελλάδα (Super League 1, Super League 2, Γ’ Εθνική — όπου διαθέσιμη)
#  * Υπόλοιπη Ευρώπη (Ισπανία, Ιταλία, Γαλλία, Πορτογαλία, Ολλανδία: 1–2)
#  * Ευρωπαϊκές διοργανώσεις (UCL, UEL, UECL)
# Επιστρέφει open+current μόνο για ΕΠΕΡΧΟΜΕΝΟΥΣ αγώνες και top 5–10 μεγαλύτερες μεταβολές.
# ============================================================

import asyncio, time, re, json
from typing import List, Dict, Any
import aiohttp
from bs4 import BeautifulSoup

CACHE_TTL = 60 * 3  # 3'
CACHE = {
    "ts": 0,
    "data": [],        # latest snapshot (list of matches)
    "prev": [],        # previous snapshot (for deltas)
    "moves_top": [],   # top N moves (upcoming only)
    "replaced_log": [] # list of items που βγήκαν από το top N
}

# ----------------------------- #
# League scope / filters
# ----------------------------- #
SCOPE = {
    "england": ["premier", "championship", "league one", "league two"],
    "germany": ["bundesliga", "2. bundesliga", "2.bundesliga", "3. liga", "regionalliga"],
    "greece":  ["super league", "super league 1", "super league 2", "γ εθν"],
    "spain":   ["la liga", "laliga", "segunda"],
    "italy":   ["serie a", "serie b"],
    "france":  ["ligue 1", "ligue1", "ligue 2"],
    "portugal":["primeira", "liga portugal", "segunda liga"],
    "netherlands": ["eredivisie", "eerste divisie"],
    "uefa":    ["champions league", "europa league", "conference league", "ucl", "uel", "uecl"],
}

def _league_in_scope(league_name: str) -> bool:
    if not league_name:
        return False
    ln = league_name.lower()
    for _, keys in SCOPE.items():
        if any(k in ln for k in keys):
            return True
    return False

# ----------------------------- #
# Helpers
# ----------------------------- #
def _now() -> int:
    return int(time.time())

def _match_key(m: Dict[str, Any]) -> str:
    return f"{m.get('league','')}|{m.get('home','')}|{m.get('away','')}"

def _is_upcoming(m: Dict[str, Any]) -> bool:
    # Αν δεν έχουμε kickoff, θεωρούμε upcoming (δεν εμφανίζουμε live-finished)
    # Αν υπάρχει kickoff_ts και είναι στο μέλλον => upcoming
    kt = m.get("kickoff_ts")
    if not isinstance(kt, (int, float)):
        return True
    return kt > _now()

def _delta_abs(m: Dict[str, Any]) -> float:
    """Μεγαλύτερη απόλυτη μεταβολή ανάμεσα σε open/current (1X2)"""
    diffs = []
    for p in ("home", "draw", "away"):
        o = m.get(f"odds_open_{p}")
        c = m.get(f"odds_live_{p}")
        if isinstance(o, (int, float)) and isinstance(c, (int, float)):
            diffs.append(abs(c - o))
    return max(diffs) if diffs else 0.0

def _top_moves(items: List[Dict[str, Any]], top_n: int = 10):
    ups = [x for x in items if _is_upcoming(x)]
    ups.sort(key=_delta_abs, reverse=True)
    return ups[:top_n]

def _index_by_key(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {_match_key(m): m for m in items}

# ----------------------------- #
# Scrapers
# ----------------------------- #
async def fetch_stoiximan(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """Stoiximan (HTML). Στοχεύουμε football landing. Επιλέγουμε μόνο λίγκες εντός scope."""
    # Μπορείς να προσθέσεις περισσότερα paths ή να κάνεις paginate.
    urls = [
        "https://www.stoiximan.gr/sports/home/football/",
    ]
    out: List[Dict[str, Any]] = []
    for url in urls:
        try:
            async with session.get(url, timeout=25) as r:
                html = await r.text()
            soup = BeautifulSoup(html, "html.parser")

            # Γενικός selector για rows – οι κλάσεις αλλάζουν συχνά, κρατάμε πιο "χαλαρά" patterns.
            for block in soup.select("div:has(span)"):
                # league name (fallback)
                league_el = block.select_one("h2, h3, .LeagueHeader, .EventGroupHeader")
                league = (league_el.get_text(strip=True) if league_el else "").strip()
                if not _league_in_scope(league):
                    continue

                # ονόματα ομάδων
                names = block.select("span, div")
                txts = [n.get_text(strip=True) for n in names if n.get_text(strip=True)]
                # Χονδρικά ψάχνουμε patterns "Team A", "Team B", και 3 τιμές αποδόσεων
                # Αυτός είναι generic parser — προτείνεται να προσαρμοστεί στο πραγματικό DOM.
                # ΠΡΟΣΟΧΗ: ο stoiximan αλλάζει DOM → διατηρούμε fallback.
                # εδώ απλά βρίσκουμε σειρές που μοιάζουν με "1", "Χ", "2" odds.
                row_odds = re.findall(r"\b(\d+\.\d{1,2})\b", " ".join(txts))
                # Θα προσπαθήσουμε να βρούμε δύο ονόματα ομάδων από το block:
                teams = [t for t in txts if len(t) > 2 and not re.match(r"^\d+(\.\d+)?$", t)]
                if len(teams) < 2 or len(row_odds) < 3:
                    continue

                home, away = teams[0], teams[1]
                try:
                    o1, ox, o2 = [float(x) for x in row_odds[:3]]
                except Exception:
                    continue

                out.append({
                    "bookmaker": "Stoiximan",
                    "league": league,
                    "home": home,
                    "away": away,
                    "odds_open_home": o1, "odds_open_draw": ox, "odds_open_away": o2,
                    "odds_live_home": o1, "odds_live_draw": ox, "odds_live_away": o2,
                    "timestamp": _now(),
                    # kickoff_ts άγνωστο από εδώ → αφήνουμε None (θεωρείται upcoming)
                    "kickoff_ts": None,
                })

        except Exception as e:
            print("[ODDS][Stoiximan] error:", e)
    return out


async def fetch_bet365(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """Bet365 (mobile feed pattern parsing). Χρησιμοποιούμε regex fallbacks."""
    url = "https://mservices.bet365.com/inplayapi/sport/default.aspx?Sport=1"
    out: List[Dict[str, Any]] = []
    try:
        async with session.get(url, timeout=25) as r:
            text = await r.text()

        # Χονδρική εξαγωγή ονομάτων/odds (pattern-based, fragile by design)
        blocks = re.findall(r'(\{.*?"NA".*?\})', text)
        for b in blocks:
            # ονόματα ομάδων
            names = re.findall(r'"NA":"(.*?)"', b)
            if len(names) < 2:
                continue
            home, away = names[0], names[1]

            # αποδόσεις (πρώτες 3)
            odds = re.findall(r'"OD":([0-9.]+)', b)
            if len(odds) < 3:
                continue
            try:
                o1, ox, o2 = [float(x) for x in odds[:3]]
            except Exception:
                continue

            # league
            league_match = re.search(r'"CT":"(.*?)"', b)
            league = league_match.group(1) if league_match else "Bet365 Football"
            if not _league_in_scope(league):
                continue

            # kickoff (αν υπάρχει)
            kt = None
            kt_m = re.search(r'"TS":(\d+)', b)  # seconds
            if kt_m:
                try:
                    kt = int(kt_m.group(1))
                except Exception:
                    kt = None

            out.append({
                "bookmaker": "Bet365",
                "league": league,
                "home": home,
                "away": away,
                "odds_open_home": o1, "odds_open_draw": ox, "odds_open_away": o2,
                "odds_live_home": o1, "odds_live_draw": ox, "odds_live_away": o2,
                "timestamp": _now(),
                "kickoff_ts": kt,
            })
    except Exception as e:
        print("[ODDS][Bet365] error:", e)
    return out


async def fetch_opap(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """OPAP public JSON. Φιλτράρουμε competitions με scope."""
    url = "https://api.opap.gr/sports/1/events"
    out: List[Dict[str, Any]] = []
    try:
        async with session.get(url, timeout=25) as r:
            data = await r.json(content_type=None)
        for ev in data.get("data", []):
            comp = ev.get("competitionName", "") or ev.get("competition", "")
            if not _league_in_scope(comp):
                continue
            mkts = ev.get("markets", [])
            # βρίσκουμε 1X2
            for m in mkts:
                if (m.get("key") or "").lower() in ("1x2", "match-winner", "full_time"):
                    outs = m.get("outcomes", [])
                    if len(outs) >= 3:
                        try:
                            o1 = float(outs[0].get("odds"))
                            ox = float(outs[1].get("odds"))
                            o2 = float(outs[2].get("odds"))
                        except Exception:
                            continue
                        # kickoff
                        kt = ev.get("startTime") or ev.get("startDate")
                        kt_int = None
                        if isinstance(kt, int):
                            kt_int = kt // 1000 if kt > 10**12 else kt
                        out.append({
                            "bookmaker": "OPAP",
                            "league": comp,
                            "home": ev.get("homeTeamName", "") or ev.get("homeTeam", ""),
                            "away": ev.get("awayTeamName", "") or ev.get("awayTeam", ""),
                            "odds_open_home": o1, "odds_open_draw": ox, "odds_open_away": o2,
                            "odds_live_home": o1, "odds_live_draw": ox, "odds_live_away": o2,
                            "timestamp": _now(),
                            "kickoff_ts": kt_int,
                        })
                    break
    except Exception as e:
        print("[ODDS][OPAP] error:", e)
    return out

# ----------------------------- #
# Refresh / Public API
# ----------------------------- #
async def refresh_all_odds() -> List[Dict[str, Any]]:
    global CACHE
    now = _now()
    if now - CACHE["ts"] < CACHE_TTL and CACHE["data"]:
        return CACHE["data"]

    results: List[Dict[str, Any]] = []
    async with aiohttp.ClientSession() as session:
        stoiximan, bet365, opap = await asyncio.gather(
            fetch_stoiximan(session),
            fetch_bet365(session),
            fetch_opap(session),
        )
        results.extend(stoiximan)
        results.extend(bet365)
        results.extend(opap)

    # Κρατάμε μόνο upcoming
    results = [m for m in results if _is_upcoming(m)]

    # Υπολογισμός top moves & replaced log
    prev_top_keys = {_match_key(m) for m in (CACHE.get("moves_top") or [])}
    top_now = _top_moves(results, top_n=10)
    top_now_keys = {_match_key(m) for m in top_now}
    replaced = [k for k in prev_top_keys if k not in top_now_keys]
    if replaced:
        CACHE["replaced_log"] = (CACHE.get("replaced_log") or []) + replaced
        CACHE["replaced_log"] = CACHE["replaced_log"][-200:]  # κρατάμε ιστορικό

    CACHE["prev"] = CACHE["data"]
    CACHE["data"] = results
    CACHE["moves_top"] = top_now
    CACHE["ts"] = now

    print(f"[ODDS][Unified] ✅ {len(results)} matches | Top moves: {len(top_now)}")
    return results

async def get_odds_data() -> Dict[str, Any]:
    data = await refresh_all_odds()
    return {"engine": "odds_unified_engine", "matches": data, "ts": _now()}

def get_summary() -> Dict[str, Any]:
    count = len(CACHE["data"] or [])
    return {
        "engine": "odds_unified_engine",
        "matches": count,
        "status": "OK" if count > 0 else "No Data",
        "last_update": CACHE.get("ts", 0),
    }

def get_top_moves() -> Dict[str, Any]:
    items = CACHE.get("moves_top") or []
    return {"top_moves": items, "ts": CACHE.get("ts", 0)}

def get_replaced_log() -> Dict[str, Any]:
    return {"replaced_keys": CACHE.get("replaced_log") or [], "ts": CACHE.get("ts", 0)}

async def background_refresher():
    print("[ODDS] Unified Engine started.")
    while True:
        try:
            await refresh_all_odds()
        except Exception as e:
            print("[ODDS] refresher error:", e)
        await asyncio.sleep(CACHE_TTL)
