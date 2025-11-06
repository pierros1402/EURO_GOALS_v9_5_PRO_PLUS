# ============================================================
# EURO_GOALS v9.5.4 PRO+ — Database Initializer for matches.db
# ============================================================
import sqlite3
from datetime import datetime

DB_PATH = "goalmatrix.db"

schema = """
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_xg REAL,
    away_xg REAL,
    over_line REAL,
    kickoff_utc TEXT,
    updated_at TEXT
);
"""

demo_data = [
    (
        "Premier League",
        "Arsenal",
        "Chelsea",
        1.62,
        1.10,
        2.5,
        "2025-11-06T19:30:00Z",
        datetime.utcnow().isoformat()
    ),
    (
        "Super League Greece",
        "Panathinaikos",
        "PAOK",
        1.35,
        1.20,
        2.25,
        "2025-11-06T20:00:00Z",
        datetime.utcnow().isoformat()
    )
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(schema)
    conn.commit()

    # Check if table already has data
    cursor.execute("SELECT COUNT(*) FROM matches;")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.executemany("""
            INSERT INTO matches
            (league, home_team, away_team, home_xg, away_xg, over_line, kickoff_utc, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, demo_data)
        conn.commit()
        print(f"✅ Demo matches inserted ({len(demo_data)} rows).")
    else:
        print("ℹ️ Table already has data, no inserts made.")

    cursor.close()
    conn.close()
    print("✅ Database initialized successfully.")


if __name__ == "__main__":
    init_db()
