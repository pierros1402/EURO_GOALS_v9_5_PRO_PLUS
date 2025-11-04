// ==============================================
// EURO_GOALS v9.4.4 PRO+ — Service Worker (Push)
// ==============================================

self.addEventListener("install", (e) => {
  console.log("[SW] Installing...");
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  console.log("[SW] Activated.");
  e.waitUntil(self.clients.claim());
});

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
