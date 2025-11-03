// ============================================================
// EURO_GOALS – Service Worker for Push
// ============================================================
self.addEventListener("push", function (event) {
  let data = {};
  try { data = event.data.json(); } catch (e) {}
  const title = data.title || "EURO_GOALS Alert";
  const body = data.body || "New SmartMoney event detected.";
  const options = {
    body,
    icon: "/static/icons/ball.png",
    badge: "/static/icons/ball.png",
    data: data.url || "/",
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", function (event) {
  event.notification.close();
  const url = event.notification.data || "/";
  event.waitUntil(clients.openWindow(url));
});
