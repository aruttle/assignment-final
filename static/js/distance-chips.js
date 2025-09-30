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

  function showCTA() {
    document.querySelectorAll(".distance-cta").forEach(btn => { btn.hidden = false; });
  }
  function hideCTA() {
    document.querySelectorAll(".distance-cta").forEach(btn => { btn.hidden = true; });
  }

  function setDistances(pos) {
    if (!pos || !pos.coords) return;
    const myLat = pos.coords.latitude;
    const myLon = pos.coords.longitude;
    document.querySelectorAll(".distance-chip").forEach(chip => {
      const lat = parseFloat(chip.dataset.lat);
      const lon = parseFloat(chip.dataset.lon);
      if (Number.isNaN(lat) || Number.isNaN(lon)) return;
      const km = distanceKm(myLat, myLon, lat, lon);
      chip.textContent = `${km.toFixed(km >= 10 ? 0 : 1)} km away`;
      chip.hidden = false;
    });
  }

  function requestPosition(fromUserGesture = false) {
    if (!("geolocation" in navigator)) return;
    navigator.geolocation.getCurrentPosition(
      pos => {
        window.__SEA_USER_POS__ = pos; // cache for HTMX swaps
        hideCTA();
        setDistances(pos);
      },
      err => {
        // If user explicitly denies, keep CTA visible for instructions
        if (err && err.code === 1 /* PERMISSION_DENIED */) {
          showCTA();
        } else {
          // For timeouts / unavailable, leave chips hidden but show CTA if called by user
          if (fromUserGesture) showCTA();
        }
      },
      { enableHighAccuracy: false, maximumAge: 5 * 60_000, timeout: 8000 }
    );
  }

  // Expose a click handler for “Enable location” buttons
  window.SEA_requestLocation = function () {
    requestPosition(true);
  };

  async function ensurePermissionAndMaybeRequest() {
    if (!("permissions" in navigator) || !navigator.permissions.query) {
      // Older browsers: just ask
      requestPosition(false);
      return;
    }
    try {
      const status = await navigator.permissions.query({ name: "geolocation" });
      if (status.state === "granted") {
        hideCTA();
        requestPosition(false);
      } else if (status.state === "prompt") {
        // Might be blocked unless triggered by user gesture, so show the CTA
        showCTA();
      } else {
        // denied
        showCTA();
      }
    } catch {
      // If permissions API throws, fall back
      requestPosition(false);
    }
  }

  function scanAndApply() {
    const cached = window.__SEA_USER_POS__;
    if (cached) {
      hideCTA();
      setDistances(cached);
    } else {
      ensurePermissionAndMaybeRequest();
    }
  }

  document.addEventListener("DOMContentLoaded", scanAndApply);
  document.body.addEventListener("htmx:afterSettle", scanAndApply);
  document.body.addEventListener("htmx:afterSwap", scanAndApply);
})();
