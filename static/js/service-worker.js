/* ============================================================
   EURO_GOALS PRO+ UNIFIED – Service Worker (Stable v9.5.x)
   Strategy:
   - HTML: network-first with offline fallback
   - Static (JS/CSS/Icons): cache-first with versioned precache
   - APIs: network-first with runtime cache
   - Push & Notification click handling
   ============================================================ */

const SW_VERSION = "egpwa-v9.5.x-unified-002";
const PRECACHE = `eg-precache-${SW_VERSION}`;
const RUNTIME  = `eg-runtime-${SW_VERSION}`;

// --- Core assets to precache (must exist & be lightweight)
const CORE_ASSETS = [
  "/",                             // main route
  "/offline.html",                 // backup offline
  "/static/css/style.css",
  "/static/css/unified_theme.css",
  "/static/js/system_status.js",
  "/static/js/main_unified.js",
  "/static/icons/eg_logo.png",
  "/static/icons/eurogoals_512.png",
  "/static/manifest.json"
];

// --- Optional: frequently used endpoints for offline cache
const OPTIONAL_PREFETCH = [
  "/system_status_html",
  "/goalmatrix_summary",
  "/smartmoney_monitor"
];

// Utility helper
async function addAllQuiet(cache, urls) {
  for (const url of [...new Set(urls)]) {
    try { await cache.add(new Request(url, { cache: "no-store" })); }
    catch (_e) { /* skip errors */ }
  }
}

/* ---------------- Install ---------------- */
self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(PRECACHE);
    await addAllQuiet(cache, CORE_ASSETS);
    await addAllQuiet(cache, OPTIONAL_PREFETCH);
    await self.skipWaiting();
  })());
});

/* ---------------- Activate ---------------- */
self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(
      names
        .filter((n) => ![PRECACHE, RUNTIME].includes(n))
        .map((n) => caches.delete(n))
    );
    await self.clients.claim();
  })());
});

/* ---------------- Fetch ---------------- */
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method !== "GET") return;

  // ---------- HTML navigation (network-first)
  const isHTML = request.mode === "navigate" ||
                 (request.headers.get("accept") || "").includes("text/html");

  if (isHTML) {
    event.respondWith((async () => {
      try {
        const fresh = await fetch(request, { cache: "no-store" });
        const cache = await caches.open(RUNTIME);
        cache.put(request, fresh.clone());
        return fresh;
      } catch {
        const cache = await caches.open(PRECACHE);
        return (await cache.match(request)) ||
               (await cache.match("/")) ||
               (await cache.match("/offline.html")) ||
               new Response("Offline", { status: 503, headers: { "Content-Type": "text/plain" }});
      }
    })());
    return;
  }

  // ---------- Static assets (cache-first)
  const isStatic =
    url.pathname.startsWith("/static/") ||
    [".webmanifest", ".json", ".png", ".ico", ".svg", ".jpg", ".jpeg", ".css", ".js"]
      .some(ext => url.pathname.endsWith(ext));

  if (isStatic) {
    event.respondWith((async () => {
      const cache = await caches.open(PRECACHE);
      const cached = await cache.match(request);
      if (cached) return cached;
      try {
        const fresh = await fetch(request);
        if (fresh.ok && url.origin === self.location.origin) cache.put(request, fresh.clone());
        return fresh;
      } catch {
        return (await caches.match("/offline.html")) ||
               new Response("", { status: 504 });
      }
    })());
    return;
  }

  // ---------- Other GET (APIs etc.): network-first
  event.respondWith((async () => {
    const cache = await caches.open(RUNTIME);
    try {
      const fresh = await fetch(request, { cache: "no-store" });
      if (fresh.ok && url.origin === self.location.origin) cache.put(request, fresh.clone());
      return fresh;
    } catch {
      const cached = await cache.match(request);
      if (cached) return cached;
      return (await caches.match("/offline.html")) ||
             new Response(JSON.stringify({ offline: true }), {
               status: 200,
               headers: { "Content-Type": "application/json" }
             });
    }
  })());
});

/* ---------------- Messages ---------------- */
self.addEventListener("message", (event) => {
  if ((event.data || {}).type === "SKIP_WAITING") self.skipWaiting();
});

/* ---------------- Push Notifications ---------------- */
self.addEventListener("push", (event) => {
  try {
    const data = event.data ? event.data.json() : {};
    const title = data.title || "EURO_GOALS Alert";
    const body  = data.body  || "New update available";
    const icon  = data.icon  || "/static/icons/eg_logo.png";
    const tag   = data.tag   || "euro-goals";
    event.waitUntil(self.registration.showNotification(title, { body, icon, tag }));
  } catch {}
});

/* ---------------- Notification Click ---------------- */
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil((async () => {
    const all = await clients.matchAll({ type: "window", includeUncontrolled: true });
    const targetUrl = "/";
    const opened = all.find((c) => (c.url || "").includes(self.location.origin));
    if (opened) {
      opened.focus();
      opened.postMessage({ type: "FOCUS_FROM_NOTIFICATION" });
    } else {
      await clients.openWindow(targetUrl);
    }
  })());
});
