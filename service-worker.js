const CACHE_NAME = "aimatchlab-cache-v1";

const ASSETS = [
    "/",
    "/matchlab",
    "/manifest.json",
    "/static/js/aimatchlab.js",
    "/static/css/aimatchlab.css",

    "/static/icons/icon-192.png",
    "/static/icons/icon-512.png",
    "/static/icons/icon-1024.png",
    "/static/icons/icon-maskable-512.png"
];

self.addEventListener("install", event => {
    event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)));
    self.skipWaiting();
});

self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.map(k => (k !== CACHE_NAME ? caches.delete(k) : null)))
        )
    );
    self.clients.claim();
});

self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request).then(cached => {
            return cached || fetch(event.request);
        })
    );
});
