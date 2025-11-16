// =======================================================
// AI MATCHLAB Frontend Engine – PREMIUM PACK v0.9.3
// =======================================================

const API_STATUS = "/ai/status";
const API_LIVE = "/ai/source-a/live";
const API_RECENT = "/ai/source-a/recent";
const API_UPCOMING = "/ai/source-a/upcoming";

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

const goalOverlay = document.getElementById("goalFlashOverlay");

let currentFilter = "all";
let lastMatches = [];
let lastScoreMap = new Map();
let deferredPrompt = null;

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
// PWA INSTALL HANDLING
// =======================================================

window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    installBtn.style.display = "inline-flex";
});

installBtn.addEventListener("click", async () => {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        const choice = await deferredPrompt.userChoice;
        console.log("[AIML] Install choice:", choice.outcome);
        deferredPrompt = null;
        installBtn.style.display = "none";
    } else {
        // iOS or unsupported: show simple instructions
        alert("To install AI MatchLab:\n\nOn iOS: Share → 'Add to Home Screen'\nOn Android: Use browser menu → 'Install app'.");
    }
});

// =======================================================
// FETCH HELPERS
// =======================================================

async function fetchJSON(url) {
    try {
        const res = await fetch(url + (url.includes("?") ? "&" : "?") + "t=" + Date.now(), {
            cache: "no-store"
        });
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

// =======================================================
// STATUS
// =======================================================

async function loadStatus() {
    const data = await fetchJSON(API_STATUS);

    if (data._fetchError || data._parseError || data.ok === false) {
        workerStatusValue.textContent = "Error";
        workerStatusValue.classList.remove("aiml-summary-ok");
        workerStatusValue.classList.add("aiml-summary-issue");
        workerSummaryCaption.textContent = data.message || "Worker unreachable";
    } else {
        const raw = data.raw || data.status || data;
        const ok = raw.ok !== undefined ? raw.ok : true;
        const version = raw.version || data.version || "A2-FINAL-v3";
        const ts = raw.timestamp || new Date().toISOString();

        workerStatusValue.textContent = ok ? "Online" : "Issue";
        workerStatusValue.classList.toggle("aiml-summary-ok", !!ok);
        workerStatusValue.classList.toggle("aiml-summary-issue", !ok);
        workerSummaryCaption.textContent = `Version: ${version} • ${ts}`;
    }

    statusBox.textContent = JSON.stringify(data, null, 2);
    return data;
}

// =======================================================
// LIVE DATA
// =======================================================

function extractMatches(raw) {
    if (!raw) return [];

    // If backend already normalized
    if (Array.isArray(raw.normalizedPreview)) {
        return raw.normalizedPreview;
    }

    let events = null;

    if (Array.isArray(raw.events)) events = raw.events;
    else if (Array.isArray(raw.data?.events)) events = raw.data.events;
    else if (Array.isArray(raw.data)) events = raw.data;
    else if (Array.isArray(raw.matches)) events = raw.matches;

    if (!events) return [];

    const matches = events.map((ev) => {
        const safe = (obj, path, fallback = null) => {
            try {
                return path.split(".").reduce((acc, k) => (acc && acc[k] !== undefined ? acc[k] : undefined), obj) ?? fallback;
            } catch {
                return fallback;
            }
        };

        const home =
            safe(ev, "homeTeam.name") ||
            safe(ev, "home.name") ||
            safe(ev, "homeTeam.shortName") ||
            "Home";

        const away =
            safe(ev, "awayTeam.name") ||
            safe(ev, "away.name") ||
            safe(ev, "awayTeam.shortName") ||
            "Away";

        const homeScore =
            safe(ev, "homeScore.display") ??
            safe(ev, "homeScore.current") ??
            safe(ev, "homeScore.normaltime") ??
            safe(ev, "homeScore", 0);

        const awayScore =
            safe(ev, "awayScore.display") ??
            safe(ev, "awayScore.current") ??
            safe(ev, "awayScore.normaltime") ??
            safe(ev, "awayScore", 0);

        const status =
            safe(ev, "status.type") ||
            safe(ev, "status.description") ||
            safe(ev, "status", "UNKNOWN");

        const minute =
            safe(ev, "time.minute") ??
            safe(ev, "time.currentPeriodStartMinute") ??
            safe(ev, "time", null);

        const tournament =
            safe(ev, "tournament.name") ||
            safe(ev, "league.name") ||
            null;

        const country =
            safe(ev, "tournament.category.name") ||
            safe(ev, "league.country") ||
            null;

        const id =
            safe(ev, "id") ||
            safe(ev, "matchId") ||
            safe(ev, "eventId") ||
            `${home}-${away}-${status}`;

        let bucket = "upcoming";
        const s = (status || "").toString().toLowerCase();
        if (s.includes("live") || s === "inprogress") bucket = "live";
        else if (s.includes("finished") || s === "ft") bucket = "recent";

        return {
            id,
            home,
            away,
            score: `${homeScore} - ${awayScore}`,
            minute: minute ? `${minute}'` : "-",
            status,
            league: tournament,
            country,
            bucket,
            _raw: ev
        };
    });

    return matches;
}

function showSkeleton(show) {
    liveSkeleton.style.display = show ? "flex" : "none";
}

function showPlaceholder(show) {
    livePlaceholder.style.display = show ? "block" : "none";
}

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

        // goal flash detection
        const key = m.id || `${m.home}-${m.away}`;
        const prevScore = lastScoreMap.get(key);
        if (prevScore && prevScore !== m.score && m.bucket === "live") {
            card.classList.add("aiml-goal-card");
            triggerGoalOverlay();
        }
        lastScoreMap.set(key, m.score);

        card.innerHTML = `
            <div class="aiml-match-header">
                <div>${m.home} vs ${m.away}</div>
                <div class="aiml-match-score">${m.score}</div>
            </div>
            <div class="aiml-match-subrow">
                ${m.league || ""} ${m.country ? " • " + m.country : ""}
            </div>
            <div class="aiml-match-badges">
                <span class="aiml-chip ${m.bucket === "live" ? "aiml-chip-live" : ""}">${m.status || "-"}</span>
                <span class="aiml-chip">${m.minute}</span>
                <span class="aiml-chip ${m.bucket === "upcoming" ? "aiml-chip-upcoming" : ""}">Bucket: ${m.bucket}</span>
                <span class="aiml-chip">ID: ${m.id || "n/a"}</span>
            </div>
        `;
        liveContainer.appendChild(card);
    });
}

