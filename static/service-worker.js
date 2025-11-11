// ============================================================
// EURO_GOALS v9.6.8 PRO+ — Auto-Refresh PWA + Offline Cache
// ============================================================

const CACHE_VERSION = "v9_6_8";
const CACHE_NAME = `eurogoals-${CACHE_VERSION}-cache`;
const OFFLINE_URL = "/";

// ------------------------------------------------------------
// Βασικά αρχεία προς αποθήκευση (cache)
// ------------------------------------------------------------
const ASSETS = [
  "/",
  "/index.html",
  "/static/css/style.css",
  "/static/css/unified_theme.css",
  "/static/css/panels.css",
  "/static/js/system_summary.js",
  "/static/js/goalmatrix_panel.js",
  "/static/js/smartmoney_panel.js",
  "/static/js/unified_expansion.js",
  "/static/js/theme_toggle.js",
  "/static/icons/eurogoals_192.png",
  "/static/icons/eurogoals_512.png",
  "/api/system/check"
];

// ------------------------------------------------------------
// INSTALL — Προφόρτωση των βασικών πόρων
// ------------------------------------------------------------
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
  console.log(`[EURO_GOALS] ✅ Service Worker εγκαταστάθηκε (${CACHE_NAME})`);
});

// ------------------------------------------------------------
// ACTIVATE — Καθαρισμός παλαιών cache εκδόσεων
// ------------------------------------------------------------
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log(`[EURO_GOALS] 🧹 Διαγραφή παλιού cache: ${key}`);
            return caches.delete(key);
          }
        })
      )
    )
  );
  return self.clients.claim();
});

// ------------------------------------------------------------
// FETCH — Cache-first με network fallback
// ------------------------------------------------------------
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request)
        .then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          return response;
        })
        .catch(() => caches.match(OFFLINE_URL));
    })
  );
});

// ------------------------------------------------------------
// AUTO-REFRESH — Αναγκαστική ανανέωση σε νέα έκδοση
// ------------------------------------------------------------
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "NEW_VERSION") {
    self.skipWaiting();
    console.log("[EURO_GOALS] 🔄 Νέα έκδοση ενεργοποιήθηκε, γίνεται refresh.");
  }
});
