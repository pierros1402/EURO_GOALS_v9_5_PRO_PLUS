const CACHE_VERSION = "eurogoals-v3";
const CORE_CACHE = "core-" + CACHE_VERSION;
const RUNTIME_CACHE = "runtime-" + CACHE_VERSION;

const CORE_ASSETS = [
  "/",
  "/static/manifest.json"
];

// INSTALL
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CORE_CACHE).then((cache) => cache.addAll(CORE_ASSETS))
  );
  self.skipWaiting();
});

// ACTIVATE
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CORE_CACHE && key !== RUNTIME_CACHE)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// FETCH
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // API → network first
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(event.request)
        .then((response) => response)
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // STATIC → cache first
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return (
        cached ||
        fetch(event.request).then((response) => {
          const copy = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(event.request, copy);
          });
          return response;
        })
      );
    })
  );
});
