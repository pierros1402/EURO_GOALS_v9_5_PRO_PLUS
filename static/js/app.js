/* ============================================================
   AI MATCHLAB — ENTERPRISE APP ENGINE
   Version: 1.0.0
   PWA install · Service Worker · Worker fetch loop · UI glue
   ============================================================ */

console.log("[AI MATCHLAB] app.js enterprise engine loaded");

/* ------------------------------------------------------------
   CONFIG
------------------------------------------------------------ */

const WORKER_ENDPOINT = "/worker/betfair/live"; // <-- εδώ θα βάζεις τον Worker σου
const FETCH_INTERVAL_MS = 5000;                 // κάθε 5s refresh
let deferredPrompt = null;

/* ------------------------------------------------------------
   HELPERS
------------------------------------------------------------ */

function $(id) {
    return document.getElementById(id);
}

function setText(id, value) {
    const el = $(id);
    if (el) el.textContent = value;
}

/* ------------------------------------------------------------
   PWA: BEFORE INSTALL PROMPT
------------------------------------------------------------ */

window.addEventListener("beforeinstallprompt", (e) => {
    console.log("[PWA] beforeinstallprompt fired");
    e.preventDefault();
    deferredPrompt = e;

    const installBtn = $("installBtn");
    if (installBtn) installBtn.style.display = "flex";
});

const installBtn = $("installBtn");
if (installBtn) {
    installBtn.addEventListener("click", async () => {
        if (!deferredPrompt) {
            console.warn("[PWA] No deferredPrompt available.");
            return;
        }
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        console.log("[PWA] User choice:", outcome);
        deferredPrompt = null;
        installBtn.style.display = "none";
    });
}

/* ------------------------------------------------------------
   PWA: SERVICE WORKER REGISTER
------------------------------------------------------------ */

if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker
            .register("/service-worker.js")
            .then((reg) => {
                console.log("[SW] Registered:", reg.scope);
            })
            .catch((err) => {
                console.error("[SW] Registration failed:", err);
            });
    });
}

/* ------------------------------------------------------------
   QUICK REFRESH & THEME TOGGLE
------------------------------------------------------------ */

const quickRefreshBtn = $("quickRefreshBtn");
if (quickRefreshBtn) {
    quickRefreshBtn.addEventListener("click", () => {
        console.log("[AI MATCHLAB] Quick refresh");
        window.location.reload();
    });
}

const themeToggleBtn = $("themeToggleBtn");
if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
        document.body.classList.toggle("theme-light");
        console.log("[Theme] toggled");
    });
}

/* ------------------------------------------------------------
   STATUS BAR UTIL
------------------------------------------------------------ */

function updateStatus(msg) {
    setText("status-text", msg);
}

/* ------------------------------------------------------------
   WORKER STATUS UI
------------------------------------------------------------ */

function setWorkerStatus(isOk) {
    const pill = $("worker-status");
    if (!pill) return;
    const dot = pill.querySelector(".dot");
    const label = pill.querySelector(".status-label");
    if (dot) {
        dot.classList.remove("dot-ok", "dot-fail");
        dot.classList.add(isOk ? "dot-ok" : "dot-fail");
    }
    if (label) {
        label.textContent = isOk ? "Worker: Connected" : "Worker: Disconnected";
    }
}

/* ------------------------------------------------------------
   MATCH RENDERING
------------------------------------------------------------ */

function renderMatches(data) {
    const container = $("matches-container");
    if (!container) return;

    container.innerHTML = ""; // καθάρισμα

    if (!data || !Array.isArray(data.matches) || data.matches.length === 0) {
        container.innerHTML =
            '<div style="opacity:0.6;font-size:13px;">No live matches available.</div>';
        return;
    }

    data.matches.forEach((m) => {
        const row = document.createElement("div");
        row.className = "match-row";
        row.dataset.matchId = m.id || "";

        // βασικά πεδία με fallbacks
        const home = m.home || "Home";
        const away = m.away || "Away";
        const league = m.league || "League";
        const minute = m.minute || "–";
        const score = m.score || "–";
        const odds = m.odds || { o1: "-", x: "-", o2: "-" };
        const volume = m.volume || 0;
        const signal = m.signal || "Neutral";

        // Εκτίμηση “έντασης” ρευστότητας
        let barClass = "";
        if (volume > 100000) barClass = "bar-liquidity";
        else if (volume > 50000) barClass = "bar-liquidity bar-medium";
        else barClass = "bar-liquidity bar-low";

        // Signal class
        let sClass = "signal-neutral";
        if (signal === "Strong" || signal === "SmartMoney") sClass = "signal-strong";
        else if (signal === "Watch" || signal === "Watchlist") sClass = "signal-watch";

        row.innerHTML = `
            <div class="m-col m-col-teams">
                <span class="team home">${home}</span>
                <span class="vs"> vs </span>
                <span class="team away">${away}</span>
                <span class="league-tag">${league}</span>
            </div>
            <div class="m-col m-col-time">
                <span class="minute">${minute}</span>
                <span class="score">${score}</span>
            </div>
            <div class="m-col m-col-odds">
                <span class="odd">1: ${odds.o1 ?? "-"}</span>
                <span class="odd">X: ${odds.x ?? "-"}</span>
                <span class="odd">2: ${odds.o2 ?? "-"}</span>
            </div>
            <div class="m-col m-col-volume">
                <div class="bar-wrap">
                    <div class="bar ${barClass}"></div>
                </div>
                <span class="vol-label">€ ${volume.toLocaleString()}</span>
            </div>
            <div class="m-col m-col-signal">
                <span class="signal-badge ${sClass}">
                    ${signal}
                </span>
            </div>
        `;

        // click → ενημέρωση B5 matrix “Selected match”
        row.addEventListener("click", () => {
            const label = `${home} vs ${away} (${league})`;
            setText("matrix-selected-match", label);
        });

        container.appendChild(row);
    });
}

