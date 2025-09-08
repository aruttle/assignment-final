// static/js/map.js
let map;
let markersLayer = L.layerGroup();

function initMap() {
  const el = document.getElementById('map');
  if (!el) { console.warn('Map container #map not found.'); return; }
  if (typeof L === 'undefined') { console.error('Leaflet (L) not defined.'); return; }

  map = L.map('map').setView([52.68, -9.00], 10);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  markersLayer.addTo(map);
  console.log('Map initialized (v2).');
}

function addSpot(spot) {
  const url = `/safety/panel/?lat=${spot.lat}&lon=${spot.lon}`;
  const popupHtml = `
    <div>
      <strong>${spot.name}</strong><br>
      ${spot.type}
      <div class="mt-2">
        <button class="btn btn-sm btn-outline-primary"
                onclick="htmx.ajax('GET', '${url}', { target: '#safety-panel', swap: 'innerHTML' })">
          Check safety
        </button>
      </div>
    </div>`;
  const marker = L.marker([spot.lat, spot.lon]).bindPopup(popupHtml);
  markersLayer.addLayer(marker);
}


function clearSpots() { markersLayer.clearLayers(); }

function updateSpots(spots) {
  clearSpots();
  spots.forEach(addSpot);
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
})(function () { initMap(); });
