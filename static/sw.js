// Idealisto PWA: red primero para páginas (nunca una home vieja tras un deploy),
// caché como respaldo sin conexión.
const CACHE = 'idealisto-v2';
self.addEventListener('install', e => { self.skipWaiting(); e.waitUntil(caches.open(CACHE).then(c => c.addAll(['/']))); });
self.addEventListener('activate', e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  // Ni la API ni las páginas personales (cuenta, informes, enlaces de acceso) pasan por la caché.
  if (e.request.method !== 'GET' || u.origin !== location.origin || /^\/(api|mis-informes|informe|acceso)(\/|$)/.test(u.pathname)) return;
  e.respondWith(fetch(e.request).then(r => {
    if (r.ok && (e.request.mode === 'navigate' || /\.(js|svg|png)$/.test(u.pathname))) {
      const copia = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copia));
    }
    return r;
  }).catch(() => caches.match(e.request).then(r => r || caches.match('/'))));
});
