// ============================================================
// SMARTMONEY PANEL JS v3.0.0 — EURO_GOALS PRO+ Unified
// Multi-source Odds Tracker (Bet365 / Stoiximan / OPAP)
// Alert >= 0.20 (visual blink + sound)
// ============================================================

(async function () {
  const elBody = document.getElementById("smartmoney-body");
  const elStatus = document.getElementById("smartmoney-status-pill");
  const elCount = document.getElementById("smartmoney-count");
  const elLast = document.getElementById("smartmoney-last");
  const audioAlert = new Audio("/static/sounds/alert.mp3");
  audioAlert.volume = 0.7;

  let lastAlerts = {};

  async function getJSON(url) {
    try {
      const r = await fetch(url, { cache: "no-store" });
      if (!r.ok) throw new Error(r.statusText);
      return await r.json();
    } catch (e) {
      console.error("[SmartMoney] Fetch error:", e);
      return null;
    }
  }

  function blinkRow(row) {
    row.classList.add("blink");
    setTimeout(() => row.classList.remove("blink"), 2500);
  }

  async function refreshPanel() {
    const summary = await getJSON("/api/smartmoney/summary");
    const data = await getJSON("/api/smartmoney/alerts");

    if (!summary || !data) {
      elStatus.textContent = "Failing";
      elStatus.className = "px-2 py-1 rounded text-xs bg-red-700 text-white";
      elBody.innerHTML = `<tr><td colspan="8" class="p-2 text-center text-red-300">⚠️ SmartMoney feed unavailable</td></tr>`;
      return;
    }

    elStatus.textContent = summary.status;
    elStatus.className =
      "px-2 py-1 rounded text-xs " +
      (summary.status === "OK"
        ? "bg-green-700 text-white"
        : summary.status === "Degraded"
        ? "bg-amber-600 text-white"
        : "bg-red-700 text-white");

    elCount.textContent = `Alerts: ${summary.count ?? 0}`;
    elLast.textContent = `Last update: ${new Date(
      (summary.last_updated_ts ?? 0) * 1000
    ).toLocaleTimeString("el-GR")}`;

    const alerts = data.alerts || [];
    if (!alerts.length) {
      elBody.innerHTML = `<tr><td colspan="8" class="p-2 text-center text-gray-400">No active SmartMoney alerts</td></tr>`;
      return;
    }

    elBody.innerHTML = "";
    for (const a of alerts) {
      const diff = a.movement ?? 0;
      const diffAbs = Math.abs(diff);
      const isUp = diff > 0;
      const diffClass =
        diffAbs >= 0.2
          ? isUp
            ? "text-green-400 font-bold"
            : "text-red-500 font-bold"
          : "text-gray-300";

      const row = document.createElement("tr");
      row.innerHTML = `
        <td class="p-2">${a.source || "—"}</td>
        <td class="p-2">${a.league || "-"}</td>
        <td class="p-2">${a.match || "-"}</td>
        <td class="p-2">${a.market || a.type || "—"}</td>
        <td class="p-2">${a.open?.toFixed?.(2) ?? "-"}</td>
        <td class="p-2">${a.current?.toFixed?.(2) ?? "-"}</td>
        <td class="p-2 ${diffClass}">
          ${isUp ? "▲" : "▼"} ${diffAbs.toFixed(2)}
        </td>
        <td class="p-2 text-xs text-gray-400">${a.timestamp || ""}</td>
      `;

      const prev = lastAlerts[a.match + a.source];
      const changed =
        !prev || Math.abs(prev - diff) >= 0.2 || prev * diff < 0;

      if (changed && diffAbs >= 0.2) {
        blinkRow(row);
        try {
          audioAlert.currentTime = 0;
          await audioAlert.play();
        } catch (e) {
          console.warn("[SmartMoney] Audio blocked:", e);
        }
      }

      elBody.appendChild(row);
      lastAlerts[a.match + a.source] = diff;
    }
  }

  await refreshPanel();
  setInterval(refreshPanel, 30000);

  const style = document.createElement("style");
  style.textContent = `
    .blink { animation: blinkEffect 1s ease-in-out 3; }
    @keyframes blinkEffect {
      0%, 100% { background-color: transparent; }
      50% { background-color: rgba(255, 0, 0, 0.25); }
    }
  `;
  document.head.appendChild(style);
})();
