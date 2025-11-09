// ============================================================
// EURO_GOALS PRO+ Unified — Service Worker Registration
// ============================================================

if ("serviceWorker" in navigator) {
  window.addEventListener("load", async () => {
    try {
      const reg = await navigator.serviceWorker.register("/static/service-worker.js");
      console.log("[EURO_GOALS] ✅ Service Worker registered:", reg.scope);
    } catch (err) {
      console.warn("[EURO_GOALS] ⚠️ Service Worker registration failed:", err);
    }
  });
} else {
  console.warn("[EURO_GOALS] Service Workers not supported in this browser.");
}
