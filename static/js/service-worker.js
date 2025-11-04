// ==============================================
// EURO_GOALS v9.4.4 PRO+ — Service Worker (Push)
// ==============================================

// Όταν φτάνει Push Notification από τον server:
self.addEventListener('push', function (event) {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    console.error('Push event parse error:', e);
  }

  const title = data.title || 'EURO_GOALS';
  const body = data.body || 'Νέα ειδοποίηση';
  const url = data.url || '/';
  const tag = data.tag || 'eurogoals';
  const icon = '/static/icons/ball-512.png';  // μπορείς να βάλεις όποιο θες
  const badge = '/static/icons/badge-128.png'; // προαιρετικό

  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      tag,
      icon,
      badge,
      data: { url },
      renotify: true
    })
  );
});

// Όταν ο χρήστης κάνει click στο notification:
self.addEventListener('notificationclick', function (event) {
  event.notification.close();

  const url = event.notification?.data?.url || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(windowClients => {
      for (let client of windowClients) {
        if (client.url.includes(self.origin) && 'focus' in client) {
          client.navigate(url);
          return client.focus();
        }
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});

// Προαιρετικά: keep alive
self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(clients.claim());
});
