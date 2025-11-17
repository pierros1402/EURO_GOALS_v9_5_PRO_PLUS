// =======================================================
// AI MATCHLAB Frontend Engine – v0.9.3 PRO
// Unified Worker Edition (FastAPI + Cloudflare Worker)
// =======================================================

const AIML_VERSION = "v0.9.3-PRO";

// ---- Worker / Backend endpoints ------------------------

const WORKER_BASE = "https://aimatchlab.pierros1402.workers.dev";

const API_STATUS = `${WORKER_BASE}/api/status`;
const API_LIVE = `${WORKER_BASE}/api/live`; // unified live/recent/upcoming feed

const BACKEND_HEALTH = "/health";

// ---- DOM REFS ------------------------------------------

const refreshBtn = document.getElementById("refreshBtn");
const installBtn = document.getElementById("installBtn");
const themeToggleBtn = document.getElementById("themeToggleBtn");

const backendStatusValue = document.getElementById("backendStatusValue");
const workerStatusValue = document.getElementById("workerStatusValue");
const workerSummaryCaption = document.getElementById("workerSummaryCaption");
const feedStatusValue = document.getElementById("feedStatusValue");
const feedSummaryCaption = document.getElementById("feedSummaryCaption");

const liveContainer = document.getElementById("liveContainer");
const liveSkeleton = document.getElementById("liveSkeleton");
const livePlaceholder = document.getElementById("livePlaceholder");

const statusBox = document.getElementById("statusBox");
const liveDebugBox = document.getElementById("liveDebugBox");
const debugPanel = document.getElementById("debugPanel");
const toggleDebugBtn = document.getElementById("toggleDebugBtn");

const btnAll = document.getElementById("btnAll");
const btnLive = document.getElementById("btnLive");
const btnRecent = document.getElementById("btnRecent");
const btnUpcoming = document.getElementById("btnUpcoming");
const btnWidgets = document.getElementById("btnWidgets");

const goalOverlay = document.getElementById("goalFlashOverlay");

const widgetsContainer = document.getElementById("widgetsContainer");

// ---- STATE ---------------------------------------------

let currentFilter = "all";
let lastMatches = [];
let lastScoreMap = new Map();

// =======================================================
// THEME SYSTEM
// =======================================================

const THEMES = ["blue", "dark", "light", "amoled"];
const THEME_STORAGE_KEY = "aimatchlab_theme";

function applyTheme(theme) {
    const root = document.documentElement;
    if (!THEMES.includes(theme)) theme = "blue";
    root.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
    console.log("[AIML] Theme applied:", theme);
}

function initTheme() {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    applyTheme(saved || "blue");
}

themeToggleBtn.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "blue";
    const idx = THEMES.indexOf(current);
    const next = THEMES[(idx + 1) % THEMES.length];
    applyTheme(next);
});

// =======================================================
// HELPERS
// =======================================================

async function fetchJSON(url) {
    try {
        const res = await fetch(
            url + (url.includes("?") ? "&" : "?") + "t=" + Date.now(),
            { cache: "no-store" }
        );
        const text = await res.text();
        try {
            return JSON.parse(text);
        } catch (e) {
            return { _parseError: true, raw: text, message: e.toString() };
        }
    } catch (err) {
        return { _fetchError: true, message: err.toString() };
    }
}

function showSkeleton(show) {
    liveSkeleton.style.display = show ? "flex" : "none";
}

function showPlaceholder(show) {
    livePlaceholder.style.display = show ? "block" : "none";
}

// =======================================================
// HEALTH – BACKEND + WORKER STATUS
// =======================================================

async function checkBackend() {
    try {
        const data = await fetchJSON(BACKEND_HEALTH);
        if (data._fetchError || data._parseError) throw new Error(data.message || "Health error");

        backendStatusValue.textContent = "Online";
        backendStatusValue.classList.add("aiml-summary-ok");
        backendStatusValue.classList.remove("aiml-summary-issue");
    } catch (err) {
        backendStatusValue.textContent = "Error";
        backendStatusValue.classList.remove("aiml-summary-ok");
        backendStatusValue.classList.add("aiml-summary-issue");
    }
}

