// GOALMATRIX PANEL JS v1.0.0
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
    } catch (e) {
      return null;
    }
  }

  async function refreshAll() {
    const summary = await getJSON("/api/goalmatrix/summary");
    const data = await getJSON("/api/goalmatrix/items");

    if (!summary) {
      elStatus.textContent = "Failing";
      elStatus.className = "px-2 py-1 rounded text-xs bg-red-200";
      elBody.innerHTML = `<tr><td colspan="6" class="p-2">Error loading GoalMatrix</td></tr>`;
      return;
    }

    elStatus.textContent = summary.status;
    elStatus.className = "px-2 py-1 rounded text-xs " + (
      summary.status === "OK" ? "bg-green-200" :
      summary.status === "No Data" ? "bg-amber-200" :
      "bg-red-200"
    );

    elTotal.textContent = "Matches: " + (summary.total_matches ?? 0);
    elAvg.textContent = "Avg xG: " + (summary.avg_goals ?? 0);
    elTime.textContent = "Last Updated: " + new Date((summary.last_updated_ts ?? 0) * 1000).toLocaleTimeString();

    const items = (data && data.items) ? data.items : [];
    if (!items.length) {
      elBody.innerHTML = `<tr><td colspan="6" class="p-2">No data available</td></tr>`;
      return;
    }

    elBody.innerHTML = items.map(x => `
      <tr>
        <td class="p-2">${x.league}</td>
        <td class="p-2">${x.home} – ${x.away}</td>
        <td class="p-2">${x.xg_home}</td>
        <td class="p-2">${x.xg_away}</td>
        <td class="p-2 font-semibold">${x.expected_goals}</td>
        <td class="p-2">${x.tendency}</td>
      </tr>
    `).join("");
  }

  elBtn.addEventListener("click", refreshAll);
  await refreshAll();
  setInterval(refreshAll, 30000);
})();
