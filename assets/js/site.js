/* Swarm Dynamics: page behaviour. The page reads and navigates without this file; it adds the remembered theme,
   reading progress, the chapter in the top bar, a language switch that keeps the place, scroll-linked depth for
   chapter plates and part statements, atlas search and the figure viewer. Nothing here intercepts scrolling. */
(function () {
  'use strict';
  var d = document, root = d.documentElement, w = window;
  var T = {};
  try { T = JSON.parse((d.getElementById('ui-i18n') || {}).textContent || '{}'); } catch (e) {}
  function $(s, c) { return (c || d).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); }
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) {} return null; }
  function isStatic() { return root.classList.contains('static'); }
  var raf = w.requestAnimationFrame ? w.requestAnimationFrame.bind(w) : function (f) { return setTimeout(f, 16); };

  /* ---------- theme: the checkbox works alone; here it is remembered and mirrored on <html> */
  var box = d.getElementById('theme'), meta = $('meta[name="theme-color"]');
  function paint() {
    var light = !!(box && box.checked);
    root.classList.toggle('light', light);
    if (meta) meta.setAttribute('content', light ? '#f6f8f7' : '#0a0c0d');
    d.dispatchEvent(new CustomEvent('aas:theme'));
  }
  if (box) {
    box.checked = store('aas-theme') === 'light';
    paint();
    box.addEventListener('change', function () { paint(); store('aas-theme', box.checked ? 'light' : 'dark'); });
    w.addEventListener('pageshow', function () { box.checked = store('aas-theme') === 'light'; paint(); });
  }
  var mq = w.matchMedia ? w.matchMedia('(prefers-reduced-motion: reduce)') : null;
  if (mq) {
    var onMq = function (e) { root.classList.toggle('static', e.matches); dirty = true; pinPlates(); tick(); };
    if (mq.addEventListener) mq.addEventListener('change', onMq); else if (mq.addListener) mq.addListener(onMq);
  }

  /* ---------- wide tables: show the hint only where the table really scrolls */
  function markTables() { $$('.table-wrap').forEach(function (t) { t.classList.toggle('is-scrollable', t.scrollWidth > t.clientWidth + 2); }); }
  markTables();
  w.addEventListener('resize', markTables);

  /* ---------- contents sheet (a <details>): close on choice, outside tap or Escape */
  var mt = $('.mtoc');
  if (mt) {
    $$('a', mt).forEach(function (a) { a.addEventListener('click', function () { mt.open = false; }); });
    d.addEventListener('click', function (e) { if (mt.open && !mt.contains(e.target)) mt.open = false; });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && mt.open) { mt.open = false; $('summary', mt).focus(); } });
    mt.addEventListener('toggle', function () {
      if (!mt.open) return;
      var nav = $('nav', mt), on = $('.secs a.on', mt) || $('li.cur > a', mt);
      if (nav && on) nav.scrollTop = Math.max(0, on.offsetTop - nav.clientHeight / 3);
    });
  }

  /* ---------- the single page: where the reader is */
  var main = d.getElementById('main');
  var here = $('.here'), hereN = $('.here-n'), hereT = $('.here-t'), bar = $('.progress'), rail = $('.rail'), lang = $('a.langbtn');
  var chapters = $$('main section.chapter[data-k], main section.refsec[data-k], main section.part[id]');   // a part opener is a place too
  var anchorSel = 'main :is(section.chapter, section.refsec, section.part, section.intro, section.hero, .flow > h3, .flow > h4, .pin-text, article.case, section.note, figure.fig, .scene, li.w)[id]';
  var anchors = [], tops = [], chTops = [], dirty = true, curCh = null, curA = null;
  function docTop(el) { return el.getBoundingClientRect().top + w.pageYOffset; }
  function measure() {   // only rendered anchors, in the order of their tops (rows hidden by an atlas filter have no place)
    var list = $$(anchorSel).filter(function (e) { return e.getClientRects().length; })
      .map(function (e) { return { e: e, t: docTop(e) }; }).sort(function (a, b) { return a.t - b.t; });
    anchors = list.map(function (x) { return x.e; });
    tops = list.map(function (x) { return x.t; });
    chTops = chapters.map(docTop);
    dirty = false;
  }
  function find(list, y) {   // last index with list[i] <= y
    var lo = 0, hi = list.length - 1, ans = -1;
    while (lo <= hi) { var mid = (lo + hi) >> 1; if (list[mid] <= y) { ans = mid; lo = mid + 1; } else hi = mid - 1; }
    return ans;
  }
  function chapterLabel(sec) {
    if (sec.classList.contains('part')) {   // while a part statement is read, the bar names that part, not the chapter before it
      var pk = $('.part-k', sec), pt = $('.part-t', sec), m = /([IVX]+)\s*$/.exec(pk ? pk.textContent : '');
      return { n: m ? m[1] : '·', t: pt ? pt.textContent : '' };
    }
    var k = sec.getAttribute('data-k'), t = $('.plate-t, .refhead h2', sec), short = mt && $('.outline li[data-k="' + k + '"] > a', mt);
    var n = /^ch\d\d$/.test(k) ? String(parseInt(k.slice(2), 10)) : (k === 'atlas' ? '12' : '·');
    if (short) { short = short.cloneNode(true); var nn = $('.nn', short); if (nn) nn.remove(); }   // the contents' short title fits the bar
    return { n: n, t: short ? short.textContent.trim() : (t ? t.textContent : '') };
  }
  var outlineItems = mt ? $$('.outline li[data-k]', mt) : [];
  var railLinks = rail ? $$('a[data-k]', rail) : [];
  var railIdx = railLinks.map(function (a) { var k = a.getAttribute('data-k'); for (var i = 0; i < chapters.length; i++) if (chapters[i].getAttribute('data-k') === k) return i; return -1; });
  function place() {
    if (dirty) measure();
    var y = w.pageYOffset, vh = w.innerHeight;
    if (bar) {
      var max = Math.max(1, d.documentElement.scrollHeight - vh);
      bar.style.setProperty('--p', Math.max(0, Math.min(1, y / max)).toFixed(4));
    }
    var ci = find(chTops, y + vh * 0.3), ch = ci >= 0 ? chapters[ci] : null;
    if (ch !== curCh) {
      curCh = ch;
      if (here) {
        if (ch) {
          var lab = chapterLabel(ch);
          hereN.textContent = lab.n; hereT.textContent = lab.t;
          here.setAttribute('href', '#' + ch.id);
          here.classList.add('on'); here.classList.remove('swap'); void here.offsetWidth; here.classList.add('swap');
        } else here.classList.remove('on');
      }
      var k = ch ? ch.getAttribute('data-k') : '';
      outlineItems.forEach(function (li) { li.classList.toggle('cur', li.getAttribute('data-k') === k); });
      if (rail) {
        rail.classList.toggle('on', !!ch);
        railLinks.forEach(function (a, j) {   // done = everything above the current place, a part opener included
          var me = a.getAttribute('data-k') === k;
          a.classList.toggle('cur', me);
          a.classList.toggle('done', !me && railIdx[j] >= 0 && railIdx[j] < ci);
        });
      }
    }
    var ai = find(tops, y + Math.min(160, vh * 0.25)), a = ai >= 0 ? anchors[ai] : null;
    if (a !== curA) {
      curA = a;
      if (mt && a) {
        var hid = a.id;
        $$('.secs a.on', mt).forEach(function (x) { x.classList.remove('on'); });
        if (/-s-\d+$/.test(hid)) { var l = $('.secs a[href="#' + hid + '"]', mt); if (l) l.classList.add('on'); }
      }
      syncLang();
    }
  }
  function syncLang() {
    if (!lang) return;
    var base = lang.getAttribute('href').split('#')[0], h = location.hash.slice(1), id = '';
    if (curA && curA.id) id = curA.id;
    else if (h && !/^zoom/.test(h)) id = h;
    lang.setAttribute('href', base + (id && w.pageYOffset > 40 ? '#' + id : ''));
  }
  if (lang) {
    var fresh = function () { place(); };
    lang.addEventListener('pointerdown', fresh);
    lang.addEventListener('focus', fresh);
    lang.addEventListener('click', function () { place(); syncLang(); });
  }

  /* ---------- scroll-linked depth: --p (0 → 1 across the viewport), --e (entry), --c (a plate being covered) */
  var sl = $$('[data-sl]'), live = new Set(), plates = $$('.plate');
  function pinPlates() {
    var vh = w.innerHeight;
    plates.forEach(function (pl) {
      var inner = $('.plate-in', pl);
      if (!inner || isStatic()) { pl.classList.remove('pin'); return; }
      var need = inner.offsetHeight + parseFloat(getComputedStyle(pl).paddingTop) + parseFloat(getComputedStyle(pl).paddingBottom);
      pl.classList.toggle('pin', need <= vh * 0.98);
    });
  }
  function depth() {
    var vh = w.innerHeight;
    live.forEach(function (el) {
      var r = el.getBoundingClientRect();
      var p = (vh - r.top) / (vh + r.height), e = (vh - r.top) / (vh * 0.55);
      el.style.setProperty('--p', Math.max(0, Math.min(1, p)).toFixed(3));
      el.style.setProperty('--e', Math.max(0, Math.min(1, e)).toFixed(3));
      if (el.classList.contains('pin')) {
        var sh = el.nextElementSibling;
        if (sh) {
          var c = 1 - sh.getBoundingClientRect().top / vh;
          el.style.setProperty('--c', Math.max(0, Math.min(1, c)).toFixed(3));
        }
      }
    });
  }
  if ('IntersectionObserver' in w) {   // also under reduced motion: the preference can change while the page is open
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) live.add(e.target); else { live.delete(e.target); } });
      tick();
    }, { rootMargin: '25% 0px 25% 0px' });
    sl.forEach(function (el) { io.observe(el); });
  }
  var ticking = 0;
  function tick() {
    if (ticking) return;
    ticking = raf(function () { ticking = 0; place(); if (!isStatic()) depth(); });
  }
  w.addEventListener('scroll', tick, { passive: true });
  w.addEventListener('resize', function () { dirty = true; pinPlates(); markTables(); tick(); });
  if ('ResizeObserver' in w && main) {
    var rt = 0;
    new ResizeObserver(function () { clearTimeout(rt); rt = setTimeout(function () { dirty = true; tick(); }, 120); }).observe(main);
  }
  w.addEventListener('hashchange', function () { dirty = true; tick(); });
  /* an address with a fragment lands on its target even if late layout (images, pinning) moved it, until the reader moves */
  var moved = false;
  ['wheel', 'touchstart', 'keydown', 'pointerdown'].forEach(function (ev) { w.addEventListener(ev, function () { moved = true; }, { passive: true, once: true }); });
  function toHash() {
    if (moved || location.hash.length < 2) return;
    var id = location.hash.slice(1); try { id = decodeURIComponent(id); } catch (e) {}
    var t = d.getElementById(id);
    if (!t || t.closest('.lightbox')) return;
    var sb = root.style.scrollBehavior; root.style.scrollBehavior = 'auto';
    t.scrollIntoView({ block: 'start' });
    root.style.scrollBehavior = sb;
  }
  w.addEventListener('load', function () { dirty = true; pinPlates(); toHash(); tick(); });
  pinPlates();
  toHash();
  tick();

  /* ---------- a card addressed by the URL: open its authors-and-source disclosure if that was the target */
  function openTarget() {
    var id = decodeURIComponent(location.hash.slice(1));
    if (!id || /^zoom|-zoom-/.test(id)) return;
    var el = d.getElementById(id);
    var det = el && el.closest && el.closest('details');
    if (det && !det.open) det.open = true;
  }
  openTarget();
  w.addEventListener('hashchange', openTarget);
  w.addEventListener('beforeprint', function () { $$('details.pass').forEach(function (x) { x.open = true; }); });

  /* ---------- atlas: text search, visible count, reset; the radio filters themselves are CSS */
  var q = d.getElementById('atlas-q');
  if (q) {
    var items = $$('.worklist .w'), cnt = d.getElementById('atlas-count'), empty = d.getElementById('atlas-empty');
    var reset = d.getElementById('atlas-reset'), panel = $('.fpanel'), radios = $$('.filters input[type=radio]');
    var texts = items.map(function (li) { return li.textContent.toLowerCase(); });
    var update = function () {
      var words = q.value.trim().toLowerCase().split(/\s+/).filter(Boolean), n = 0;
      items.forEach(function (li, i) {
        var hit = words.every(function (x) { return texts[i].indexOf(x) >= 0; });
        li.classList.toggle('hide', !hit);
        if (hit && li.offsetParent !== null) n++;
      });
      cnt.textContent = (T.shown || 'Shown') + ': ' + n + ' / ' + items.length;
      if (empty) empty.classList.toggle('on', n === 0);
      if (reset) reset.hidden = !(words.length || radios.some(function (r) { return r.checked && !/-all$/.test(r.id); }));
      dirty = true; tick();   // rows came and went: measure the places again, even when the list kept its height
      d.dispatchEvent(new CustomEvent('aas:atlas'));
    };
    q.addEventListener('input', update);
    radios.forEach(function (r) { r.addEventListener('change', function () { setTimeout(update, 0); }); });
    if (reset) reset.addEventListener('click', function () {
      q.value = '';
      radios.forEach(function (r) { if (/-all$/.test(r.id)) r.checked = true; });
      update();
      q.focus();
    });
    if (panel && w.matchMedia && matchMedia('(max-width: 760px)').matches && !/^#a-/.test(location.hash)) panel.open = false;
    update();
    w.aasAtlasUpdate = update;
  }

  /* ---------- figure viewer: built on first use; zoom, pan, swipe between the page's figures */
  var figs = $$('figure.fig');
  if (!figs.length || !w.HTMLDialogElement) return;
  var ICON = {
    zoom: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2M11 8.5v5M8.5 11h5"/></svg>',
    fit: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2M8.5 11h5"/></svg>',
    orig: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6M20 4l-8 8M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>',
    close: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>',
    prev: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>',
    next: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>'
  };
  var dlg, stage, img, cap, count, bZoom, bOrig, bClose, bPrev, bNext, hint, hintTimer = 0;
  var V = { i: 0, s: 1, x: 0, y: 0, pushed: false };
  function light() { return root.classList.contains('light'); }
  function source(fig) { var a = $('a.zoom', fig); return (light() && a.getAttribute('data-full-light')) || a.getAttribute('data-full'); }
  function thumb(fig) {
    var im = $$('.frame img', fig).filter(function (x) { return x.offsetParent !== null; })[0] || $('.frame img', fig);
    return im ? (im.currentSrc || im.src) : '';
  }
  function zoomButton() {
    var z = V.s > 1.01;
    bZoom.innerHTML = (z ? ICON.fit : ICON.zoom) + '<span class="lab">' + (z ? T.v_fit : T.v_zoom) + '</span>';
    bZoom.setAttribute('aria-label', z ? T.v_fit : T.v_zoom);
    stage.classList.toggle('zoomed', z);
  }
  function bounds(s) {
    var wi = img.offsetWidth * s, he = img.offsetHeight * s, W = stage.clientWidth, H = stage.clientHeight;
    return { x: Math.max(0, (wi - W) / 2 + 12), y: Math.max(0, (he - H) / 2 + 12) };
  }
  function clamp() { var b = bounds(V.s); V.x = Math.max(-b.x, Math.min(b.x, V.x)); V.y = Math.max(-b.y, Math.min(b.y, V.y)); }
  function apply(anim) {
    stage.classList.toggle('anim', !!anim && !isStatic());
    img.style.transform = 'translate(' + V.x.toFixed(1) + 'px,' + V.y.toFixed(1) + 'px) scale(' + V.s.toFixed(4) + ')';
    zoomButton();
  }
  function maxScale() { var nat = img.naturalWidth && img.offsetWidth ? img.naturalWidth / img.offsetWidth : 1; return Math.max(3, Math.min(8, nat * 1.6)); }
  function zoomAt(s, px, py, anim) {
    s = Math.max(1, Math.min(maxScale(), s));
    var k = s / V.s;
    V.x = px - (px - V.x) * k; V.y = py - (py - V.y) * k; V.s = s;
    if (s <= 1.001) { V.s = 1; V.x = 0; V.y = 0; }
    clamp(); apply(anim);
  }
  function rel(e) { var r = stage.getBoundingClientRect(); return { x: e.clientX - r.left - r.width / 2, y: e.clientY - r.top - r.height / 2 }; }
  function toggleZoom(px, py) {
    if (V.s > 1.01) zoomAt(1, 0, 0, true);
    else zoomAt(Math.max(2.5, Math.min(img.naturalWidth / Math.max(1, img.offsetWidth), 4)), px || 0, py || 0, true);
  }
  function show(i) {
    V.i = (i + figs.length) % figs.length; V.s = 1; V.x = 0; V.y = 0;
    var fig = figs[V.i], full = source(fig), th = thumb(fig);
    img.classList.toggle('chart', !!$('.frame.chart', fig));
    img.src = th || full;
    img.alt = ($('.frame img', fig) || {}).alt || '';
    if (full && full !== th) {
      var pre = new Image(), want = V.i;
      pre.onload = function () { if (V.i === want) { img.src = full; clamp(); apply(false); } };
      pre.src = full;
    }
    var fc = $('figcaption', fig).cloneNode(true);
    $$('.orig', fc).forEach(function (x) { x.remove(); });
    cap.innerHTML = fc.innerHTML;
    count.textContent = figs.length > 1 ? (T.v_count || '{i} / {n}').replace('{i}', V.i + 1).replace('{n}', figs.length) : '';
    bOrig.href = full;
    apply(false);
  }
  function open(i) {
    if (!dlg) build();
    show(i);
    if (dlg.open) return;
    dlg.showModal();
    root.classList.add('vw-lock');
    try { history.pushState({ aasViewer: 1 }, ''); V.pushed = true; } catch (e) { V.pushed = false; }
    if (!store('aas-vw-hint')) {
      hint.classList.add('on'); clearTimeout(hintTimer);
      hintTimer = setTimeout(function () { hint.classList.remove('on'); }, 2600);
      store('aas-vw-hint', '1');
    }
    dlg.focus({ preventScroll: true });
  }
  function close() { if (dlg && dlg.open) dlg.close(); }
  function build() {
    dlg = d.createElement('dialog');
    dlg.className = 'viewer';
    dlg.setAttribute('aria-label', T.v_title || 'Figure viewer');
    dlg.setAttribute('tabindex', '-1');
    dlg.innerHTML = '<div class="vw-top"><span class="vw-count"></span>' +
      '<button class="vw-b vw-zoom" type="button"></button>' +
      '<a class="vw-b vw-orig" target="_blank" rel="noopener">' + ICON.orig + '<span class="lab"></span></a>' +
      '<button class="vw-b vw-close" type="button">' + ICON.close + '</button></div>' +
      '<div class="vw-stage"><img class="vw-img" alt="" draggable="false">' +
      '<button class="vw-nav vw-prev" type="button">' + ICON.prev + '</button><button class="vw-nav vw-next" type="button">' + ICON.next + '</button>' +
      '<span class="vw-hint"></span></div><div class="vw-cap"></div>';
    d.body.appendChild(dlg);
    stage = $('.vw-stage', dlg); img = $('.vw-img', dlg); cap = $('.vw-cap', dlg); count = $('.vw-count', dlg);
    bZoom = $('.vw-zoom', dlg); bOrig = $('.vw-orig', dlg); bClose = $('.vw-close', dlg);
    bPrev = $('.vw-prev', dlg); bNext = $('.vw-next', dlg); hint = $('.vw-hint', dlg);
    bClose.setAttribute('aria-label', T.v_close || 'Close');
    bPrev.setAttribute('aria-label', T.v_prev || 'Previous');
    bNext.setAttribute('aria-label', T.v_next || 'Next');
    $('.lab', bOrig).textContent = T.v_orig || 'Original';
    hint.textContent = T.v_hint || '';
    bPrev.hidden = bNext.hidden = figs.length < 2;
    dlg.addEventListener('close', function () {
      root.classList.remove('vw-lock');
      if (V.pushed) { V.pushed = false; try { history.back(); } catch (e) {} }
      var a = $('a.zoom', figs[V.i]);
      if (a) a.focus({ preventScroll: true });
    });
    bClose.addEventListener('click', close);
    bPrev.addEventListener('click', function () { show(V.i - 1); });
    bNext.addEventListener('click', function () { show(V.i + 1); });
    bZoom.addEventListener('click', function () { toggleZoom(0, 0); });
    dlg.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight' && V.s <= 1.01) { show(V.i + 1); e.preventDefault(); }
      else if (e.key === 'ArrowLeft' && V.s <= 1.01) { show(V.i - 1); e.preventDefault(); }
      else if (e.key === '+' || e.key === '=') { zoomAt(V.s * 1.5, 0, 0, true); e.preventDefault(); }
      else if (e.key === '-') { zoomAt(V.s / 1.5, 0, 0, true); e.preventDefault(); }
      else if (e.key === '0') { zoomAt(1, 0, 0, true); e.preventDefault(); }
    });
    w.addEventListener('resize', function () { if (dlg.open) { clamp(); apply(false); } });
    var P = {}, g = null, lastTap = 0;
    function pts() { return Object.keys(P).map(function (k) { return P[k]; }); }
    stage.addEventListener('pointerdown', function (e) {
      if (e.button > 0 || e.target.closest('.vw-nav')) return;
      stage.setPointerCapture(e.pointerId);
      P[e.pointerId] = { x: e.clientX, y: e.clientY };
      var p = pts();
      if (p.length === 1) g = { mode: 'pan', x0: e.clientX, y0: e.clientY, vx: V.x, vy: V.y, t: Date.now(), moved: false };
      else if (p.length === 2) {
        var r = stage.getBoundingClientRect();
        g = { mode: 'pinch', dist: Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y) || 1, s: V.s, x: V.x, y: V.y,
              mx: (p[0].x + p[1].x) / 2 - r.left - r.width / 2, my: (p[0].y + p[1].y) / 2 - r.top - r.height / 2, moved: true };
      }
    });
    stage.addEventListener('pointermove', function (e) {
      if (!P[e.pointerId] || !g) return;
      P[e.pointerId] = { x: e.clientX, y: e.clientY };
      var p = pts();
      if (g.mode === 'pinch' && p.length >= 2) {
        var dist = Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y) || 1;
        var s = Math.max(1, Math.min(maxScale(), g.s * dist / g.dist)), k = s / g.s;
        V.s = s; V.x = g.mx - (g.mx - g.x) * k; V.y = g.my - (g.my - g.y) * k;
        clamp(); apply(false);
      } else if (g.mode === 'pan') {
        var dx = e.clientX - g.x0, dy = e.clientY - g.y0;
        if (Math.abs(dx) + Math.abs(dy) > 6) g.moved = true;
        if (V.s > 1.01) { V.x = g.vx + dx; V.y = g.vy + dy; clamp(); apply(false); stage.classList.add('dragging'); }
        else if (g.moved) img.style.transform = 'translate(' + dx.toFixed(1) + 'px,' + Math.max(0, dy).toFixed(1) + 'px)';
      }
    });
    function end(e) {
      if (!P[e.pointerId]) return;
      delete P[e.pointerId];
      stage.classList.remove('dragging');
      if (!g) return;
      if (g.mode === 'pinch') { if (!pts().length) { g = null; if (V.s < 1.05) zoomAt(1, 0, 0, true); } return; }
      var dx = e.clientX - g.x0, dy = e.clientY - g.y0, fast = Date.now() - g.t < 600;
      if (V.s <= 1.01 && g.moved) {
        if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) && figs.length > 1) show(V.i + (dx < 0 ? 1 : -1));
        else if (dy > 90 && Math.abs(dy) > Math.abs(dx) && fast) close();
        else apply(true);
      } else if (!g.moved) {
        var ir = img.getBoundingClientRect();
        if (V.s <= 1.01 && (e.clientX < ir.left || e.clientX > ir.right || e.clientY < ir.top || e.clientY > ir.bottom)) { g = null; close(); return; }
        var now = Date.now();
        if (now - lastTap < 320) { var q2 = rel(e); toggleZoom(q2.x, q2.y); lastTap = 0; }
        else lastTap = now;
      }
      g = null;
    }
    stage.addEventListener('pointerup', end);
    stage.addEventListener('pointercancel', end);
    stage.addEventListener('wheel', function (e) {
      e.preventDefault();
      var p = rel(e);
      if (e.ctrlKey || e.metaKey) zoomAt(V.s * Math.exp(-e.deltaY * 0.01), p.x, p.y, false);
      else if (V.s > 1.01) { V.x -= e.deltaX; V.y -= e.deltaY; clamp(); apply(false); }
    }, { passive: false });
  }
  w.addEventListener('popstate', function () { if (dlg && dlg.open) { V.pushed = false; dlg.close(); } });
  figs.forEach(function (fig, i) {
    $('a.zoom', fig).addEventListener('click', function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button > 0) return;
      e.preventDefault();
      open(i);
    });
  });
  /* an address with #<page>-zoom-N (the no-script lightbox) opens the viewer instead */
  var m = /^#(.+)-zoom-(\d+)$/.exec(location.hash);
  if (m) {
    var k = figs.map(function (f) { return f.id; }).indexOf(m[1] + '-fig-' + m[2]);
    if (k >= 0) { try { history.replaceState(null, '', '#' + m[1] + '-fig-' + m[2]); } catch (e) {} figs[k].scrollIntoView(); open(k); }
  }
})();
