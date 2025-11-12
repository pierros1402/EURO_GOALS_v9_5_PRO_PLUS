# ============================================================
# EURO_GOALS — Flashscore Parser v1.0
# Standings / Fixtures / Match Summary (robust + fallbacks)
# ============================================================

from __future__ import annotations
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re

# -------------------------
# Standings
# -------------------------
def parse_standings_html(html: str) -> List[Dict[str, Any]]:
    """
    Επιστρέφει λίστα από rows: {pos, team, p, w, d, l, gf, ga, gd, pts}
    """
    out: List[Dict[str, Any]] = []
    if not html:
        return out

    soup = BeautifulSoup(html, "html.parser")

    # Heuristic 1: πίνακες με headers που μοιάζουν σε standings
    tables = soup.find_all("table")
    for tbl in tables:
        header_text = " ".join((tbl.find("thead") or tbl).get_text(" ", strip=True).lower().split())
        if any(k in header_text for k in ["pos", "team", "pts", "w", "d", "l"]) or "standings" in header_text:
            body = tbl.find("tbody") or tbl
            for tr in body.find_all("tr"):
                tds = [td.get_text(" ", strip=True) for td in tr.find_all(["td","th"])]
                if len(tds) < 5:
                    continue
                row = _row_from_cells(tds)
                if row:
                    out.append(row)
            if out:
                return out

    # Heuristic 2: regex σε γραμμές που μοιάζουν με standings
    for m in re.finditer(r"(\d+)\s+([A-Za-zΑ-Ωα-ω .'\-]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([+\-]?\d+)\s+(\d+)", html):
        try:
            pos, team, p, w, d, l, gd, pts = m.groups()
            out.append({
                "pos": int(pos), "team": team.strip(),
                "p": int(p), "w": int(w), "d": int(d), "l": int(l),
                "gf": None, "ga": None, "gd": int(gd), "pts": int(pts)
            })
        except Exception:
            pass

    return out

def _row_from_cells(cells: List[str]) -> Optional[Dict[str, Any]]:
    """
    Προσπαθεί να χαρτογραφήσει δυναμικά κελιά standings σε δομή.
    Common patterns: [Pos, Team, P, W, D, L, GF, GA, GD, Pts]
    """
    try:
        # Βρες πρώτο int = θέση
        pos_idx = next(i for i,c in enumerate(cells) if re.fullmatch(r"\d+", c))
        pos = int(cells[pos_idx])
    except Exception:
        return None

    # Θεώρησε team = το επόμενο string (μη-αριθμητικό)
    team = None
    for i in range(pos_idx+1, min(len(cells), pos_idx+4)):
        if not re.fullmatch(r"[+\-]?\d+", cells[i]):
            team = cells[i]
            team_idx = i
            break
    if not team:
        return None

    # μάζεψε τα υπόλοιπα ως αριθμούς
    nums = [c for c in cells[team_idx+1:] if re.fullmatch(r"[+\-]?\d+", c)]
    # πάρε τα τελευταία 6-7 για w/d/l/gf/ga/gd/pts ή p/w/d/l/gd/pts
    nums = list(map(int, nums[-7:])) if len(nums) >= 7 else list(map(int, nums[-6:]))

    row = {"pos": pos, "team": team, "p": None, "w": None, "d": None, "l": None, "gf": None, "ga": None, "gd": None, "pts": None}
    # Γέμισμα από το τέλος προς την αρχή
    fields_pref = ["pts", "gd", "ga", "gf", "l", "d", "w", "p"]
    for v, k in zip(reversed(nums), fields_pref):
        row[k] = v
    return row

# -------------------------
# Fixtures / Results list
# -------------------------
def parse_fixtures_html(html: str) -> List[Dict[str, Any]]:
    """
    Επιστρέφει λίστα αντικειμένων: {date, home, away, hs, as, status}
    - Αν ο αγώνας είναι προγραμματισμένος, hs/as=None, status="NS"
    - Αν έχει λήξει, status="FT" και γεμίζουν hs/as
    """
    out: List[Dict[str, Any]] = []
    if not html:
        return out
    soup = BeautifulSoup(html, "html.parser")

    # Αναζήτηση blocks με ομάδες/ημερομηνίες
    # Χαλαρό pattern: βρίσκουμε γραμμές με τύπο "Home - Away" και δίπλα score ή ώρα
    text = soup.get_text("\n", strip=True)
    lines = [l for l in text.split("\n") if l.strip()]
    for i, line in enumerate(lines):
        # αναγνώριση score π.χ. "2 - 1" ή "1:1"
        score_m = re.search(r"(\d+)\s*[-:]\s*(\d+)", line)
        if score_m and i > 0:
            home_away = lines[i-1]
            # προσπαθούμε να σπάσουμε σε δύο ομάδες
            parts = re.split(r"\s+-\s+|\s+vs\s+|\s+–\s+", home_away)
            if len(parts) == 2:
                hs, aS = score_m.groups()
                out.append({
                    "date": None, "home": parts[0].strip(), "away": parts[1].strip(),
                    "hs": int(hs), "as": int(aS), "status": "FT"
                })
        else:
            # scheduled line με ώρα, π.χ. "20:00"
            if re.search(r"\b([01]?\d|2[0-3]):[0-5]\d\b", line) and i > 0:
                home_away = lines[i-1]
                parts = re.split(r"\s+-\s+|\s+vs\s+|\s+–\s+", home_away)
                if len(parts) == 2:
                    out.append({
                        "date": None, "home": parts[0].strip(), "away": parts[1].strip(),
                        "hs": None, "as": None, "status": "NS"
                    })
    return dedupe_matches(out)

def dedupe_matches(lst: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for m in lst:
        key = (m["home"], m["away"], m.get("hs"), m.get("as"))
        if key in seen: 
            continue
        seen.add(key)
        out.append(m)
    return out

# -------------------------
# Match Summary (Last-5 / H2H)
# -------------------------
def parse_match_html(html: str) -> Dict[str, Any]:
    """
    Επιστρέφει:
    {
      "last5_home": [ {date, opponent, res, score}, ... ],
      "last5_away": [...],
      "h2h": [ {date, home, away, score, res_home}, ... ]
    }
    Προσπάθεια με heuristics — αν δεν βρεθεί σίγουρο μοτίβο, επιστρέφει κενά.
    """
    out = {"last5_home": [], "last5_away": [], "h2h": []}
    if not html: 
        return out
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    lines = [l for l in text.split("\n") if l.strip()]

    # Heuristic: μαζεύουμε μέχρι 10 αποτελέσματα που ταιριάζουν σε "TeamX - TeamY" + score
    matches = []
    for i, line in enumerate(lines):
        m = re.search(r"(\d{1,2}\s*[./-]\s*\d{1,2}\s*[./-]\s*\d{2,4})", line)  # ημερομηνία
        score = re.search(r"(\d+)\s*[-:]\s*(\d+)", line)
        if score and i>0:
            names = re.split(r"\s+-\s+|\s+vs\s+|\s+–\s+", lines[i-1])
            if len(names)==2:
                matches.append({
                    "date": m.group(1) if m else None,
                    "home": names[0].strip(),
                    "away": names[1].strip(),
                    "score": score.group(0)
                })
    # Διαχωρισμός σε H2H ~ πρώτα 10 και τα υπόλοιπα ως potential last5 pools
    out["h2h"] = matches[:10]
    # Το last5 δεν μπορούμε να το αποδώσουμε με βεβαιότητα χωρίς σταθερό DOM,
    # οπότε το αφήνουμε κενό εδώ — θα προκύψει από το τοπικό history_engine.
    return out
