/* ============================================================
   AI MATCHLAB — MAIN JAVASCRIPT CONTROLLER
   Handles:
   - Worker communication
   - Panel switching
   - DOM updates
   - Loading UI
   - Overview Panel
   - Bookmakers Compare Panel (Stoiximan/OPAP/Pame mock odds)
   ============================================================ */

console.log("AI MATCHLAB JS Loaded.");

let BOOKMAKERS_STATE = {
    matches: []
};


// ------------------------------------------------------------
// SHOW/HIDE LOADING
// ------------------------------------------------------------
function showLoading() {
    const box = document.getElementById("loading");
    if (box) box.classList.remove("hidden");
}

function hideLoading() {
    const box = document.getElementById("loading");
    if (box) box.classList.add("hidden");
}


// ------------------------------------------------------------
/* GENERIC WORKER CALL (GET) */
// ------------------------------------------------------------
async function callWorker(path, params = {}) {
    try {
        showLoading();

        const usp = new URLSearchParams(params);
        const qs = usp.toString();
        const url = qs ? `/api/worker/${path}?${qs}` : `/api/worker/${path}`;

        const response = await fetch(url);

        if (!response.ok) {
            console.error("Worker error:", response.status);
            throw new Error("Worker returned error");
        }

        return await response.json();

    } catch (err) {
        console.error("Worker call failed:", err);
        return { error: "Worker connection failed" };
    } finally {
        hideLoading();
    }
}


// ------------------------------------------------------------
// PANEL LOADER (MAIN ENTRY)
// ------------------------------------------------------------
async function loadPanel(panel) {
    const title = document.getElementById("panel-title");
    const container = document.getElementById("panel-content");

    title.innerText = panel.charAt(0).toUpperCase() + panel.slice(1);

    container.innerHTML = `
        <div class="placeholder">
            Loading ${panel}...
        </div>
    `;

    // Worker path mapping
    const workerPath = {
        "overview": "live/overview",
        "live": "live/overview",
        "predictions": "aimatchlab/predictions",
        "smartmoney": "aimatchlab/smartmoney",
        "heatmaps": "aimatchlab/heatmaps",
        "stats": "aimatchlab/stats",
        "bookmakers": "live/overview"
    }[panel] || `aimatchlab/${panel}`;

    const data = await callWorker(workerPath);

    if (panel === "overview") {
        renderOverviewPanel(data);
        return;
    }

    if (panel === "bookmakers") {
        renderBookmakersPanel(data);
        return;
    }

    // Generic render for other panels
    renderPanelData(panel, data);
}



