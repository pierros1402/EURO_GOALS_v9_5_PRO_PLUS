// ============================================================
// EURO_GOALS PRO+ v9.5.5 — GoalMatrix Panel (Unified Odds Mode)
// ============================================================
(async function () {
  const elBody = document.getElementById("gm-body");
  const elStatus = document.getElementById("gm-status-pill");
  const elBtn = document.getElementById("gm-refresh");
  const elTotal = document.getElementById("gm-summary-total");
  const elTime = document.getElementById("gm-summary-time");
  const elReplaced = document.getElementById("gm-replaced");
  const elReplacedList = document.getElementById("gm-replaced-list");

  let lastTopMatches = [];

  async function getJSON(url) {
    try {
      const r = await fetch(url, { cache: "no-store" });
      if (!r.ok) throw new Error(r.statusText);
      return await r.json();
    } catch (err) {
      console.warn("[EURO_GOALS] GoalMatrix fetch error:", err);
      return null;
    }
  }

  function renderTable(matches) {
    elBody.innerHTML = matches
      .map((m) => {
        const move =
          m.current_odds > m.opening_odds
            ? "↑"
            : m.current_odds < m.opening_odds
            ? "↓"
            : "–";
        const moveClass =
          m.current_odds > m.opening_odds
            ? "text-green-400"
            : m.current_odds < m.opening_odds
            ? "text-red-400"
            : "text-gray-300";

        return `
          <tr class="hover:bg-neutral-800/60 transition">
            <td class="p-2">${m.league || "-"}</td>
            <td class="p-2">${m.home_team || "-"} – ${m.away_team || "-"}</td>
            <td class="p-2 text-right">${m.opening_odds?.toFixed?.(2) ?? "–"}</td>
            <td class="p-2 text-right">${m.current_odds?.toFixed?.(2) ?? "–"}</td>
            <td class="p-2 text-center ${moveClass}">${move}</td>
          </tr>`;
      })
      .join("");
  }

  async function refreshAll() {
    const data = await getJSON("/api/odds/data");
    if (!data || !data.items) {
      elStatus.textContent = "OFF";
      elStatus.className = "px-2 py-1 rounded text-xs bg-red-600 text-white";
      elBody.innerHTML =
        `<tr><td colspan="5" class="p-2 text-center text-gray-400">⚠ No data received</td></tr>`;
      return;
    }

    elStatus.textContent = "ON";
    elStatus.className = "px-2 py-1 rounded text-xs bg-green-500 text-black font-semibold";

    // Επερχόμενοι αγώνες (μόνο)
    const upcoming = data.items.filter((m) => m.status === "upcoming");

    // Ταξινόμηση κατά μέγεθος μεταβολής
    upcoming.sort(
      (a, b) =>
        Math.abs(b.current_odds - b.opening_odds) -
        Math.abs(a.current_odds - a.opening_odds)
    );

    const top10 = upcoming.slice(0, 10);
    renderTable(top10);

    // Ενημέρωση replaced list
    const replaced = lastTopMatches.filter(
      (old) => !top10.find((n) => n.id === old.id)
    );
    if (replaced.length) {
      elReplaced.classList.remove("hidden");
      elReplacedList.innerHTML =
        replaced
          .map(
            (r) =>
              `<li>${r.league || ""}: ${r.home_team} – ${r.away_team} (${r.opening_odds.toFixed(
                2
              )}→${r.current_odds.toFixed(2)})</li>`
          )
          .join("") + elReplacedList.innerHTML;
    }

    lastTopMatches = top10;
    elTotal.textContent = `Matches: ${upcoming.length}`;
    elTime.textContent =
      "Last update: " + new Date().toLocaleTimeString("el-GR", { hour12: false });
  }

  elBtn?.addEventListener("click", refreshAll);
  await refreshAll();
  setInterval(refreshAll, 30000);
})();
