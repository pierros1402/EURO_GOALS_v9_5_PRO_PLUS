// EURO_GOALS – Service Worker (Push Notifications)

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("push", (event) => {
  let data = {};
  try { data = event.data.json(); } catch (e) {}
  const title = data.title || "EURO_GOALS Alert";
  const body  = data.body  || "SmartMoney event detected";
  const url   = data.url   || "/smartmoney/heatmap";
  const options = {
    body,
    icon: "/static/icons/ball.png",
    badge: "/static/icons/ball.png",
    data: { url }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || "/";
  event.waitUntil(clients.openWindow(url));
});
