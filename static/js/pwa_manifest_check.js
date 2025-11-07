// ======================================================
// EURO_GOALS v9.5.0 PRO+
// Manifest & Service Worker verification script
// ======================================================
(async function(){
  console.log("🔍 Checking PWA manifest & service worker...");

  // Check Manifest
  try {
    const res = await fetch("/static/manifest.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const manifest = await res.json();
    console.log("✅ PWA Manifest loaded:", manifest.name, manifest.version || "v9.5.0 PRO+");
  } catch (err) {
    console.warn("❌ Manifest failed to load:", err);
  }

  // Check Service Worker registration
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.getRegistration()
      .then(reg => {
        if (reg) {
          console.log("✅ Service Worker active:", reg.scope);
        } else {
          console.warn("⚠️ No Service Worker registered yet.");
        }
      })
      .catch(err => console.warn("❌ Service Worker check failed:", err));
  } else {
    console.warn("🚫 Service Workers not supported in this browser.");
  }

  // Check if Add-to-Home capability exists
  if (window.matchMedia("(display-mode: standalone)").matches) {
    console.log("📱 Running as installed PWA (standalone mode).");
  } else {
    console.log("🌐 Running in browser tab mode.");
  }
})();