function triggerGoalOverlay() {
    if (!goalOverlay) return;
    goalOverlay.style.display = "flex";
    setTimeout(() => {
        goalOverlay.style.display = "none";
    }, 1200);
}

async function loadLive(filterForApi = "live") {
    showSkeleton(true);
    showPlaceholder(false);

    let endpoint = API_LIVE;
    if (filterForApi === "recent") endpoint = API_RECENT;
    if (filterForApi === "upcoming") endpoint = API_UPCOMING;

    const data = await fetchJSON(endpoint);

    liveDebugBox.textContent = JSON.stringify(data, null, 2);

    if (data._fetchError || data._parseError || data.ok === false) {
        feedStatusValue.textContent = "Feed error";
        feedStatusValue.classList.remove("aiml-summary-ok");
        feedStatusValue.classList.add("aiml-summary-issue");
        feedSummaryCaption.textContent = data.message || "Worker feed unreachable";

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
            source: endpoint,
            matches_preview: matches.slice(0, 5)
        },
        null,
        2
    );

    showSkeleton(false);
    renderMatches(currentFilter);
}

// =======================================================
// TABS & FILTER
// =======================================================

function setActiveTab(filter) {
    currentFilter = filter;
    [btnAll, btnLive, btnRecent, btnUpcoming].forEach((btn) =>
        btn.classList.remove("aiml-tab-active")
    );
    if (filter === "all") btnAll.classList.add("aiml-tab-active");
    if (filter === "live") btnLive.classList.add("aiml-tab-active");
    if (filter === "recent") btnRecent.classList.add("aiml-tab-active");
    if (filter === "upcoming") btnUpcoming.classList.add("aiml-tab-active");
    renderMatches(filter);
}

btnAll.addEventListener("click", () => setActiveTab("all"));
btnLive.addEventListener("click", () => setActiveTab("live"));
btnRecent.addEventListener("click", () => setActiveTab("recent"));
btnUpcoming.addEventListener("click", () => setActiveTab("upcoming"));

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
// MAIN REFRESH CYCLE
// =======================================================

async function refreshAll() {
    await Promise.all([loadStatus(), loadLive("live")]);
}

refreshBtn.addEventListener("click", () => {
    refreshAll();
});

// Auto-refresh
setInterval(() => {
    refreshAll();
}, 15000);

// =======================================================
// INIT
// =======================================================

(function init() {
    initTheme();
    setActiveTab("all");
    backendStatusValue.textContent = "Online";

    refreshAll();

    console.log("[AIML] Premium engine initialised v0.9.3.");
})();
