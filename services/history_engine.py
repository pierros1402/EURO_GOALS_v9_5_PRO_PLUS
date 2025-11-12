# ============================================================
# EURO_GOALS — HISTORY ENGINE v1.0 (10y datasets)
# ============================================================
# Αρμοδιότητες:
# - Φόρτωση ιστορικών δεδομένων 10 ετών ανά λίγκα
# - Standings by date  (live "as-of" snapshot)
# - Last-5 ανά ομάδα (form)
# - Head-to-Head (H2H)
# - Schedule window: date-7 … date+7
# - Lightweight cache + ανεκτικότητα σε ελλιπή αρχεία
# ------------------------------------------------------------
# Δομή αρχείων (παράδειγμα):
# data/history/<league_code>/
#   seasons/2016.json, ..., 2025.json      (matches list)
#   standings/2016.json, ..., 2025.json    (table snapshots per round/date)
# league_code π.χ.: "england/premier-league", "greece/super-league"
# ============================================================

from __future__ import annotations
import os, json, time, datetime as dt
from typing import Dict, List, Any, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(os.path.dirname(BASE_DIR), "data", "history")

CACHE_TTL = int(os.getenv("HISTORY_CACHE_TTL", "900"))
_cache: Dict[str, Any] = {}
_cache_ts: Dict[str, float] = {}

def _cache_get(k: str):
    ts = _cache_ts.get(k, 0.0)
    if time.time() - ts < CACHE_TTL:
        return _cache.get(k)
    return None

def _cache_set(k: str, v: Any):
    _cache[k] = v
    _cache_ts[k] = time.time()

def _parse_date(s: str) -> dt.date:
    # αναμένουμε "YYYY-MM-DD"
    return dt.datetime.strptime(s[:10], "%Y-%m-%d").date()

def _season_years(around: dt.date) -> List[int]:
    # κρατά 10 σεζόν γύρω από το έτος του around (τρέχουσα σεζόν inclusive)
    y = around.year
    return list(range(y-9, y+1))

def _league_paths(league: str) -> Dict[str, str]:
    root = os.path.join(DATA_ROOT, league.replace("..","").strip("/"))
    return {
        "root": root,
        "seasons": os.path.join(root, "seasons"),
        "standings": os.path.join(root, "standings")
    }

def _safe_load_json(path: str) -> Any:
    key = f"file:{path}"
    hit = _cache_get(key)
    if hit is not None:
        return hit
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _cache_set(key, data)
        return data
    except Exception:
        return None

# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def get_match_context(
    league: str,
    home: str,
    away: str,
    date_iso: str,
    window_back: int = 7,
    window_fwd: int = 7,
) -> Dict[str, Any]:
    """
    Επιστρέφει ενοποιημένο match-center payload:
    - standings_as_of
    - last5_home / last5_away
    - h2h (τελευταία 10)
    - schedule_window (prev/next 7 ημέρες)
    - goal_diffs (home/away συνολικά, as-of)
    """
    asof = _parse_date(date_iso)
    seasons, standings = _load_10y(league, asof)
    matches_all = _flatten_matches(seasons)

    # 1) Standing snapshot as-of
    table = _standings_as_of(standings, asof)

    # 2) Last-5 per team (μέχρι as-of, αγώνες της λίγκας)
    last5_home = _last_n_form(matches_all, home, asof, n=5)
    last5_away = _last_n_form(matches_all, away, asof, n=5)

    # 3) H2H (τελευταίοι 10 αγώνες home vs away, όλες οι διοργανώσεις αυτής της λίγκας)
    h2h = _h2h(matches_all, home, away, asof, n=10)

    # 4) Schedule window (prev/next 7d)
    window = _window(matches_all, asof, window_back, window_fwd, teams=[home, away])

    # 5) Goal diffs από standings (as-of)
    gd_home, pts_home, pos_home = _team_snapshot(table, home)
    gd_away, pts_away, pos_away = _team_snapshot(table, away)

    return {
        "league": league,
        "match": {"home": home, "away": away, "date": str(asof)},
        "standings_as_of": table,
        "home": {
            "team": home,
            "position": pos_home,
            "points": pts_home,
            "goal_diff": gd_home,
            "last5": last5_home
        },
        "away": {
            "team": away,
            "position": pos_away,
            "points": pts_away,
            "goal_diff": gd_away,
            "last5": last5_away
        },
        "h2h": h2h,
        "schedule_window": window
    }

# ------------------------------------------------------------
# Internals
# ------------------------------------------------------------

def _load_10y(league: str, asof: dt.date) -> Tuple[Dict[int, Any], Dict[int, Any]]:
    paths = _league_paths(league)
    years = _season_years(asof)
    seasons: Dict[int, Any] = {}
    standings: Dict[int, Any] = {}
    for y in years:
        s_path = os.path.join(paths["seasons"], f"{y}.json")
        t_path = os.path.join(paths["standings"], f"{y}.json")
        s = _safe_load_json(s_path) or []
        t = _safe_load_json(t_path) or {}
        seasons[y] = s
        standings[y] = t
    return seasons, standings