async function loadStatus() {
    const data = await fetchJSON(API_STATUS);

    if (data._fetchError || data._parseError || data.ok === false) {
        workerStatusValue.textContent = "Error";
        workerStatusValue.classList.remove("aiml-summary-ok");
        workerStatusValue.classList.add("aiml-summary-issue");
        workerSummaryCaption.textContent = data.message || "Worker unreachable";

        statusBox.textContent = JSON.stringify(data, null, 2);
        return;
    }

    workerStatusValue.textContent = "OK";
    workerStatusValue.classList.add("aiml-summary-ok");
    workerStatusValue.classList.remove("aiml-summary-issue");

    const ver = data.version || data.workerVersion || "unknown";
    workerSummaryCaption.textContent = `Worker online (v ${ver})`;

    statusBox.textContent = JSON.stringify(
        {
            ok: data.ok,
            service: data.service,
            version: data.version,
            timestamp: data.timestamp
        },
        null,
        2
    );
}

// =======================================================
// NORMALISATION / MATCH LIST
// =======================================================

function extractMatches(raw) {
    if (!raw) return [];

    if (Array.isArray(raw.normalizedPreview)) {
        return raw.normalizedPreview;
    }

    let events = null;

    if (Array.isArray(raw.matches)) events = raw.matches;
    else if (Array.isArray(raw.events)) events = raw.events;
    else if (Array.isArray(raw.data?.events)) events = raw.data.events;
    else if (Array.isArray(raw.data)) events = raw.data;

    if (!events) return [];

    const matches = events.map((ev) => {
        const safe = (obj, path, fallback = null) => {
            try {
                return (
                    path
                        .split(".")
                        .reduce(
                            (acc, k) =>
                                acc && acc[k] !== undefined ? acc[k] : undefined,
                            obj
                        ) ?? fallback
                );
            } catch {
                return fallback;
            }
        };

        const home =
            ev.home ||
            safe(ev, "strHomeTeam") ||
            safe(ev, "homeTeam.name") ||
            safe(ev, "home.name") ||
            safe(ev, "homeTeam.shortName") ||
            "Home";

        const away =
            ev.away ||
            safe(ev, "strAwayTeam") ||
            safe(ev, "awayTeam.name") ||
            safe(ev, "away.name") ||
            safe(ev, "awayTeam.shortName") ||
            "Away";

        const homeScore =
            ev.score_home ??
            safe(ev, "intHomeScore") ??
            safe(ev, "homeScore.display") ??
            safe(ev, "homeScore.current") ??
            safe(ev, "homeScore.normaltime") ??
            safe(ev, "homeScore", 0) ??
            0;

        const awayScore =
            ev.score_away ??
            safe(ev, "intAwayScore") ??
            safe(ev, "awayScore.display") ??
            safe(ev, "awayScore.current") ??
            safe(ev, "awayScore.normaltime") ??
            safe(ev, "awayScore", 0) ??
            0;

        const statusRaw =
            ev.status ||
            safe(ev, "status.type") ||
            safe(ev, "status.description") ||
            "UNKNOWN";

        const minute =
            ev.minute ??
            safe(ev, "time.minute") ??
            safe(ev, "time.currentPeriodStartMinute") ??
            safe(ev, "time", null);

        const league =
            ev.league ||
            safe(ev, "strLeague") ||
            safe(ev, "tournament.name") ||
            safe(ev, "league.name") ||
            null;

        const country =
            safe(ev, "tournament.category.name") ||
            safe(ev, "league.country") ||
            null;

        const kickoff =
            ev.kickoff ||
            (ev.date && ev.time ? `${ev.date} ${ev.time}` : null) ||
            safe(ev, "kickoffTime", null);

        const id =
            ev.id ||
            safe(ev, "id") ||
            safe(ev, "matchId") ||
            safe(ev, "eventId") ||
            `${home}-${away}-${statusRaw}`;

        let bucket = "upcoming";
        const s = (statusRaw || "").toString().toLowerCase();

        if (
            s.includes("live") ||
            s.includes("1st") ||
            s.includes("2nd") ||
            s === "inprogress"
        ) {
            bucket = "live";
        } else if (s.includes("finished") || s === "ft" || s === "fulltime") {
            bucket = "recent";
        }

        return {
            id,
            home,
            away,
            score: `${homeScore} - ${awayScore}`,
            minute: minute ? `${minute}'` : "-",
            status: statusRaw,
            league,
            country,
            kickoff,
            bucket,
            _raw: ev
        };
    });

    return matches;
}

