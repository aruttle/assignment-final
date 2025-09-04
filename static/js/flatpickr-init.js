document.addEventListener("DOMContentLoaded", function () {
  const el = document.querySelector("[data-flatpickr]");
  if (el) {
    flatpickr(el, { enableTime: true, dateFormat: "Y-m-d H:i" });
  }
});
