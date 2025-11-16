// =======================================================
// AI MATCHLAB Frontend Engine – PREMIUM v0.9.3
// =======================================================

console.log("AI MATCHLAB JS v0.9.3 loaded");

// ------------------------------
// DOM Elements
// ------------------------------
const liveContainer = document.getElementById("liveContainer");
const debugPanel = document.getElementById("debugPanel");

const btnAll = document.getElementById("btnAll");
const btnLive = document.getElementById("btnLive");
const btnRecent = document.getElementById("btnRecent");
const btnUpcoming = document.getElementById("btnUpcoming");

const workerStatusText = document.getElementById("workerStatusText");
const workerJsonBox = document.getElementById("workerJsonBox");
const lastPayloadBox = document.getElementById("lastPayloadBox");
const btnRefresh = document.getElementById("refreshBtn");

let currentView = "all";

// ------------------------------
// API CALL HELPERS
// ------------------------------

async function apiGet(endpoint) {
    try {
        const r = await fetch(endpoint + "?t=" + Date.now());
        const data = await r.json();
        return data;
    } catch (e) {
        return { ok: false, error: e.toString() };
    }
}

// ------------------------------
// RENDER MATCH CARD
// ------------------------------

function renderMatch(m) {
    return `
        <div class="matchCard">
            <div style="font-size:17px; margin-bottom:4px;">
                ${m.home || "Team A"} vs ${m.away || "Team B"}
            </div>
            <div style="opacity:0.7; font-size:14px;">
                ${m.status || "Scheduled"} — ${m.time || "-"}
            </div>
        </div>
    `;
}

// ------------------------------
// RENDER FULL LIST
// ------------------------------

function renderMatches(list) {
    if (!list || list.length === 0) {
        liveContainer.innerHTML = `<div style="opacity:0.5;padding:20px;">No matches.</div>`;
        return;
    }

    liveContainer.innerHTML = list.map(renderMatch).join("");
}

// ------------------------------
// LOAD FEED FOR CURRENT VIEW
// ------------------------------

async function loadFeed() {
    let endpoint = "/ai/source-a/live";

    if (currentView === "recent") endpoint = "/ai/source-a/recent";
    if (currentView === "upcoming") endpoint = "/ai/source-a/upcoming";

    debugPanel.innerHTML = "Loading " + currentView + "...";

    const data = await apiGet(endpoint);

    if (!data || data.ok === false) {
        liveContainer.innerHTML = `<div style="color:#f55; padding:20px;">Feed error.</div>`;
        debugPanel.innerHTML = JSON.stringify(data, null, 2);
        return;
    }

    // list found in data.normalizedPreview
    const list = data.normalizedPreview || [];

    renderMatches(list);
    debugPanel.innerHTML = JSON.stringify(data, null, 2);
}

// ------------------------------
// LOAD WORKER STATUS
// ------------------------------

async function loadWorkerStatus() {
    const data = await apiGet("/ai/status");

    if (!data || data.ok === false) {
        workerStatusText.innerHTML = `<span style="color:#f55;">Worker error</span>`;
        workerJsonBox.innerHTML = JSON.stringify(data, null, 2);
        return;
    }

    workerStatusText.innerHTML = `<span style="color:#6f6;">OK</span>`;
    workerJsonBox.innerHTML = JSON.stringify(data.raw, null, 2);
}

// ------------------------------
// BUTTON EVENTS
// ------------------------------

btnAll.addEventListener("click", () => {
    currentView = "all";
    highlightTabs();
    loadFeed();
});

btnLive.addEventListener("click", () => {
    currentView = "live";
    highlightTabs();
    loadFeed();
});

btnRecent.addEventListener("click", () => {
    currentView = "recent";
    highlightTabs();
    loadFeed();
});

btnUpcoming.addEventListener("click", () => {
    currentView = "upcoming";
    highlightTabs();
    loadFeed();
});

btnRefresh.addEventListener("click", () => {
    loadFeed();
    loadWorkerStatus();
});

function highlightTabs() {
    btnAll.classList.remove("activeTab");
    btnLive.classList.remove("activeTab");
    btnRecent.classList.remove("activeTab");
    btnUpcoming.classList.remove("activeTab");

    if (currentView === "all") btnAll.classList.add("activeTab");
    if (currentView === "live") btnLive.classList.add("activeTab");
    if (currentView === "recent") btnRecent.classList.add("activeTab");
    if (currentView === "upcoming") btnUpcoming.classList.add("activeTab");
}

// ------------------------------
// AUTO REFRESH
// ------------------------------

setInterval(() => {
    loadFeed();
}, 12000);

setInterval(() => {
    loadWorkerStatus();
}, 15000);

// ------------------------------
// INIT
// ------------------------------

highlightTabs();
loadFeed();
loadWorkerStatus();
