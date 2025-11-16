// ============================================================================
// AI MATCHLAB v0.9.0 BETA — FULL FRONTEND ENGINE
// EXTENDED EDITION — COMPLETE FILE
// ============================================================================

console.log("🚀 AI MatchLab v0.9.0 BETA — FULL EXTENDED EDITION LOADED");

// ============================================================================
// GLOBAL CONFIG
// ============================================================================
const WORKER_BASE = "/api";
const VERSION = "0.9.0";
const REFRESH_INTERVAL = 20000;   // 20s auto-refresh
let lastMatrixHash = null;


// ============================================================================
// UTILS
// ============================================================================
function safeJSON(text) {
    try {
        return JSON.parse(text);
    } catch (e) {
        console.warn("JSON parse error:", e);
        return { error: "json_parse_error" };
    }
}

function hashObject(obj) {
    return btoa(unescape(encodeURIComponent(JSON.stringify(obj))));
}


// ============================================================================
// UPDATE-DETECTION LOGIC
// ============================================================================
async function checkVersion() {
    try {
        const res = await fetch(`${WORKER_BASE}/status`, { cache: "no-store" });
        const data = await res.json();

        if (data.version && data.version !== VERSION) {
            showUpdateBanner(data.version);
        }
    } catch (e) {
        console.warn("version check failed", e);
    }
}

function showUpdateBanner(v) {
    const div = document.createElement("div");
    div.style.cssText = `
        position: fixed; bottom: 0; left: 0; right: 0;
        background: #ffb300; padding: 14px; color: #000;
        font-weight: bold; text-align:center;
        z-index: 9999; cursor:pointer;
    `;
    div.innerText = `New version available (${v}) — TAP TO UPDATE`;
    div.onclick = () => location.reload();
    document.body.appendChild(div);
}


// ============================================================================
// INSTALLATION LOGIC (PWA)
// ============================================================================
let deferredPrompt = null;

window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    document.getElementById("installBanner").style.display = "block";
});

document.getElementById("installBtn").addEventListener("click", async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
    document.getElementById("installBanner").style.display = "none";
});


// ============================================================================
// MAIN LIVE MATRIX FETCHER
// ============================================================================
async function loadLiveMatrix() {
    const debug = document.getElementById("debugPanel");
    debug.innerText = "Fetching /matrix…";

    try {
        const t0 = performance.now();
        const res = await fetch(`${WORKER_BASE}/matrix`, { cache: "no-store" });

        const text = await res.text();
        const data = safeJSON(text);

        const latency = (performance.now() - t0).toFixed(0);

        // hash compare — avoid useless re-render
        const newHash = hashObject(data);
        if (lastMatrixHash === newHash) {
            debug.innerText =
                `No changes • Latency ${latency}ms • ${new Date().toLocaleTimeString()}`;
            return;
        }

        lastMatrixHash = newHash;
        updateLiveUI(data);
        updateDebug(data, latency);

    } catch (err) {
        debug.innerText = "ERROR: " + err;
        console.error("Matrix error:", err);
    }
}


// ============================================================================
// UI RENDERER — LIVE MATRIX
// ============================================================================
function updateLiveUI(data) {
    const container = document.getElementById("liveContainer");
    container.innerHTML = "";

    if (!data || !Array.isArray(data.matches)) {
        container.innerHTML = "<p>No live matches.</p>";
        return;
    }

    data.matches.forEach((m) => {
        const card = document.createElement("div");
        card.className = "matchCard";

        const color = m.status === "LIVE" ? "#0f0" : "#ccc";

        card.innerHTML = `
            <div style="font-size:16px; font-weight:700; color:${color}">
                ${m.home} vs ${m.away}
            </div>

            <div>Status: ${m.status}</div>
            <div>Score: ${m.score}</div>
            <div>Minute: ${m.minute}'</div>

            <div style="margin-top:6px; opacity:0.7">
                xG Home: ${m.xg_home} • xG Away: ${m.xg_away}
            </div>

            <div style="margin-top:6px; opacity:0.7">
                Momentum: ${m.momentum}
            </div>

            <div style="margin-top:6px; opacity:0.7">
                Pressure Index: ${m.pressure}
            </div>
        `;

        card.onclick = () => openInspector(m);
        container.appendChild(card);
    });
}


// ============================================================================
// MATCH INSPECTOR (DETAILED VIEW)
// ============================================================================
function openInspector(m) {
    const div = document.createElement("div");
    div.style.cssText = `
        position: fixed; top:0; left:0; right:0; bottom:0;
        background:#000; padding:20px; overflow-y:auto;
        z-index:99999; color:#fff;
    `;

    div.innerHTML = `
        <h2>${m.home} vs ${m.away}</h2>
        <p><b>Status:</b> ${m.status}</p>
        <p><b>Score:</b> ${m.score}</p>
        <p><b>Minute:</b> ${m.minute}'</p>

        <h3>Advanced Stats</h3>
        <p>xG Home: ${m.xg_home}</p>
        <p>xG Away: ${m.xg_away}</p>
        <p>Momentum: ${m.momentum}</p>
        <p>Pressure: ${m.pressure}</p>
        <p>Attack Rate: ${m.attack_rate}</p>

        <button id="closeInspector" style="
            padding:10px 16px; margin-top:20px; background:#f00; color:#fff;
            border:none; border-radius:6px; cursor:pointer;
        ">Close</button>
    `;

    div.querySelector("#closeInspector").onclick = () => div.remove();
    document.body.appendChild(div);
}


// ============================================================================
// DEBUG PANEL UPDATE
// ============================================================================
function updateDebug(data, latency) {
    const debug = document.getElementById("debugPanel");

    debug.innerText =
        "Last update: " + new Date().toLocaleTimeString() +
        "\nMatches: " + (data.matches ? data.matches.length : 0) +
        "\nWorker Status: " + (data.status || "n/a") +
        "\nWorker Latency: " + latency + "ms" +
        "\nVersion: " + VERSION +
        "\nHash: " + lastMatrixHash +
        "\n" + (data.debug ? JSON.stringify(data.debug, null, 2) : "");
}


// ============================================================================
// AUTO-REFRESH + VERSION CHECK
// ============================================================================
setInterval(() => {
    loadLiveMatrix();
    checkVersion();
}, REFRESH_INTERVAL);


// ============================================================================
// FIRST LOAD
// ============================================================================
checkVersion();
loadLiveMatrix();

