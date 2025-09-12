// Ready 2 Dink Service Worker - Force Fresh Content
const CACHE_VERSION = 'v2.0.1'; // Increment this to force cache invalidation
const CACHE_NAME = `ready2dink-${CACHE_VERSION}`;

// Force immediate activation and take control of clients
self.addEventListener('install', function(event) {
  console.log('Service Worker installing with version:', CACHE_VERSION);
  // Force new service worker to become active immediately
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  console.log('Service Worker activating with version:', CACHE_VERSION);
  event.waitUntil(
    // Delete old caches and immediately claim all clients
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(function() {
      // Take control of all clients immediately
      return self.clients.claim();
    })
  );
});

// Network-first strategy for HTML documents to prevent stale pages
self.addEventListener('fetch', function(event) {
  // For HTML documents, always try network first
  if (event.request.mode === 'navigate' || 
      (event.request.headers.get('accept') && event.request.headers.get('accept').includes('text/html'))) {
    
    event.respondWith(
      fetch(event.request)
        .then(function(response) {
          // If network succeeds, return fresh content
          console.log('Serving fresh HTML from network:', event.request.url);
          return response;
        })
        .catch(function() {
          // Only fallback to cache if network fails
          return caches.match(event.request)
            .then(function(response) {
              if (response) {
                console.log('Network failed, serving from cache:', event.request.url);
                return response;
              }
              // If not in cache either, show offline page or basic error
              return new Response('Network error and no cached version available', {
                status: 503,
                statusText: 'Service Unavailable'
              });
            });
        })
    );
  }
  
  // For static assets, use cache-first strategy
  else if (event.request.url.includes('/static/')) {
    event.respondWith(
      caches.match(event.request)
        .then(function(response) {
          if (response) {
            return response;
          }
          return fetch(event.request)
            .then(function(response) {
              if (response.status === 200) {
                const responseClone = response.clone();
                caches.open(CACHE_NAME)
                  .then(function(cache) {
                    cache.put(event.request, responseClone);
                  });
              }
              return response;
            });
        })
    );
  }
});

// Push notification handler
self.addEventListener("push", function(event) {
  const options = {
    body: event.data ? event.data.text() : "Ready 2 Dink notification",
    icon: "/static/images/ready2dink-logo.png",
    badge: "/static/images/ready2dink-logo.png"
  };
  event.waitUntil(
    self.registration.showNotification("Ready 2 Dink", options)
  );
});

// Message handler for manual cache refresh
self.addEventListener('message', function(event) {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then(function(cacheNames) {
        return Promise.all(
          cacheNames.map(function(cacheName) {
            return caches.delete(cacheName);
          })
        );
      })
    );
  }
});