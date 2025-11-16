// ============================================================
// AI MATCHLAB – FRONTEND ENGINE (v1.0.0)
// - Backend health
// - Worker /status
// - Live feed (/ai/source-a/live via backend proxy)
// - Rendering: LIVE / RECENT / UPCOMING
// - Raw debug panels
// - PWA Install logic (Android + iOS support)
// ============================================================

// =============== API ENDPOINTS ===============

// FastAPI backend (μένει ίδιο)
const API_BACKEND_HEALTH = "/health";

// Worker endpoints (ΝΕΑ B-μορφή paths)
const WORKER_BASE = "https://ai-matchlab-live-proxy.pierros1402.workers.dev";

const API_WORKER_STATUS = `${WORKER_BASE}/status`;
const API_LIVE_FEED     = `${WORKER_BASE}/ai/source-a/live`;

// =============== INSTALL PROMPT HANDLER ===============
let deferredPrompt = null;

// DOM helper
function $(id) {
    return document.getElementById(id);
}

// Apply pill visual state
function setStatusPill(el, state, text) {
    if (!el) return;
    el.classList.remove("status-ok", "status-error", "status-warn", "status-unknown");

    switch (state) {
        case "ok": el.classList.add("status-ok"); break;
        case "error": el.classList.add("status-error"); break;
        case "warn": el.classList.add("status-warn"); break;
        default: break;
    }

    if (text) el.textContent = text;
}

function formatTime(date) {
    return date.toLocaleTimeString("en-GB", { hour12: false });
}
// ============================================================
// BACKEND HEALTH CHECK
// ============================================================

async function checkBackendHealth() {
    const pill = $("aml-backend-status");

    try {
        const res = await fetch(API_BACKEND_HEALTH, { cache: "no-store" });
        const data = await res.json();

        if (data.ok) {
            setStatusPill(pill, "ok", "Online");
        } else {
            setStatusPill(pill, "warn", "Degraded");
        }
    } catch (error) {
        setStatusPill(pill, "error", "Offline");
    }
}


// ============================================================
// WORKER STATUS (/status)
// ============================================================

async function checkWorkerStatus() {
    const pill = $("aml-worker-status");
    const rawPre = $("aml-worker-status-raw");

    try {
        const res = await fetch(API_WORKER_STATUS, { cache: "no-store" });
        const data = await res.json();

        rawPre.textContent = JSON.stringify(data, null, 2);

        if (data.ok) {
            setStatusPill(pill, "ok", "OK");
        } else {
            setStatusPill(pill, "warn", "Issue");
        }

    } catch (error) {
        setStatusPill(pill, "error", "Error");
        rawPre.textContent = "Worker status failed: " + String(error);
    }
}
// ============================================================
// NORMALIZE LIVE FEED PAYLOAD
// ============================================================

function normalizeMatchesFromPayload(payload) {
    // Ιδανικό σχήμα:
    // { matches: [...], meta: {...} }
    if (!payload) return [];

    if (Array.isArray(payload.matches)) {
        return payload.matches;
    }

    // Αν είναι ήδη array, το παίρνουμε όπως είναι
    if (Array.isArray(payload)) {
        return payload;
    }

    // Αν είναι απλό object (όπως jsonplaceholder demo),
    // φτιάχνουμε ένα debug match
    if (!payload.matches) {
        return [
            {
                id: "debug_1",
                home: String(payload.title || "Demo Home"),
                away: "Demo Away",
                league: "Debug Feed",
                kickoff: "",
                status: "debug",
                minute: null,
                score_home: 0,
                score_away: 0,
                kind: "debug"
            }
        ];
    }

    return [];
}


// ============================================================
// FILTER MATCHES BY VIEW (all / live / recent / upcoming)
// ============================================================

function filterMatches(matches, view) {
    if (view === "all") return matches;

    return matches.filter((m) => {
        const kind = (m.kind || "").toLowerCase();

        if (view === "live") {
            return kind === "live" || kind === "live_sim";
        }
        if (view === "recent") {
            return kind === "recent";
        }
        if (view === "upcoming") {
            return kind === "upcoming";
        }
        return true;
    });
}


