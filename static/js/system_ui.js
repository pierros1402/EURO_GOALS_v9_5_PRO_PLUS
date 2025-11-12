// ============================================================
// EURO_GOALS PRO+ v9.9.0 — System UI / PWA Logic
// ============================================================

const log = (...args) => console.log("[EURO_GOALS]", ...args);
const updateBanner = document.getElementById("eg-update");
const installButton = document.getElementById("btnInstall");
const updateButton = document.getElementById("btnUpdate");
const iosBanner = document.getElementById("eg-install-ios");
const iosClose = document.getElementById("eg-install-ios-close");

let deferredPrompt;

// ------------------------------------------------------------
// SERVICE WORKER REGISTRATION
// ------------------------------------------------------------
if ("serviceWorker" in navigator) {
  window.addEventListener("load", async () => {
    try {
      const reg = await navigator.serviceWorker.register("/static/service-worker.js");
      log("Service Worker registered:", reg.scope);

      // Reload page when new version becomes active
      reg.addEventListener("updatefound", () => {
        const newWorker = reg.installing;
        newWorker.addEventListener("statechange", () => {
          if (newWorker.state === "installed" && navigator.serviceWorker.controller) {
            updateBanner.classList.remove("hidden");
          }
        });
      });
    } catch (e) {
      console.error("[EURO_GOALS] SW registration failed:", e);
    }
  });
}

// ------------------------------------------------------------
// INSTALL PROMPT HANDLING (Chrome/Edge/Android)
// ------------------------------------------------------------
window.addEventListener("beforeinstallprompt", e => {
  e.preventDefault();
  deferredPrompt = e;
  installButton.classList.remove("hidden");
});

installButton?.addEventListener("click", async () => {
  installButton.classList.add("hidden");
  if (deferredPrompt) {
    deferredPrompt.prompt();
    const choice = await deferredPrompt.userChoice;
    if (choice.outcome === "accepted") log("App installed!");
    deferredPrompt = null;
  }
});

// ------------------------------------------------------------
// UPDATE AVAILABLE BANNER
// ------------------------------------------------------------
updateButton?.addEventListener("click", async () => {
  updateBanner.classList.add("hidden");
  if (navigator.serviceWorker?.controller) {
    navigator.serviceWorker.controller.postMessage({ type: "SKIP_WAITING" });
  }
  setTimeout(() => window.location.reload(), 1000);
});

// ------------------------------------------------------------
// iOS ADD TO HOME BANNER
// ------------------------------------------------------------
function isIos() {
  return /iphone|ipad|ipod/.test(window.navigator.userAgent.toLowerCase());
}
function isInStandaloneMode() {
  return "standalone" in window.navigator && window.navigator.standalone;
}

if (isIos() && !isInStandaloneMode()) {
  setTimeout(() => iosBanner?.classList.remove("hidden"), 2000);
  iosClose?.addEventListener("click", () => iosBanner.classList.add("hidden"));
}

// ------------------------------------------------------------
// THEME SWITCHING
// ------------------------------------------------------------
document.querySelectorAll(".eg-theme")?.forEach(btn => {
  btn.addEventListener("click", e => {
    const mode = e.target.dataset.theme;
    localStorage.setItem("theme", mode);
    applyTheme(mode);
  });
});

function applyTheme(mode) {
  if (mode === "auto") {
    document.documentElement.removeAttribute("data-theme");
  } else {
    document.documentElement.setAttribute("data-theme", mode);
  }
}
applyTheme(localStorage.getItem("theme") || "auto");

// ------------------------------------------------------------
// MISC — Toggle Settings, Overlay
// ------------------------------------------------------------
const settingsBtn = document.getElementById("btnSettings");
const settingsPanel = document.getElementById("eg-settings");
const overlayBtn = document.getElementById("btnToggleOverlay");
const overlay = document.getElementById("eg-overlay");
const overlayClose = document.getElementById("ovClose");

settingsBtn?.addEventListener("click", () => settingsPanel.classList.toggle("hidden"));
overlayBtn?.addEventListener("click", () => overlay.classList.toggle("hidden"));
overlayClose?.addEventListener("click", () => overlay.classList.add("hidden"));
