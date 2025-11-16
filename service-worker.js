// =======================================================
// AI MATCHLAB PWA SERVICE WORKER v0.9.3
// =======================================================

const CACHE_NAME = "aimatchlab-cache-v1";

const ASSETS = [
    "/",
    "/matchlab",
    "/manifest.json",
    "/static/css/aimatchlab.css",
    "/static/js/aimatchlab.js",
    "/static/icons/aimatchlab_192.png",
    "/static/icons/aimatchlab_512.png"
];

self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.map(k => k !== CACHE_NAME && caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request).then(response => 
            response || fetch(event.request)
        )
    );
});
