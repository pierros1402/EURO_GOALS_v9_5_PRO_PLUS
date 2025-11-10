// ============================================================
// EURO_GOALS v9.6.1 PRO+ — Unified Service Worker
// ============================================================

const CACHE_NAME = "eurogoals-v961-cache";
const OFFLINE_URL = "/";

const ASSETS = [
  "/",
  "/index.html",
  "/static/css/style.css",
  "/static/css/unified_theme.css",
  "/static/js/system_summary.js",
  "/static/js/goalmatrix_panel.js",
  "/static/js/smartmoney_panel.js",
  "/static/js/unified_expansion.js",
  "/static/icons/eurogoals_192.png",
  "/static/icons/eurogoals_512.png",
  "/api/system/check"
];

// ------------------------------------------------------------
// INSTALL — Precache βασικά assets
// ------------------------------------------------------------
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
  console.log("[EURO_GOALS] ✅ Service Worker installed.");
});

// ------------------------------------------------------------
// ACTIVATE — Καθαρισμός παλιών cache
// ------------------------------------------------------------
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => {
        if (k !== CACHE_NAME) return caches.delete(k);
      }))
    )
  );
  console.log("[EURO_GOALS] 🧹 Old caches cleared.");
  return self.clients.claim();
});

// ------------------------------------------------------------
// FETCH — Cache-first με fallback στο δίκτυο
// ------------------------------------------------------------
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  event.respondWith(
    caches.match(event.request)
      .then(cached => {
        if (cached) return cached;
        return fetch(event.request)
          .then(resp => {
            const clone = resp.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
            return resp;
          })
          .catch(() => caches.match(OFFLINE_URL));
      })
  );
});

// ------------------------------------------------------------
// MESSAGE — Ενημέρωση clients για νέα έκδοση
// ------------------------------------------------------------
self.addEventListener("message", (event) => {
  if (event.data === "skipWaiting") {
    self.skipWaiting();
    console.log("[EURO_GOALS] 🔁 Manual refresh triggered.");
  }
});
