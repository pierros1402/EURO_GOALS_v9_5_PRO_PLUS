/* ============================================================
   EURO_GOALS PRO+ v10.2.1 — Goal & SmartMoney Auto-Refresh
   ============================================================ */

console.log("[EG] goal_smart_refresh.js v10.2.1 loaded");

const REFRESH_FROM_SERVER = 10 * 1000; // 10s

async function fetchJSON(url) {
    try {
        const r = await fetch(url, { cache: "no-store" });
        if (!r.ok) return null;
        return await r.json();
    } catch {
        return null;
    }
}

/* ------------------------------------------------------------
   SYSTEM STATUS BAR
------------------------------------------------------------ */

async function updateSystemStatus() {
    const data = await fetchJSON("/api/system/status");
    if (!data) return;

    const ts = document.getElementById("sys-ts");
    if (ts) ts.textContent = data.timestamp.split("T")[1].replace("Z","");

    const engines = data.engines || {};

    const s1 = document.getElementById("eng-sm");
    const s2 = document.getElementById("eng-gm");
    const s3 = document.getElementById("eng-dj");

    if (s1) s1.textContent = engines.smartmoney || "--";
    if (s2) s2.textContent = engines.goalmatrix || "--";
    if (s3) s3.textContent = engines.dowjones || "--";
}

/* ------------------------------------------------------------
   GOAL MATRIX PANEL
------------------------------------------------------------ */

async function updateGoalMatrix() {
    const data = await fetchJSON("/api/goal_matrix/summary");
    if (!data || !data.items) return;

    const body = document.getElementById("gm-body");
    if (!body) return;

    let html = "";
    for (const row of data.items) {
        html += `
        <tr>
            <td>${row.league || "-"}</td>
            <td>${row.match || "-"}</td>
            <td>${row.initial_odds || "-"}</td>
            <td>${row.current_odds || "-"}</td>
            <td>${row.movement || "-"}</td>
        </tr>`;
    }
    body.innerHTML = html;
}

/* ------------------------------------------------------------
   SMARTMONEY PANEL
------------------------------------------------------------ */

async function updateSmartMoney() {
    const data = await fetchJSON("/api/smartmoney/summary");
    if (!data || !data.items) return;

    const body = document.getElementById("sm-body");
    if (!body) return;

    let html = "";
    for (const row of data.items) {
        html += `
        <tr>
            <td>${row.league || "-"}</td>
            <td>${row.match || "-"}</td>
            <td>${row.odds || "-"}</td>
            <td>${row.change || "-"}</td>
            <td>${row.alerts || 0}</td>
        </tr>`;
    }
    body.innerHTML = html;

    const alertBadge = document.getElementById("sm-alert-count");
    if (alertBadge) alertBadge.textContent = data.alerts || 0;
}

/* ------------------------------------------------------------
   SMARTMONEY LOG PANEL
------------------------------------------------------------ */

async function updateSmartMoneyLog() {
    const data = await fetchJSON("/api/smartmoney/log");
    if (!data || !data.items) return;

    const body = document.getElementById("sm-log-body");
    if (!body) return;

    let html = "";
    for (const row of data.items) {
        html += `
        <tr>
            <td>${row.ts ? row.ts.split("T")[1].replace("Z","") : "-"}</td>
            <td>${row.league || "-"}</td>
            <td>${row.match || "-"}</td>
            <td>${row.odds || "-"}</td>
        </tr>`;
    }

    body.innerHTML = html;
}

/* ------------------------------------------------------------
   MASTER REFRESH LOOP
------------------------------------------------------------ */

async function masterRefresh() {
    updateSystemStatus();
    updateGoalMatrix();
    updateSmartMoney();
    updateSmartMoneyLog();
}

setInterval(masterRefresh, REFRESH_FROM_SERVER);
window.addEventListener("load", masterRefresh);
