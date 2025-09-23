// static/js/map-thumbs.js
// Initialize small Leaflet thumbnails for elements with .map-thumb
(function () {
  function initThumb(el) {
    if (el.dataset.initialized === "1") return;
    el.dataset.initialized = "1";

    const lat = parseFloat(el.dataset.lat);
    const lon = parseFloat(el.dataset.lon);
    const zoom = parseInt(el.dataset.zoom || "12", 10);

    if (!Number.isFinite(lat) || !Number.isFinite(lon) || typeof L === "undefined") return;

    const m = L.map(el, {
      attributionControl: false,
      zoomControl: false,
      dragging: false,
      scrollWheelZoom: false,
      doubleClickZoom: false,
      boxZoom: false,
      keyboard: false,
      tap: false,
      touchZoom: false,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
    }).addTo(m);

    m.setView([lat, lon], zoom);
    L.marker([lat, lon]).addTo(m);

    // Invalidate after paint so Leaflet sizes correctly inside the card
    setTimeout(() => m.invalidateSize(), 50);
  }

  function scan(root) {
    (root || document).querySelectorAll(".map-thumb").forEach(initThumb);
  }

  // Initial load
  document.addEventListener("DOMContentLoaded", function () {
    scan(document);
  });

  // Re-scan after HTMX swaps/settle
  if (window.htmx) {
    htmx.on("htmx:afterSwap", (e) => scan(e.target));
    htmx.on("htmx:afterSettle", (e) => scan(e.target));
  }
})();
