// Энгийн PWA cache strategy:
//   - HTML: network-first (онлайн үед хамгийн шинэ хувилбарыг авна,
//           офлайн бол кэшээс)
//   - Bусад (icon, manifest): cache-first (хурдан ачаалах)
//
// CACHE_NAME-ыг өөрчилбөл хуучин кэшийг бүгдийг устгана.
const CACHE_NAME = "morning-news-v2";
const PRECACHE = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icon-192.png",
  "./icon-512.png",
  "./icon-180.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      // Зарим файл байхгүй байж болзошгүй тул алдаа гарвал бүгдийг хаахгүй
      Promise.allSettled(PRECACHE.map((url) => cache.add(url)))
    )
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);

  // Cross-origin request-ыг (Binance, Yahoo, exchange rate API гэх мэт)
  // огт cache хийхгүй — real-time шинэ өгөгдөл хэрэгтэй.
  if (url.origin !== self.location.origin) return;

  const isHTML =
    req.mode === "navigate" ||
    url.pathname.endsWith("/") ||
    url.pathname.endsWith(".html");

  if (isHTML) {
    // Network-first: онлайн бол хамгийн сүүлийн хувилбарыг авч хадгална.
    event.respondWith(
      fetch(req)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
          return response;
        })
        .catch(() =>
          caches.match(req).then((cached) => cached || caches.match("./index.html"))
        )
    );
  } else {
    // Cache-first: icon, manifest гэх мэт хувирах нь ховор файл.
    event.respondWith(
      caches.match(req).then(
        (cached) =>
          cached ||
          fetch(req).then((response) => {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
            return response;
          })
      )
    );
  }
});
