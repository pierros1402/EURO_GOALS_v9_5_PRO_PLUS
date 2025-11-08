/* EURO_GOALS PRO+ v9.5.2 – Fullscreen PWA Service Worker */
const EG_VERSION = 'v9.5.2';
const STATIC_CACHE = `eg-static-${EG_VERSION}`;
const RUNTIME_CACHE = `eg-runtime-${EG_VERSION}`;
const OFFLINE_URL = '/public/offline.html';

const PRECACHE_URLS = [
  '/', // main entry
  '/public/manifest.webmanifest',
  '/public/offline.html',
  '/public/icons/icon-192.png',
  '/public/icons/icon-512.png',
  '/static/css/style.css',
  '/static/js/main.js'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys.filter(k => ![STATIC_CACHE, RUNTIME_CACHE].includes(k))
          .map(k => caches.delete(k))
    );
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (e) => {
  const { request } = e;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // HTML
  if (request.destination === 'document') {
    e.respondWith((async () => {
      try {
        const net = fetch(request);
        e.waitUntil((async () => {
          const res = await net;
          const cache = await caches.open(RUNTIME_CACHE);
          cache.put(request, res.clone());
        })());
        const cached = await caches.match(request);
        return cached || net;
      } catch {
        return (await caches.match(request)) || (await caches.match(OFFLINE_URL));
      }
    })());
    return;
  }

  // Static assets
  if (['style','script','image','font','audio'].includes(request.destination)) {
    e.respondWith((async () => {
      const cached = await caches.match(request);
      if (cached) return cached;
      try {
        const res = await fetch(request);
        const cache = await caches.open(STATIC_CACHE);
        cache.put(request, res.clone());
        return res;
      } catch {
        return cached || Response.error();
      }
    })());
    return;
  }

  // API/JSON
  if (url.pathname.startsWith('/api/') || url.pathname.endsWith('.json')) {
    e.respondWith((async () => {
      const cache = await caches.open(RUNTIME_CACHE);
      try {
        const res = await fetch(request);
        cache.put(request, res.clone());
        return res;
      } catch {
        const cached = await caches.match(request);
        if (cached) return cached;
        return new Response(JSON.stringify({ offline: true }), {
          headers: { 'Content-Type': 'application/json' }
        });
      }
    })());
    return;
  }

  // Default
  e.respondWith((async () => {
    const cached = await caches.match(request);
    return cached || fetch(request).catch(() => cached || Response.error());
  })());
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

self.addEventListener('push', (event) => {
  if (!event.data) return;
  const data = (() => { try { return event.data.json(); } catch { return { title: 'EURO_GOALS', body: event.data.text() }; } })();
  event.waitUntil(
    self.registration.showNotification(data.title || 'EURO_GOALS', {
      body: data.body || '',
      icon: '/public/icons/icon-192.png',
      badge: '/public/icons/icon-192.png',
      data: data.data || {}
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const targetUrl = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(clients => {
        const open = clients.find(c => c.url.includes(location.origin));
        if (open) { open.focus(); open.navigate(targetUrl); }
        else { self.clients.openWindow(targetUrl); }
      })
  );
});
