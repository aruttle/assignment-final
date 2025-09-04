// static/js/map.js
let map;
let markersLayer = L.layerGroup();

function initMap() {
  const el = document.getElementById('map');
  if (!el) {
    console.warn('Map container #map not found.');
    return;
  }
  if (typeof L === 'undefined') {
    console.error('Leaflet (L) is not defined. Check the Leaflet <script> include.');
    return;
  }

  // Center roughly on the Shannon Estuary
  map = L.map('map').setView([52.68, -9.00], 10);

  // Free OpenStreetMap tiles (with attribution)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  markersLayer.addTo(map);

  // Optional default point
  // addSpot({ name: 'Bunratty Pier', lat: 52.699, lon: -8.814, type: 'kayak' });

  console.log('Map initialized.');
}

function addSpot(spot) {
  const marker = L.marker([spot.lat, spot.lon])
    .bindPopup(`<strong>${spot.name}</strong><br>${spot.type}`);
  markersLayer.addLayer(marker);
}

function clearSpots() {
  markersLayer.clearLayers();
}

function updateSpots(spots) {
  clearSpots();
  spots.forEach(addSpot);
  // Fit bounds if we have markers
  if (markersLayer.getLayers().length > 0) {
    const groupBounds = L.featureGroup(markersLayer.getLayers()).getBounds();
    map.fitBounds(groupBounds.pad(0.2));
  }
  console.log(`Loaded ${spots.length} spots.`);
}

// DOM ready 
(function ready(fn) {
  if (document.readyState !== 'loading') fn();
  else document.addEventListener('DOMContentLoaded', fn);
})(function () {
  initMap();
});
