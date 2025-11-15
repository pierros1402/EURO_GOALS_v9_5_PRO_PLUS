/* ============================================================
   AI MATCHLAB — APP.JS
   PWA install handler · UI interactions · Status updates
   ============================================================ */

console.log("[AI MATCHLAB] app.js loaded");

let deferredPrompt = null;

/* ------------------------------------------------------------
   PWA INSTALL EVENT
------------------------------------------------------------ */

// Fired when the browser detects that the app can be installed
window.addEventListener("beforeinstallprompt", (e) => {
    console.log("[PWA] beforeinstallprompt fired");
    e.preventDefault();
    deferredPrompt = e;

    const installBtn = document.getElementById("installBtn");
    installBtn.style.display = "flex"; // make visible
});

// Install button action
const installBtn = document.getElementById("installBtn");

if (installBtn) {
    installBtn.addEventListener("click", async () => {
        if (!deferredPrompt) {
            console.warn("[PWA] Install prompt not ready");
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
   QUICK REFRESH BUTTON
------------------------------------------------------------ */
const quickRefreshBtn = document.getElementById("quickRefreshBtn");

if (quickRefreshBtn) {
    quickRefreshBtn.addEventListener("click", () => {
        console.log("[AI MATCHLAB] Quick refresh triggered");
        window.location.reload();
    });
}

/* ------------------------------------------------------------
   THEME TOGGLE (DARK / LIGHT) — Future Expansion
------------------------------------------------------------ */
const themeToggleBtn = document.getElementById("themeToggleBtn");

if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
        document.body.classList.toggle("theme-light");
        console.log("[Theme] mode switched");
    });
}

/* ------------------------------------------------------------
   STATUS BAR TEXT UPDATE
------------------------------------------------------------ */
function updateStatus(msg) {
    const statusText = document.getElementById("status-text");
    if (statusText) {
        statusText.textContent = msg;
    }
}

// Initial status message
updateStatus("AI MatchLab ready.");