// ------------------------------------------------------------
// OVERVIEW PANEL (Featured Matches + Quick Summary)
// ------------------------------------------------------------
function renderOverviewPanel(data) {
    const container = document.getElementById("panel-content");

    const matches = extractMatches(data);
    const featured = matches.slice(0, 6);

    if (!featured.length) {
        container.innerHTML = `
            <div class="placeholder">
                No live matches available right now.<br>
                Try again in a few minutes.
            </div>
        `;
        return;
    }

    const totalMatches = matches.length;
    const leaguesSet = new Set(
        matches.map(m => getField(m, ["league", "competition", "tournament"], "Unknown"))
    );
    const totalLeagues = leaguesSet.size;

    let html = `
        <div style="display:flex; gap:16px; margin-bottom:16px; flex-wrap:wrap;">
            <div class="panel" style="flex:1; min-width:200px;">
                <div class="placeholder" style="padding:10px; text-align:left;">
                    <div style="font-size:12px; text-transform:uppercase; color:#9ca3af;">Total Matches</div>
                    <div style="font-size:24px; font-weight:700;">${totalMatches}</div>
                </div>
            </div>
            <div class="panel" style="flex:1; min-width:200px;">
                <div class="placeholder" style="padding:10px; text-align:left;">
                    <div style="font-size:12px; text-transform:uppercase; color:#9ca3af;">Leagues</div>
                    <div style="font-size:24px; font-weight:700;">${totalLeagues}</div>
                </div>
            </div>
        </div>
    `;

    html += `
        <div class="panel">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div style="font-weight:600;">Featured Matches</div>
                <div style="font-size:12px; color:#9ca3af;">(Top ${featured.length} from live hub)</div>
            </div>
    `;

    html += `<table class="data-table"><thead><tr>
        <th>League</th>
        <th>Match</th>
        <th>Kickoff</th>
        <th>Status</th>
    </tr></thead><tbody>`;

    featured.forEach(m => {
        const league = getField(m, ["league", "competition", "tournament"], "Unknown");
        const home = getField(m, ["home", "home_team", "team_home", "homeName"], "Home");
        const away = getField(m, ["away", "away_team", "team_away", "awayName"], "Away");
        const status = getField(m, ["status", "live_status"], "-");
        const kickoff = getField(m, ["kickoff", "start_time", "time"], "-");

        html += `
            <tr>
                <td>${league}</td>
                <td>${home} vs ${away}</td>
                <td>${kickoff}</td>
                <td>${status}</td>
            </tr>
        `;
    });

    html += `</tbody></table></div>`;

    html += `
        <div style="margin-top:16px; text-align:right; font-size:13px; color:#9ca3af;">
            Full odds comparison available in <strong>Bookmakers Compare</strong> panel.
        </div>
    `;

    container.innerHTML = html;
}



