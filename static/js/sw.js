/* ============================================================
   EURO_GOALS PRO+ UNIFIED – Service Worker (v9.5.x)
   Strategy:
   - HTML: network-first with offline fallback
   - Static (JS/CSS/Icons): cache-first with versioned precache
   - Offline fallback: /public/offline.html (and /offline.html as backup)
   ============================================================ */

const SW_VERSION = "egpwa-v9.5.x-dblue-001";
const PRECACHE = `eg-precache-${SW_VERSION}`;
const RUNTIME = `eg-runtime-${SW_VERSION}`;

// --- Core assets to precache (must be fast, small, stable)
const CORE_ASSETS = [
  "/",                            // main route
  "/public/offline.html",         // preferred offline fallback
  "/offline.html",                // backup path (in case of different mount)
  "/static/css/unified_theme.css",
  "/static/js/main_unified.js",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",

  // manifest: try both paths to be safe
  "/public/manifest.webmanifest",
  "/manifest.webmanifest",
];

// Optional: add API endpoints you want available offline as last-known
const OPTIONAL_PREFETCH = [
  "/system_status_html",
  "/goalmatrix_summary",
  "/smartmoney_monitor",
];

// Utility: cache a list of URLs (unique, ignore failures)
async function addAllQuiet(cache, urls) {
  for (const url of [...new Set(urls)]) {
    try { await cache.add(new Request(url, { cache: "no-store" })); }
    catch (_e) { /* ignore individual failures */ }
  }
}

/* ---------------- Install ---------------- */
self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(PRECACHE);
    await addAllQuiet(cache, CORE_ASSETS);
    await addAllQuiet(cache, OPTIONAL_PREFETCH);
    // Take control immediately on next load
    await self.skipWaiting();
  })());
});

/* ---------------- Activate ---------------- */
self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    // Cleanup old caches
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

  // Only handle GET
  if (request.method !== "GET") return;

  // HTML navigation requests → network-first with offline fallback
  const isHTML = request.mode === "navigate" ||
                 (request.headers.get("accept") || "").includes("text/html");

  if (isHTML) {
    event.respondWith((async () => {
      try {
        const fresh = await fetch(request, { cache: "no-store" });
        // Optionally update runtime cache with latest HTML
        const cache = await caches.open(RUNTIME);
        cache.put(request, fresh.clone());
        return fresh;
      } catch (_err) {
        // Try cache
        const cache = await caches.open(PRECACHE);
        const cached = await cache.match(request) || await cache.match("/");
        if (cached) return cached;
        // Offline fallback
        return (await cache.match("/public/offline.html")) ||
               (await cache.match("/offline.html")) ||
               new Response("Offline", { status: 503, headers: { "Content-Type": "text/plain" }});
      }
    })());
    return;
  }

  // Static assets (CSS/JS/Icons/Manifest) → cache-first
  const isStatic =
    url.pathname.startsWith("/static/") ||
    url.pathname.endsWith(".webmanifest") ||
    url.pathname.endsWith(".json") ||
    url.pathname.endsWith(".png") ||
    url.pathname.endsWith(".ico") ||
    url.pathname.endsWith(".svg") ||
    url.pathname.endsWith(".jpg") ||
    url.pathname.endsWith(".jpeg") ||
    url.pathname.endsWith(".css") ||
    url.pathname.endsWith(".js");

  if (isStatic) {
    event.respondWith((async () => {
      const cache = await caches.open(PRECACHE);
      const cached = await cache.match(request);
      if (cached) return cached;
      try {
        const fresh = await fetch(request);
        // Only cache successful, same-origin responses
        if (fresh.ok && url.origin === self.location.origin) {
          cache.put(request, fresh.clone());
        }
        return fresh;
      } catch (_err) {
        // last resort: any offline fallback
        const off = await caches.match("/public/offline.html") ||
                    await caches.match("/offline.html");
        return off || new Response("", { status: 504 });
      }
    })());
    return;
  }

  // Other GET (e.g., JSON APIs) → network-first with runtime cache fallback
  event.respondWith((async () => {
    const cache = await caches.open(RUNTIME);
    try {
      const fresh = await fetch(request, { cache: "no-store" });
      if (fresh.ok && url.origin === self.location.origin) {
        cache.put(request, fresh.clone());
      }
      return fresh;
    } catch (_err) {
      const cached = await cache.match(request);
      if (cached) return cached;
      // generic offline response
      const off = await caches.match("/public/offline.html") ||
                  await caches.match("/offline.html");
      return off || new Response(JSON.stringify({ offline: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      });
    }
  })());
});

/* ---------------- Client Messages (for updates) ---------------- */
self.addEventListener("message", (event) => {
  const { type } = event.data || {};
  if (type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

/* ---------------- Optional: Push Notifications ---------------- */
self.addEventListener("push", (event) => {
  try {
    const data = event.data ? event.data.json() : {};
    const title = data.title || "EURO_GOALS Alert";
    const body  = data.body  || "New update available";
    const icon  = data.icon  || "/static/icons/icon-192.png";
    const tag   = data.tag   || "euro-goals";
    event.waitUntil(self.registration.showNotification(title, { body, icon, tag }));
  } catch (_e) {
    // silent
  }
});

/* ---------------- Optional: Notification Click ---------------- */
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil((async () => {
    const allClients = await clients.matchAll({ type: "window", includeUncontrolled: true });
    const targetUrl = "/"; // open dashboard
    const opened = allClients.find((c) => (c.url || "").includes(self.location.origin));
    if (opened) {
      opened.focus();
      opened.postMessage({ type: "FOCUS_FROM_NOTIFICATION" });
      return;
    }
    await clients.openWindow(targetUrl);
  })());
});
