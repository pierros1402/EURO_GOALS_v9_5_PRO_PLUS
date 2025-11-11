self.addEventListener('install', e => {
  self.skipWaiting();
});
self.addEventListener('activate', e => {
  clients.claim();
});
self.addEventListener('fetch', e => {
  // Network-first
  e.respondWith(fetch(e.request).catch(() => caches.match('/offline')));
});
