// ============================================================
// GOALMATRIX PANEL JS v1.1 (Stable Unified)
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
    const data = await getJSON("/api/goalmatrix/items");

    if (!summary) {
      elStatus.textContent = "Failing";
      elStatus.className = "status-pill bg-red";
      elBody.innerHTML = `<tr><td colspan="6">⚠️ Error loading GoalMatrix</td></tr>`;
      return;
    }

    elStatus.textContent = summary.status;
    elStatus.className =
      "status-pill " +
      (summary.status === "OK"
        ? "bg-green"
        : summary.status === "No Data"
        ? "bg-yellow"
        : "bg-red");

    elTotal.textContent = "Matches: " + (summary.total_matches ?? 0);
    elAvg.textContent = "Avg xG: " + (summary.avg_goals ?? 0);
    elTime.textContent =
      "Last Update: " +
      new Date((summary.last_updated_ts ?? 0) * 1000).toLocaleTimeString();

    const items = (data && data.items) ? data.items : [];
    if (!items.length) {
      elBody.innerHTML = `<tr><td colspan="6">No data available</td></tr>`;
      return;
    }

    elBody.innerHTML = items
      .map(
        (x) => `
      <tr>
        <td>${x.league}</td>
        <td>${x.home} – ${x.away}</td>
        <td>${x.xg_home}</td>
        <td>${x.xg_away}</td>
        <td><b>${x.expected_goals}</b></td>
        <td>${x.tendency}</td>
      </tr>`
      )
      .join("");
  }

  elBtn?.addEventListener("click", refreshAll);
  await refreshAll();
  setInterval(refreshAll, 30000);
})();

