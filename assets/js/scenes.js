/* Swarm Dynamics: the native scenes. Every scene's markup already shows its end state; this file plays the way
   there when the scene is on screen. One scheduler: a scene runs while at least a quarter of it is visible, at
   most two run at once, all stop on a hidden tab, and under reduced motion nothing moves. The prologue and the
   Agensh scene are played by story.js. */
(function () {
  'use strict';
  var d = document, root = d.documentElement, w = window, NS = 'http://www.w3.org/2000/svg';
  var T = {};
  try { T = JSON.parse((d.getElementById('ui-i18n') || {}).textContent || '{}'); } catch (e) {}
  var RU = (root.getAttribute('lang') || '') === 'ru';
  function $(s, c) { return (c || d).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); }
  function mk(name, attrs, parent) {
    var e = d.createElementNS(NS, name);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function isStatic() { return root.classList.contains('static'); }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  var E = { out: function (t) { return 1 - Math.pow(1 - t, 3); }, io: function (t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; } };
  function num(v, dec) { var s = v.toFixed(dec); return RU ? s.replace('.', ',') : s; }
  function visibleSvg(list) { for (var i = 0; i < list.length; i++) if (list[i].getClientRects().length) return list[i]; return list[0]; }
  function css(name) { return getComputedStyle(root).getPropertyValue(name).trim(); }
  function abs(el) {   // absolute position of an SVG element from the translate() chain up to its <svg>
    var x = 0, y = 0;
    for (var n = el; n && n.nodeName !== 'svg'; n = n.parentNode) {
      var t = n.getAttribute && n.getAttribute('transform'), m = t && /translate\(\s*([-\d.]+)[ ,]+([-\d.]+)\s*\)/.exec(t);
      if (m) { x += +m[1]; y += +m[2]; }
    }
    return { x: x, y: y };
  }

  /* ---------------------------------------------------------------- the scheduler */
  var R = {}, scenes = [];
  function def(name, fn) { R[name] = fn; }
  function Scene(el) {
    this.el = el; this.t = 0; this.ei = 0; this.ev = []; this.dur = 0; this.idle = false;
    this.visible = false; this.ratio = 0; this.paused = false; this.ended = false; this.started = false;
    this.btn = $('.sc-pp', el); this.items = $$('.sc-narr .beats li', el); this.dots = $$('.sc-head .dots i', el);
  }
  Scene.prototype.at = function (t, fn) { this.ev.push([t, fn]); this.ev.sort(function (a, b) { return a[0] - b[0]; }); return this; };
  Scene.prototype.beat = function (i) {
    this.items.forEach(function (li, j) { li.classList.toggle('now', j === i); });
    this.dots.forEach(function (x, j) { x.classList.toggle('on', j <= i); });
    this.el.setAttribute('data-beat', i);
  };
  Scene.prototype.reset = function () {
    this.t = 0; this.ei = 0; this.ended = false; this.el.classList.remove('ended');
    if (this.onReset) this.onReset();
    this.label();
  };
  Scene.prototype.finish = function () {   // an idle scene keeps moving after its story: it keeps Pause, not Replay
    this.ended = true; this.el.classList.toggle('ended', !this.idle);
    if (this.onEnd) this.onEnd();
    this.label();
  };
  Scene.prototype.label = function () {
    if (!this.btn) return;
    var b = this.btn, k = this.ended && !this.idle ? 'data-replay' : (this.paused ? 'data-play' : 'data-pause');
    b.setAttribute('aria-label', b.getAttribute(k) || '');
    this.el.classList.toggle('paused', this.paused);
  };
  Scene.prototype.step = function (dt) {
    this.t += dt;
    while (this.ei < this.ev.length && this.ev[this.ei][0] <= this.t) this.ev[this.ei++][1]();
    if (this.onTick) this.onTick(this.t, dt);
    if (this.dur && this.t >= this.dur && !this.ended) this.finish();
  };
  Scene.prototype.active = function () {
    return this.visible && !this.paused && (!this.ended || this.idle) && !d.hidden && !isStatic();
  };
  var rafId = 0, last = 0, MAX = 2;
  function loop(now) {
    rafId = 0;
    var dt = Math.min((now - last) / 1000, 0.05); last = now;
    var act = scenes.filter(function (s) { return s.active(); }).sort(function (a, b) { return b.ratio - a.ratio; }).slice(0, MAX);
    act.forEach(function (s) { s.step(dt); });
    if (act.length) rafId = requestAnimationFrame(loop);
  }
  function kick() {
    if (!rafId && scenes.some(function (s) { return s.active(); })) { last = performance.now(); rafId = requestAnimationFrame(loop); }
  }
  function start(s) {
    if (s.started) return;
    s.started = true; s.el.classList.add('shown');
    if (s.onStart) s.onStart();
  }
  d.addEventListener('visibilitychange', kick);
  var io = 'IntersectionObserver' in w ? new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      var s = e.target.__scene; if (!s) return;
      s.ratio = e.intersectionRatio;
      s.visible = e.isIntersecting && (e.intersectionRatio >= 0.25 || e.intersectionRect.height > w.innerHeight * 0.5);
      if (s.visible) start(s);
    });
    kick();
  }, { threshold: [0, 0.1, 0.25, 0.5, 0.75] }) : null;

  var booted = [];
  function register(s) {   // the moving page: the scheduler, the observer and the pause button, once per scene
    if (s.reg) return;
    s.reg = true; scenes.push(s);
    if (s.btn) s.btn.addEventListener('click', function () {
      if (s.ended && !s.idle) { s.paused = false; s.reset(); }
      else s.paused = !s.paused;
      s.label(); kick();
    });
    s.reset();
    if (io) io.observe(s.el); else { s.visible = true; start(s); kick(); }
  }
  function settle(s) {     // reduced motion: the complete end state; only the interactions remain
    s.el.classList.add('shown');
    if (s.reg && !s.ended) s.finish();
    if (s.onStatic) s.onStatic();
  }
  function boot(el) {
    var name = el.getAttribute('data-scene'), fn = R[name];
    if (!fn || el.__scene) return;
    var s = new Scene(el); el.__scene = s; booted.push(s);
    fn(s, el);
    if (isStatic()) settle(s); else register(s);
  }
  /* the reduced-motion preference can change while the page is open: settle every scene, or bring them all to life */
  var mqr = w.matchMedia ? w.matchMedia('(prefers-reduced-motion: reduce)') : null;
  function onMotionPref() {
    root.classList.toggle('static', !!mqr.matches);
    if (isStatic()) booted.forEach(settle);
    else booted.forEach(function (s) { if (s.reg) { s.paused = false; s.reset(); s.label(); } else register(s); });
    kick();
  }
  if (mqr) { if (mqr.addEventListener) mqr.addEventListener('change', onMotionPref); else if (mqr.addListener) mqr.addListener(onMotionPref); }

  /* ---------------------------------------------------------------- shared tooltip for [data-tip] marks */
  function tips(el) {
    var tip = $('.sc-tip', el); if (!tip) return;
    function show(t) {
      var r = t.getBoundingClientRect(), pr = el.getBoundingClientRect();
      tip.textContent = t.getAttribute('data-tip');
      tip.style.left = clamp(r.left + r.width / 2 - pr.left, 120, pr.width - 120) + 'px';
      tip.style.top = (r.top - pr.top) + 'px';
      tip.classList.add('on');
    }
    function hide() { tip.classList.remove('on'); }
    el.addEventListener('pointerover', function (e) { var t = e.target.closest('[data-tip]'); if (t && el.contains(t)) show(t); });
    el.addEventListener('pointerout', function (e) { if (e.target.closest('[data-tip]')) hide(); });
    el.addEventListener('focusin', function (e) { var t = e.target.closest('[data-tip]'); if (t) show(t); });
    el.addEventListener('focusout', hide);
  }

  /* ---------------------------------------------------------------- Fig. 1.1: the logic of the field */
  def('fieldmap', function (s, el) {
    var fm = $('.fm', el), svg = $('.fm-flow', el), cols = $$('.fm-col', el);
    var pair = el.closest('.pin-pair'), lis = pair ? $$('li[data-fm-col]', pair) : [];
    var rib = [], shown = 0, hotN = 0, stacked = false;
    function geom() {
      var b = fm.getBoundingClientRect();
      svg.setAttribute('viewBox', '0 0 ' + b.width.toFixed(0) + ' ' + b.height.toFixed(0));
      svg.textContent = '';
      rib = []; stacked = false;
      for (var i = 0; i < cols.length - 1; i++) {
        var a = $('.fm-nodes', cols[i]).getBoundingClientRect(), c = $('.fm-nodes', cols[i + 1]).getBoundingClientRect(), dpath;
        if (c.left >= a.right - 4) {
          var sx = a.right - b.left + 2, sy = a.top + a.height / 2 - b.top, ex = c.left - b.left - 2, ey = c.top + c.height / 2 - b.top, dx = (ex - sx) * 0.55;
          dpath = 'M' + sx + ' ' + sy + 'C' + (sx + dx) + ' ' + sy + ' ' + (ex - dx) + ' ' + ey + ' ' + ex + ' ' + ey;
        } else {
          stacked = true;
          var sx2 = a.left + a.width / 2 - b.left, sy2 = a.bottom - b.top + 2, ex2 = c.left + c.width / 2 - b.left, ey2 = c.top - b.top - 2, dy = (ey2 - sy2) * 0.6;
          dpath = 'M' + sx2 + ' ' + sy2 + 'C' + sx2 + ' ' + (sy2 + dy) + ' ' + ex2 + ' ' + (ey2 - dy) + ' ' + ex2 + ' ' + ey2;
        }
        var g = mk('g', { 'class': 'rib' }, svg);
        var band = mk('path', { 'class': 'rb', d: dpath, 'stroke-width': 16 }, g);
        var line = mk('path', { 'class': 'rl', d: dpath }, g);
        var len = line.getTotalLength();
        var pts = [0, 1, 2].map(function (k) { return mk('circle', { 'class': 'pt' + (i === 2 && k === 2 ? ' r' : ''), r: 3.2, opacity: 0 }, g); });
        rib.push({ g: g, band: band, line: line, len: len, pts: pts });
      }
      draw(shown, true);
      scan();
    }
    function draw(n, instant) {
      rib.forEach(function (r, i) {
        var on = i < n - 1;
        [r.band, r.line].forEach(function (p) {
          p.style.transition = instant ? 'none' : 'stroke-dashoffset .9s cubic-bezier(.16,1,.3,1)';
          p.style.strokeDasharray = r.len + ' ' + r.len;
          p.style.strokeDashoffset = on ? 0 : r.len;
        });
      });
    }
    function light(n) { shown = n; cols.forEach(function (c, i) { c.classList.toggle('lit', i < n); }); draw(n, false); }
    function hot(n) {
      hotN = n;
      cols.forEach(function (c, i) { c.classList.toggle('hot', i === n - 1); });
      lis.forEach(function (li) { li.classList.toggle('on', +li.getAttribute('data-fm-col') === n); });
    }
    /* Stacked columns (phones): a column appears when the reader reaches it, not when the clock says so, so a jump into
       the middle of the figure never lands on blank space waiting for earlier beats played off screen. The column
       nearest the middle of the screen is the one highlighted and narrated. */
    function scan() {
      if (!stacked || isStatic()) return;
      var vh = w.innerHeight, reached = 0, near = 0, best = 1e9;
      cols.forEach(function (c, i) {
        var r = c.getBoundingClientRect(), dc = Math.abs((r.top + r.bottom) / 2 - vh / 2);
        if (r.top < vh * 0.88) reached = i + 1;
        if (r.bottom > 0 && r.top < vh && dc < best) { best = dc; near = i + 1; }
      });
      if (reached > shown) light(reached);
      if (near && near <= shown && near !== hotN) { hot(near); s.beat(near - 1); }
    }
    var sf = 0;
    w.addEventListener('scroll', function () { if (stacked && !sf) sf = requestAnimationFrame(function () { sf = 0; scan(); }); }, { passive: true });
    s.dur = 9.2; s.idle = true;
    s.at(0.1, function () { if (stacked) scan(); else { light(1); hot(1); s.beat(0); } })
     .at(2.2, function () { if (!stacked) { light(2); hot(2); s.beat(1); } })
     .at(4.4, function () { if (!stacked) { light(3); hot(3); s.beat(2); } })
     .at(6.6, function () { if (!stacked) { light(4); hot(4); s.beat(3); } })
     .at(9.0, function () { if (!stacked) hot(0); });
    s.onReset = function () { light(0); hot(0); s.beat(-1); scan(); };
    s.onTick = function (t) {
      rib.forEach(function (r, i) {
        var on = i < shown - 1;
        r.pts.forEach(function (p, k) {
          if (!on) { p.setAttribute('opacity', 0); return; }
          var u = ((t / 2.6) + k / 3) % 1, pt = r.line.getPointAtLength(r.len * E.io(u));
          p.setAttribute('cx', pt.x.toFixed(1)); p.setAttribute('cy', pt.y.toFixed(1));
          p.setAttribute('opacity', (Math.sin(u * Math.PI) * 0.95).toFixed(2));
        });
      });
    };
    s.onStatic = function () { shown = 4; cols.forEach(function (c) { c.classList.add('lit'); }); geom(); };
    function hoverCol(n) { if (n) hot(n); else if (s.ended || isStatic()) hot(0); }
    cols.forEach(function (c, i) {
      c.addEventListener('pointerenter', function () { hoverCol(i + 1); });
      c.addEventListener('pointerleave', function () { hoverCol(0); });
    });
    lis.forEach(function (li) {
      li.addEventListener('pointerenter', function () { hoverCol(+li.getAttribute('data-fm-col')); });
      li.addEventListener('pointerleave', function () { hoverCol(0); });
    });
    geom();
    var rt = 0;
    w.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(geom, 150); });
    if ('ResizeObserver' in w) new ResizeObserver(function () { clearTimeout(rt); rt = setTimeout(geom, 120); }).observe(fm);
  });

  /* ---------------------------------------------------------------- Fig. 1.2: how many agents */
  def('scale', function (s, el) {
    var tip = $('.sk-tip', el), plot = $('.sk-plot', el), touchArmed = null;
    $$('.sk-svg', el).forEach(function (svg) {
      var dots = $$('.dot', svg).sort(function (a, b) { return +$('.mk', a).getAttribute('cx') - +$('.mk', b).getAttribute('cx'); });
      dots.forEach(function (a, i) { $('.mk', a).style.transitionDelay = (i * 7) + 'ms'; a.setAttribute('tabindex', i ? '-1' : '0'); });
      svg.addEventListener('keydown', function (e) {
        var cur = d.activeElement, i = dots.indexOf(cur);
        if (i < 0) return;
        var k = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : (e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0);
        if (!k) return;
        e.preventDefault();
        var nx = dots[clamp(i + k, 0, dots.length - 1)];
        cur.setAttribute('tabindex', '-1'); nx.setAttribute('tabindex', '0'); nx.focus();
      });
    });
    function show(a) {
      var c = $('.mk', a), r = c.getBoundingClientRect(), pr = plot.getBoundingClientRect();
      var lay = a.closest('.sk-lay'), kind = lay ? lay.getAttribute('data-lay') : 'sim';
      tip.innerHTML = '';
      var b = d.createElement('b'); b.textContent = a.getAttribute('data-t'); tip.appendChild(b);
      var m = d.createElement('span'); m.className = 'm'; m.textContent = a.getAttribute('data-v') + ' · ' + a.getAttribute('data-e'); tip.appendChild(m);
      var x = d.createElement('span'); x.className = 'x'; x.textContent = a.getAttribute('data-note'); tip.appendChild(x);
      tip.style.left = clamp(r.left + r.width / 2 - pr.left, 150, pr.width - 150) + 'px';
      tip.style.top = (r.top - pr.top) + 'px';
      clearTimeout(hideT);
      tip.classList.add('on');
      $$('.dot.cur', el).forEach(function (o) { o.classList.remove('cur'); });
      a.classList.add('cur');
      void kind;
    }
    var hideT = 0;
    function hideNow() { tip.classList.remove('on'); $$('.dot.cur', el).forEach(function (o) { o.classList.remove('cur'); }); }
    function hide() { clearTimeout(hideT); hideT = setTimeout(hideNow, 140); }
    plot.addEventListener('pointerover', function (e) { var a = e.target.closest('.dot'); if (a && e.pointerType !== 'touch') show(a); });
    plot.addEventListener('pointerout', function (e) {
      var a = e.target.closest('.dot');
      if (a && e.pointerType !== 'touch' && !(e.relatedTarget && a.contains(e.relatedTarget))) hide();
    });
    plot.addEventListener('focusin', function (e) { var a = e.target.closest('.dot'); if (a) show(a); });
    plot.addEventListener('focusout', hide);
    /* touch: the first tap on a dot shows its work, a second tap on the same dot follows the link */
    plot.addEventListener('pointerdown', function (e) {
      var a = e.target.closest('.dot');
      touchArmed = e.pointerType === 'touch' && a ? { a: a, was: a.classList.contains('cur') && tip.classList.contains('on') } : null;
    });
    plot.addEventListener('click', function (e) {
      var a = e.target.closest('.dot');
      if (!a) { hide(); return; }
      if (touchArmed && touchArmed.a === a && !touchArmed.was) { e.preventDefault(); show(a); }
      touchArmed = null;
    });
    $$('.sk-r', el).forEach(function (r) { r.addEventListener('change', hideNow); });
    s.dur = 1.5;
  });

  /* ---------------------------------------------------------------- Fig. 1.3–1.6: plain data charts */
  ['rhythm', 'orgs', 'models'].forEach(function (n) { def(n, function (s, el) { tips(el); s.dur = 1.2; }); });
  function setAtlas(t, e) {
    var ids = ['ft-' + t, 'fe-' + e];
    $$('.filters input[type=radio]').forEach(function (r) { if (/-all$/.test(r.id) && !/^f[te]-/.test(r.id)) r.checked = true; });
    ids.forEach(function (id) { var r = d.getElementById(id); if (r) r.checked = true; });
    var q = d.getElementById('atlas-q'); if (q) q.value = '';
    if (w.aasAtlasUpdate) w.aasAtlasUpdate();
  }
  def('topics', function (s, el) {
    tips(el); s.dur = 1.2;
    el.addEventListener('click', function (e) {
      var a = e.target.closest('.tm-v'); if (!a) return;
      setAtlas(a.getAttribute('data-ft'), a.getAttribute('data-fe'));
      var list = $('#atlas .atlas');
      if (list) {
        e.preventDefault();
        try { history.pushState(null, '', '#atlas'); } catch (x) {}
        list.scrollIntoView({ behavior: isStatic() ? 'auto' : 'smooth', block: 'start' });
      }
    });
  });
  def('atlasmap', function (s, el) {
    tips(el);
    function sync() {
      var t = $('.filters input[name="ft"]:checked'), e = $('.filters input[name="fe"]:checked');
      var tk = t ? t.id.slice(3) : '', ek = e ? e.id.slice(3) : '';
      $$('.tm-v', el).forEach(function (a) { a.classList.toggle('sel', a.getAttribute('data-ft') === tk && a.getAttribute('data-fe') === ek); });
    }
    el.addEventListener('click', function (e) {
      var a = e.target.closest('.tm-v'); if (!a) return;
      e.preventDefault();
      if (a.classList.contains('sel')) setAtlas('all', 'all'); else setAtlas(a.getAttribute('data-ft'), a.getAttribute('data-fe'));
      sync();
    });
    d.addEventListener('aas:atlas', sync);
    sync();
  });

  /* ---------------------------------------------------------------- λ: parallel work buys time with tokens */
  def('lambda', function (s, el) {
    var lx = $('.lx', el), one = $('.lx-one .lx-tr i', el), trs = $('.lx-trs', el), tk1 = $('.lx-tk1 .lx-tb i', el), tkN = $('.lx-tkn .lx-tb i', el);
    var read = $('.lx-read', el), who = $('.lx-many .lx-who', el), who2 = $('.lx-who2', el), vt = $('.lx-vt', el), vc = $('.lx-vc', el), chart = $('.lx-chart', el);
    var N = +lx.getAttribute('data-n'), L0 = +lx.getAttribute('data-l'), L = L0, RUN = 6.5, user = false;
    var extra = (read.getAttribute('data-extra') || '').split(' ').map(Number);   // the one choice outside the measured range
    function lamText(l) { return l === 1 ? '1' : num(l, 2).replace(/0+$/, '').replace(/[.,]$/, ''); }
    function plu(n, forms) {
      var f = forms.split('|'), a = n % 10, b = n % 100;
      if (!RU) return n === 1 ? f[0] : f[1];
      return a === 1 && b !== 11 ? f[0] : (a >= 2 && a <= 4 && (b < 12 || b > 14) ? f[1] : f[2]);
    }
    function parts() {
      var t = Math.pow(N, -L), c = Math.pow(N, 1 - L);
      return { tt: '1/' + num(1 / t, 1).replace(/[.,]0$/, ''), cc: '×' + (Math.abs(c - Math.round(c)) < 0.01 ? String(Math.round(c)) : num(c, c < 10 ? 2 : 1)) };
    }
    function curve(f) {
      var x0 = 40, x1 = 322, y0 = 196, y1 = 20, o = [];
      for (var i = 0; i <= 60; i++) {
        var n = 1 + i * 15 / 60, X = x0 + Math.log2(n) / 4 * (x1 - x0), Y = y0 - Math.log2(f(n)) / 4 * (y0 - y1);
        o.push(X.toFixed(1) + ' ' + Y.toFixed(1));
      }
      return 'M' + o.join(' L');
    }
    function Yf(f) { return (196 - Math.log2(f) / 4 * 176).toFixed(1); }
    function apart(a, b) {   // the curve labels, as in scenes_mech.py: where the curves end, a line apart when the ends nearly meet
      var g = 16, m = (a + b) / 2;
      return Math.abs(a - b) >= g ? [a, b] : (a <= b ? [m - g / 2, m + g / 2] : [m + g / 2, m - g / 2]);
    }
    function setChart() {
      var X = (40 + Math.log2(N) / 4 * 282).toFixed(1), ly = apart(+Yf(Math.pow(16, L)), +Yf(Math.pow(16, 1 - L)));
      $('.c-s', chart).setAttribute('d', curve(function (n) { return Math.pow(n, L); }));
      $('.c-c', chart).setAttribute('d', curve(function (n) { return Math.pow(n, 1 - L); }));
      $('.m-s', chart).setAttribute('cx', X); $('.m-s', chart).setAttribute('cy', Yf(Math.pow(N, L)));
      $('.m-c', chart).setAttribute('cx', X); $('.m-c', chart).setAttribute('cy', Yf(Math.pow(N, 1 - L)));
      $('.cl-s', chart).setAttribute('y', ly[0].toFixed(1));
      $('.cl-c', chart).setAttribute('y', ly[1].toFixed(1));
    }
    function setup() {
      trs.textContent = '';
      for (var i = 0; i < N; i++) { var t = d.createElement('i'); t.style.setProperty('--k', i); trs.appendChild(t); }
      lx.style.setProperty('--t', Math.pow(N, -L).toFixed(4)); lx.style.setProperty('--c', Math.pow(N, 1 - L).toFixed(4));
      var lab = who.getAttribute('data-tpl').replace('{n}', N).replace('{w}', plu(N, who.getAttribute('data-w'))), p = parts();
      who.textContent = lab; who2.textContent = lab; vt.textContent = p.tt; vc.textContent = p.cc;
      read.textContent = read.getAttribute('data-tpl').replace('{n}', N).replace('{l}', lamText(L)).replace('{t}', p.tt).replace('{c}', p.cc)
        + (N === extra[0] && L === extra[1] ? read.getAttribute('data-ext') : '');
      setChart();
      $$('.opt[data-n]', el).forEach(function (b) { b.setAttribute('aria-pressed', +b.getAttribute('data-n') === N ? 'true' : 'false'); });
      $$('.opt[data-l]', el).forEach(function (b) { b.setAttribute('aria-pressed', +b.getAttribute('data-l') === L ? 'true' : 'false'); });
    }
    function progress(t) {
      var ts = RUN * Math.pow(N, -L), a = clamp(t / RUN, 0, 1), b = clamp(t / ts, 0, 1);
      one.style.setProperty('--pr', a.toFixed(4)); trs.style.setProperty('--pm', b.toFixed(4));
      tk1.style.setProperty('--tk', a.toFixed(4)); tkN.style.setProperty('--tk', b.toFixed(4));
    }
    s.onTick = function (t) { progress(t - 0.6); };
    s.onReset = function () { progress(-1); if (!user) { L = L0; setup(); s.beat(0); } };
    s.dur = RUN + 5.6;
    s.at(0.6, function () { if (!user) s.beat(1); })
     .at(0.6 + RUN * Math.pow(16, -L0) + 0.1, function () { if (!user) s.beat(2); })
     .at(RUN + 1.0, function () { if (user) return; s.beat(3); L = 0.68; setup(); })
     .at(RUN + 2.5, function () { if (user) return; L = 0.48; setup(); })
     .at(RUN + 4.0, function () { if (user) return; L = L0; setup(); });
    s.onStatic = function () { progress(99); };
    el.addEventListener('click', function (e) {
      var b = e.target.closest('.opt'); if (!b) return;
      user = true;
      if (b.hasAttribute('data-n')) N = +b.getAttribute('data-n'); else L = +b.getAttribute('data-l');
      setup();
      if (isStatic()) { progress(99); return; }
      s.paused = false; s.reset(); s.label(); kick();
    });
    setup();
  });

  /* ---------------------------------------------------------------- the equalization ledger */
  def('ledger', function (s, el) {
    var tbody = $('tbody', el), rows = $$('tr[data-i]', tbody), heads = $$('tr.lg-h', tbody), order = ['tok', 'lvl', 'time', 'ag', 'price', 'none'], user = false;
    function arrange(mode) {
      var first = new Map();
      rows.concat(heads).forEach(function (r) { first.set(r, r.getBoundingClientRect().top); });
      if (mode === 'group') {
        order.forEach(function (g) {
          var h = heads.filter(function (x) { return x.getAttribute('data-g') === g; })[0];
          var rs = rows.filter(function (x) { return x.getAttribute('data-g') === g; });
          if (!rs.length) return;
          h.hidden = false; tbody.appendChild(h);
          rs.forEach(function (r) { tbody.appendChild(r); });
        });
      } else {
        heads.forEach(function (h) { h.hidden = true; tbody.appendChild(h); });
        rows.slice().sort(function (a, b) { return a.getAttribute('data-i') - b.getAttribute('data-i'); }).forEach(function (r) { tbody.insertBefore(r, heads[0]); });
      }
      el.classList.toggle('grouped', mode === 'group');
      $$('.lg-tools .opt', el).forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-mode') === mode ? 'true' : 'false'); });
      if (isStatic()) return;
      rows.concat(heads).forEach(function (r) {
        var f = first.get(r), l = r.getBoundingClientRect().top;
        if (f === undefined || r.hidden) return;
        var dy = f - l; if (!dy) return;
        r.style.transition = 'none'; r.style.transform = 'translateY(' + dy + 'px)';
        r.getBoundingClientRect();
        r.style.transition = ''; r.style.transform = '';
      });
    }
    el.addEventListener('click', function (e) { var b = e.target.closest('.lg-tools .opt'); if (!b) return; user = true; arrange(b.getAttribute('data-mode')); });
    s.dur = 2.2;
    s.at(1.6, function () { if (!user && !el.classList.contains('grouped')) arrange('group'); });
  });

  /* ---------------------------------------------------------------- HiddenBench: facts that do not add up */
  def('hidden', function (s, el) {
    var svgs = $$('.hb-svg', el), svg, fx, bars = $$('.pb li', el), packets = [], ALL = bars.map(function (b, i) { return i; });
    function bind() { svg = visibleSvg(svgs); fx = $('.fx', svg); }
    bind();
    function pos(sel) { var n = $(sel, svg); return n ? abs(n) : { x: 0, y: 0 }; }
    function hand(k, lab) {
      var ag = $('.ag-' + k, svg), tiles = $$('.hand .tl', ag);
      for (var i = 0; i < tiles.length; i++) if ($('text', tiles[i]).textContent === lab) return abs(tiles[i]);
      return abs(ag);
    }
    function send(k, lab, slotSel, delay, cls) {
      var a = hand(k, lab), b = pos(slotSel + ' .tl');
      var g = mk('g', { 'class': 'tl ' + cls, transform: 'translate(' + a.x + ' ' + a.y + ')' }, fx);
      mk('rect', { x: -15, y: -12, width: 30, height: 24, rx: 6 }, g);
      var tx = mk('text', { dy: '.35em', 'text-anchor': 'middle' }, g); tx.textContent = lab;
      packets.push({ g: g, a: a, b: b, t0: s.t + (delay || 0), dur: 0.8, slot: $(slotSel, svg) });
    }
    function phase(p) { el.setAttribute('data-phase', p); el.classList.remove('verdict'); }
    function dim(on) { bars.forEach(function (li, i) { li.classList.toggle('dim', on.indexOf(i) < 0); }); }
    function wait(all, sel) { $$(sel || '.slot', svg).forEach(function (x) { x.classList.toggle('wait', all); }); }
    function clear() {   // every responsive variant, not only the one now bound: no packet left in flight, no slot waiting
      svgs.forEach(function (v) { var f = $('.fx', v); if (f) f.textContent = ''; $$('.slot', v).forEach(function (x) { x.classList.remove('wait'); }); });
      packets = [];
    }
    /* bars: 0 groups with facts spread, 1 exchange-then-decide, 2 one agent with all facts, 3–4 all facts revealed in round one */
    s.dur = 16.2;
    s.at(0.05, function () { bind(); phase('pre'); s.beat(0); dim(ALL); })
     .at(1.4, function () { phase('talk'); wait(true); s.beat(1); [1, 2, 3, 4].forEach(function (k, i) { send(k, i % 2 ? 'B' : 'A', i % 2 ? '.s-B' : '.s-A', i * 0.35, 'sh'); }); })
     .at(3.1, function () { [3, 1].forEach(function (k, i) { send(k, i ? 'A' : 'B', i ? '.s-A' : '.s-B', i * 0.35, 'sh'); }); })
     .at(4.8, function () { el.classList.add('verdict'); s.beat(2); dim([0]); })
     /* Exchange-Decide: the table makes room for the unique facts; whether all of them arrive is not drawn */
     .at(7.4, function () { phase('ask'); wait(false, '.s-c1, .s-c2, .s-c3, .s-c4'); s.beat(3); dim([1]); })
     /* the separate forced reveal: every fact in round one */
     .at(10.0, function () { phase('swap'); wait(true); fx.textContent = ''; packets = []; s.beat(4); dim([3, 4]);
        [1, 2, 3, 4].forEach(function (k, i) { send(k, 'c' + k, '.s-c' + k, i * 0.3, 'un'); });
        send(1, 'A', '.s-A', 1.3, 'sh'); send(2, 'B', '.s-B', 1.5, 'sh'); })
     .at(13.4, function () { el.classList.add('verdict'); dim([2, 3, 4]); });
    s.onTick = function (t) {
      for (var i = packets.length - 1; i >= 0; i--) {
        var p = packets[i], u = (t - p.t0) / p.dur;
        if (u < 0) continue;
        if (u >= 1) { if (p.slot) p.slot.classList.remove('wait'); p.g.remove(); packets.splice(i, 1); continue; }
        var e = E.io(u), x = p.a.x + (p.b.x - p.a.x) * e, y = p.a.y + (p.b.y - p.a.y) * e - Math.sin(u * Math.PI) * 26;
        p.g.setAttribute('transform', 'translate(' + x.toFixed(1) + ' ' + y.toFixed(1) + ')');
      }
    };
    s.onReset = function () { clear(); phase('pre'); s.beat(-1); dim(ALL); };
    s.onEnd = function () { clear(); phase('swap'); el.classList.add('verdict'); dim(ALL); };
    /* under reduced motion the markup's end state stays: a resize must not reset it to the empty first phase */
    w.addEventListener('resize', function () { var o = svg; bind(); if (o !== svg && !isStatic()) s.reset(); });
  });

  /* ---------------------------------------------------------------- Mind viruses: an idea passed along a chain */
  def('virus', function (s, el) {
    var svgs = $$('.mv-svg', el), svg, fx, pk = [];
    function bind() { svg = visibleSvg(svgs); fx = $('.fx', svg); }
    bind();
    function nodes(r) { return $$('.nd[data-r="' + r + '"]', svg).sort(function (a, b) { return a.getAttribute('data-i') - b.getAttribute('data-i'); }); }
    function hop(r, i, t0, block) {   // block: the next agent refuses; the idea stops halfway
      var ns = nodes(r), a = abs(ns[i]), b = ns[i + 1] ? abs(ns[i + 1]) : a;
      var g = mk('g', { 'class': 'pk' + (block ? ' blk' : ''), transform: 'translate(' + a.x + ' ' + a.y + ')', opacity: 0 }, fx);
      mk('circle', { r: 5 }, g);
      pk.push({ g: g, a: a, b: block ? { x: a.x + (b.x - a.x) * 0.55, y: a.y } : b, t0: t0, dur: 0.5, done: function () { if (ns[i + 1]) ns[i + 1].classList.add('on'); }, fade: block });
    }
    function chain(r) {   // hop along the infected stretch, then into the first agent that resists
      var ns = nodes(r), t = s.t;
      for (var i = 0; i + 1 < ns.length; i++) {
        var nx = ns[i + 1];
        if (nx.classList.contains('inf')) hop(r, i, t + i * 0.52, false);
        else { if (nx.classList.contains('ref')) hop(r, i, t + i * 0.52, true); break; }
      }
    }
    function mark(r) { $$('.mv-m[data-r="' + r + '"]', svg).forEach(function (m) { m.classList.add('on'); }); }
    s.dur = 9.6;
    s.at(0.05, function () { bind(); s.beat(0); nodes('plain')[0].classList.add('on'); nodes('warned')[0].classList.add('on'); })
     .at(1.0, function () { s.beat(1); chain('plain'); })
     .at(1.25, function () { chain('warned'); })
     .at(5.9, function () { s.beat(2); mark('plain'); })
     .at(6.9, function () { s.beat(3); mark('warned'); });
    s.onTick = function (t) {
      for (var i = pk.length - 1; i >= 0; i--) {
        var p = pk[i], u = (t - p.t0) / p.dur;
        if (u < 0) continue;
        if (u >= 1) { p.g.remove(); pk.splice(i, 1); if (p.done) p.done(); continue; }
        if (!p.fade) p.g.setAttribute('opacity', 1);
        var e = E.io(u);
        p.g.setAttribute('transform', 'translate(' + (p.a.x + (p.b.x - p.a.x) * e).toFixed(1) + ' ' + (p.a.y - Math.sin(u * Math.PI) * 10).toFixed(1) + ')');
        if (p.fade) p.g.setAttribute('opacity', (1 - u).toFixed(2));
      }
    };
    function clear() { $$('.fx', el).forEach(function (f) { f.textContent = ''; }); pk = []; }   // the packets of every variant
    s.onReset = function () {
      el.classList.add('armed');
      $$('.nd', el).forEach(function (n) { n.classList.remove('on'); n.style.transitionDelay = ''; });
      $$('.mv-m', el).forEach(function (n) { n.classList.remove('on'); });
      clear(); s.beat(-1);
    };
    s.onEnd = function () { clear(); el.classList.remove('armed'); };
    w.addEventListener('resize', function () { var o = svg; bind(); if (o !== svg && !isStatic()) s.reset(); });
  });

  /* ---------------------------------------------------------------- DeepMind: one loophole, a shared proof store */
  def('loophole', function (s, el) {
    var svgs = $$('.lh-svg', el), svg;
    function bind() { svg = visibleSvg(svgs); }
    bind();
    var D1 = 7, D2 = 4;     // seconds for the first 57 minutes and for the last 27
    function minute(t) { return t <= D1 ? t / D1 * 57 : Math.min(84, 57 + (t - D1) / D2 * 27); }
    var cells, ags, ph, fill, ax;
    function grab() {
      cells = $$('.pc[data-i]', svg).sort(function (a, b) { return a.getAttribute('data-i') - b.getAttribute('data-i'); });
      ags = $$('.ad[data-g]', svg); ph = $('.tl-ph', svg); fill = $('.tl-fill', svg);
      var axl = $('.tl-ax', svg); ax = axl ? [+axl.getAttribute('x1'), +axl.getAttribute('x2')] : null;
    }
    grab();
    var groupAt = { ex: [57, 60], cv: [64, 70], wb: [68, 80], un: [80, 82] };
    function paint(m) {
      cells.forEach(function (c, i) {
        var at = i < 37 ? (i + 1) / 37 * 56 : 57 + Math.pow((i - 36) / 34, 0.7) * 26;
        c.classList.toggle('on', m >= at);
      });
      var k = {};
      ags.forEach(function (a) {
        var g = a.getAttribute('data-g'), r = groupAt[g]; k[g] = (k[g] || 0) + 1;
        var n = { ex: 9, cv: 5, wb: 24, un: 62 }[g], at = r[0] + (r[1] - r[0]) * (k[g] - 1) / Math.max(1, n - 1);
        a.classList.toggle('on', m >= at);
        if (a.classList.contains('first')) a.classList.toggle('flag', m >= 57);
      });
      if (ph && ax) ph.setAttribute('x', (ax[0] + (ax[1] - ax[0]) * m / 84).toFixed(1));
      if (fill) fill.style.transform = 'scaleX(' + (m / 84).toFixed(4) + ')';
    }
    s.dur = D1 + D2 + 1.6;
    s.at(0.05, function () { bind(); grab(); s.beat(0); })
     .at(0.9, function () { s.beat(1); })
     .at(D1, function () { s.beat(2); })
     .at(D1 + D2 * 0.35, function () { s.beat(3); });
    s.onTick = function (t) { paint(minute(t)); };
    s.onReset = function () { el.classList.add('armed'); paint(0); s.beat(-1); };
    s.onEnd = function () { paint(84); el.classList.remove('armed'); };
    /* under reduced motion the other layout shows the end state too; with motion it starts over */
    w.addEventListener('resize', function () { var o = svg; bind(); if (o !== svg) { grab(); if (isStatic()) paint(84); else s.reset(); } });
  });

  /* ---------------------------------------------------------------- Echo: thirty copies, about one vote */
  def('echo', function (s, el) {
    var svg = $('.ec-svg', el), trailsG = $('.trails', svg), dots = $$('.ed', svg), meter = $('.ec-meter', el), mb = $('b', meter), ml = $('span', meter);
    var P = dots.map(function (c) { return { c: c, x: +c.getAttribute('data-x'), y: +c.getAttribute('data-y'), ex: +c.getAttribute('data-ex'), ey: +c.getAttribute('data-ey') }; });
    var trails = [], mix = false, RUN = 6.5, T0 = 1.2;   // one continuous pull, not a round-by-round measurement
    function setMeter(v, lab) { mb.textContent = v; ml.textContent = lab; }
    function at(p, u, spread) {   // position after a fraction u of the debate
      var e = E.io(u), k = spread || 1;
      return { x: p.x + (p.ex * k - p.x) * e, y: p.y + (p.ey * k - p.y) * e };
    }
    function place(u, spread) {
      P.forEach(function (p, i) {
        var q = at(p, u, spread);
        p.c.setAttribute('cx', q.x.toFixed(1)); p.c.setAttribute('cy', q.y.toFixed(1));
        if (trails[i]) trails[i].setAttribute('d', 'M' + p.x.toFixed(1) + ' ' + p.y.toFixed(1) + ' L' + q.x.toFixed(1) + ' ' + q.y.toFixed(1));
      });
    }
    function newTrails() { trailsG.textContent = ''; trails = P.map(function () { return mk('path', {}, trailsG); }); }
    var phase2 = T0 + RUN + 2.6;
    s.dur = phase2 + T0 + RUN + 1.4;
    s.at(0.05, function () { s.beat(0); })
     .at(T0, function () { s.beat(1); })
     .at(T0 + RUN, function () { s.beat(2); setMeter(meter.getAttribute('data-end'), meter.getAttribute('data-label')); })
     .at(phase2, function () { s.beat(3); mix = true; svg.classList.add('mix'); newTrails(); setMeter(meter.getAttribute('data-start'), meter.getAttribute('data-start-label')); })
     .at(phase2 + T0 + RUN, function () { setMeter(meter.getAttribute('data-mix'), meter.getAttribute('data-label')); });
    s.onTick = function (t) {
      var tt = t - (mix ? phase2 : 0) - T0;
      place(clamp(tt / RUN, 0, 1), mix ? 1.9 : 1);
    };
    s.onReset = function () { mix = false; svg.classList.remove('mix'); newTrails(); place(0, 1); s.beat(-1); setMeter(meter.getAttribute('data-start'), meter.getAttribute('data-start-label')); };
    s.onEnd = function () { mix = false; svg.classList.remove('mix'); trailsG.textContent = ''; place(1, 1); setMeter(meter.getAttribute('data-end'), meter.getAttribute('data-label')); };
  });

  /* ---------------------------------------------------------------- Consensus: the threshold, a toy model */
  /* The same toy as scripts/scenes_mech.py (see the comment there): an agent reads the mean answer of all the others, m,
     and picks the favoured answer with probability 1/(1 + e^(−2(K·m + h))). The bar under the chart is the exact
     distribution of a group's end state after R rounds from a random start, recomputed when K changes. */
  def('consensus', function (s, el) {
    var svgs = $$('.cs-svg', el), range = $('.cs-k', el), out = $('.cs-o', el), ob = $('.cs-out', el), svg, sims = [], G, labs;
    var CN = +ob.getAttribute('data-n'), CH = +ob.getAttribute('data-h'), CR = +ob.getAttribute('data-r'), CC = +ob.getAttribute('data-cut');
    function P(K, m) { return 1 / (1 + Math.exp(-2 * (K * m + CH))); }
    function X(K) { return G.x0 + (K - 0.2) / 1.8 * (G.x1 - G.x0); }
    function Y(f) { return G.y0 - f * (G.y0 - G.y1); }
    function kText(K) { return num(K, 2).replace(/0$/, '').replace(/[.,]$/, ''); }
    function fresh(sm) { sm.tot = 0; sm.st = sm.rects.map(function () { var v = Math.random() < 0.5 ? 1 : -1; sm.tot += v; return v; }); }
    function bind() {
      svg = visibleSvg(svgs); labs = (svg.getAttribute('data-l') || '').split('|');
      G = { x0: +svg.getAttribute('data-x0'), x1: +svg.getAttribute('data-x1'), y0: +svg.getAttribute('data-y0'), y1: +svg.getAttribute('data-y1') };
      var dots = $$('.mk.live', svg), K2 = range ? +range.value : 1.6;
      sims = $$('.snap', svg).map(function (g, j) {
        var sm = { rects: $$('.g8 .op', g), K: j === 2 ? K2 : +g.getAttribute('data-k'), sv: $('.sv', g), sv2: $('.sv2', g), lab: $('.sl', g), dot: dots[j] };
        fresh(sm); return sm;
      });
    }
    function draw(sm) {
      var a = 0;
      sm.rects.forEach(function (r, i) { var on = sm.st[i] > 0; if (on) a++; r.setAttribute('class', 'op ' + (on ? 'a' : 'b')); });
      var f = a / sm.st.length;
      sm.sv2.textContent = Math.round(f * 100) + (RU ? ' %' : '%');
      if (sm.dot) { sm.dot.setAttribute('cx', X(sm.K).toFixed(1)); sm.dot.setAttribute('cy', Y(f).toFixed(1)); }
    }
    function stepSim(sm, n) {
      var N = sm.st.length;
      for (var k = 0; k < n; k++) {
        var i = (Math.random() * N) | 0, v = Math.random() < P(sm.K, (sm.tot - sm.st[i]) / (N - 1)) ? 1 : -1;
        sm.tot += v - sm.st[i]; sm.st[i] = v;
      }
    }
    function outcomes(K) {   // the count of agents on the favoured answer is a birth–death chain: evolve its distribution
      var N = CN, v = new Float64Array(N + 1), w2 = new Float64Array(N + 1), up = new Float64Array(N + 1), dn = new Float64Array(N + 1), c = 1, sum = 0, k, t, x;
      for (k = 0; k <= N; k++) { v[k] = c; sum += c; c = c * (N - k) / (k + 1); }
      for (k = 0; k <= N; k++) {
        v[k] /= sum;
        up[k] = (N - k) / N * P(K, (2 * k - N + 1) / (N - 1));
        dn[k] = k / N * (1 - P(K, (2 * k - N - 1) / (N - 1)));
      }
      for (t = 0; t < CR * N; t++) {
        for (k = 0; k <= N; k++) w2[k] = v[k] * (1 - up[k] - dn[k]) + (k ? v[k - 1] * up[k - 1] : 0) + (k < N ? v[k + 1] * dn[k + 1] : 0);
        x = v; v = w2; w2 = x;
      }
      var a = 0, b = 0;
      for (k = CC; k <= N; k++) a += v[k];
      for (k = 0; k <= N - CC; k++) b += v[k];
      return [a, 1 - a - b, b];
    }
    function pctRound(ps) {   // whole percentages adding up to 100: largest remainder, ties to the earlier item
      var raw = ps.map(function (p) { return p * 100; }), fl = raw.map(Math.floor), left = 100 - fl.reduce(function (a, b) { return a + b; }, 0);
      raw.map(function (r, i) { return i; }).sort(function (i, j) { return (raw[j] - fl[j]) - (raw[i] - fl[i]) || i - j; }).slice(0, left).forEach(function (i) { fl[i]++; });
      return fl;
    }
    function setOut(K) {
      var ps = outcomes(K), pc = pctRound(ps);
      $$('.cs-bar i', ob).forEach(function (seg, i) { seg.style.setProperty('--w', ps[i].toFixed(4)); });
      $$('.cs-out-l b', ob).forEach(function (b, i) { b.textContent = pc[i] + (RU ? ' %' : '%'); });
      $('.cs-out-t', ob).textContent = ob.getAttribute('data-tpl').replace('{v}', kText(K));
    }
    var pend = 0;
    function setK(K) {
      var sm = sims[2]; sm.K = K;
      sm.sv.textContent = sm.sv.textContent.replace(/=\s*[\d.,]+/, '= ' + kText(K));
      if (sm.lab && labs.length === 3) sm.lab.textContent = labs[K < 0.9 ? 0 : (K <= 1.1 ? 1 : 2)];
      if (out) out.textContent = kText(K);
      if (sm.dot) sm.dot.setAttribute('cx', X(K).toFixed(1));
      if (!pend) pend = requestAnimationFrame(function () { pend = 0; setOut(range ? +range.value : K); });
    }
    bind();
    s.idle = true; s.dur = 10;
    s.at(0.05, function () { s.beat(0); }).at(2.6, function () { s.beat(1); }).at(5.2, function () { s.beat(2); }).at(7.8, function () { s.beat(3); });
    var acc = 0;
    s.onTick = function (t, dt) {
      acc += dt;
      if (acc < 1 / 30) return;
      acc = 0;
      sims.forEach(function (sm) { stepSim(sm, 24); draw(sm); });
    };
    s.onReset = function () { sims.forEach(function (sm) { fresh(sm); draw(sm); }); s.beat(-1); };
    s.onStatic = function () { sims.forEach(function (sm) { fresh(sm); stepSim(sm, CR * CN); draw(sm); }); };   // a run of R rounds, still
    if (range) range.addEventListener('input', function () { setK(+range.value); if (isStatic() || !s.active()) { var sm = sims[2]; stepSim(sm, 6000); draw(sm); } });
    w.addEventListener('resize', function () { var o = svg; svg = visibleSvg(svgs); if (o !== svg) { bind(); if (range) setK(+range.value); } });
  });

  /* ---------------------------------------------------------------- Moltbook: registrations and owners */
  /* The canvas lies over the visible SVG and replaces only its glyphs (squares and dots), so the labels and both keys
     stay on screen. Square i belongs to owner i mod 17: ≈88 squares a dot, as in the static figure. */
  def('moltbook', function (s, el) {
    var art = $('.mb-art', el), svgs = $$('.mb-svg', el), cv = $('.mb-cv', el), ctx = cv.getContext && cv.getContext('2d');
    if (!ctx) return;
    var svg, G, scale = 1, dpr = Math.min(2, w.devicePixelRatio || 1), cols = {}, sq = [], owners = [];
    function colors() { cols = { a: css('--c1'), b: css('--em-l'), s: css('--stage-top') }; }
    function geo() {   // the layout follows the breakpoint, as in the CSS, not whichever SVG happens to be displayed
      svg = svgs[w.matchMedia && w.matchMedia('(max-width: 640px)').matches && svgs[1] ? 1 : 0];
      G = {};
      ['W', 'H', 'cols', 'cell', 'gx', 'gy', 'ox', 'oy', 'ocols', 'ostep', 'orad'].forEach(function (k) { G[k] = +svg.getAttribute('data-' + k.toLowerCase()); });
      sq = []; owners = [];
      for (var j = 0; j < 17; j++) owners.push({ x: G.ox + G.orad + (j % G.ocols) * G.ostep, y: G.oy + G.orad + Math.floor(j / G.ocols) * G.ostep });
      for (var i = 0; i < 1500; i++) {
        var a = Math.random() * 2 * Math.PI, r = Math.sqrt(Math.random()) * 7;
        sq.push({ ox: G.gx + (i % G.cols) * G.cell, oy: G.gy + Math.floor(i / G.cols) * G.cell, k: i % 17, jx: Math.cos(a) * r - 2.5, jy: Math.sin(a) * r - 2.5 });
      }
    }
    function size() {
      geo();
      var r = svg.getBoundingClientRect(), ar = art.getBoundingClientRect();
      scale = r.width / G.W;
      cv.width = Math.round(r.width * dpr); cv.height = Math.round(G.H * scale * dpr);
      cv.style.width = r.width + 'px'; cv.style.height = (G.H * scale) + 'px';
      cv.style.left = (r.left - ar.left) + 'px'; cv.style.top = (r.top - ar.top) + 'px';
      colors();
    }
    function frame(t) {
      ctx.setTransform(dpr * scale, 0, 0, dpr * scale, 0, 0);
      ctx.clearRect(0, 0, G.W, G.H);
      var fin = clamp((t - 0.1) / 1.0, 0, 1), dot = clamp((t - 1.6) / 0.6, 0, 1), fly = clamp((t - 1.8) / 2.2, 0, 1), back = clamp((t - 5.6) / 1.1, 0, 1);
      ctx.fillStyle = cols.a;
      for (var i = 0; i < sq.length; i++) {
        var p = sq[i], o = owners[p.k], lag = (i % G.cols) / (G.cols * 4);
        var e = E.io(clamp(fly * 1.25 - lag, 0, 1)) * (1 - E.io(clamp(back * 1.25 - lag, 0, 1)));
        ctx.globalAlpha = 0.75 * clamp(fin * 40 - Math.floor(i / G.cols), 0, 1);
        if (ctx.globalAlpha > 0.01) ctx.fillRect(p.ox + (o.x + p.jx - p.ox) * e, p.oy + (o.y + p.jy - p.oy) * e, 5, 5);
      }
      if (dot > 0) {   // owners on top of their piles
        ctx.globalAlpha = dot; ctx.fillStyle = cols.b; ctx.strokeStyle = cols.s; ctx.lineWidth = 2;
        owners.forEach(function (o) { ctx.beginPath(); ctx.arc(o.x, o.y, G.orad * (0.4 + 0.6 * E.out(dot)), 0, 2 * Math.PI); ctx.fill(); ctx.stroke(); });
      }
      ctx.globalAlpha = 1;
    }
    s.dur = 7.2;
    s.at(0.05, function () { s.beat(0); }).at(1.6, function () { s.beat(1); }).at(5.4, function () { s.beat(2); });
    s.onStart = function () { size(); };
    s.onTick = function (t) { if (!el.classList.contains('live')) { size(); el.classList.add('live'); } frame(t); };
    s.onReset = function () { s.beat(-1); };
    s.onEnd = function () { el.classList.remove('live'); };
    d.addEventListener('aas:theme', colors);
    w.addEventListener('resize', function () { if (el.classList.contains('live')) size(); });
  });

  $$('[data-scene]').forEach(function (el) { if (el.getAttribute('data-scene') !== 'agensh') boot(el); });
})();
