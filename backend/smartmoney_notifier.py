# ================================================
# EURO_GOALS v9.4.2 – SmartMoney Auto-Notifier PRO
# Real APIs: TheOddsAPI + SportMonks
# ================================================
import os
import time
import json
import math
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# ---------- ENV ----------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///matches.db")

THEODDSAPI_KEY = os.getenv("THEODDSAPI_KEY")
SPORTMONKS_API_KEY = os.getenv("SPORTMONKS_API_KEY")

REFRESH_SEC = int(os.getenv("SMARTMONEY_PRO_REFRESH", "60"))
ALERT_THRESHOLD = float(os.getenv("SMARTMONEY_PRO_ALERT_THRESHOLD", "0.05"))
SOURCES = [s.strip() for s in os.getenv("SMARTMONEY_PRO_SOURCES", "theoddsapi").split(",") if s.strip()]
REGIONS = os.getenv("SMARTMONEY_PRO_REGIONS", "eu").replace(" ", "")
MARKETS = os.getenv("SMARTMONEY_PRO_MARKETS", "h2h")
BOOKMAKERS = [b.strip() for b in os.getenv("SMARTMONEY_PRO_BOOKMAKERS", "bet365,betano,pinnacle").split(",") if b.strip()]

# bookmaker aliases mapping (to normalize names from aggregators)
BOOKMAKER_ALIASES = {
    "bet365": {"bet365", "Bet365", "BET365"},
    "betano": {"Betano", "BETANO", "Stoiximan", "STOIXIMAN"},
    "pinnacle": {"Pinnacle", "PINNACLE"},
    "williamhill": {"William Hill", "WilliamHill"},
    "unibet": {"Unibet"},
    "betfair": {"Betfair"},
    "opap": {"OPAP", "Pame Stoixima", "PameStoixima"},  # σπάνιο σε aggregators
}

def normalize_bookmaker(name: str) -> str:
    for norm, variants in BOOKMAKER_ALIASES.items():
        if name in variants or name.lower() == norm:
            return norm
    return name.lower().replace(" ", "")

# ---------- DB ----------
def get_engine() -> Engine:
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    return create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

engine = get_engine()

def init_tables():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS smartmoney_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_utc TEXT NOT NULL,
            source TEXT NOT NULL,
            sport_key TEXT,
            match_id TEXT,
            home TEXT,
            away TEXT,
            market TEXT,
            bookmaker TEXT,
            selection TEXT,
            old_price REAL,
            new_price REAL,
            change_pct REAL,
            note TEXT
        );
        """))
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS smartmoney_state (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """))

