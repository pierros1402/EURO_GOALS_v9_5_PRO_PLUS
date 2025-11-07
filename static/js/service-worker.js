// =====================================================
// EURO_GOALS v9.5.0 PRO+
// Progressive Web App Service Worker
// Features:
// ✅ Smart Offline Caching
// ✅ Auto-Update Notifier
// ✅ Versioned Cache Control
// ✅ Graceful Recovery if Render Sleep
// =====================================================

const CACHE_VERSION = 'v950_proplus_v2';
const CACHE_NAME = `euro_goals_${CACHE_VERSION}`;
const CORE_ASSETS = [
  '/',
  '/static/css/style.css',
  '/static/js/ui_controls.js',
  '/static/js/ui_alerts.js',
  '/static/js/pwa_manifest_check.js',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/splash_720x1280.png',
  '/static/icons/splash_1080x1920.png',
  '/static/manifest.json'
];

// =====================================================
// 🧱 INSTALL: Pre-cache core files
// =====================================================
self.addEventListener('install', (event) => {
  console.log(`[SW] Installing ${CACHE_NAME}...`);
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(CORE_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// =====================================================
// 🔁 ACTIVATE: Remove old caches + claim clients
// =====================================================
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating new cache...');
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys
        .filter(k => k.startsWith('euro_goals_') && k !== CACHE_NAME)
        .map(k => {
          console.log('[SW] Removing old cache:', k);
          return caches.delete(k);
        })
    ))
  );
  return self.clients.claim();
});

// =====================================================
// ⚙️ FETCH: Network-first for HTML, cache-first for assets
// =====================================================
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  if (req.headers.get('accept')?.includes('text/html')) {
    // HTML: Network first
    event.respondWith(
      fetch(req)
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE_NAME).then(c => c.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req))
    );
  } else {
    // Assets: Cache first
    event.respondWith(
      caches.match(req).then(
        cached => cached ||
          fetch(req).then(res => {
            const copy = res.clone();
            caches.open(CACHE_NAME).then(c => c.put(req, copy));
            return res;
          }).catch(() => caches.match('/static/icons/icon-192.png'))
      )
    );
  }
});

// =====================================================
// 🔔 AUTO-UPDATE NOTIFIER
// =====================================================
self.addEventListener('message', (event) => {
  if (event.data === 'skipWaiting') {
    console.log('[SW] Skip waiting triggered manually.');
    self.skipWaiting();
  }
});

// When new SW is waiting, notify all clients
self.addEventListener('install', () => {
  self.registration.onupdatefound = () => {
    const newWorker = self.registration.installing;
    if (!newWorker) return;
    newWorker.addEventListener('statechange', () => {
      if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
        self.clients.matchAll({ type: 'window' }).then(clients => {
          for (const client of clients) {
            client.postMessage({ type: 'NEW_VERSION' });
          }
        });
      }
    });
  };
});

// =====================================================
// 🧭 FALLBACK: handle offline or Render sleep
// =====================================================
self.addEventListener('fetch', (event) => {
  event.respondWith(
    fetch(event.request).catch(async () => {
      const cache = await caches.open(CACHE_NAME);
      const match = await cache.match(event.request);
      if (match) return match;
      return new Response('<h1>⚠️ Offline Mode</h1><p>Trying to reconnect to Render...</p>', {
        headers: { 'Content-Type': 'text/html' }
      });
    })
  );
});
