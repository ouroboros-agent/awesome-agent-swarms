/* A deterministic clock for capturing the Field page frame by frame.

   Installed before any page script (Playwright add_init_script). The page's own code is untouched: it keeps asking for
   animation frames, reading the time and starting CSS transitions; this file only decides when "now" is.

   - requestAnimationFrame callbacks wait in a queue and run in __vc.step(), with the virtual time as their timestamp;
   - performance.now() and Date.now() follow the same clock; setTimeout/setInterval fire on it;
   - CSS transitions and animations are held paused and moved to their virtual time through the Web Animations API,
     and finished at their end, so opacity/transform fades in the page advance exactly as far as the canvas does;
   - smooth scrolling of an element (the phone's tab strip) is re-timed on the same clock;
   - Math.random is a seeded generator: where the page throws dice (which pull requests merge in scene 3, which agent
     restarts in scene 4), two captures of one storyboard throw the same ones and give the same frames.

   One call is one video frame: __vc.frame({dt, y, run, n}) scrolls the window to y (if given), runs an optional action,
   advances the clock by dt milliseconds in n equal steps (default 1), running the queued animation frames and syncing
   the CSS animations at each step. */
(() => {
  'use strict';
  if (window.__vc) return;
  const W = window;
  let vt = 0;                              /* virtual time, ms */
  const epoch = Date.now();
  let rafId = 0; const rafQ = new Map();
  let tId = 0; const timers = new Map();
  const tweens = new Set();
  const seen = new WeakMap();
  const log = [];

  W.requestAnimationFrame = cb => { rafQ.set(++rafId, cb); return rafId; };
  W.cancelAnimationFrame = id => { rafQ.delete(id); };
  const vnow = () => vt;
  try { Object.defineProperty(Performance.prototype, 'now', { value: vnow, configurable: true, writable: true }); } catch (e) { try { performance.now = vnow; } catch (x) { /* read-only */ } }
  Date.now = () => epoch + vt;
  let seed = 0x9E3779B9;                   /* mulberry32: the same sequence in every capture */
  Math.random = () => { seed = (seed + 0x6D2B79F5) >>> 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  W.setTimeout = (fn, ms, ...a) => { timers.set(++tId, { at: vt + Math.max(0, +ms || 0), fn, a, every: 0 }); return tId; };
  W.setInterval = (fn, ms, ...a) => { const e = Math.max(1, +ms || 0); timers.set(++tId, { at: vt + e, fn, a, every: e }); return tId; };
  W.clearTimeout = W.clearInterval = id => { timers.delete(id); };

  /* smooth scrolling of an element, on the virtual clock (the page calls bar.scrollBy({left, behavior:'smooth'})) */
  const SMOOTH_MS = 340;
  const ease = u => u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
  const oBy = Element.prototype.scrollBy, oTo = Element.prototype.scrollTo;
  function smooth(el, x, y) {
    const mx = Math.max(0, el.scrollWidth - el.clientWidth), my = Math.max(0, el.scrollHeight - el.clientHeight);
    for (const t of tweens) if (t.el === el) tweens.delete(t);
    tweens.add({ el, x0: el.scrollLeft, y0: el.scrollTop, x1: Math.min(mx, Math.max(0, x)), y1: Math.min(my, Math.max(0, y)), t0: vt });
  }
  Element.prototype.scrollBy = function (o) {
    if (o && typeof o === 'object' && o.behavior === 'smooth') { smooth(this, this.scrollLeft + (+o.left || 0), this.scrollTop + (+o.top || 0)); return; }
    return oBy.apply(this, arguments);
  };
  Element.prototype.scrollTo = function (o) {
    if (o && typeof o === 'object' && o.behavior === 'smooth') { smooth(this, o.left === undefined ? this.scrollLeft : +o.left, o.top === undefined ? this.scrollTop : +o.top); return; }
    return oTo.apply(this, arguments);
  };

  function syncAnims() {
    let list; try { list = document.getAnimations(); } catch (e) { return 0; }
    for (const a of list) {
      let t0 = seen.get(a);
      if (t0 === undefined) { t0 = vt; seen.set(a, t0); try { a.pause(); } catch (e) { /* not pausable */ } }
      const local = vt - t0; let end = Infinity;
      try { end = a.effect.getComputedTiming().endTime; } catch (e) { /* no effect timing */ }
      try { if (local >= end) a.finish(); else a.currentTime = local; } catch (e) { /* removed meanwhile */ }
    }
    return list.length;
  }
  function fireTimers() {
    for (let guard = 0; guard < 2000; guard++) {
      let best = null, bid = 0;
      for (const [id, t] of timers) if (t.at <= vt && (!best || t.at < best.at)) { best = t; bid = id; }
      if (!best) return;
      if (best.every) best.at += best.every; else timers.delete(bid);
      try { best.fn.apply(W, best.a); } catch (e) { log.push('timer: ' + e); }
    }
  }
  function step(dt) {
    vt += dt;
    fireTimers();
    for (const t of tweens) {
      const u = Math.min(1, (vt - t.t0) / SMOOTH_MS), e = ease(u);
      t.el.scrollLeft = t.x0 + (t.x1 - t.x0) * e; t.el.scrollTop = t.y0 + (t.y1 - t.y0) * e;
      if (u >= 1) tweens.delete(t);
    }
    const cbs = [...rafQ.values()]; rafQ.clear();
    for (const cb of cbs) { try { cb(vt); } catch (e) { log.push('raf: ' + (e && e.stack || e)); } }
    return syncAnims();
  }
  W.__vc = {
    get t() { return vt; },
    log,
    step,
    sync: syncAnims,
    pending: () => rafQ.size,
    /* one video frame */
    frame(o) {
      o = o || {};
      if (typeof o.y === 'number') W.scrollTo(0, o.y);
      if (o.run) { try { (0, eval)(o.run); } catch (e) { log.push('run: ' + e); } }
      /* a time-lapse runs several of the page's own frames inside one video frame (o.n): the page never sees a step
         longer than it would in a browser (field.js caps one step at 50 ms), only the last of them is photographed */
      const k = Math.max(1, o.n | 0), d = (o.dt === undefined ? 1000 / 60 : o.dt) / k; let n = 0;
      for (let i = 0; i < k; i++) n = step(d);
      return { t: vt, y: W.scrollY, anims: n, raf: rafQ.size };
    },
    /* many steps without painting: settle the page or jump ahead */
    run(n, dt, y) { for (let i = 0; i < n; i++) { if (typeof y === 'number') W.scrollTo(0, y); step(dt === undefined ? 1000 / 60 : dt); } return vt; }
  };
})();
