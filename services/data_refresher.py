# ============================================================
# EURO_GOALS DATA REFRESHER ENGINE — v9.7.5 PRO+ (Unified Layer)
# ============================================================
# Αυτόματο σύστημα παρακολούθησης και επανεκκίνησης
# του background loop SmartMoney + GoalMatrix
# ------------------------------------------------------------
# Τρέχει μαζί με τη main (auto_refresh_loop), ελέγχει την υγεία του
# και διασφαλίζει ότι το σύστημα συνεχίζει να ανανεώνεται ακόμα κι αν
# υπάρξει προσωρινό σφάλμα στο Cloudflare Worker ή στα APIs.
# ============================================================

import asyncio, time, requests, traceback
from services import smartmoney_engine, goal_matrix_engine

WORKER_BASE = (os.getenv("SMARTMONEY_WORKER_URL", "") or "").rstrip("/")
REFRESH_INTERVAL = 180   # 3 λεπτά
HEALTH_CHECK_INTERVAL = 600  # 10 λεπτά
_last_run = 0

# ------------------------------------------------------------
# HELPER — GET MATCH IDS FROM WORKER
# ------------------------------------------------------------
def get_active_matches():
    """
    Ενοποιεί ενεργά match IDs από Betfair + Bet365 + Stoiximan + OPAP
    μέσω του Cloudflare Worker.
    """
    matches = set()
    if not WORKER_BASE:
        return ["12345", "23456", "34567"]

    sources = {
        "betfair": "/betfair/markets",
        "bet365":  "/bet365/odds?match=1",
        "stoiximan": "/stoiximan/odds?match=1",
        "opap": "/opap/odds?match=1"
    }

    try:
        # --- Betfair Markets (κύρια πηγή IDs)
        r = requests.get(f"{WORKER_BASE}{sources['betfair']}", timeout=10)
        if r.ok:
            data = r.json()
            for m in data.get("markets", []):
                if mid := m.get("marketId"):
                    matches.add(mid)
    except Exception as e:
        print("[EURO_GOALS] ⚠️ Cannot load Betfair markets:", e)

    # --- Optional quick reach test για άλλες πηγές
    for key, path in sources.items():
        if key == "betfair":
            continue
        try:
            test_url = f"{WORKER_BASE}{path}"
            r = requests.get(test_url, timeout=6)
            if r.ok:
                matches.add(key.upper() + "_TEST")
        except Exception as e:
            print(f"[EURO_GOALS] ⚠️ {key} unreachable:", e)

    if not matches:
        matches = {"12345", "23456", "34567"}
    return list(matches)

# ------------------------------------------------------------
# MAIN REFRESH LOOP
# ------------------------------------------------------------
async def start_refresher():
    global _last_run
    print("[EURO_GOALS] 🔁 DataRefresher engine started (interval:", REFRESH_INTERVAL, "sec)")
    while True:
        try:
            matches = get_active_matches()
            print(f"[EURO_GOALS] 🔄 Refreshing {len(matches)} matches...")

            for match_id in matches:
                try:
                    sm = smartmoney_engine.get_odds_snapshot(match_id)
                    gm = goal_matrix_engine.get_goal_matrix(match_id)
                    print(f"[EURO_GOALS] ✅ Match {match_id} refreshed | Sources={sm.get('sources')}")
                except Exception as sub_e:
                    print(f"[EURO_GOALS] ⚠️ Sub-refresh failed for {match_id}:", sub_e)

            _last_run = time.time()
            print("[EURO_GOALS] 🕒 Cycle complete |", time.strftime("%H:%M:%S"))
        except Exception as e:
            print("[EURO_GOALS] ❌ Refresher loop error:", e)
            traceback.print_exc()
        await asyncio.sleep(REFRESH_INTERVAL)

# ------------------------------------------------------------
# WATCHDOG — HEALTH MONITOR
# ------------------------------------------------------------
async def refresher_health_monitor():
    """
    Παρακολουθεί τον κύκλο ανανέωσης και αν καθυστερήσει >15 λεπτά,
    επανεκκινεί αυτόματα το refresher loop.
    """
    global _last_run
    print("[EURO_GOALS] 🧠 Refresher watchdog active (interval:", HEALTH_CHECK_INTERVAL, "sec)")
    while True:
        try:
            if _last_run > 0:
                delta = time.time() - _last_run
                if delta > 900:  # 15 λεπτά χωρίς νέο κύκλο
                    print("[EURO_GOALS] ⚠️ Refresher seems stuck, restarting loop...")
                    asyncio.create_task(start_refresher())
                    _last_run = time.time()
            await asyncio.sleep(HEALTH_CHECK_INTERVAL)
        except Exception as e:
            print("[EURO_GOALS] ❌ Watchdog error:", e)
            await asyncio.sleep(HEALTH_CHECK_INTERVAL)
