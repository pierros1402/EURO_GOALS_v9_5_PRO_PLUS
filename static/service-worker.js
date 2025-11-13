/* ============================================================
   EURO_GOALS — Service Worker v9.9.16
   - Cache-first για static assets
   - Stale-while-revalidate για APIs (μικρό TTL)
   - Update flow: SKIP_WAITING μέσω postMessage
   ============================================================ */

const STATIC_CACHE = "eg-static-v9.9.16";
const API_CACHE    = "eg-api-v9.9.16";
const STATIC_ASSETS = [
  "/", "/static/manifest.json",
  "/static/css/unified_theme.css",
  "/static/js/goal_smart_refresh.js",
  "/static/icons/eurogoals_192.png",
  "/static/icons/eurogoals_512.png"
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(STATIC_CACHE).then((c) => c.addAll(STATIC_ASSETS))
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => ![STATIC_CACHE, API_CACHE].includes(k)).map(k => caches.delete(k)));
    self.clients.claim();
  })());
});

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  const isAPI = url.pathname.startsWith("/api/");

  // Cache-first για static
  if (!isAPI) {
    e.respondWith((async () => {
      const cached = await caches.match(e.request);
      if (cached) return cached;
      try {
        const res = await fetch(e.request);
        const cache = await caches.open(STATIC_CACHE);
        cache.put(e.request, res.clone());
        return res;
      } catch {
        return cached || Response.error();
      }
    })());
    return;
  }

  // SWR για API (με μικρό caching)
  e.respondWith((async () => {
    const cache = await caches.open(API_CACHE);
    const cached = await cache.match(e.request);
    const fetchPromise = fetch(e.request).then((res) => {
      // cache only 200/OK
      if (res && res.status === 200) cache.put(e.request, res.clone());
      return res;
    }).catch(() => cached);
    return cached || fetchPromise;
  })());
});
