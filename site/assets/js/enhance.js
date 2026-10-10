/* Optional enhancements. Every page is fully readable and navigable without this file. */
(function () {
  "use strict";
  var d = document, root = d.documentElement;
  root.classList.add("has-js"); d.body && d.body.classList.add("has-js");
  // 1. remember the theme across pages (the toggle itself is a plain checkbox)
  var t = d.getElementById("theme");
  try {
    if (t) {
      if (localStorage.getItem("aas-theme") === "light") t.checked = true;
      t.addEventListener("change", function () { localStorage.setItem("aas-theme", t.checked ? "light" : "dark"); });
    }
  } catch (e) {}
  // 2. show the scroll hint only under tables that actually overflow
  function markTables() {
    [].forEach.call(d.querySelectorAll(".table-wrap"), function (w) {
      w.classList.toggle("is-scrollable", w.scrollWidth > w.clientWidth + 2);
    });
  }
  markTables(); window.addEventListener("resize", markTables);
  // 3. language switch keeps the section anchor
  [].forEach.call(d.querySelectorAll("a.langbtn"), function (a) {
    a.addEventListener("click", function () { if (location.hash && /^#(s-|w-|a-|fig-)/.test(location.hash)) a.href = a.href.split("#")[0] + location.hash; });
  });
  // 4. Escape closes an enlarged figure
  d.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && /^#zoom-/.test(location.hash)) location.hash = location.hash.replace("#zoom-", "#fig-");
  });
  // 5. atlas: text search + visible count (radio filters are pure CSS)
  var q = d.getElementById("atlas-q"), cnt = d.getElementById("atlas-count");
  if (q) {
    var items = [].slice.call(d.querySelectorAll(".worklist .w"));
    var label = root.lang === "ru" ? "Показано: " : "Shown: ";
    var update = function () {
      var s = q.value.trim().toLowerCase(), n = 0;
      items.forEach(function (li) {
        var hit = !s || li.textContent.toLowerCase().indexOf(s) >= 0;
        li.classList.toggle("hide", !hit);
        if (hit && li.offsetParent !== null) n++;
      });
      cnt.textContent = label + n + " / " + items.length;
    };
    q.addEventListener("input", update);
    [].forEach.call(d.querySelectorAll(".filters input[type=radio]"), function (r) { r.addEventListener("change", function () { setTimeout(update, 0); }); });
    update();
  }
})();
