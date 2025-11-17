// ===============================
// AI MATCHLAB PWA SERVICE WORKER
// Versioned Cache Control: 0.9.3
// ===============================

const CACHE_VERSION = "0.9.3";
const CACHE_NAME = `aimatchlab-cache-v${CACHE_VERSION}`;

const FILES_TO_CACHE = [
    "/matchlab",
    "/manifest.json",

    // CSS
    "/static/css/aimatchlab.css",
    "/static/css/main.css",
    "/static/css/mobile.css",

    // JS
    "/static/js/aimatchlab.js",
    "/static/js/app.js",
    "/static/js/lang_manager.js",

    // ICONS
    "/static/icons/icon-192.png",
    "/static/icons/icon-512.png",
    "/static/icons/icon-1024.png",
    "/static/icons/icon-maskable-512.png"
];

// -------------------------------------------------
// INSTALL
// -------------------------------------------------
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(FILES_TO_CACHE);
        })
    );
    self.skipWaiting();
});

// -------------------------------------------------
// ACTIVATE — Delete old caches
// -------------------------------------------------
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys
                  .filter((key) => key !== CACHE_NAME)
                  .map((key) => caches.delete(key))
            )
        )
    );
    self.clients.claim();
});

// -------------------------------------------------
// FETCH HANDLER
// -------------------------------------------------
self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request).then((cached) => {
            return cached || fetch(event.request);
        })
    );
});
