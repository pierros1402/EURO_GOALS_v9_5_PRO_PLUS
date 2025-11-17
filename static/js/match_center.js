// =======================================================
// AI MATCHLAB – MATCH CENTER (Unified Worker Version)
// v0.9.3 — Full worker integration
// =======================================================

(function () {
    // ========== DOM REFS ==========
    const mcLeague = document.getElementById("mcLeague");
    const mcStatus = document.getElementById("mcStatus");
    const mcMinute = document.getElementById("mcMinute");
    const mcBucket = document.getElementById("mcBucket");
    const mcHomeName = document.getElementById("mcHomeName");
    const mcAwayName = document.getElementById("mcAwayName");
    const mcHomeExtra = document.getElementById("mcHomeExtra");
    const mcAwayExtra = document.getElementById("mcAwayExtra");
    const mcScore = document.getElementById("mcScore");
    const mcKickoff = document.getElementById("mcKickoff");
    const mcOverviewText = document.getElementById("mcOverviewText");
    const mcDebugBox = document.getElementById("mcDebugBox");
    const mcEndpointLabel = document.getElementById("mcEndpointLabel");

    const tabOverview = document.getElementById("mcTabOverview");
    const tabEvents = document.getElementById("mcTabEvents");
    const tabLineups = document.getElementById("mcTabLineups");
    const tabStats = document.getElementById("mcTabStats");

    const panelOverview = document.getElementById("mcOverviewPanel");
    const panelEvents = document.getElementById("mcEventsPanel");
    const panelLineups = document.getElementById("mcLineupsPanel");
    const panelStats = document.getElementById("mcStatsPanel");
    const eventsList = document.getElementById("mcEventsList");

    // CHANGE THIS ONLY IF THE DOMAIN CHANGES
    const WORKER_BASE = "https://aimatchlab.pierros1402.workers.dev";

    // ======================================================
    // HELPERS
    // ======================================================
    function safe(obj, path, fallback = null) {
        try {
            return path.split(".").reduce((acc, key) => acc?.[key], obj) ?? fallback;
        } catch {
            return fallback;
        }
    }

    async function fetchJSON(url) {
        try {
            const res = await fetch(url, { headers: { "accept": "application/json" } });
            return await res.json();
        } catch (e) {
            return { ok: false, error: String(e) };
        }
    }

    function parseMatches(data) {
        if (!data) return [];
        if (Array.isArray(data.matches)) return data.matches;
        if (Array.isArray(data.events)) return data.events;
        return [];
    }

    function setTabs(active) {
        [
            [tabOverview, panelOverview, "overview"],
            [tabEvents, panelEvents, "events"],
            [tabLineups, panelLineups, "lineups"],
            [tabStats, panelStats, "stats"],
        ].forEach(([btn, panel, key]) => {
            btn.classList.toggle("aiml-tab-active", key === active);
            panel.style.display = key === active ? "block" : "none";
        });
    }

    function buildOverviewText(match) {
        const home = match.home || match.strHomeTeam || "Home";
        const away = match.away || match.strAwayTeam || "Away";
        const league = match.league || match.strLeague || "League";
        const status = match.status || match.strStatus || "UNKNOWN";
        const minute = match.minute || "-";
        const kickoff = match.kickoff || match.date || "";

        return `${home} vs ${away} — ${league}\nStatus: ${status} (${minute}')\n${kickoff ? "Kickoff: " + kickoff : ""}`;
    }

    function renderEvents(match) {
        eventsList.innerHTML = "";
        const rawEvents = match.events || [];

        if (!rawEvents.length) {
            const li = document.createElement("li");
            li.className = "aiml-event-row";
            li.textContent = "No events available.";
            eventsList.appendChild(li);
            return;
        }

        rawEvents.forEach(ev => {
            const li = document.createElement("li");
            li.className = "aiml-event-row";
            const minute = ev.minute ?? "-";
            const type = ev.type ?? "Event";
            const player = ev.player ? ` (${ev.player})` : "";
            li.textContent = `${minute}' — ${type}${player}`;
            eventsList.appendChild(li);
        });
    }

    // ======================================================
    // MAIN FLOW
    // ======================================================
    async function init() {
        // URL example: /match_center?id=123&bucket=live
        const q = new URLSearchParams(window.location.search);
        const matchId = q.get("id");
        const bucket = q.get("bucket") || "live";

        if (!matchId) {
            mcOverviewText.textContent = "Error: missing match ID.";
            return;
        }

        // -----------------------------
        // 1) LOAD MATCH DETAILS
        // -----------------------------
        const MATCH_URL = `${WORKER_BASE}/api/match?id=${matchId}`;

        mcEndpointLabel.textContent = MATCH_URL;

        const payload = await fetchJSON(MATCH_URL);
        mcDebugBox.textContent = JSON.stringify(payload, null, 2);

        if (!payload.ok || !payload.match) {
            mcOverviewText.textContent = "Match not found in worker.";
            return;
        }

        const match = payload.match;

        // -----------------------------
        // 2) RENDER BASIC INFO
        // -----------------------------
        const home = match.home || match.strHomeTeam || "Home";
        const away = match.away || match.strAwayTeam || "Away";
        const league = match.league || match.strLeague || "League";
        const status = match.status || "UNKNOWN";
        const minute = match.minute || "-";
        const kickoff = match.kickoff || "";

        const homeScore = match.score_home ?? match.homeScore ?? 0;
        const awayScore = match.score_away ?? match.awayScore ?? 0;

        mcLeague.textContent = league;
        mcStatus.textContent = status;
        mcMinute.textContent = minute;
        mcBucket.textContent = bucket;
        mcHomeName.textContent = home;
        mcAwayName.textContent = away;
        mcScore.textContent = `${homeScore} - ${awayScore}`;
        mcKickoff.textContent = kickoff ? `Kickoff: ${kickoff}` : "";

        mcOverviewText.textContent = buildOverviewText(match);

        // -----------------------------
        // 3) EVENTS
        // -----------------------------
        renderEvents(match);

        // Default tab
        setTabs("overview");
    }

    // ======================================================
    // TABS EVENTS
    // ======================================================
    tabOverview.addEventListener("click", () => setTabs("overview"));
    tabEvents.addEventListener("click", () => setTabs("events"));
    tabLineups.addEventListener("click", () => setTabs("lineups"));
    tabStats.addEventListener("click", () => setTabs("stats"));

    // ======================================================
    // START
    // ======================================================
    init();
})();