// ============================================================
// RENDER MATCH CARDS  (FULL FUNCTION)
// ============================================================

function renderMatches(matches) {
    const container = $("aml-live-container");
    if (!container) return;

    container.innerHTML = "";

    if (!matches || !matches.length) {
        const div = document.createElement("div");
        div.className = "aml-placeholder";
        div.textContent = "No matches available (yet).";
        container.appendChild(div);
        return;
    }

    matches.forEach((m) => {
        const card = document.createElement("div");
        card.className = "aml-card";

        const league = m.league || "Unknown League";
        const home = m.home || "Home";
        const away = m.away || "Away";
        const kickoff = m.kickoff || "";
        const status = (m.status || "unknown").toLowerCase();
        const minute = m.minute;
        const kind = (m.kind || "").toLowerCase();

        const scoreHome = m.score_home ?? m.home_score ?? "-";
        const scoreAway = m.score_away ?? m.away_score ?? "-";

        // Header
        const header = document.createElement("div");
        header.className = "aml-card-header";
        header.innerHTML = `
            <div class="aml-card-league">${league}</div>
            <div class="aml-card-teams">${home} vs ${away}</div>
            <div class="aml-card-meta">
                ${kickoff ? kickoff : "No kickoff data"} · ${status}
            </div>
        `;

        // Score
        const score = document.createElement("div");
        score.className = "aml-card-score";
        score.innerHTML = `
            <div class="aml-score-main">${scoreHome} : ${scoreAway}</div>
            <div class="aml-score-minute">${minute != null ? minute + "'" : ""}</div>
        `;

        // Tags
        const tags = document.createElement("div");
        tags.className = "aml-card-tags";

        const tag = document.createElement("span");
        tag.className = "aml-tag";

        if (kind === "live" || kind === "live_sim") {
            tag.classList.add("aml-tag-live");
            tag.textContent = "LIVE";
        } else if (kind === "recent") {
            tag.classList.add("aml-tag-recent");
            tag.textContent = "RECENT";
        } else if (kind === "upcoming") {
            tag.classList.add("aml-tag-upcoming");
            tag.textContent = "UPCOMING";
        } else if (kind === "debug") {
            tag.classList.add("aml-tag-debug");
            tag.textContent = "DEBUG FEED";
        } else {
            tag.textContent = kind || "UNKNOWN";
        }

        tags.appendChild(tag);

        // Attach parts
        card.appendChild(header);
        card.appendChild(score);
        card.appendChild(tags);

        // 🔥 GOAL FLASH EFFECT (προστέθηκε εδώ)
        applyGoalFlashIfNeeded(m, card);

        container.appendChild(card);
    });
}
// ============================================================
// FETCH LIVE FEED
// ============================================================

async function fetchLiveFeed(manual = false) {
    const pill = $("aml-feed-status");
    const rawPre = $("aml-live-raw");

    try {
        if (manual) {
            setStatusPill(pill, "warn", "Refreshing…");
        } else {
            setStatusPill(pill, "warn", "Updating…");
        }

        const res = await fetch(API_LIVE_FEED, { cache: "no-store" });
        const data = await res.json();

        rawPre.textContent = JSON.stringify(data, null, 2);

        // Normalize matches
        const matches = normalizeMatchesFromPayload(data);
        liveDataCache = matches;

        const filtered = filterMatches(matches, currentViewFilter);
        renderMatches(filtered);

        setStatusPill(pill, "ok", `OK (${matches.length})`);

        const now = new Date();
        const lastUpdateEl = $("aml-last-update");
        if (lastUpdateEl) {
            lastUpdateEl.textContent = formatTime(now);
        }

    } catch (error) {
        setStatusPill(pill, "error", "Feed error");
        if (rawPre) {
            rawPre.textContent = "Live feed error: " + String(error);
        }
    }
}
// ============================================================
// VIEW FILTER CHIPS (ALL / LIVE / RECENT / UPCOMING)
// ============================================================

