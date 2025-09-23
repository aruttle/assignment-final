// static/js/home-swiper.js
// Home page swiper: builds slides from /spots.json, uses per-location images,
// and supports "View on map" (panToSpot). Also updates the Leaflet map markers.

(function () {
  const SPOTS_URL = "/spots.json";
  const IMG_BASE = "/static/images/spots/";
  const FALLBACK_IMG = "/static/images/spot-default.jpg";
  const EXTS = [".webp", ".jpg", ".jpeg", ".png"];
  let spotSwiper = null;

  function initSwiper() {
    if (typeof Swiper === "undefined") return null;
    if (spotSwiper) return spotSwiper;
    spotSwiper = new Swiper(".sea-swiper", {
      slidesPerView: 1.1,
      spaceBetween: 12,
      a11y: { enabled: true },
      pagination: { el: ".swiper-pagination", clickable: true },
      navigation: { nextEl: ".swiper-button-next", prevEl: ".swiper-button-prev" },
      breakpoints: { 576: { slidesPerView: 2 }, 768: { slidesPerView: 3 }, 992: { slidesPerView: 4 } },
    });
    return spotSwiper;
  }

  function slugify(s) {
    return String(s || "")
      .toLowerCase()
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)+/g, "");
  }
  function slugCandidates(name) {
    const full = slugify(name);
    const tokens = full.split("-").filter(Boolean);
    const generic = new Set(["pier","marina","club","harbour","harbor","beach","point","park","castle","bridge"]);
    let trimmed = tokens.slice();
    while (trimmed.length && generic.has(trimmed[trimmed.length - 1])) trimmed.pop();

    const out = new Set();
    if (full) out.add(full);
    if (trimmed.length) out.add(trimmed.join("-"));
    if (tokens.length >= 1) out.add(tokens[0]);
    if (tokens.length >= 2) out.add(tokens.slice(0, 2).join("-"));
    return Array.from(out);
  }

  function pickFirstAvailable(candidates, done, fallback = FALLBACK_IMG) {
    if (!candidates || !candidates.length) { done(fallback); return; }
    let i = 0;
    const tester = new Image();
    tester.onload = () => done(candidates[i]);
    tester.onerror = () => {
      i += 1;
      if (i < candidates.length) tester.src = candidates[i];
      else done(fallback);
    };
    tester.src = candidates[0];
  }

  function normalize(payload) {
    if (!payload) return [];
    if (Array.isArray(payload.features)) {
      return payload.features.map((f) => {
        const p = f.properties || {};
        const c = (f.geometry && f.geometry.coordinates) || [null, null]; // [lon, lat]
        return { name: p.name, type: p.type, lon: c[0], lat: c[1], image: p.image || p.photo || null, activities: p.activities || [] };
      });
    }
    if (Array.isArray(payload)) return payload;
    return [];
  }

  function renderSpotSlides(payload) {
    const wrap = document.getElementById("spot-swiper-wrapper");
    if (!wrap) return;
    wrap.innerHTML = "";

    const items = normalize(payload).slice(0, 12);
    const sw = initSwiper();

    items.forEach((s) => {
      const title = s.name || "Spot";
      const type = (s.type || "").toString();
      const lat = s.lat, lon = s.lon;

      let candidates = [];
      if (s.image) {
        candidates = [s.image];
      } else {
        const slugs = slugCandidates(title);
        candidates = slugs.flatMap((sl) => EXTS.map((ext) => IMG_BASE + sl + ext));
      }

      const slide = document.createElement("div");
      slide.className = "swiper-slide";
      slide.innerHTML = `
        <div class="spot-card shadow-sm">
          <div class="spot-card-img" role="img" aria-label="${title}"></div>
          <div class="spot-card-body">
            ${type ? `<div class="badge rounded-pill text-bg-light mb-2">${type}</div>` : ``}
            <h3 class="h6 mb-2">${title}</h3>
            <div class="d-flex gap-2">
              ${lat!=null && lon!=null
                ? `<a href="#map" class="btn btn-sm btn-outline-secondary" data-lat="${lat}" data-lon="${lon}">View on map</a>`
                : ``}
            </div>
          </div>
        </div>`;

      wrap.appendChild(slide);

      // Set background once we find a real image
      const imgEl = slide.querySelector(".spot-card-img");
      imgEl.style.backgroundImage =
        `linear-gradient(0deg, rgba(0,0,0,.35), rgba(0,0,0,.15)), url('${FALLBACK_IMG}')`;
      pickFirstAvailable(candidates, (url) => {
        imgEl.style.backgroundImage =
          `linear-gradient(0deg, rgba(0,0,0,.35), rgba(0,0,0,.15)), url('${url}')`;
      });
    });

    if (sw) sw.update();
  }

  // ---- helpers that run after we load spots ----
  function afterLoad(data) {
    try { window._seaSpotsGeoJSON = data; } catch(_) {}
    // NEW: also update the map markers if the map script is present
    if (typeof window.updateSpots === "function") {
      window.updateSpots(data);
    }
    renderSpotSlides(data);
  }

  function handleXHR(xhr) {
    try { afterLoad(JSON.parse(xhr.responseText)); } catch (_) {}
  }

  // Works whether the HTMX response is swapped or not
  document.addEventListener("htmx:afterOnLoad", (e) => {
    if (e.target && e.target.id === "spot-data") handleXHR(e.detail.xhr);
  });
  document.addEventListener("htmx:afterRequest", (e) => {
    if (e.target && e.target.id === "spot-data") handleXHR(e.detail.xhr);
  });

  // Fallback: fetch if HTMX ran before this script
  document.addEventListener("DOMContentLoaded", function () {
    initSwiper();
    if (window._seaSpotsGeoJSON) {
      afterLoad(window._seaSpotsGeoJSON);
    } else {
      try { fetch(SPOTS_URL).then((r) => r.json()).then(afterLoad).catch(() => {}); } catch (_) {}
    }
  });

  // Global click: View on map
  document.addEventListener("click", function (e) {
    const a = e.target.closest("a[data-lat][data-lon]");
    if (!a) return;
    const lat = parseFloat(a.dataset.lat);
    const lon = parseFloat(a.dataset.lon);
    if (Number.isFinite(lat) && Number.isFinite(lon)) {
      if (typeof window.panToSpot === "function") window.panToSpot(lat, lon, 12);
      else if (window._seaMap && typeof window._seaMap.setView === "function") window._seaMap.setView([lat, lon], 12);
    }
  });

  // Expose for debugging if needed
  window._seaRenderSpotSlides = renderSpotSlides;
})();
