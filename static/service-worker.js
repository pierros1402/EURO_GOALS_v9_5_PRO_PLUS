// =====================================================
// EURO_GOALS v9.5.0 PRO+
// Service Worker for PWA Offline + Cache Control
// =====================================================

const CACHE_NAME = 'euro_goals_v950_proplus_v1';
const APP_SHELL = [
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
// 🧱 Install – Precache core files
// =====================================================
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Installing…');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[ServiceWorker] Precaching app shell');
        return cache.addAll(APP_SHELL);
      })
  );
  self.skipWaiting();
});

// =====================================================
// 🔁 Activate – Cleanup old caches
// =====================================================
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activating new version…');
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

// =====================================================
// ⚙️ Fetch – Serve from cache, fallback to network
// =====================================================
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  event.respondWith(
    caches.match(req).then(cached => {
      return cached || fetch(req).then(res => {
        // Dynamic caching for new assets
        return caches.open(CACHE_NAME).then(cache => {
          cache.put(req, res.clone());
          return res;
        });
      }).catch(() => {
        // Offline fallback page (if any)
        return caches.match('/static/icons/icon-192.png');
      });
    })
  );
});

// =====================================================
// 🧭 Message – Manual cache refresh
// =====================================================
self.addEventListener('message', (event) => {
  if (event.data === 'force-update') {
    console.log('[ServiceWorker] Manual cache refresh triggered');
    self.skipWaiting();
  }
});
