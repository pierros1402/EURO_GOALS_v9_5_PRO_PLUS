// ============================================================
// AI MatchLab – PWA Service Worker (v1.0.0)
// ============================================================

const CACHE_NAME = "aimatchlab-v1";
const APP_ASSETS = [
    "/", 
    "/static/css/aimatchlab.css",
    "/static/js/aimatchlab.js",
    "/manifest.json"
];

// Install SW → pre-cache
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(APP_ASSETS);
        })
    );
});

// Activate SW → cleanup old caches
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys
                    .filter((key) => key !== CACHE_NAME)
                    .map((key) => caches.delete(key))
            );
        })
    );
});

// Fetch handler (cache-first for assets)
self.addEventListener("fetch", (event) => {
    const req = event.request;

    // Only GET requests
    if (req.method !== "GET") {
        return;
    }

    event.respondWith(
        caches.match(req).then((cached) => {
            return (
                cached ||
                fetch(req).catch(() =>
                    new Response(
                        "Offline — Unable to reach server.",
                        { status: 503 }
                    )
                )
            );
        })
    );
});
