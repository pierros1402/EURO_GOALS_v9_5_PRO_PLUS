/* ============================================================
   AI MATCHLAB — SERVICE WORKER
   Offline caching · Fast loading · Cache versioning
   ============================================================ */

const CACHE_NAME = "aimatchlab-cache-v1";
const URLS_TO_CACHE = [
  "/",
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/icons/aimatchlab-192.png",
  "/static/icons/aimatchlab-512.png"
];

/* ------------------------------------------------------------
   INSTALL — cache critical assets
------------------------------------------------------------ */
self.addEventListener("install", (event) => {
  console.log("[SW] Install event");

  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[SW] Caching initial assets");
      return cache.addAll(URLS_TO_CACHE);
    })
  );

  self.skipWaiting();
});

/* ------------------------------------------------------------
   ACTIVATE — delete old caches
------------------------------------------------------------ */
self.addEventListener("activate", (event) => {
  console.log("[SW] Activate event");

  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log("[SW] Deleting old cache:", key);
            return caches.delete(key);
          }
        })
      );
    })
  );

  self.clients.claim();
});

/* ------------------------------------------------------------
   FETCH — try cache first, fallback to network
------------------------------------------------------------ */
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      if (response) {
        return response;
      }
      return fetch(event.request);
    })
  );
});
