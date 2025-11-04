// ==============================================
// EURO_GOALS v9.4.4 PRO+ — Service Worker (Push)
// ==============================================

// Όταν φτάνει Push Notification από τον server
self.addEventListener('push', event => {
  if (!event.data) return;

  let data = {};
  try {
    data = event.data.json();
  } catch (e) {
    console.error('[EURO_GOALS] Push event parse error:', e);
  }

  const title = data.title || 'EURO_GOALS';
  const options = {
    body: data.body || 'Νέα ειδοποίηση',
    icon: '/static/icons/ball-512.png',     // κύριο εικονίδιο
    badge: '/static/icons/badge-128.png',   // μικρό badge (προαιρετικό)
    tag: data.tag || 'eurogoals',
    renotify: true,
    data: {
      url: data.url || '/',
      timestamp: Date.now()
    }
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Όταν ο χρήστης κάνει click στο notification
self.addEventListener('notificationclick', event => {
  event.notification.close();

  const targetUrl = event.notification.data?.url || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(windowClients => {
      for (let client of windowClients) {
        if (client.url.includes(self.origin) && 'focus' in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      if (clients.openWindow) return clients.openWindow(targetUrl);
    })
  );
});

// Keep-alive & instant activation
self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(clients.claim());
});