/* ------------------------------------------------------------
   TOOLS PANEL (B4) RENDERING
------------------------------------------------------------ */

function renderTools(data) {
    // Trends
    const trendList = $("trend-list");
    if (trendList) {
        trendList.innerHTML = "";
        const trends = data.trends || [];
        if (trends.length === 0) {
            trendList.innerHTML =
                '<li style="opacity:0.6;font-size:13px;">No trend data available.</li>';
        } else {
            trends.forEach((t) => {
                const li = document.createElement("li");
                li.innerHTML = `
                    <span>${t.label || "Trend"}</span>
                    <strong>${t.value || ""}</strong>
                `;
                trendList.appendChild(li);
            });
        }
    }

    // Alerts
    const alertList = $("alert-list");
    if (alertList) {
        alertList.innerHTML = "";
        const alerts = data.alerts || [];
        if (alerts.length === 0) {
            alertList.innerHTML =
                '<li class="alert-item alert-soft" style="opacity:0.7;">No active alerts.</li>';
        } else {
            alerts.forEach((a) => {
                const li = document.createElement("li");
                li.className = "alert-item " + (a.level === "strong" ? "alert-strong" : "alert-soft");
                li.textContent = a.message || "Alert";
                alertList.appendChild(li);
            });
        }
    }

    // Quick stats
    setText("stats-markets", data.stats?.markets?.toString() ?? "—");
    setText("stats-latency", data.stats?.latencyMs?.toString() ?? "—");
    setText("stats-ai-rules", data.stats?.aiRules?.toString() ?? "—");
}

/* ------------------------------------------------------------
   SYSTEM SUMMARY (B2) RENDERING
------------------------------------------------------------ */

function renderSystemSummary(data) {
    setText("status-live-count", data.summary?.liveMatches?.toString() ?? "—");
    setText("status-market-count", data.summary?.activeMarkets?.toString() ?? "—");

    if (data.summary?.lastUpdate) {
        setText("status-last-update", data.summary.lastUpdate);
    } else {
        const now = new Date();
        setText("status-last-update", now.toLocaleTimeString());
    }
}

/* ------------------------------------------------------------
   WORKER FETCH LOOP
------------------------------------------------------------ */

async function fetchWorkerData() {
    try {
        updateStatus("Fetching data from worker...");
        const resp = await fetch(WORKER_ENDPOINT, { cache: "no-store" });
        if (!resp.ok) {
            throw new Error("HTTP " + resp.status);
        }
        const json = await resp.json();
        console.log("[Worker] data received", json);

        setWorkerStatus(true);
        updateStatus("Live data loaded.");
        renderMatches(json);
        renderTools(json);
        renderSystemSummary(json);
    } catch (err) {
        console.error("[Worker] fetch error:", err);
        setWorkerStatus(false);
        updateStatus("Worker connection error.");
    }
}

/* ------------------------------------------------------------
   FALLBACK DUMMY DATA (ΑΝ ΘΕΛΕΙΣ ΝΑ ΒΛΕΠΕΙΣ ΚΑΤΙ ΧΩΡΙΣ WORKER)
------------------------------------------------------------ */

function loadDummyOnceIfNeeded() {
    const container = $("matches-container");
    if (!container) return;
    if (container.children.length > 0) return; // αν έχει ήδη δεδομένα, δεν χρειάζεται

    console.log("[Dummy] Loading fallback data.");
    const dummy = {
        matches: [
            {
                id: "dm-1",
                home: "AI United",
                away: "Data City",
                league: "ENG · Premier League",
                minute: "41'",
                score: "2 – 1",
                odds: { o1: "1.88", x: "3.40", o2: "4.20" },
                volume: 134200,
                signal: "SmartMoney"
            },
            {
                id: "dm-2",
                home: "Signal FC",
                away: "Liquidity Rovers",
                league: "EU · Champions League",
                minute: "HT",
                score: "1 – 1",
                odds: { o1: "2.20", x: "3.20", o2: "3.40" },
                volume: 98250,
                signal: "Balanced"
            }
        ],
        trends: [
            { label: "UCL · Over 2.5", value: "↑ 12.5%" },
            { label: "ENG · Match Odds", value: "€ 76k / 5min" }
        ],
        alerts: [
            { level: "strong", message: "Dummy: Suspended market (sample)" }
        ],
        summary: {
            liveMatches: 2,
            activeMarkets: 12,
            lastUpdate: new Date().toLocaleTimeString()
        },
        stats: {
            markets: 12,
            latencyMs: 42,
            aiRules: 8
        }
    };

    setWorkerStatus(false);
    renderMatches(dummy);
    renderTools(dummy);
    renderSystemSummary(dummy);
    updateStatus("Dummy data loaded (no worker).");
}

/* ------------------------------------------------------------
   INIT
------------------------------------------------------------ */

function init() {
    console.log("[AI MATCHLAB] Initializing enterprise UI...");
    updateStatus("AI MatchLab ready.");

    // Πρώτο fetch στον Worker
    fetchWorkerData()
        .then(() => {
            // Αν θέλεις dummy ΜΟΝΟ σε αποτυχία, μπορείς να αφαιρέσεις το loadDummyOnceIfNeeded εδώ.
            console.log("[Init] Worker fetch initial completed.");
        })
        .catch(() => {
            // Fallback dummy αν κάτι πάει πολύ λάθος
            loadDummyOnceIfNeeded();
        });

    // Περιοδικό refresh
    setInterval(fetchWorkerData, FETCH_INTERVAL_MS);
}

document.addEventListener("DOMContentLoaded", init);