def _flatten_matches(seasons: Dict[int, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for y, lst in seasons.items():
        if not isinstance(lst, list):
            continue
        for m in lst:
            try:
                # Αναμενόμενα πεδία: date, home, away, hs, as, status, round
                m2 = {
                    "date": m.get("date"),
                    "home": m.get("home"),
                    "away": m.get("away"),
                    "hs": m.get("hs"),
                    "as": m.get("as"),
                    "status": m.get("status", "FT"),
                    "round": m.get("round"),
                    "season": y,
                }
                out.append(m2)
            except Exception:
                continue
    out.sort(key=lambda x: (x["date"] or "", x["home"] or "", x["away"] or ""))
    return out

def _standings_as_of(standings_years: Dict[int, Any], asof: dt.date) -> List[Dict[str, Any]]:
    """
    standings file format (per season JSON):
    {
      "snapshots": [
        { "date": "YYYY-MM-DD", "table": [ { "team": "...", "pts": 32, "gd": +10, "pos": 3 }, ... ] },
        ...
      ]
    }
    Επιλέγουμε το πιο κοντινό snapshot <= asof
    """
    snapshots: List[Tuple[dt.date, List[Dict[str, Any]]]] = []
    for y, blob in standings_years.items():
        snaps = (blob or {}).get("snapshots", [])
        for s in snaps:
            try:
                d = _parse_date(s.get("date"))
                snapshots.append((d, s.get("table", [])))
            except Exception:
                pass
    snapshots.sort(key=lambda x: x[0])
    chosen: List[Dict[str, Any]] = []
    for d, table in snapshots:
        if d <= asof:
            chosen = table
        else:
            break
    # normalise / fill
    out = []
    for row in (chosen or []):
        out.append({
            "team": row.get("team"),
            "pts": row.get("pts"),
            "gd": row.get("gd"),
            "pos": row.get("pos"),
            "p": row.get("p"),
            "w": row.get("w"),
            "d": row.get("d"),
            "l": row.get("l")
        })
    return out

def _last_n_form(matches: List[Dict[str,Any]], team: str, asof: dt.date, n: int=5) -> List[Dict[str, Any]]:
    played = []
    for m in matches:
        try:
            d = _parse_date(m["date"])
        except Exception:
            continue
        if d > asof:  # μόνο μέχρι as-of
            continue
        if m["home"] == team or m["away"] == team:
            res = _result_for_team(m, team)
            played.append({
                "date": m["date"],
                "opponent": m["away"] if m["home"] == team else m["home"],
                "res": res,  # "W/D/L"
                "score": f'{m.get("hs","")}-{m.get("as","")}',
            })
    played.sort(key=lambda x: x["date"], reverse=True)
    return played[:n]

def _result_for_team(m: Dict[str,Any], team: str) -> str:
    try:
        hs, aS = int(m.get("hs", 0) or 0), int(m.get("as", 0) or 0)
    except Exception:
        return "-"
    if m.get("status","FT") != "FT":
        return "-"
    if m["home"] == team:
        if hs > aS: return "W"
        if hs < aS: return "L"
        return "D"
    else:
        if aS > hs: return "W"
        if aS < hs: return "L"
        return "D"

def _h2h(matches: List[Dict[str,Any]], a: str, b: str, asof: dt.date, n: int=10) -> List[Dict[str,Any]]:
    out = []
    for m in matches:
        try:
            d = _parse_date(m["date"])
        except Exception:
            continue
        if d > asof:  # μόνο παρελθόν
            continue
        if {m["home"], m["away"]} == {a, b}:
            out.append({
                "date": m["date"],
                "home": m["home"],
                "away": m["away"],
                "score": f'{m.get("hs","")}-{m.get("as","")}',
                "res_home": _result_for_team(m, m["home"])
            })
    out.sort(key=lambda x: x["date"], reverse=True)
    return out[:n]

def _window(matches: List[Dict[str,Any]], center: dt.date, back: int, fwd: int, teams: Optional[List[str]]=None) -> Dict[str, List[Dict[str,Any]]]:
    start = center - dt.timedelta(days=back)
    end   = center + dt.timedelta(days=fwd)
    prev, next_ = [], []
    for m in matches:
        try:
            d = _parse_date(m["date"])
        except Exception:
            continue
        if d < start or d > end:
            continue
        if teams and not (m["home"] in teams or m["away"] in teams):
            continue
        bucket = prev if d <= center else next_
        bucket.append({
            "date": m["date"],
            "home": m["home"],
            "away": m["away"],
            "score": f'{m.get("hs","")}-{m.get("as","")}' if m.get("status","")=="FT" else None
        })
    prev.sort(key=lambda x: x["date"])
    next_.sort(key=lambda x: x["date"])
    return {"prev": prev, "next": next_}

def _team_snapshot(table: List[Dict[str,Any]], team: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    for row in table:
        if (row.get("team") or "").lower() == team.lower():
            return row.get("gd"), row.get("pts"), row.get("pos")
    return None, None, None
