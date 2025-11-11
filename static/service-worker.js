// ============================================================
// EURO_GOALS PRO+ Service Worker — Stable name + Auto Version
// ============================================================

// Αυτό δημιουργεί auto-version string (π.χ. eg-v25-972)
const CACHE = 'eg-v' + new Date().getFullYear().toString().slice(-2) + '-972';

const ASSETS = [
  '/',
  '/static/css/unified_theme.css',
  '/static/js/overlay.js',
  '/static/icons/eurogoals_192.png',
  '/static/icons/eurogoals_512.png',
  '/static/manifest.json'
];

// ------------------------------------------------------------
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(ASSETS))
  );
});

// ------------------------------------------------------------
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
});

// ------------------------------------------------------------
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (ASSETS.some(a => url.pathname === a)) {
    event.respondWith(
      caches.match(event.request).then(r => r || fetch(event.request))
    );
  }
});
