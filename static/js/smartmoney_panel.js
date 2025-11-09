// ============================================================
// SMARTMONEY PANEL JS v1.3 (Unified PRO+ v9.5.5)
// ============================================================
(async function () {
  const elBody = document.getElementById("sm-body");
  const elStatus = document.getElementById("sm-status-pill");
  const elBtn = document.getElementById("sm-refresh");
  const elTotal = document.getElementById("sm-summary-total");
  const elAvg = document.getElementById("sm-summary-avg");
  const elTime = document.getElementById("sm-summary-time");

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
    const summary = await getJSON("/api/smartmoney/summary");
    const alerts = await getJSON("/api/smartmoney/alerts");

    if (!summary) {
      elStatus.textContent = "Failing";
      elStatus.className = "status-pill bg-red";
      elBody.innerHTML = `<tr><td colspan="6">⚠️ Error loading SmartMoney</td></tr>`;
      return;
    }

    // --- Συνοπτικά στοιχεία SmartMoney ---
    elStatus.textContent = summary.status ?? "Active";
    elStatus.className =
      "status-pill " +
      (summary.status === "OK"
        ? "bg-green"
        : summary.status === "No Data"
        ? "bg-yellow"
        : "bg-blue");

    elTotal.textContent = "Signals: " + (summary.total_signals ?? 0);
    elAvg.textContent = "Avg Δ%: " + (summary.avg_change ?? "0.00");
    elTime.textContent =
      "Last Update: " +
      new Date((summary.last_updated_ts ?? Date.now() / 1000) * 1000).toLocaleTimeString();

    // --- Ανάλυση δεδομένων SmartMoney (ενότητα πίνακα) ---
    const items = summary.items ?? summary.data ?? [];
    if (!items.length) {
      elBody.innerHTML = `<tr><td colspan="6">No SmartMoney data available</td></tr>`;
      return;
    }

    elBody.innerHTML = items
      .map(
        (x) => `
      <tr>
        <td>${x.league ?? "-"}</td>
        <td>${x.match ?? "-"}</td>
        <td>${x.open_odds ?? "-"}</td>
        <td>${x.current_odds ?? "-"}</td>
        <td>${x.delta ?? "0.00"}%</td>
        <td>${x.signal ?? "-"}</td>
      </tr>`
      )
      .join("");

    // --- Προαιρετικά Alerts ---
    if (alerts?.alerts?.length) {
      console.log("[SmartMoney Alerts]", alerts.alerts.length, "active alerts");
    }
  }

  elBtn?.addEventListener("click", refreshAll);
  await refreshAll();
  setInterval(refreshAll, 30000);
})();
