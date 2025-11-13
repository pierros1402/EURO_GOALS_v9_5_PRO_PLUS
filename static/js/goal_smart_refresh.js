async function fetchJSON(url) {
    try {
        const r = await fetch(url);
        return await r.json();
    } catch (e) {
        console.error("JSON fetch failed:", e);
        return null;
    }
}

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function setPill(id, state) {
    const el = document.getElementById(id);
    if (!el) return;

    el.classList.remove("eg-status-on", "eg-status-off", "eg-status-warn");

    if (state === "on") el.classList.add("eg-status-on");
    else if (state === "off") el.classList.add("eg-status-off");
    else el.classList.add("eg-status-warn");
}

/* ============================================================
   REFRESH ENGINE
   ============================================================ */

async function refreshSystemStatus() {
    const data = await fetchJSON("/api/system/status");
    if (!data) return;

    setText("eg-system-time", data.timestamp);
    setText("eg-status-last-update", data.timestamp);

    // Worker status
    const w = data.worker.http_status === 200 ? "on" : "off";
    setPill("eg-dowjones-worker-status", w);

    // SmartMoney & GoalMatrix always mirror worker
    setPill("eg-smartmoney-engine", w);
    setPill("eg-goalmatrix-engine", w);

    // Connection
    setText("eg-connection-status", navigator.onLine ? "Online" : "Offline");
}

async function refreshSmartMoney() {
    const data = await fetchJSON("/api/smartmoney/summary");
    if (!data) return;

    setText("sm-updated", data.updated);
    setText("sm-total-alerts", data.alerts);

    setPill("sm-alerts-pill", data.alerts > 0 ? "warn" : "on");

    // Fill table
    const body = document.getElementById("sm-body");
    if (!body) return;
    body.innerHTML = "";

    for (const row of data.items) {
        body.innerHTML += `
            <tr>
              <td>${row.league}</td>
              <td>${row.match}</td>
              <td>${row.odds ?? "--"}</td>
              <td>${row.change ?? "--"}</td>
              <td>${row.alerts}</td>
            </tr>
        `;
    }
}

async function refreshGoalMatrix() {
    const data = await fetchJSON("/api/goal_matrix/summary");
    if (!data) return;

    setText("gm-updated", data.updated);
    setText("gm-total", data.total);

    setPill("gm-status-pill", data.total > 0 ? "on" : "off");

    const body = document.getElementById("gm-body");
    body.innerHTML = "";

    for (const row of data.items) {
        body.innerHTML += `
            <tr>
              <td>${row.league}</td>
              <td>${row.match}</td>
              <td>${row.initial_odds ?? "--"}</td>
              <td>${row.current_odds ?? "--"}</td>
              <td>${row.movement ?? "--"}</td>
            </tr>
        `;
    }
}

async function refreshSmartMoneyLog() {
    const data = await fetchJSON("/api/smartmoney/log");
    if (!data) return;

    const body = document.getElementById("sm-log-body");
    body.innerHTML = "";

    for (const row of data.items) {
        body.innerHTML += `
            <tr>
              <td>${row.ts}</td>
              <td>${row.league}</td>
              <td>${row.match}</td>
              <td style="text-align:right;">${row.odds ?? "--"}</td>
            </tr>
        `;
    }
}

/* ============================================================
   MAIN LOOP
   ============================================================ */

async function refreshAll() {
    refreshSystemStatus();
    refreshSmartMoney();
    refreshGoalMatrix();
    refreshSmartMoneyLog();
}

document.getElementById("force-refresh")?.addEventListener("click", refreshAll);

refreshAll();
setInterval(refreshAll, 10000);
