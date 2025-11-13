/* ============================================================
   EURO_GOALS PRO+ v10.2.1 — Service Worker
   Offline + Cache + Auto Update
   ============================================================ */

const CACHE_NAME = "eg-cache-v10.2.1";
const STATIC_ASSETS = [
    "/",
    "/static/manifest.json",
    "/static/icons/eurogoals_192.png",
    "/static/icons/eurogoals_512.png",
    "/static/css/unified_theme.css",
    "/static/js/goal_smart_refresh.js",
    "/static/pwa/pwa_update_monitor.js"
];

/* INSTALL ---------------------------------------------------*/
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

/* ACTIVATE --------------------------------------------------*/
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
            )
        )
    );
    self.clients.claim();
});

/* FETCH -----------------------------------------------------*/
self.addEventListener("fetch", (event) => {
    if (event.request.url.includes("/api/")) {
        return event.respondWith(fetch(event.request));
    }

    event.respondWith(
        caches.match(event.request).then((cached) => {
            return (
                cached ||
                fetch(event.request).then((response) => {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, copy);
                    });
                    return response;
                })
            );
        })
    );
});

/* AUTO-UPDATE NOTIFICATION ---------------------------------*/
self.addEventListener("message", (event) => {
    if (event.data === "checkForUpdate") {
        self.skipWaiting();
    }
});
