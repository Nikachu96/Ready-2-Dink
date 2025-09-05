// Minimal service worker
self.addEventListener("push", function(event) {
  const options = {
    body: event.data ? event.data.text() : "Ready 2 Dink notification",
    icon: "/static/images/ready2dink-logo.png"
  };
  event.waitUntil(
    self.registration.showNotification("Ready 2 Dink", options)
  );
});
