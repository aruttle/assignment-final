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

  // Expose a manual request function (used by the “Enable location” button)
  window.SEA_requestLocation = function () {
    if (!("geolocation" in navigator)) return;
    navigator.geolocation.getCurrentPosition(
      pos => {
        window.__SEA_USER_POS__ = pos;
        setDistances(pos);
      },
      err => {
        // Helpful hint so folks know what to do in Chrome
        alert(
          "Location is blocked. In Chrome, click the lock icon → Site settings → Location → Allow, then reload."
        );
      },
      { enableHighAccuracy: false, maximumAge: 5 * 60_000, timeout: 8000 }
    );
  };

  function showCTAIfNeeded() {
    const cta = document.querySelector(".distance-cta");
    if (!cta || !("geolocation" in navigator)) return;

    if (navigator.permissions && navigator.permissions.query) {
      navigator.permissions
        .query({ name: "geolocation" })
        .then(status => {
          if (status.state === "prompt" || status.state === "denied") {
            cta.hidden = false;
          }
        })
        .catch(() => { /* ignore */ });
    } else {
      // Older browsers: show the CTA
      cta.hidden = false;
    }
  }

  function requestPositionMaybe() {
    // If we already have a location (from earlier), reuse it
    const cached = window.__SEA_USER_POS__;
    if (cached) {
      setDistances(cached);
      return;
    }
    // Otherwise, request in the background (Chrome may not prompt without a user gesture)
    if (!("geolocation" in navigator)) return;
    navigator.geolocation.getCurrentPosition(
      pos => {
        window.__SEA_USER_POS__ = pos;
        setDistances(pos);
      },
      () => { /* stay quiet; CTA will be there if needed */ },
      { enableHighAccuracy: false, maximumAge: 5 * 60_000, timeout: 8000 }
    );
  }

  function init() {
    requestPositionMaybe();
    showCTAIfNeeded();
  }

  document.addEventListener("DOMContentLoaded", init);
  document.body.addEventListener("htmx:afterSettle", init);
})();
