// ============================================================
// GOALMATRIX PANEL JS v1.2 (Unified PRO+ v9.5.5)
// ============================================================
(async function () {
  const elBody = document.getElementById("gm-body");
  const elStatus = document.getElementById("gm-status-pill");
  const elBtn = document.getElementById("gm-refresh");
  const elTotal = document.getElementById("gm-summary-total");
  const elAvg = document.getElementById("gm-summary-avg");
  const elTime = document.getElementById("gm-summary-time");

  async function getJSON(url) {
    try {
      const r = await fetch(url, { cache: "no-store" });
      if (!r.ok) throw new Error(r.statusText);
      return await r.json();
    } catch {
      return null;
    }
  }

  async function refreshAll() {
    const summary = await getJSON("/api/goalmatrix/summary");

    if (!summary) {
      elStatus.textContent = "Failing";
      elStatus.className = "status-pill bg-red";
      elBody.innerHTML = `<tr><td colspan="6">⚠️ Error loading GoalMatrix</td></tr>`;
      return;
    }

    // --- Στατιστικά σύνοψης ---
    elStatus.textContent = summary.status ?? "Active";
    elStatus.className =
      "status-pill " +
      (summary.status === "OK"
        ? "bg-green"
        : summary.status === "No Data"
        ? "bg-yellow"
        : "bg-blue");

    elTotal.textContent = "Matches: " + (summary.total_matches ?? 0);
    elAvg.textContent = "Avg xG: " + (summary.avg_goals ?? 0);
    elTime.textContent =
      "Last Update: " +
      new Date((summary.last_updated_ts ?? Date.now() / 1000) * 1000).toLocaleTimeString();

    // --- Αν υπάρχουν αναλυτικά items μέσα στο summary ---
    const items = summary.items ?? summary.data ?? [];
    if (!items.length) {
      elBody.innerHTML = `<tr><td colspan="6">No GoalMatrix data available</td></tr>`;
      return;
    }

    // --- Απόδοση λίστας ---
    elBody.innerHTML = items
      .map(
        (x) => `
      <tr>
        <td>${x.league ?? "-"}</td>
        <td>${x.home ?? "-"} – ${x.away ?? "-"}</td>
        <td>${x.xg_home ?? "-"}</td>
        <td>${x.xg_away ?? "-"}</td>
        <td><b>${x.expected_goals ?? "-"}</b></td>
        <td>${x.tendency ?? "-"}</td>
      </tr>`
      )
      .join("");
  }

  elBtn?.addEventListener("click", refreshAll);
  await refreshAll();
  setInterval(refreshAll, 30000);
})();
