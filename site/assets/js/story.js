/* Index scene: the three schemes play one after another on their own; picking a scheme stops the rotation.
   Without this file the page is complete: the scene shows the end state of the chosen scheme, the steps a list.
   Ported from the approved prototype-v2/src/app.js; texts come from #story-i18n so both languages share it. */
(function () {
  'use strict';
  var root = document.documentElement;
  var NS = 'http://www.w3.org/2000/svg';
  var mq = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
  var L = { agent: 'agent {k}', live: {}, rows: [] };
  try { L = JSON.parse(document.getElementById('story-i18n').textContent); } catch (e) {}
  function label(k, text) { return L.agent.replace('{k}', k) + ' · ' + text; }
  function isStatic() { return root.classList.contains('static'); }
  function $(s, c) { return (c || document).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); }
  function mk(name, attrs, parent) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function onView(el, fn, opts) {
    if (!('IntersectionObserver' in window)) { fn(true); return null; }
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { fn(e.isIntersecting, io); }); }, opts || { threshold: 0.15 });
    io.observe(el);
    return io;
  }

  /* ================= the scene ================= */
  var hero = document.getElementById('how');
  var svgs = hero ? $$('svg.tp', hero) : [];
  if (svgs.length) (function () {
    /* Two geometries of the scene (wide and portrait); the visible one is animated. */
    var svg, fx, rowsG, hub, coll, RG;
    var narr = $('.narr', hero);
    var btn = $('.pp', hero);
    var radios = $$('input[name="mode"]', hero);
    var ORDER = ['ind', 'coord', 'mem'];
    var AG = [1, 2, 3, 4, 5, 6];
    var ags = {}, slots = {};
    function visibleSvg() {
      for (var i = 0; i < svgs.length; i++) if (svgs[i].getClientRects().length) return svgs[i];
      return svgs[0];
    }
    function bind(el) {
      svg = el; fx = $('.fx', svg); rowsG = $('.log .rows', svg); hub = $('.hub', svg); coll = $('.coll', svg);
      ags = {}; slots = {};
      $$('.ag', svg).forEach(function (g) { ags[g.getAttribute('data-n')] = g; });
      $$('.slot', svg).forEach(function (s) { slots[s.getAttribute('data-n')] = s; });
      RG = {};
      ['y0', 'h', 'x0', 'w', 'dot', 'tx'].forEach(function (k) { RG[k] = +rowsG.getAttribute('data-' + k); });
    }
    function ch(id) { return svg.querySelector('[data-ch="' + id + '"]'); }
    bind(visibleSvg());

    var S = { mode: 'ind', t: 0, i: 0, auto: true, paused: false, visible: true, raf: 0, last: 0, pk: [], lane: {}, rows: [], meter: 0.16, amb: 0, amb2: 0 };
    var I = false; // play events instantly (reduced motion)

    function pos(k) {
      var p = ags[k].getAttribute('data-' + S.mode).split(',');
      return { x: +p[0], y: +p[1] };
    }
    function send(id, a, b, cls, dur, done, linear) {
      if (I) { if (done) done(); return null; }
      var path = ch(id);
      var g = mk('g', { 'class': 'pk ' + cls }, fx);
      mk('circle', { 'class': 'h', r: cls === 'p-k' ? 11 : 7 }, g);
      mk('circle', { 'class': 'c', r: cls === 'p-k' ? 5 : (cls === 'p-q' ? 4 : 3.5) }, g);
      var p = { g: g, path: path, len: path.getTotalLength(), a: a, b: b, t0: S.t, dur: dur, done: done, lin: !!linear };
      S.pk.push(p);
      place(p, 0);
      return p;
    }
    function place(p, u) {
      var e = p.lin ? u : (u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2);
      var pt = p.path.getPointAtLength(p.len * (p.a + (p.b - p.a) * e));
      p.g.setAttribute('transform', 'translate(' + pt.x.toFixed(1) + ' ' + pt.y.toFixed(1) + ')');
    }
    function know(k, kind) {
      var a = ags[k];
      a.classList.add('k', kind);
      if (S.mode === 'ind') {
        var s = slots[k];
        if (s.classList.contains('on')) s.classList.add('k');
        if (S.lane[k]) S.lane[k].g.setAttribute('class', 'pk p-k');
        ch('ind-' + k).classList.add('k');
      }
    }
    function hot(id, dir) { ch(id).classList.add('hot', 'hot-' + dir); }
    function beat(i) {
      narr.setAttribute('data-beat', i);
      $$('.beats', narr).forEach(function (ol) {
        var on = ol.classList.contains('beats-' + S.mode);
        $$('li', ol).forEach(function (li, j) { li.classList.toggle('now', on && j === i); });
      });
    }
    function meter(v) { S.meter = Math.min(0.94, v); hub.style.setProperty('--m', S.meter.toFixed(3)); }
    function ripple(k) {
      if (I) return;
      var p = pos(k);
      var g = mk('g', { transform: 'translate(' + p.x + ' ' + p.y + ')' }, fx);
      mk('rect', { 'class': 'rip', x: -64, y: -22, width: 128, height: 44, rx: 22 }, g);
      mk('rect', { 'class': 'rip', x: -64, y: -22, width: 128, height: 44, rx: 22 }, g);
      setTimeout(function () { g.remove(); }, 2000);
    }
    function slot(k) {
      var s = slots[k];
      s.classList.add('on');
      if (ags[k].classList.contains('k')) s.classList.add('k');
    }

    /* ---- the log ---- */
    var VIS = 4;
    function row(k, text, isK) {
      var g = mk('g', { 'class': 'row' + (isK ? ' k' : '') }, rowsG);
      mk('rect', { 'class': 'rh', x: RG.x0, y: -(RG.h - 2) / 2, width: RG.w, height: RG.h - 2, rx: 8 }, g);
      mk('circle', { 'class': 'rd', cx: RG.dot, r: 4 }, g);
      mk('text', { 'class': 'rt', x: RG.tx, dy: '.35em' }, g).textContent = label(k, text);
      if (!I) {
        g.style.opacity = '0';
        g.style.transform = 'translate(0px,' + (RG.y0 + VIS * RG.h) + 'px)';
        g.getBoundingClientRect();
      }
      S.rows.push(g);
      var n = S.rows.length;
      S.rows.forEach(function (r, j) {
        var s = j - Math.max(0, n - VIS);
        r.style.transform = 'translate(0px,' + (RG.y0 + s * RG.h) + 'px)';
        r.style.opacity = s < 0 ? '0' : '1';
      });
      return g;
    }
    function resetRows() {
      rowsG.textContent = '';
      S.rows = [];
      var keep = I; I = true;
      (L.rows || []).forEach(function (r) { row(r[0], r[1]); });
      I = keep;
    }
    var finding = null;
    function ask(k) {
      send('me-' + k, 0, 1, 'p-q', 0.55, function () {
        hot('me-' + k, 'out');
        send('me-' + k, 1, 0, 'p-k', 0.75, function () { know(k, 'ask'); });
      });
    }

    /* ---- scenarios ---- */
    var LANE = { 1: 7.7, 2: 7.2, 3: 6.8, 4: 8.0, 5: 7.4, 6: 7.8 };
    var M = {
      ind: { dur: 11, ev: [
        [0.7, function () { AG.forEach(function (k) { S.lane[k] = send('ind-' + k, 0, 1, 'p-work', LANE[k], function () { slot(k); }, true); }); }],
        [2.1, function () { know(3, 'src'); ripple(3); beat(1); }],
        [4.4, function () { know(1, 'redo'); beat(2); }],
        [5.2, function () { know(5, 'redo'); }],
        [8.8, function () { coll.classList.add('done'); beat(3); }]
      ] },
      coord: { dur: 11.4, ev: [
        [2.2, function () { know(3, 'src'); beat(1); hot('co-3', 'in'); send('co-3', 0, 1, 'p-k', 1, function () { hub.classList.add('k'); }); }],
        [3.9, function () {
          beat(2); hot('co-1', 'out'); hot('co-5', 'out');
          send('co-1', 1, 0, 'p-k', 1, function () { know(1, 'got'); });
          send('co-5', 1, 0, 'p-k', 1, function () { know(5, 'got'); hub.classList.remove('k'); });
        }],
        [6.9, function () { beat(3); hub.classList.add('full'); if (I) meter(0.88); }]
      ], amb: function (t) {
        if (t >= S.amb) {
          var k = AG[Math.floor(Math.random() * 6)];
          send('co-' + k, 0, 1, 'p-co', 0.85, function () { meter(S.meter + 0.045); });
          S.amb = t + 0.36 + Math.random() * 0.4;
        }
        if (t >= S.amb2) {
          var k2 = AG[Math.floor(Math.random() * 6)];
          send('co-' + k2, 1, 0, 'p-co', 0.85);
          S.amb2 = t + 0.7 + Math.random() * 0.6;
        }
      } },
      mem: { dur: 12, ev: [
        [0.9, function () { send('me-6', 0, 1, 'p-mem', 0.7, function () { row(6, L.live.t6); }); }],
        [2.0, function () { know(3, 'src'); beat(1); hot('me-3', 'in'); send('me-3', 0, 1, 'p-k', 0.8, function () { finding = row(3, L.live.t3, true); }); }],
        [3.3, function () { send('me-2', 0, 1, 'p-mem', 0.7, function () { row(2, L.live.t2); }); }],
        [4.2, function () { beat(2); ask(1); }],
        [5.6, function () { ask(5); }],
        [7.3, function () { send('me-4', 0, 1, 'p-mem', 0.7, function () { row(4, L.live.t4); }); }],
        [8.6, function () { beat(3); ags[3].classList.add('done'); if (finding) finding.classList.add('flash'); }]
      ] }
    };

    /* ---- control ---- */
    function clearStage() {
      S.pk = []; S.lane = {}; fx.textContent = ''; finding = null;
      AG.forEach(function (k) { ags[k].setAttribute('class', 'ag'); slots[k].setAttribute('class', 'slot'); });
      $$('.ch', svg).forEach(function (c) { c.classList.remove('hot', 'hot-in', 'hot-out', 'k'); });
      hub.classList.remove('k', 'full'); coll.classList.remove('done');
      meter(0.16);
      resetRows();
    }
    function bar() { return $('.mode input:checked ~ label .prog i', hero); }
    function start(mode) {
      S.mode = mode; S.t = 0; S.i = 0; S.amb = 0.9; S.amb2 = 1.5;
      hero.setAttribute('data-mode', mode);
      $$('.prog i', hero).forEach(function (i) { i.style.transform = 'scaleX(0)'; });
      clearStage();
      beat(0);
      if (isStatic()) {
        I = true;
        M[mode].ev.forEach(function (e) { e[1](); });
        I = false;
      }
    }
    function running() { return !S.paused && S.visible && !document.hidden && !isStatic(); }
    function kick() {
      hero.classList.toggle('offscreen', !S.visible || document.hidden);
      if (!S.raf && running()) { S.last = performance.now(); S.raf = requestAnimationFrame(frame); }
    }
    function check(mode) { radios.forEach(function (r) { r.checked = r.value === mode; }); }
    function frame(now) {
      S.raf = 0;
      if (!running()) return;
      var dt = Math.min((now - S.last) / 1000, 0.05);
      S.last = now;
      S.t += dt;
      var m = M[S.mode];
      while (S.i < m.ev.length && m.ev[S.i][0] <= S.t) { m.ev[S.i][1](); S.i++; }
      if (m.amb && S.t < m.dur - 1.2) m.amb(S.t);
      for (var j = S.pk.length - 1; j >= 0; j--) {
        var p = S.pk[j], u = (S.t - p.t0) / p.dur;
        if (u >= 1) { S.pk.splice(j, 1); p.g.remove(); if (p.done) p.done(); }
        else place(p, u);
      }
      if (S.auto) { var b = bar(); if (b) b.style.transform = 'scaleX(' + Math.min(1, S.t / m.dur).toFixed(4) + ')'; }
      if (S.t >= m.dur) {
        var nx = S.auto ? ORDER[(ORDER.indexOf(S.mode) + 1) % ORDER.length] : S.mode;
        check(nx); start(nx);
      }
      S.raf = requestAnimationFrame(frame);
    }
    function manual() { S.auto = false; hero.classList.remove('auto'); }

    /* On a phone the list of schemes sits under the scene: keep the scene in view, or the change goes unseen. */
    var stageEl = $('.stage', hero);
    function reveal() {
      var r = stageEl.getBoundingClientRect(), vh = window.innerHeight || 0;
      var seen = Math.min(r.bottom, vh) - Math.max(r.top, 0);
      if (seen < r.height * 0.6) stageEl.scrollIntoView({ behavior: isStatic() ? 'auto' : 'smooth', block: 'nearest' });
    }
    radios.forEach(function (r) {
      r.addEventListener('change', function () { if (r.checked) { manual(); start(r.value); reveal(); kick(); } });
      var lab = hero.querySelector('label[for="' + r.id + '"]');
      lab.addEventListener('click', function () { if (r.checked) manual(); });
    });
    btn.addEventListener('click', function () {
      S.paused = !S.paused;
      hero.classList.toggle('paused', S.paused);
      btn.setAttribute('aria-label', S.paused ? btn.getAttribute('data-play') : btn.getAttribute('data-pause'));
      kick();
    });
    document.addEventListener('visibilitychange', kick);
    onView(stageEl, function (vis) { S.visible = vis; kick(); }, { threshold: 0.2 });
    if (mq) {
      var onMq = function (e) { root.classList.toggle('static', e.matches); start(S.mode); kick(); };
      if (mq.addEventListener) mq.addEventListener('change', onMq); else if (mq.addListener) mq.addListener(onMq);
    }
    var mqN = window.matchMedia ? window.matchMedia('(max-width: 599px)') : null;
    if (mqN) {
      var onN = function () {
        var v = visibleSvg();
        if (v === svg) return;
        fx.textContent = ''; S.pk = [];
        bind(v); start(S.mode); kick();
      };
      if (mqN.addEventListener) mqN.addEventListener('change', onN); else if (mqN.addListener) mqN.addListener(onN);
    }
    var first = radios.filter(function (r) { return r.checked; })[0];
    start(first ? first.value : 'ind');
    kick();
  })();

  /* ================= reveal on scroll ================= */
  $$('.ladder, #line-chart').forEach(function (el) {
    if (isStatic()) return;
    el.classList.add('reveal');
    onView(el, function (vis, io) { if (vis) { el.classList.add('in'); if (io) io.unobserve(el); } }, { threshold: 0.35 });
  });

  /* ================= Agensh: how entries reach an agent ================= */
  var fig = $('.chn-fig');
  if (fig && !isStatic()) (function () {
    var phs = $$('.ph', fig);
    var items = $$('[data-t]', fig).map(function (el) { return { el: el, t: +el.getAttribute('data-t') }; });
    var DUR = 6.5, elapsed = 0, visible = false, raf = 0, last = 0;
    fig.classList.add('armed');
    function paint(u) {
      phs.forEach(function (ph) {
        var a = +ph.getAttribute('data-a'), b = +ph.getAttribute('data-b');
        ph.setAttribute(ph.getAttribute('data-axis'), (a + (b - a) * u).toFixed(1));
      });
      items.forEach(function (it) { if (it.t <= u + 0.005) it.el.classList.add('on'); });
    }
    function active() { return visible && !document.hidden && !isStatic() && elapsed < DUR; }
    function step(now) {
      raf = 0;
      if (!active()) { fig.classList.remove('playing'); return; }
      elapsed = Math.min(DUR, elapsed + Math.min((now - last) / 1000, 0.05));
      last = now; paint(elapsed / DUR);
      if (elapsed < DUR) raf = requestAnimationFrame(step);
      else fig.classList.remove('playing');
    }
    function kick() {
      if (isStatic()) { elapsed = DUR; paint(1); }
      if (active() && !raf) {
        fig.classList.add('playing'); last = performance.now(); raf = requestAnimationFrame(step);
      } else if (!active()) fig.classList.remove('playing');
    }
    document.addEventListener('visibilitychange', kick);
    if (mq) {
      if (mq.addEventListener) mq.addEventListener('change', kick); else if (mq.addListener) mq.addListener(kick);
    }
    onView(fig, function (vis) { visible = vis; kick(); }, { threshold: 0.2 });
  })();

  /* ================= chart tooltips ================= */
  var chart = document.getElementById('line-chart');
  var tip = document.getElementById('tip');
  if (chart && tip) {
    var hide = function () { tip.classList.remove('on'); };
    $$('.pt', chart).forEach(function (pt) {
      var show = function () {
        var r = $('.mk', pt).getBoundingClientRect(), cr = chart.getBoundingClientRect();
        tip.innerHTML = '';
        var b = document.createElement('b'); b.textContent = pt.getAttribute('data-v');
        var sm = document.createElement('small'); sm.textContent = ' · ' + pt.getAttribute('data-label');
        tip.appendChild(b); tip.appendChild(sm);
        var x = r.left + r.width / 2 - cr.left, half = tip.offsetWidth / 2 || 70;
        tip.style.left = Math.max(half + 4, Math.min(cr.width - half - 4, x)) + 'px';
        tip.style.top = (r.top - cr.top) + 'px';
        tip.classList.add('on');
      };
      pt.addEventListener('mouseenter', show); pt.addEventListener('focus', show);
      pt.addEventListener('mouseleave', hide); pt.addEventListener('blur', hide);
    });
  }
})();