// ------------------------------------------------------------
// BOOKMAKERS COMPARE PANEL
// ------------------------------------------------------------
function renderBookmakersPanel(data) {
    const container = document.getElementById("panel-content");

    const matches = extractMatches(data);

    if (!matches.length) {
        container.innerHTML = `
            <div class="placeholder">
                No live matches available from live hub.
            </div>
        `;
        return;
    }

    // Enrich with mock odds for 3 Greek bookmakers
    BOOKMAKERS_STATE.matches = matches.map(m => ({
        ...m,
        odds: {
            stoiximan: generateMockOdds(m, "stoiximan"),
            opap: generateMockOdds(m, "opap"),
            pame: generateMockOdds(m, "pame")
        }
    }));

    // Build league list
    const leagueSet = new Set(
        BOOKMAKERS_STATE.matches.map(m =>
            getField(m, ["league", "competition", "tournament"], "Unknown")
        )
    );
    const leagues = Array.from(leagueSet).sort();

    let html = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:8px;">
            <div style="font-weight:600;">Bookmakers Compare — Full Match List</div>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
                <select id="bm-league-filter" style="padding:4px 8px; border-radius:8px; border:1px solid #1f2937; background:#111827; color:#e5e7eb;">
                    <option value="">All Leagues</option>
                    ${leagues.map(l => `<option value="${escapeHtml(l)}">${escapeHtml(l)}</option>`).join("")}
                </select>
                <input id="bm-search" type="text" placeholder="Search match..."
                       style="padding:4px 8px; border-radius:8px; border:1px solid #1f2937; background:#111827; color:#e5e7eb; min-width:180px;" />
            </div>
        </div>

        <div style="overflow-x:auto;">
            <table class="data-table" id="bm-table">
                <thead>
                    <tr>
                        <th>League</th>
                        <th>Match</th>
                        <th>Kickoff</th>
                        <th>Market</th>
                        <th>Stoiximan</th>
                        <th>OPAP</th>
                        <th>Pamestoixima</th>
                        <th>Best</th>
                    </tr>
                </thead>
                <tbody id="bm-tbody"></tbody>
            </table>
        </div>
    `;

    container.innerHTML = html;

    const leagueSelect = document.getElementById("bm-league-filter");
    const searchInput = document.getElementById("bm-search");

    leagueSelect.addEventListener("change", updateBookmakersTableBody);
    searchInput.addEventListener("input", updateBookmakersTableBody);

    updateBookmakersTableBody();
}


function updateBookmakersTableBody() {
    const tbody = document.getElementById("bm-tbody");
    if (!tbody) return;

    const leagueFilter = document.getElementById("bm-league-filter")?.value || "";
    const search = (document.getElementById("bm-search")?.value || "").toLowerCase();

    const rows = [];

    BOOKMAKERS_STATE.matches.forEach(m => {
        const league = getField(m, ["league", "competition", "tournament"], "Unknown");
        const home = getField(m, ["home", "home_team", "team_home", "homeName"], "Home");
        const away = getField(m, ["away", "away_team", "team_away", "awayName"], "Away");
        const kickoff = getField(m, ["kickoff", "start_time", "time"], "-");

        if (leagueFilter && league !== leagueFilter) return;

        const matchLabel = `${home} vs ${away}`.toLowerCase();
        if (search && !matchLabel.includes(search)) return;

        const odds = m.odds || {};
        const markets = ["1", "X", "2", "over_2_5", "under_2_5", "gg", "ng"];
        const marketLabels = {
            "1": "1",
            "X": "X",
            "2": "2",
            "over_2_5": "Over 2.5",
            "under_2_5": "Under 2.5",
            "gg": "GG",
            "ng": "NG"
        };

        markets.forEach(market => {
            const s = odds.stoiximan?.[market]?.price ?? "-";
            const o = odds.opap?.[market]?.price ?? "-";
            const p = odds.pame?.[market]?.price ?? "-";

            const prices = [
                { name: "Stoiximan", val: typeof s === "number" ? s : null },
                { name: "OPAP", val: typeof o === "number" ? o : null },
                { name: "Pame", val: typeof p === "number" ? p : null }
            ];

            let bestName = null;
            let bestVal = -1;
            prices.forEach(item => {
                if (item.val !== null && item.val > bestVal) {
                    bestVal = item.val;
                    bestName = item.name;
                }
            });

            rows.push(`
                <tr>
                    <td>${escapeHtml(league)}</td>
                    <td>${escapeHtml(home)} vs ${escapeHtml(away)}</td>
                    <td>${escapeHtml(kickoff)}</td>
                    <td>${marketLabels[market] || market}</td>
                    <td>${formatPriceWithBest(s, bestName === "Stoiximan")}</td>
                    <td>${formatPriceWithBest(o, bestName === "OPAP")}</td>
                    <td>${formatPriceWithBest(p, bestName === "Pame")}</td>
                    <td>${bestName ? `<span class="status-green">${bestName}</span>` : "-"}</td>
                </tr>
            `);
        });
    });

    tbody.innerHTML = rows.join("") || `
        <tr><td colspan="8" style="text-align:center; padding:20px;">No matches found for selected filters.</td></tr>
    `;
}


function formatPriceWithBest(price, isBest) {
    if (price === "-" || price === null || price === undefined) return "-";
    const val = typeof price === "number" ? price.toFixed(2) : price;
    if (!isBest) return val;
    return `<span class="status-green" style="font-weight:600;">${val}</span>`;
}



// ------------------------------------------------------------
// GENERIC PANEL RENDERING (for other panels)
// ------------------------------------------------------------
function renderPanelData(panel, data) {
    const container = document.getElementById("panel-content");

    // Error case
    if (!data || data.error) {
        container.innerHTML = `
            <div class="panel-error">
                <p style="color:#ff476f; font-size:16px;">
                    ❌ Failed to load data from Worker
                </p>
            </div>`;
        return;
    }

    if (typeof data === "string") {
        container.innerHTML = `<pre>${data}</pre>`;
        return;
    }

    if (Array.isArray(data)) {
        container.innerHTML = generateTable(data);
        return;
    }

    if (typeof data === "object") {
        container.innerHTML = objectToTable(data);
        return;
    }

    container.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
}



// ------------------------------------------------------------
// TABLE GENERATORS (generic)
// ------------------------------------------------------------
function generateTable(rows) {
    if (!rows.length) {
        return `<div class="placeholder">No data available.</div>`;
    }

    const columns = Object.keys(rows[0]);

    let html = `<table class="data-table"><thead><tr>`;
    columns.forEach(col => {
        html += `<th>${col}</th>`;
    });
    html += `</tr></thead><tbody>`;

    rows.forEach(row => {
        html += `<tr>`;
        columns.forEach(col => {
            html += `<td>${formatCell(row[col])}</td>`;
        });
        html += `</tr>`;
    });

    html += `</tbody></table>`;
    return html;
}


function objectToTable(obj) {
    let html = `<table class="data-table"><tbody>`;

    for (const key in obj) {
        html += `
            <tr>
                <th>${key}</th>
                <td>${formatCell(obj[key])}</td>
            </tr>
        `;
    }

    html += `</tbody></table>`;
    return html;
}


function formatCell(v) {
    if (v === null || v === undefined) return "-";
    if (typeof v === "boolean") return v ? "Yes" : "No";
    if (typeof v === "number") {
        return Number(v.toFixed(3));
    }
    if (typeof v === "object") {
        return JSON.stringify(v);
    }
    return v;
}



// ------------------------------------------------------------
// HELPERS
// ------------------------------------------------------------
function extractMatches(data) {
    if (!data) return [];
    if (Array.isArray(data.matches)) return data.matches;
    if (data.data && Array.isArray(data.data.matches)) return data.data.matches;
    if (Array.isArray(data.data)) return data.data;
    return [];
}

function getField(obj, keys, fallback = "") {
    if (!obj) return fallback;
    for (const k of keys) {
        if (obj[k] !== undefined && obj[k] !== null) {
            return obj[k];
        }
    }
    return fallback;
}

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}


// ------------------------------------------------------------
// MOCK ODDS GENERATION (Stoiximan / OPAP / Pame)
// ------------------------------------------------------------
function generateMockOdds(match, bookmakerKey) {
    // Μικρή διαφοροποίηση ανά bookmaker για να φαίνεται ρεαλιστικό
    const baseSeed = (String(match.id || match.match_id || match.uid || match.home || "") + bookmakerKey)
        .split("")
        .reduce((acc, ch) => acc + ch.charCodeAt(0), 0);

    function randOffset(mult = 0.15) {
        const r = Math.sin(baseSeed + Math.random()) * 10000;
        const frac = r - Math.floor(r);
        return (frac - 0.5) * mult; // -mult/2 .. +mult/2
    }

    // Βασικές αποδόσεις
    let home = 1.70 + randOffset(0.40);
    let draw = 3.40 + randOffset(0.40);
    let away = 4.20 + randOffset(0.40);

    const over25 = 1.75 + randOffset(0.30);
    const under25 = 2.05 + randOffset(0.30);
    const gg = 1.65 + randOffset(0.25);
    const ng = 2.20 + randOffset(0.25);

    function clampOdd(x) {
        return Math.max(1.10, Number(x.toFixed(2)));
    }

    return {
        "1": { price: clampOdd(home) },
        "X": { price: clampOdd(draw) },
        "2": { price: clampOdd(away) },
        "over_2_5": { price: clampOdd(over25) },
        "under_2_5": { price: clampOdd(under25) },
        "gg": { price: clampOdd(gg) },
        "ng": { price: clampOdd(ng) }
    };
}



// ------------------------------------------------------------
// TOP BAR BUTTONS
// ------------------------------------------------------------
function refreshData() {
    const title = document.getElementById("panel-title");
    const panel = title.innerText.toLowerCase();
    loadPanel(panel);
}

function openWorkspace() {
    window.location.href = "/workspace";
}


// Auto-load overview at startup
window.addEventListener("DOMContentLoaded", () => {
    loadPanel("overview");
});