// =======================================================
// GOAL FLASH
// =======================================================

function detectGoalsAndFlash(matches) {
    const changedIds = [];

    matches.forEach((m) => {
        const prev = lastScoreMap.get(m.id);
        if (prev && prev !== m.score && m.bucket === "live") {
            changedIds.push(m.id);
        }
        lastScoreMap.set(m.id, m.score);
    });

    if (!changedIds.length) return;

    goalOverlay.classList.add("visible");
    setTimeout(() => goalOverlay.classList.remove("visible"), 1200);
}

// =======================================================
// RENDER MATCH CARDS
// =======================================================

function renderMatches(filter) {
    liveContainer.querySelectorAll(".aiml-match-card").forEach((n) => n.remove());

    let list = lastMatches;
    if (filter !== "all") list = list.filter((m) => m.bucket === filter);

    if (!list.length) {
        showPlaceholder(true);
        return;
    }

    showPlaceholder(false);

    list.forEach((m) => {
        const card = document.createElement("div");
        card.className = "aiml-match-card";

        const topRow = document.createElement("div");
        topRow.className = "aiml-match-top";

        const leagueSpan = document.createElement("span");
        leagueSpan.className = "aiml-match-league";
        leagueSpan.textContent = m.league || "—";

        const statusSpan = document.createElement("span");
        statusSpan.className = "aiml-match-status";
        statusSpan.textContent = m.status || "";

        topRow.appendChild(leagueSpan);
        topRow.appendChild(statusSpan);

        const midRow = document.createElement("div");
        midRow.className = "aiml-match-mid";

        const homeSpan = document.createElement("div");
        homeSpan.className = "aiml-team-name";
        homeSpan.textContent = m.home;

        const scoreSpan = document.createElement("div");
        scoreSpan.className = "aiml-score";
        scoreSpan.textContent = m.score;

        const awaySpan = document.createElement("div");
        awaySpan.className = "aiml-team-name";
        awaySpan.textContent = m.away;

        midRow.appendChild(homeSpan);
        midRow.appendChild(scoreSpan);
        midRow.appendChild(awaySpan);

        const bottomRow = document.createElement("div");
        bottomRow.className = "aiml-match-bottom";

        const minuteSpan = document.createElement("span");
        minuteSpan.className = "aiml-minute";
        minuteSpan.textContent = m.minute;

        const countrySpan = document.createElement("span");
        countrySpan.className = "aiml-country";
        countrySpan.textContent = m.country || "";

        bottomRow.appendChild(minuteSpan);
        bottomRow.appendChild(countrySpan);

        card.appendChild(topRow);
        card.appendChild(midRow);
        card.appendChild(bottomRow);

        // Click → Match Center
        card.addEventListener("click", () => {
            const url = `/match_center?id=${encodeURIComponent(
                m.id
            )}&bucket=${encodeURIComponent(m.bucket || "all")}`;
            window.open(url, "_blank");
        });

        liveContainer.appendChild(card);
    });
}

// =======================================================
// LIVE FEED LOADER
// =======================================================