def save_alert(alert: Dict):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO smartmoney_alerts
            (ts_utc, source, sport_key, match_id, home, away, market, bookmaker, selection, old_price, new_price, change_pct, note)
            VALUES (:ts_utc, :source, :sport_key, :match_id, :home, :away, :market, :bookmaker, :selection, :old_price, :new_price, :change_pct, :note)
        """), alert)

def get_last_snapshot(key: str) -> Optional[Dict]:
    with engine.begin() as conn:
        row = conn.execute(text("SELECT value FROM smartmoney_state WHERE key = :k"), {"k": key}).fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return None

def set_last_snapshot(key: str, value: Dict):
    with engine.begin() as conn:
        val = json.dumps(value, ensure_ascii=False)
        conn.execute(text("""
            INSERT INTO smartmoney_state(key, value)
            VALUES (:k, :v)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """), {"k": key, "v": val})

# ---------- FETCHERS ----------
def fetch_theoddsapi_odds(sport_key: str = "soccer_epl") -> List[Dict]:
    """
    Docs: https://the-odds-api.com/
    """
    if not THEODDSAPI_KEY:
        return []
    url = (
        f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
        f"?apiKey={THEODDSAPI_KEY}&regions={REGIONS}&markets={MARKETS}&oddsFormat=decimal&dateFormat=iso"
    )
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []

def fetch_sportmonks_odds(league_id: Optional[int] = None) -> List[Dict]:
    """
    SportMonks odds feed (requires proper plan). We guard failures gracefully.
    Example endpoint (Odds by fixtures): /odds/ in soccer includes markets/bo
    """
    if not SPORTMONKS_API_KEY:
        return []
    # Using fixtures odds (pseudo-generalized due to plan variance)
    base = "https://api.sportmonks.com/v3/football/odds"
    params = {
        "api_token": SPORTMONKS_API_KEY,
        "include": "bookmaker,market,fixture.participants",
        "per_page": 50,
    }
    if league_id:
        params["filters"] = f"league_id:{league_id}"
    try:
        r = requests.get(base, params=params, timeout=25)
        r.raise_for_status()
        data = r.json()
        # normalize to a structure similar to TheOddsAPI list of events
        return data.get("data", [])
    except Exception:
        return []

# ---------- NORMALIZERS ----------
def theoddsapi_to_map(events: List[Dict]) -> Dict[str, Dict]:
    """
    Returns map: event_key -> {
      'home': str, 'away': str,
      'bookmakers': { norm_name: {'h2h': {selection->price}, 'totals': {...}, 'spreads': {...}} }
    }
    """
    out = {}
    for ev in events:
        key = ev.get("id") or ev.get("key") or f"{ev.get('sport_key','soccer')}::{ev.get('commence_time')}::{ev.get('home_team')}::{ev.get('away_team')}"
        home = ev.get("home_team") or ""
        away = ev.get("away_team") or ""
        bookies = {}
        for b in ev.get("bookmakers", []):
            bname = normalize_bookmaker(b.get("title", ""))
            if BOOKMAKERS and bname not in BOOKMAKERS:
                continue
            markets = {}
            for m in b.get("markets", []):
                mkey = m.get("key")  # h2h / totals / spreads
                sel_map = {}
                for o in m.get("outcomes", []):
                    name = o.get("name")
                    price = o.get("price")
                    if name and price:
                        sel_map[name] = float(price)
                if sel_map:
                    markets[mkey] = sel_map
            if markets:
                bookies[bname] = markets
        if bookies:
            out[key] = {"home": home, "away": away, "bookmakers": bookies, "sport_key": ev.get("sport_key", "soccer")}
    return out

def sportmonks_to_map(rows: List[Dict]) -> Dict[str, Dict]:
    """
    Highly simplified normalizer (SportMonks varies per plan).
    We map to: fixture_id -> {home, away, bookmakers -> markets(h2h/totals/spreads)->selection->price}
    """
    out = {}
    for r in rows:
        fixture = r.get("fixture") or r.get("fixture_id")
        if isinstance(fixture, dict):
            fid = str(fixture.get("id"))
            parts = fixture.get("participants", [])
            home, away = "", ""
            for p in parts:
                if p.get("meta", {}).get("location") == "home":
                    home = p.get("name", "")
                elif p.get("meta", {}).get("location") == "away":
                    away = p.get("name", "")
        else:
            fid = str(fixture)
            home, away = "", ""
        if not fid:
            continue

        b = r.get("bookmaker")
        market = r.get("market")
        price = r.get("price")
        selection = (r.get("label") or r.get("outcome") or "").strip()

        if not (b and market and price and selection):
            # attempt nested schema
            bname = normalize_bookmaker((b or {}).get("name", "")) if isinstance(b, dict) else normalize_bookmaker(str(b))
            mkey = (market or {}).get("key") if isinstance(market, dict) else str(market or "h2h")
            pr = float((price or {}).get("decimal", price or 0))
        else:
            bname = normalize_bookmaker(b if isinstance(b, str) else str(b))
            mkey = market if isinstance(market, str) else str(market)
            pr = float(price)

        if BOOKMAKERS and bname not in BOOKMAKERS:
            continue

        event = out.setdefault(fid, {"home": home, "away": away, "bookmakers": {}, "sport_key": "soccer"})
        markets = event["bookmakers"].setdefault(bname, {})
        msel = markets.setdefault(mkey, {})
        if pr:
            msel[selection] = pr
    return out

# ---------- DIFF / ALERTS ----------
def pct_drop(old: float, new: float) -> float:
    if not old or not new:
        return 0.0
    return (old - new) / old

def compare_and_alert(prev: Dict, curr: Dict, source: str):
    """
    Compare old vs new maps and emit alerts when price drops exceed ALERT_THRESHOLD.
    """
    for ev_key, ev in curr.items():
        home = ev.get("home", "")
        away = ev.get("away", "")
        sport_key = ev.get("sport_key", "soccer")
        prev_ev = prev.get(ev_key, {})
        for bname, markets in ev.get("bookmakers", {}).items():
            prev_markets = prev_ev.get("bookmakers", {}).get(bname, {})
            for mkey, sel_map in markets.items():
                prev_sel_map = prev_markets.get(mkey, {})
                for selection, new_price in sel_map.items():
                    old_price = prev_sel_map.get(selection)
                    if old_price and new_price < old_price:
                        drop = pct_drop(float(old_price), float(new_price))
                        if drop >= ALERT_THRESHOLD and drop > 0:
                            alert = {
                                "ts_utc": datetime.now(timezone.utc).isoformat(),
                                "source": source,
                                "sport_key": sport_key,
                                "match_id": ev_key,
                                "home": home,
                                "away": away,
                                "market": mkey,
                                "bookmaker": bname,
                                "selection": selection,
                                "old_price": float(old_price),
                                "new_price": float(new_price),
                                "change_pct": round(drop, 4),
                                "note": f"{bname} {mkey} {selection}: {old_price} -> {new_price}",
                            }
                            save_alert(alert)
                            push_sse(alert)

# ---------- SSE BUS ----------
_sse_clients: List[Tuple[float, "queue.Queue"]] = []
try:
    import queue
except Exception:
    queue = None

def register_client() -> "queue.Queue":
    q = queue.Queue()
    _sse_clients.append((time.time(), q))
    return q

def push_sse(payload: Dict):
    if not queue:
        return
    msg = f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    stale = []
    for i, (t0, q) in enumerate(_sse_clients):
        try:
            q.put_nowait(msg)
        except Exception:
            stale.append(i)
    # cleanup (best-effort)
    for idx in reversed(stale):
        _sse_clients.pop(idx)

# ---------- MAIN LOOP ----------
_running = False
_thread: Optional[threading.Thread] = None

def poll_once():
    # TheOddsAPI (example: Premier League + general EU soccer keys)
    sources = []
    if "theoddsapi" in SOURCES:
        # you can extend this list with more sport keys you cover
        for sport_key in ["soccer_epl", "soccer_uefa_champs_league", "soccer_germany_bundesliga", "soccer_spain_la_liga", "soccer_italy_serie_a", "soccer_greece_super_league"]:
            raw = fetch_theoddsapi_odds(sport_key=sport_key)
            m = theoddsapi_to_map(raw)
            sources.append(("theoddsapi", sport_key, m))

    if "sportmonks" in SOURCES:
        sm_rows = fetch_sportmonks_odds()
        m = sportmonks_to_map(sm_rows)
        sources.append(("sportmonks", "soccer", m))

    # compare with previous snapshots
    for src_name, part_key, curr_map in sources:
        snap_key = f"snap::{src_name}::{part_key}"
        prev_map = get_last_snapshot(snap_key) or {}
        compare_and_alert(prev_map, curr_map, src_name)
        set_last_snapshot(snap_key, curr_map)

def loop_forever():
    init_tables()
    while _running:
        try:
            poll_once()
        except Exception as e:
            # push lightweight error event
            push_sse({"ts_utc": datetime.now(timezone.utc).isoformat(), "source": "smartmoney", "error": str(e)})
        time.sleep(max(10, REFRESH_SEC))

def start():
    global _running, _thread
    if _running:
        return
    _running = True
    _thread = threading.Thread(target=loop_forever, name="SmartMoneyPRO", daemon=True)
    _thread.start()

def stop():
    global _running, _thread
    _running = False
    if _thread:
        _thread.join(timeout=2.0)
        _thread = None
