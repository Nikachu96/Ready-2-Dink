// Service Worker for Push Notifications
self.addEventListener('push', function(event) {
    const options = {
        body: event.data ? event.data.text() : 'You have a new notification from Ready 2 Dink!',
        icon: '/static/images/ready2dink-logo.png',
        badge: '/static/images/ready2dink-logo.png',
        tag: 'ready2dink-notification',
        actions: [
            {
                action: 'view',
                title: 'View Match',
                icon: '/static/images/ready2dink-logo.png'
            },
            {
                action: 'close',
                title: 'Dismiss'
            }
        ],
        requireInteraction: true,
        vibrate: [200, 100, 200]
    };

    event.waitUntil(
        self.registration.showNotification('Ready 2 Dink', options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    if (event.action === 'view') {
        // Open the app when notification is clicked
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

self.addEventListener('install', function(event) {
    console.log('Service Worker installing.');
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    console.log('Service Worker activating.');
    event.waitUntil(self.clients.claim());
});