/* Zero-dependency scenario & horizon filter controller (no external calls, no storage, no user PII inputs) */
(function () {
  "use strict";

  document.querySelectorAll("[data-filter-group]").forEach(function (bar) {
    var group = bar.getAttribute("data-filter-group");
    var buttons = bar.querySelectorAll(".tab-btn");
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var val = btn.getAttribute("data-filter-value");
        buttons.forEach(function (b) {
          b.classList.toggle("active", b === btn);
        });
        document.querySelectorAll('[data-filter-target="' + group + '"]').forEach(function (el) {
          var rowVal = el.getAttribute("data-filter-item");
          if (val === "all" || rowVal === val) {
            el.style.display = "";
          } else {
            el.style.display = "none";
          }
        });
      });
    });
  });
})();
