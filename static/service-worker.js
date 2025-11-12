// ============================================================
// EURO_GOALS PRO+ v9.9.0 — Service Worker (Install + Update)
// ============================================================

const CACHE_NAME = "eg-cache-v990";
const APP_SHELL = [
  "/",
  "/static/manifest.json",
  "/static/css/unified_theme.css",
  "/static/js/system_ui.js",
  "/static/js/dowjones_ui.js",
  "/static/icons/eurogoals_192.png",
  "/static/icons/eurogoals_512.png"
];

// ------------------------------------------------------------
// INSTALL
// ------------------------------------------------------------
self.addEventListener("install", event => {
  console.log("[EURO_GOALS] Installing service worker...");
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

// ------------------------------------------------------------
// ACTIVATE
// ------------------------------------------------------------
self.addEventListener("activate", event => {
  console.log("[EURO_GOALS] Activating new service worker...");
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => k !== CACHE_NAME && caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ------------------------------------------------------------
// FETCH
// ------------------------------------------------------------
self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return;
  event.respondWith(
    caches.match(req).then(res => {
      return res || fetch(req).then(fetchRes => {
        if (fetchRes.status === 200 && fetchRes.type === "basic") {
          const clone = fetchRes.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(req, clone));
        }
        return fetchRes;
      });
    })
  );
});

// ------------------------------------------------------------
// UPDATE NOTIFICATION
// ------------------------------------------------------------
self.addEventListener("message", event => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

self.addEventListener("push", event => {
  const data = event.data?.json() || {};
  event.waitUntil(
    self.registration.showNotification(data.title || "EURO_GOALS", {
      body: data.body || "New data available",
      icon: "/static/icons/eurogoals_192.png"
    })
  );
});
