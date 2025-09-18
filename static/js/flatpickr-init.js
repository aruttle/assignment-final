// static/js/flatpickr-init.js
// Robust, idempotent Flatpickr init for SEA (supports .js-date and .js-datetime)

(function () {
  // Safely parse JSON from data-flatpickr-options
  function parseJsonOptions(el) {
    const raw = el.getAttribute("data-flatpickr-options");
    if (!raw) return {};
    try { return JSON.parse(raw); } catch { return {}; }
  }

  // Build default options based on class and data-*
  function buildOptions(el) {
    const isDateTime = el.classList.contains("js-datetime");
    const isDateOnly = el.classList.contains("js-date");

    // Common sensible defaults
    const opts = {
      altInput: true,
      time_24hr: true,
      // Fire a 'change' so HTMX or vanilla listeners react when a date is chosen
      onChange: [
        function () {
          try {
            el.dispatchEvent(new Event("change", { bubbles: true }));
            el.dispatchEvent(new Event("input", { bubbles: true }));
          } catch (_) {}
        },
      ],
    };

    // Default formats
    if (isDateTime) {
      opts.enableTime = true;
      opts.dateFormat = "Y-m-d H:i";
      opts.altFormat = "D, M j, H:i";
    } else {
      // default to date-only (also used if neither class present)
      opts.enableTime = false;
      opts.dateFormat = "Y-m-d";
      opts.altFormat = "D, M j";
    }

    // Respect data attributes if present
    if (el.dataset.minDate) opts.minDate = el.dataset.minDate;
    else if (isDateTime || isDateOnly) opts.minDate = "today"; // project default

    if (el.dataset.maxDate) opts.maxDate = el.dataset.maxDate;
    if (el.dataset.defaultDate) opts.defaultDate = el.dataset.defaultDate;

    // Allow per-input JSON override/merge
    Object.assign(opts, parseJsonOptions(el));

    return opts;
  }

  function initFlatpickrs(root) {
    if (!root) root = document;
    // Flatpickr script not loaded? bail quietly.
    if (typeof window.flatpickr === "undefined") return;

    // Support both historical and current conventions
    const selectors = [
      "input.js-date",
      "input.js-datetime",
      "input[data-flatpickr]" // opt-in via data attribute if needed
    ];

    root.querySelectorAll(selectors.join(",")).forEach(function (el) {
      // Don’t double-init
      if (el._flatpickr) return;
      try {
        const options = buildOptions(el);
        window.flatpickr(el, options);
      } catch (err) {
        // Fail silently — never block the page if one field is misconfigured
        console && console.warn && console.warn("Flatpickr init failed:", err, el);
      }
    });
  }

  // Expose for manual calls if needed
  window.initFlatpickrs = initFlatpickrs;

  // Initial load
  document.addEventListener("DOMContentLoaded", function () {
    initFlatpickrs(document);
  });

  // Re-init after HTMX swaps (new DOM fragments)
  if (window.htmx) {
    window.htmx.on("htmx:afterSwap", function (evt) {
      // evt.target is the swapped element; init inside it
      initFlatpickrs(evt.target || document);
    });
    // After settle handles lazy content that sizes after swap
    window.htmx.on("htmx:afterSettle", function (evt) {
      initFlatpickrs(evt.target || document);
    });
  }
})();
