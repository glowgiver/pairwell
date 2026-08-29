/* Pairwell service worker.
   Update rule: bump CACHE whenever files have changed. */

const CACHE = "hub-v10";

const SHELL = [
  "./",
  "./index.html",
  /* Stamped by the build with a content hash; the pages request these exact
     URLs, so the cache key matches. Bare "./app.css" would never be hit. */
  "./app.css?v=43549eb3",
  "./app.js?v=7e67a4bb",
  "./manifest.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./skincare/",
  "./hair/",
  "./workout/",
  "./kitchen/"
];

// Install: cache each shell file individually.
// cache.addAll() is all-or-nothing — one failing URL used to drop the entire
// shell silently, which meant no styling and no pages offline.
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => Promise.all(
        SHELL.map((url) =>
          cache.add(url).catch((err) => {
            console.warn("[sw] could not cache", url, err);
          })
        )
      ))
      .then(() => self.skipWaiting())
  );
});

// Activate: drop old cache versions
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// Fetch: answer from cache immediately, refresh in the background
self.addEventListener("fetch", (event) => {
  const req = event.request;

  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) {
    return;
  }

  event.respondWith(
    caches.match(req).then((cached) => {
      const fresh = fetch(req)
        .then((res) => {
          if (res && res.status === 200) {
            const copy = res.clone();
            caches.open(CACHE).then((cache) => cache.put(req, copy));
          }
          return res;
        })
        .catch(() => cached);

      return cached || fresh;
    })
  );
});
