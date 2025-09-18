(function () {
  function init(root) {
    if (!window.flatpickr) {
      console.warn("flatpickr not loaded yet");
      return;
    }
    const scope = root || document;
    const inputs = scope.querySelectorAll('input.js-datetime, input[data-flatpickr="1"]');
    inputs.forEach((el) => {
      if (el.dataset.fpBound === "1") return; // don’t re-bind
      el.dataset.fpBound = "1";
      flatpickr(el, {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        time_24hr: true,
        allowInput: true,
        minuteIncrement: 5,
      });
    });
  }

  
  window.initFlatpickrs = init;

 
  document.addEventListener("DOMContentLoaded", function () {
    init(document);
  });

  
  document.body.addEventListener("htmx:afterSwap", function (e) {
    init(e.target || document);
  });

  
  document.addEventListener("shown.bs.modal", function (e) {
    init(e.target || document);
  });
})();
