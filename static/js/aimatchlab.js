// ============================================================================
// AI MATCHLAB v0.9.2 HYBRID PRO — FRONTEND ENGINE
// Compatible with AI MATCHLAB LIVE WORKER A2-FINAL-v3
// ============================================================================

console.log("🚀 AI MatchLab v0.9.2 HYBRID PRO loaded");

// ---------------------------------------------------------------------------
// CONFIG
// ---------------------------------------------------------------------------

const WORKER_BASE = "https://ai-matchlab-live-proxy.pierros1402.workers.dev/api";
const REFRESH_MS = 8000; // auto-refresh κάθε 8 δευτερόλεπτα

const statusBar = document.getElementById("statusBar");
const liveContainer = document.getElementById("liveContainer");
const debugPanel = document.getElementById("debugPanel");
const refreshBtn = document.getElementById("refreshBtn");

// ---------------------------------------------------------------------------
// HELPERS
// ---------------------------------------------------------------------------

async function fetchJSON(url) {
    try {
        const res = await fetch(url, { cache: "no-store" });
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

function safeGet(obj, path, fallback = null) {
    try {
        return path.split(".").reduce((acc, k) => (acc && acc[k] !== undefined ? acc[k] : null), obj) ?? fallback;
    } catch {
        return fallback;
    }
}

// ---------------------------------------------------------------------------
// STATUS HANDLING (/api/status)
// ---------------------------------------------------------------------------

async function updateStatus() {
    const url = `${WORKER_BASE}/status`;
    const data = await fetchJSON(url);

    if (data._fetchError || data._parseError) {
        statusBar.textContent = "Worker status: OFFLINE or INVALID RESPONSE";
        statusBar.style.color = "#ff6b6b";
        return data;
    }

    const version = data.version || data.workerVersion || "unknown";
    const ts = data.timestamp || new Date().toISOString();

    statusBar.textContent = `Worker status: OK • Version: ${version} • ${ts}`;
    statusBar.style.color = "#9ae66e";

    return data;
}

// ---------------------------------------------------------------------------
// LIVE HANDLING (/api/live)
// ---------------------------------------------------------------------------

async function fetchLiveRaw() {
    const url = `${WORKER_BASE}/live`;
    return await fetchJSON(url);
}

// Προσπαθούμε να "νορμαλάρουμε" Sofascore-style live δομή σε απλές κάρτες
function normalizeLiveData(raw) {
    if (!raw) return { matches: [], raw };

    // Sofascore συνήθως έχει raw.events ή raw.data.events
    let events = null;

    if (Array.isArray(raw.events)) {
        events = raw.events;
    } else if (Array.isArray(safeGet(raw, "data.events"))) {
        events = safeGet(raw, "data.events");
    } else if (Array.isArray(raw.data)) {
        events = raw.data;
    } else if (Array.isArray(raw.matches)) {
        events = raw.matches;
    }

    if (!events) {
        return { matches: [], raw };
    }

    const matches = events.map(ev => {
        // Προσπαθούμε να χαρτογραφήσουμε τυπική Sofascore δομή
        const homeName =
            safeGet(ev, "homeTeam.name") ||
            safeGet(ev, "home.name") ||
            safeGet(ev, "homeTeam.shortName") ||
            "Home";

        const awayName =
            safeGet(ev, "awayTeam.name") ||
            safeGet(ev, "away.name") ||
            safeGet(ev, "awayTeam.shortName") ||
            "Away";

        const homeScore =
            safeGet(ev, "homeScore.display") ??
            safeGet(ev, "homeScore.current") ??
            safeGet(ev, "homeScore.normaltime") ??
            safeGet(ev, "homeScore", 0);

        const awayScore =
            safeGet(ev, "awayScore.display") ??
            safeGet(ev, "awayScore.current") ??
            safeGet(ev, "awayScore.normaltime") ??
            safeGet(ev, "awayScore", 0);

        const statusType =
            safeGet(ev, "status.type") ||
            safeGet(ev, "status.description") ||
            safeGet(ev, "status") ||
            "UNKNOWN";

        const minute =
            safeGet(ev, "time.minute") ??
            safeGet(ev, "time.currentPeriodStartMinute") ??
            safeGet(ev, "time", null);

        const tournament =
            safeGet(ev, "tournament.name") ||
            safeGet(ev, "league.name") ||
            null;

        const categoryName =
            safeGet(ev, "tournament.category.name") ||
            safeGet(ev, "league.country") ||
            null;

        const id =
            safeGet(ev, "id") ||
            safeGet(ev, "matchId") ||
            safeGet(ev, "eventId") ||
            null;

        // Placeholder advanced fields (ακόμα δεν τα δίνει ο Worker)
        const placeholders = {
            xgHome: "—",
            xgAway: "—",
            momentum: "—",
            pressure: "—"
        };

        return {
            id,
            home: homeName,
            away: awayName,
            score: `${homeScore} - ${awayScore}`,
            status: statusType,
            minute: minute ?? "—",
            league: tournament,
            country: categoryName,
            placeholders,
            raw: ev
        };
    });

    return { matches, raw };
}

// ---------------------------------------------------------------------------
// RENDER LIVE UI
// ---------------------------------------------------------------------------

function renderLive(matches) {
    liveContainer.innerHTML = "";

    if (!matches || matches.length === 0) {
        liveContainer.innerHTML = `<div>No live matches available.</div>`;
        return;
    }

    matches.forEach(m => {
        const card = document.createElement("div");
        card.className = "matchCard";

        const statusColor =
            m.status === "inprogress" ||
            m.status === "LIVE" ||
            m.status === "live"
                ? "#4ade80"
                : m.status === "finished" || m.status === "FT"
                ? "#60a5fa"
                : "#e5e5e5";

        const leagueInfo = m.league
            ? `${m.league}${m.country ? " • " + m.country : ""}`
            : (m.country || "");

        card.innerHTML = `
            <div class="matchHeader">
                ${m.home} vs ${m.away}
            </div>
            <div class="subInfo">
                <span style="color:${statusColor};font-weight:bold;">${m.status}</span>
                &nbsp;•&nbsp;
                Min: ${m.minute}
                &nbsp;•&nbsp;
                Score: ${m.score}
            </div>
            ${
                leagueInfo
                    ? `<div class="subInfo" style="margin-top:4px;">${leagueInfo}</div>`
                    : ""
            }
            <div class="placeholderArea">
                <div>Advanced metrics (placeholders):</div>
                <div>xG Home: ${m.placeholders.xgHome} • xG Away: ${m.placeholders.xgAway}</div>
                <div>Momentum: ${m.placeholders.momentum} • Pressure: ${m.placeholders.pressure}</div>
            </div>
            <button class="inspectBtn">Inspect</button>
            <div class="inspectorBox"></div>
        `;

        const btn = card.querySelector(".inspectBtn");
        const inspectorBox = card.querySelector(".inspectorBox");

        btn.addEventListener("click", () => {
            if (inspectorBox.style.display === "block") {
                inspectorBox.style.display = "none";
                inspectorBox.textContent = "";
            } else {
                inspectorBox.style.display = "block";
                inspectorBox.textContent = JSON.stringify(m.raw, null, 2);
            }
        });

        liveContainer.appendChild(card);
    });
}

// ---------------------------------------------------------------------------
// DEBUG PANEL
// ---------------------------------------------------------------------------

function renderDebug(payload) {
    try {
        debugPanel.textContent = JSON.stringify(payload, null, 2);
    } catch {
        debugPanel.textContent = "Unable to render debug info.";
    }
}

// ---------------------------------------------------------------------------
// MAIN REFRESH LOOP
// ---------------------------------------------------------------------------

async function refreshAll() {
    const [statusData, liveRaw] = await Promise.all([
        updateStatus(),
        fetchLiveRaw()
    ]);

    const normalized = normalizeLiveData(liveRaw);

    renderLive(normalized.matches);

    renderDebug({
        status: statusData,
        liveRaw: liveRaw,
        normalizedPreview: normalized.matches.slice(0, 5)
    });
}

// ---------------------------------------------------------------------------
// EVENT LISTENERS
// ---------------------------------------------------------------------------

refreshBtn.addEventListener("click", () => {
    refreshAll();
});

// ---------------------------------------------------------------------------
// AUTO-REFRESH START
// ---------------------------------------------------------------------------

refreshAll();
setInterval(refreshAll, REFRESH_MS);
