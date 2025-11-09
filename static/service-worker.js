// ============================================================
// EURO_GOALS v9.5.5 PRO+ Unified — Dummy Service Worker
// Safe no-cache version (avoids stale caching & PWA errors)
// ============================================================

const VERSION = "v9.5.5-dummy";
const CACHE_NAME = `eurogoals-${VERSION}`;

// Εγκατάσταση
self.addEventListener("install", (event) => {
  console.log(`[EURO_GOALS] Service Worker installed (${VERSION})`);
  self.skipWaiting();
});

// Ενεργοποίηση — καθαρισμός παλιών caches
self.addEventListener("activate", (event) => {
  console.log("[EURO_GOALS] Service Worker activated");
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.map((key) => caches.delete(key))))
  );
  return self.clients.claim();
});

// Fetch handler — μόνο online (no cache)
self.addEventListener("fetch", (event) => {
  event.respondWith(fetch(event.request));
});
