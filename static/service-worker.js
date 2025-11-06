// =======================================================
// EURO_GOALS v9.5.4 PRO+ — Unified Service Worker (Push + PWA)
// =======================================================

const CACHE_NAME = "eurogoals-v954";
const urlsToCache = ["/", "/static/manifest.json"];

// -------------------------------------------------------
// INSTALL & ACTIVATE
// -------------------------------------------------------
self.addEventListener("install", (e) => {
  console.log("[SW] Installing...");
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(urlsToCache))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  console.log("[SW] Activated.");
  e.waitUntil(self.clients.claim());
});

// -------------------------------------------------------
// FETCH (Offline cache fallback)
// -------------------------------------------------------
self.addEventListener("fetch", (e) => {
  e.respondWith(
    caches.match(e.request).then((res) => res || fetch(e.request))
  );
});

// -------------------------------------------------------
// PUSH NOTIFICATIONS
// -------------------------------------------------------
self.addEventListener("push", (event) => {
  console.log("[SW] Push received:", event.data ? event.data.text() : "(no data)");
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (err) {
    console.error("[SW] Invalid push data:", err);
  }

  const title = data.title || "EURO_GOALS Alert";
  const body = data.body || "Νέα ειδοποίηση SmartMoney.";
  const url = data.url || "/";

  event.waitUntil(
    self.registration.showNotification(title, {
      body: body,
      icon: "/static/icons/icon_red.png",
      data: { url: url },
      tag: "eurogoals-push",
    })
  );
});

// -------------------------------------------------------
// NOTIFICATION CLICK HANDLER
// -------------------------------------------------------
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data.url || "/";
  event.waitUntil(
    clients.matchAll({ type: "window" }).then((clientsArr) => {
      for (const client of clientsArr) {
        if (client.url.includes(url) && "focus" in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});
