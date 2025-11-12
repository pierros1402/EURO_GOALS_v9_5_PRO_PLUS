# ============================================================
# EURO_GOALS Data Refresher — v9.9.0 PRO+
# - Pulls Flashscore HTML via Worker
# - Parses standings & fixtures
# - Saves 10y snapshots under /data/history/<league>/
# - Safe fallbacks + logging
# ============================================================

import os, time, json, asyncio, requests, datetime as dt
from typing import Dict, Any, List
from services.flashscore_parser import parse_standings_html, parse_fixtures_html

WORKER_BASE = os.getenv("SMARTMONEY_WORKER_URL", "").rstrip("/")
REFRESH_INTERVAL = int(os.getenv("AUTO_REFRESH_INTERVAL", "180"))
HISTORY_CACHE_TTL = int(os.getenv("HISTORY_CACHE_TTL", "900"))

DATA_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "history")
os.makedirs(DATA_ROOT, exist_ok=True)

def _league_paths(league: str) -> Dict[str, str]:
    root = os.path.join(DATA_ROOT, league)
    paths = {
        "root": root,
        "seasons": os.path.join(root, "seasons"),
        "standings": os.path.join(root, "standings")
    }
    for p in paths.values():
        os.makedirs(p, exist_ok=True)
    return paths

def _years_10(asof: dt.date) -> List[int]:
    y = asof.year
    return list(range(y-9, y+1))

def _save_json(path: str, data: Any):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[EURO_GOALS] ❌ save_json {path}: {e}")
        return False

def _fetch_html(endpoint: str, params: Dict[str, Any]) -> str:
    if not WORKER_BASE:
        print("[EURO_GOALS] ⚠️ Worker base not set")
        return ""
    try:
        r = requests.get(f"{WORKER_BASE}{endpoint}", params=params, timeout=12)
        if r.status_code == 200:
            return r.text
        print(f"[EURO_GOALS] ⚠️ HTML fetch {endpoint} {params} -> {r.status_code}")
        return ""
    except Exception as e:
        print(f"[EURO_GOALS] ❌ HTML fetch error {endpoint}: {e}")
        return ""

async def refresh_league_flashscore(league_slug: str):
    """
    league_slug παράδειγμα: 'football/england/premier-league'
    Αποθήκευση:
      data/history/football/england/premier-league/standings/YYYY.json
      data/history/football/england/premier-league/seasons/YYYY.json
    """
    asof = dt.date.today()
    paths = _league_paths(league_slug)

    print(f"[EURO_GOALS] 📥 Flashscore pull: {league_slug}")

    # --- Standings (HTML → parse → snapshot)
    html_stand = _fetch_html("/flashscore/standings", {"league": league_slug})
    table = parse_standings_html(html_stand)
    if table:
        snap = {"snapshots": [{"date": str(asof), "table": table}]}
        _save_json(os.path.join(paths["standings"], f"{asof.year}.json"), snap)
        print(f"[EURO_GOALS] ✅ Standings {league_slug} saved ({asof.year}) [{len(table)} rows]")
    else:
        print(f"[EURO_GOALS] ⚠️ Standings parse empty for {league_slug}")

    # --- Fixtures/Results (HTML → parse → append to season)
    html_fix = _fetch_html("/flashscore/fixtures", {"league": league_slug})
    matches = parse_fixtures_html(html_fix)
    if matches:
        # append mode: φόρτωσε υπάρχον season file και συγχώνευσε/ανανέωσε
        season_path = os.path.join(paths["seasons"], f"{asof.year}.json")
        prev = []
        if os.path.exists(season_path):
            try:
                prev = json.load(open(season_path, "r", encoding="utf-8"))
            except Exception:
                prev = []
        merged = _merge_matches(prev, matches)
        _save_json(season_path, merged)
        print(f"[EURO_GOALS] ✅ Fixtures {league_slug} saved ({asof.year}) [{len(merged)} matches]")
    else:
        print(f"[EURO_GOALS] ⚠️ Fixtures parse empty for {league_slug}")

def _merge_matches(old: List[Dict[str, Any]], new: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ενώνει με βάση (home, away, date) — ενημερώνει σκορ/κατάσταση."""
    key = lambda m: (m.get("date"), m.get("home"), m.get("away"))
    mp = {key(m): m for m in old}
    for m in new:
        mp[key(m)] = {**mp.get(key(m), {}), **m}
    out = list(mp.values())
    out.sort(key=lambda x: (x.get("date") or "", x.get("home") or "", x.get("away") or ""))
    return out

# ------------------------------------------------------------
# BACKGROUND LOOP
# ------------------------------------------------------------
LEAGUES_FLASH = [
  # συμπλήρωσε σταδιακά — παράδειγμα:
  "football/england/premier-league",
  "football/germany/bundesliga",
  "football/greece/super-league",
  # πρόσθεσε κι άλλες...
]

async def start_background_refresh():
    print("[EURO_GOALS] 🚀 History Refresher (Flashscore) active")
    while True:
        for slug in LEAGUES_FLASH:
            try:
                await refresh_league_flashscore(slug)
            except Exception as e:
                print(f"[EURO_GOALS] ❌ league {slug}: {e}")
            await asyncio.sleep(0.5)
        print(f"[EURO_GOALS] ⏳ sleeping {REFRESH_INTERVAL}s…")
        await asyncio.sleep(REFRESH_INTERVAL)
