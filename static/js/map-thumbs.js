// static/js/map-thumbs.js
// Initialize small, non-interactive Leaflet maps for elements with .map-thumb
(function () {
  function reallyInit(el) {
    const lat = parseFloat(el.dataset.lat);
    const lon = parseFloat(el.dataset.lon);
    if (isNaN(lat) || isNaN(lon)) return;

    const map = L.map(el, {
      attributionControl: false,
      zoomControl: false,
      dragging: false,
      scrollWheelZoom: false,
      doubleClickZoom: false,
      boxZoom: false,
      keyboard: false,
      tap: false,
    }).setView([lat, lon], 12);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
    }).addTo(map);

    L.marker([lat, lon]).addTo(map);

    // Recalculate after layout settles
    setTimeout(() => map.invalidateSize(), 0);
    setTimeout(() => map.invalidateSize(), 150);
    setTimeout(() => map.invalidateSize(), 400);

    el.dataset.inited = "1";
  }

  function initThumb(el) {
    if (el.dataset.inited || typeof L === "undefined") return;

    // Wait until element has non-zero size, then init
    const tryInit = (retries = 10) => {
      if (el.clientWidth > 0 && el.clientHeight > 0) {
        reallyInit(el);
      } else if (retries > 0) {
        setTimeout(() => tryInit(retries - 1), 50);
      }
    };
    requestAnimationFrame(() => tryInit());
  }

  function scan(root) {
    (root || document).querySelectorAll(".map-thumb").forEach(initThumb);
  }

  document.addEventListener("DOMContentLoaded", function () {
    scan(document);
  });

  // After HTMX swaps settle, re-scan the swapped area
  document.body.addEventListener("htmx:afterSettle", function (e) {
    scan(e.target);
  });
})();
