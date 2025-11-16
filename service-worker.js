// ======================================================================
// AI MatchLab v0.9.0 BETA — SERVICE WORKER (FINAL for "/" route)
// ======================================================================

const CACHE_NAME = "matchlab-v0.9.0";

const CORE_ASSETS = [
  "/",                // main UI
  "/aimatchlab.js",  // frontend logic
  "/manifest.json",

  // icons
  "/static/icons/aimatchlab_192.png",
  "/static/icons/aimatchlab_512.png",
  "/static/icons/aimatchlab_maskable_512.png",
  "/static/icons/aimatchlab_1024.png"
];

// ----------------------------------------------------------------------
// INSTALL
// ----------------------------------------------------------------------
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(CORE_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// ----------------------------------------------------------------------
// ACTIVATE
// ----------------------------------------------------------------------
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.map((key) => {
        if (key !== CACHE_NAME) return caches.delete(key);
      }))
    ).then(() => self.clients.claim())
  );
});

// ----------------------------------------------------------------------
// FETCH
// ----------------------------------------------------------------------
self.addEventListener("fetch", (event) => {
  const req = event.request;

  if (req.method !== "GET") return;

  const url = new URL(req.url);

  // API = network-first
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(networkFirst(req));
    return;
  }

  // navigation fallback
  if (req.mode === "navigate") {
    event.respondWith(htmlNetworkFirst(req));
    return;
  }

  event.respondWith(cacheFirst(req));
});

// ======================================================================
// STRATEGIES
// ======================================================================
async function cacheFirst(req) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(req);

  if (cached) return cached;

  try {
    const fresh = await fetch(req);
    cache.put(req, fresh.clone());
    return fresh;
  } catch {
    return cached || Response.error();
  }
}

async function networkFirst(req) {
  const cache = await caches.open(CACHE_NAME);
  try {
    const fresh = await fetch(req);
    cache.put(req, fresh.clone());
    return fresh;
  } catch {
    return cache.match(req) || Response.error();
  }
}

async function htmlNetworkFirst(req) {
  const cache = await caches.open(CACHE_NAME);

  try {
    const fresh = await fetch(req);
    cache.put(req, fresh.clone());
    return fresh;

  } catch (err) {
    // Fallback to homepage cached version
    const cached = await cache.match("/");
    return cached || new Response(
      "<h1>Offline</h1><p>No cached homepage available.</p>",
      { headers: { "Content-Type": "text/html" } }
    );
  }
}
