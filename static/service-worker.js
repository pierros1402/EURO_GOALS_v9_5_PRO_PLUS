const CACHE_NAME = "aimatchlab-cache-v1";
const FILES_TO_CACHE = [
    "/",
    "/static/css/aimatchlab.css",
    "/static/js/aimatchlab.js",
    "/static/icons/logo_64.png",
    "/static/icons/logo_128.png",
    "/static/icons/logo_256.png",
    "/static/icons/logo_512.png"
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(FILES_TO_CACHE))
    );
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.map((k) => (k !== CACHE_NAME ? caches.delete(k) : null)))
        )
    );
    self.clients.claim();
});

self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request).then((cached) =>
            cached || fetch(event.request).catch(() =>
                caches.match("/static/icons/logo_128.png")
            )
        )
    );
});
