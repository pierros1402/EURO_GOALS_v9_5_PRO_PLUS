# ============================================================
# EURO_GOALS v9.5.4 PRO+ – Initialize goalmatrix.db
# ============================================================
import sqlite3
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "goalmatrix.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ------------------------------------------------------------
# Δημιουργία πίνακα matches
# ------------------------------------------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league TEXT,
    home_team TEXT,
    away_team TEXT,
    kickoff_utc TEXT,
    home_xg REAL,
    away_xg REAL,
    over_line REAL
)
""")

# ------------------------------------------------------------
# Εισαγωγή demo δεδομένων
# ------------------------------------------------------------
demo = [
    ("Premier League", "Arsenal", "Chelsea",
     datetime.utcnow().isoformat(), 1.8, 1.3, 2.5),
    ("Super League Greece", "Panathinaikos", "PAOK",
     datetime.utcnow().isoformat(), 1.4, 1.1, 2.5),
]
cur.executemany("""
INSERT INTO matches (league, home_team, away_team, kickoff_utc, home_xg, away_xg, over_line)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", demo)

conn.commit()
conn.close()
print("✅ goalmatrix.db created successfully with demo data.")
