// ============================================================
// ODDS PANEL SCRIPT – EURO_GOALS v9.6.1 PRO+ Unified Expansion
// ============================================================
async function loadOddsData() {
  const body = document.getElementById("odds-body");
  const pill = document.getElementById("odds-status-pill");

  try {
    const res = await fetch("/api/odds/data", { cache: "no-store" });
    if (!res.ok) throw new Error("Fetch failed");
    const data = await res.json();
    const matches = data?.matches || [];

    pill.textContent = "ON";
    pill.className = "px-2 py-1 rounded text-xs bg-green-500 text-black font-semibold";

    if (matches.length === 0) {
      body.innerHTML = `<tr><td colspan="6" class="p-2 text-center text-gray-400">No odds data available.</td></tr>`;
      return;
    }

    // Επεξεργασία μόνο επερχόμενων αγώνων & Top 10 μεταβολές
    const processed = matches
      .map(m => {
        const diff =
          Math.abs((m.odds_live_home ?? 0) - (m.odds_open_home ?? 0)) +
          Math.abs((m.odds_live_draw ?? 0) - (m.odds_open_draw ?? 0)) +
          Math.abs((m.odds_live_away ?? 0) - (m.odds_open_away ?? 0));
        return { ...m, diff };
      })
      .sort((a, b) => b.diff - a.diff)
      .slice(0, 10);

    body.innerHTML = processed
      .map(m => {
        const diffClass = m.diff > 0.2 ? "text-red-400" : "text-gray-300";
        return `
          <tr class="hover:bg-neutral-800/60 transition">
            <td class="p-2">${m.league ?? "-"}</td>
            <td class="p-2">${m.home ?? "-"} – ${m.away ?? "-"}</td>
            <td class="p-2">${m.bookmaker ?? "-"}</td>
            <td class="p-2 text-right">${(m.odds_open_home ?? "-")}/${(m.odds_open_draw ?? "-")}/${(m.odds_open_away ?? "-")}</td>
            <td class="p-2 text-right">${(m.odds_live_home ?? "-")}/${(m.odds_live_draw ?? "-")}/${(m.odds_live_away ?? "-")}</td>
            <td class="p-2 text-center ${diffClass}">${m.diff.toFixed(2)}</td>
          </tr>`;
      })
      .join("");

    document.getElementById("odds-summary-total").textContent = `Matches: ${matches.length}`;
    document.getElementById("odds-summary-bookmakers").textContent = `Bookmakers: 3`;
    document.getElementById("odds-summary-time").textContent =
      "Last update: " + new Date().toLocaleTimeString("el-GR", { hour12: false });
  } catch (err) {
    console.warn("[EURO_GOALS] Odds fetch error:", err);
    pill.textContent = "OFF";
    pill.className = "px-2 py-1 rounded text-xs bg-red-600 text-white";
    body.innerHTML = `<tr><td colspan="6" class="p-2 text-center text-gray-400">⚠ Σφάλμα φόρτωσης αποδόσεων.</td></tr>`;
  }
}

document.getElementById("odds-refresh")?.addEventListener("click", loadOddsData);
window.addEventListener("load", loadOddsData);
setInterval(loadOddsData, 180000); // 3 λεπτά