function initViewChips() {
    const chips = document.querySelectorAll(".aml-chip");

    chips.forEach((chip) => {
        chip.addEventListener("click", () => {
            const view = chip.getAttribute("data-view") || "all";
            currentViewFilter = view;

            // active chip styling
            chips.forEach((c) => c.classList.remove("aml-chip-active"));
            chip.classList.add("aml-chip-active");

            // render filtered results
            if (liveDataCache) {
                const filtered = filterMatches(liveDataCache, currentViewFilter);
                renderMatches(filtered);
            }
        });
    });
}


// ============================================================
// AUTO REFRESH LOOP
// ============================================================

function initRefreshLoop() {
    if (refreshTimer) clearInterval(refreshTimer);

    refreshTimer = setInterval(() => {
        fetchLiveFeed(false);
    }, REFRESH_INTERVAL_MS);
}


// ============================================================
// MANUAL REFRESH BUTTON
// ============================================================

function initManualRefresh() {
    const btn = $("aml-refresh-btn");
    if (!btn) return;

    btn.addEventListener("click", () => {
        fetchLiveFeed(true);
    });
}
// ============================================================
// PWA INSTALL HANDLING (ANDROID + IOS)
// ============================================================

// Save event for Android/desktop install
window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredPrompt = event;

    const btn = $("aml-install-btn");
    if (btn) btn.classList.remove("hidden");
});

function initPwaInstallButton() {
    const btn = $("aml-install-btn");
    if (!btn) return;

    // Detect iOS (iPhone/iPad)
    const isIos = /iphone|ipad|ipod/i.test(navigator.userAgent);
    const isStandalone = window.matchMedia("(display-mode: standalone)").matches;

    // =============== iOS MODE ===============
    if (isIos && !isStandalone) {
        btn.classList.remove("hidden");
        btn.textContent = "📱 Add to Home Screen";
        btn.addEventListener("click", () => {
            alert(
                "Για iPhone/iPad:\n\n" +
                "1. Πάτα το κουμπί Share (τετράγωνο με το βελάκι)\n" +
                "2. Επίλεξε 'Add to Home Screen'\n\n" +
                "Αυτός είναι ο επίσημος τρόπος εγκατάστασης σε iOS."
            );
        });
        return;
    }

    // =============== ANDROID / DESKTOP MODE ===============
    btn.addEventListener("click", async () => {
        if (!deferredPrompt) return;

        deferredPrompt.prompt();
        const result = await deferredPrompt.userChoice;

        // whatever the user picks, hide the button
        deferredPrompt = null;
        btn.classList.add("hidden");
    });
}
// ============================================================
// DOMContentLoaded → STARTUP SEQUENCE
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    // View chips (all / live / recent / upcoming)
    initViewChips();

    // Refresh now button
    initManualRefresh();

    // Backend health status
    checkBackendHealth();

    // Worker /status panel
    checkWorkerStatus();

    // First live load
    fetchLiveFeed(false);

    // Auto-refresh loop
    initRefreshLoop();

    // Install app logic (Android + iOS)
    initPwaInstallButton();
});
// ============================================================
// GOAL CHANGE DETECTION + FLASH ANIMATION
// ============================================================

// Αποθηκεύουμε παλιά σκορ για να εντοπίσουμε αλλαγές
const previousScores = new Map();

function applyGoalFlashIfNeeded(match, cardElement) {
    const key = match.id;
    if (!key) return;

    const prev = previousScores.get(key);
    const current = `${match.score_home}-${match.score_away}`;

    // Αν υπάρχει παλιό score και το σκορ άλλαξε → flash
    if (prev && prev !== current) {
        const scoreBlock = cardElement.querySelector(".aml-card-score");
        if (scoreBlock) {
            scoreBlock.classList.add("aml-goal-flash");

            // Αφαιρούμε το animation μετά από 1s
            setTimeout(() => {
                scoreBlock.classList.remove("aml-goal-flash");
            }, 900);
        }
    }

    // Αποθήκευση για επόμενο tick
    previousScores.set(key, current);
}
