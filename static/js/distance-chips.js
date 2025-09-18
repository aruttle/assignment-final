// static/js/distance-chips.js
(function () {
  // Haversine distance in km
  function distanceKm(lat1, lon1, lat2, lon2) {
    const toRad = d => (d * Math.PI) / 180;
    const R = 6371;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) ** 2;
    return R * (2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)));
  }

  function setDistances(pos) {
    const myLat = pos.coords.latitude;
    const myLon = pos.coords.longitude;
    document.querySelectorAll(".distance-chip").forEach(chip => {
      const lat = parseFloat(chip.dataset.lat);
      const lon = parseFloat(chip.dataset.lon);
      if (isNaN(lat) || isNaN(lon)) return;
      const km = distanceKm(myLat, myLon, lat, lon);
      chip.textContent = `${km.toFixed(km >= 10 ? 0 : 1)} km away`;
      chip.hidden = false;
    });
  }

  function requestPosition() {
    if (!("geolocation" in navigator)) return;
    navigator.geolocation.getCurrentPosition(
      pos => {
        window.__SEA_USER_POS__ = pos; // cache for HTMX swaps
        setDistances(pos);
      },
      // ignore errors silently; chip stays hidden
      () => {},
      { enableHighAccuracy: false, maximumAge: 5 * 60_000, timeout: 8000 }
    );
  }

  function scanAndApply() {
    const cached = window.__SEA_USER_POS__;
    if (cached) setDistances(cached);
    else requestPosition();
  }

  document.addEventListener("DOMContentLoaded", scanAndApply);
  document.body.addEventListener("htmx:afterSettle", scanAndApply);
})();