async function loadLive() {
    showSkeleton(true);
    showPlaceholder(false);

    const data = await fetchJSON(API_LIVE);

    liveDebugBox.textContent = JSON.stringify(data, null, 2);

    if (data._fetchError || data._parseError || data.ok === false) {
        feedStatusValue.textContent = "Feed error";
        feedStatusValue.classList.remove("aiml-summary-ok");
        feedStatusValue.classList.add("aiml-summary-issue");
        feedSummaryCaption.textContent =
            data.message || "Worker feed unreachable";

        showSkeleton(false);
        showPlaceholder(true);
        debugPanel.textContent = JSON.stringify(data, null, 2);
        return;
    }

    const matches = extractMatches(data);
    lastMatches = matches;

    if (!matches.length) {
        feedStatusValue.textContent = "No matches";
        feedStatusValue.classList.remove("aiml-summary-ok");
        feedStatusValue.classList.add("aiml-summary-issue");
        feedSummaryCaption.textContent = "No events from worker";
    } else {
        feedStatusValue.textContent = `${matches.length} matches`;
        feedStatusValue.classList.add("aiml-summary-ok");
        feedStatusValue.classList.remove("aiml-summary-issue");
        feedSummaryCaption.textContent = `Updated ${new Date().toLocaleTimeString()}`;
    }

    debugPanel.textContent = JSON.stringify(
        {
            status: "OK",
            source: API_LIVE,
            count: matches.length,
            preview: matches.slice(0, 5)
        },
        null,
        2
    );

    detectGoalsAndFlash(matches);
    showSkeleton(false);
    renderMatches(currentFilter);
}

// =======================================================
// TABS & FILTER
// =======================================================

function setActiveTab(filter) {
    currentFilter = filter;

    [btnAll, btnLive, btnRecent, btnUpcoming, btnWidgets].forEach((btn) =>
        btn.classList.remove("aiml-tab-active")
    );

    // Live list visible except στο Widgets
    if (filter === "widgets") {
        widgetsContainer.style.display = "block";
        liveContainer.style.display = "none";
        liveSkeleton.style.display = "none";
        livePlaceholder.style.display = "none";
    } else {
        widgetsContainer.style.display = "none";
        liveContainer.style.display = "grid";
    }

    if (filter === "all") btnAll.classList.add("aiml-tab-active");
    if (filter === "live") btnLive.classList.add("aiml-tab-active");
    if (filter === "recent") btnRecent.classList.add("aiml-tab-active");
    if (filter === "upcoming") btnUpcoming.classList.add("aiml-tab-active");
    if (filter === "widgets") btnWidgets.classList.add("aiml-tab-active");

    if (filter !== "widgets") {
        renderMatches(filter);
    }
}

btnAll.addEventListener("click", () => setActiveTab("all"));
btnLive.addEventListener("click", () => setActiveTab("live"));
btnRecent.addEventListener("click", () => setActiveTab("recent"));
btnUpcoming.addEventListener("click", () => setActiveTab("upcoming"));
btnWidgets.addEventListener("click", () => setActiveTab("widgets"));

// =======================================================
// WIDGETS PLACEHOLDER (θα μπει ScoreAxis μετά)
// =======================================================

function initWidgetsPlaceholder() {
    widgetsContainer.innerHTML = `
        <div class="aiml-widget-placeholder">
            <h3>Widgets Mode</h3>
            <p>ScoreAxis / άλλα attribution widgets θα μπουν εδώ στο επόμενο βήμα.</p>
            <p>Η βασική Live Matrix συνεχίζει να λειτουργεί κανονικά.</p>
        </div>
    `;
}

// =======================================================
// REFRESH / AUTO-REFRESH
// =======================================================

async function refreshAll() {
    await Promise.all([checkBackend(), loadStatus(), loadLive()]);
}

refreshBtn.addEventListener("click", () => {
    refreshAll();
});

// Auto-refresh κάθε 20"
setInterval(() => {
    refreshAll();
}, 20000);

// =======================================================
// DEBUG COLLAPSE
// =======================================================

let debugCollapsed = false;
toggleDebugBtn.addEventListener("click", () => {
    debugCollapsed = !debugCollapsed;
    debugPanel.style.display = debugCollapsed ? "none" : "block";
    toggleDebugBtn.textContent = debugCollapsed ? "Expand" : "Collapse";
});

// =======================================================
// INIT
// =======================================================

(function init() {
    console.log("[AIML] Initialising engine", AIML_VERSION);
    initTheme();
    initWidgetsPlaceholder();
    setActiveTab("all");
    refreshAll();
})();
