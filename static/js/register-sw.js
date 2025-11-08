/* ============================================================
   EURO_GOALS PRO+ UNIFIED – Service Worker Register + Update UI
   Version: v9.5.x
   Author: Pierros
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
  if (!("serviceWorker" in navigator)) {
    console.warn("[EURO_GOALS] Service workers not supported");
    return;
  }

  registerServiceWorker();
});

async function registerServiceWorker() {
  try {
    const reg = await navigator.serviceWorker.register("/static/js/sw.js", { scope: "/" });
    console.log("[EURO_GOALS] ✅ Service Worker registered:", reg.scope);

    // Listen for updates
    reg.addEventListener("updatefound", () => {
      const newWorker = reg.installing;
      newWorker?.addEventListener("statechange", () => {
        if (newWorker.state === "installed" && navigator.serviceWorker.controller) {
          showUpdateBanner();
        }
      });
    });

    // Message from SW (optional)
    navigator.serviceWorker.addEventListener("message", (event) => {
      console.log("[EURO_GOALS] SW message:", event.data);
    });
  } catch (err) {
    console.error("[EURO_GOALS] ❌ Service Worker registration failed:", err);
  }
}

/* ============================================================
   UPDATE BANNER (Reload Suggestion)
   ============================================================ */
function showUpdateBanner() {
  if (document.getElementById("sw-update-banner")) return;

  const banner = document.createElement("div");
  banner.id = "sw-update-banner";
  banner.className = `
    fixed bottom-4 left-1/2 transform -translate-x-1/2 z-[9999]
    bg-blue-600 text-white px-5 py-3 rounded-lg shadow-lg flex items-center gap-3
    animate-fadeIn cursor-pointer
  `;
  banner.innerHTML = `
    <span>🔄 Νέα έκδοση διαθέσιμη – Επαναφόρτωση</span>
  `;
  document.body.appendChild(banner);

  banner.addEventListener("click", async () => {
    const reg = await navigator.serviceWorker.getRegistration();
    if (reg && reg.waiting) {
      reg.waiting.postMessage({ type: "SKIP_WAITING" });
      await new Promise((r) => setTimeout(r, 1000));
      window.location.reload(true);
    } else {
      window.location.reload(true);
    }
  });

  // Auto-hide μετά από 30s
  setTimeout(() => banner.remove(), 30000);
}

/* ============================================================
   Small helper animation (fadeIn)
   ============================================================ */
const style = document.createElement("style");
style.textContent = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fadeIn { animation: fadeIn 0.5s ease-out; }
`;
document.head.appendChild(style);
