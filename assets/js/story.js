/* The prologue (#how): the sticky stage follows the step being read. Scrolling stays native: nothing snaps, nothing
   takes over the wheel, and the reader can stop on any step. Without this file, or with reduced motion, the stage is
   hidden and every scheme shows a static figure of its end state next to the full text. The motion switch in the top
   bar (html.paused) stops the flights, also one already in the air; the stage still changes state, so the reader never
   loses the picture. Also here: the Agensh room's figures fill in when they come into view. */
(function () {
  'use strict';
  var d = document, root = d.documentElement, w = window, NS = 'http://www.w3.org/2000/svg';
  function $$(s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); }
  function isStatic() { return root.classList.contains('static'); }
  function still() { return isStatic() || root.classList.contains('paused') || d.hidden; }
  function onView(el, fn, opts) {
    if (!('IntersectionObserver' in w)) { fn(true); return null; }
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { fn(e.isIntersecting, io); }); }, opts || { threshold: 0.3 });
    io.observe(el);
    return io;
  }

  /* ================= the stage ================= */
  var sec = d.getElementById('how');
  if (sec) (function () {
    var svgs = $$('.stage svg', sec), steps = $$('.steps .step', sec);
    var ORDER = ['ind-0', 'ind-2', 'ind-3', 'coord-0', 'coord-2', 'coord-3', 'mem-0', 'mem-2', 'mem-3', 'sky-1', 'sky-2', 'sky-3'];
    /* a finding travels: [delay in ms, from, to, then what else it brings]. The block or entry it lands in, the label
       on it and the rest of the list wait unseen (.wait) until the flight lands, then appear at once in its place
       (.landed): nobody is marked as having received a finding that is still on its way. */
    var FLIGHTS = {
      'coord-2': [[0, 'b3-5', 'bC-6', 'lC-6'], [760, 'bC-6', 'b1-5', 'l1-5'], [760, 'bC-6', 'b5-5', 'l5-5']],
      'mem-2': [[0, 'b3-5', 'rec', 'q1', 'q5'], [760, 'rec', 'b1-6', 'l1-6'], [760, 'rec', 'b5-6', 'l5-6']]
    };
    var cur = 'ind-0', timers = [];
    function variant(svg) { return svg.classList.contains('v-narrow') ? 'narrow' : 'wide'; }
    function part(svg, id) { var e = d.getElementById(variant(svg) + '-dyn-' + id); return e && e.closest ? e.closest('.k') || e : e; }
    function settle() {   // no flight in the air and nothing waiting: the state shown is complete
      timers.forEach(clearTimeout); timers = [];
      $$('.flight', sec).forEach(function (f) { f.remove(); });
      $$('.wait, .landed', sec).forEach(function (e) { e.classList.remove('wait', 'landed'); });
    }
    function fly(svg, f) {
      var v = variant(svg), A = d.getElementById(v + '-dyn-' + f[1]), B = d.getElementById(v + '-dyn-' + f[2]);
      if (!A || !B || !svg.getClientRects().length || !A.animate) return;
      var ax = +A.getAttribute('x'), ay = +A.getAttribute('y'), bx = +B.getAttribute('x'), by = +B.getAttribute('y');
      var held = f.slice(2).map(function (id) { return part(svg, id); }).filter(Boolean);
      held.forEach(function (e) { e.classList.add('wait'); });
      timers.push(setTimeout(function () {
        var r = d.createElementNS(NS, 'rect');
        ['x', 'y', 'width', 'height', 'rx'].forEach(function (k) { r.setAttribute(k, A.getAttribute(k)); });
        r.setAttribute('class', 'flight');
        svg.appendChild(r);
        var an = r.animate([{ transform: 'translate(0px,0px)' }, { transform: 'translate(' + (bx - ax) + 'px,' + (by - ay) + 'px)' }],
          { duration: 700, delay: 120, easing: 'cubic-bezier(.35,.1,.2,1)', fill: 'both' });
        an.onfinish = function () {
          if (!r.isConnected) return;   // settled meanwhile: a later flight may hold the same block now
          held.forEach(function (e) { if (e.classList.contains('wait')) { e.classList.remove('wait'); e.classList.add('landed'); } });
          var out = r.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 220, fill: 'forwards' });
          out.onfinish = function () { r.remove(); };
        };
      }, f[0]));
    }
    function show(s) {
      if (!s || s === cur) return;
      var forward = ORDER.indexOf(s) > ORDER.indexOf(cur);
      cur = s;
      settle();
      svgs.forEach(function (svg) {
        svg.setAttribute('data-s', s);
        if (forward && !still() && FLIGHTS[s]) FLIGHTS[s].forEach(function (f) { fly(svg, f); });
      });
    }
    d.addEventListener('aas:motion', function () { if (still()) settle(); });   // the motion switch stops a flight in the air too
    function activate(step) {
      steps.forEach(function (st) { st.classList.toggle('on', st === step); });
      show(step.getAttribute('data-s'));
    }
    var io = null, mqN = w.matchMedia ? w.matchMedia('(max-width: 760px)') : null;
    function observe() {
      if (io) { io.disconnect(); io = null; }
      if (!('IntersectionObserver' in w) || isStatic()) return;
      var narrow = mqN && mqN.matches;
      /* a reading line: mid-screen on wide screens, under the stage band on phones */
      io = new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting) activate(e.target); });
      }, { rootMargin: narrow ? '-66% 0px -33% 0px' : '-48% 0px -51% 0px' });
      steps.forEach(function (st) { io.observe(st); });
    }
    if (steps[0]) steps[0].classList.add('on');
    observe();
    if (mqN) { if (mqN.addEventListener) mqN.addEventListener('change', observe); else if (mqN.addListener) mqN.addListener(observe); }
    var mq = w.matchMedia ? w.matchMedia('(prefers-reduced-motion: reduce)') : null;
    if (mq) { var onMq = function () { settle(); observe(); }; if (mq.addEventListener) mq.addEventListener('change', onMq); else if (mq.addListener) mq.addListener(onMq); }
  })();

  /* ================= the Agensh room: figures fill in on view ================= */
  $$('.b17f, .barsf').forEach(function (f) {
    if (isStatic()) { f.classList.add('seen'); return; }
    onView(f, function (vis, io) { if (vis) { f.classList.add('seen'); if (io) io.unobserve(f); } }, { threshold: 0.3 });
  });
})();
