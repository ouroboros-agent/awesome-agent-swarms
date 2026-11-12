(function(){
'use strict';
/* ============ Field: 1,024 agents on one canvas ============ */
const D = document, root = D.documentElement;
const RM = root.classList.contains('rm');
const DATA = JSON.parse(D.getElementById('data').textContent), L = DATA.L;
const cv = D.getElementById('field'), ctx = cv.getContext('2d');
const $ = id => D.getElementById(id);

const clamp = (v, a, b) => { a = a === undefined ? 0 : a; b = b === undefined ? 1 : b; return v < a ? a : v > b ? b : v; };
const lerp = (a, b, t) => a + (b - a) * t;
const ss = t => { t = clamp(t); return t * t * (3 - 2 * t); };
const eo = t => { t = clamp(t); return 1 - Math.pow(1 - t, 3); };
const eio = t => { t = clamp(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const frac = v => v - Math.floor(v);
function rnd(seed) { let s = seed >>> 0; return () => { s = (s + 0x6D2B79F5) >>> 0; let t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const hash = n => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const NB = ' ';
const fmt = n => String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, L.num.g);
const dec = (v, d) => v.toFixed(d === undefined ? 1 : d).replace('.', L.num.d);

let W = 0, H = 0, DPR = 1, mob = false, now = 0, dt = 0.016, stiff = 70, last = 0, raf = 0;
const S = { x: 0, y: 0, w: 0, h: 0, cx: 0, cy: 0 };
let g = 20, rd = 2;

const N = 1024;
const F = () => new Float32Array(N);
const px = F(), py = F(), vx = F(), vy = F(), tx = F(), ty = F(), rr = F(), tr = F(), aa = F(), ta = F();
const cR = F(), cG = F(), cB = F(), lit = F(), tl = F();
const nx = F(), ny = F(), nr = F(), na = F(), at = F(), kk = F(), hx = F(), hy = F(), fl = F();
const tc = new Uint8Array(N), nc = new Uint8Array(N), flc = new Uint8Array(N);
const COL = new Int16Array(N), ROW = new Int16Array(N);

const INK = [238, 242, 239], EM = [95, 227, 179], EMD = [34, 168, 118], WARM = [255, 180, 84], INK2 = [183, 191, 187], INK3 = [133, 142, 138], INK4 = [90, 99, 96];
/* map themes: one related family (emerald, teal, grey-blue, neutrals); the warm colour is kept for fresh works.
   The order was searched so that themes adjacent in a column differ the most. */
const THEMES = [
  [L.themes[0], [79, 197, 207]], [L.themes[1], [34, 116, 82]], [L.themes[2], [124, 159, 198]],
  [L.themes[3], [95, 227, 179]], [L.themes[4], [33, 144, 157]], [L.themes[5], [184, 205, 228]],
  [L.themes[6], [79, 107, 142]], [L.themes[7], [67, 182, 136]], [L.themes[8], [228, 233, 230]],
  [L.themes[9], [122, 131, 127]]
];
const PAL = [INK, EM, WARM, INK3].concat(THEMES.map(t => t[1]));
const C_INK = 0, C_EM = 1, C_WARM = 2, C_DIM = 3, C_TH = 4;
const rgba = (c, a) => 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + (a < 0 ? 0 : a > 1 ? 1 : a).toFixed(3) + ')';

(function init() {
  const r = rnd(11);
  for (let i = 0; i < N; i++) { COL[i] = i % 32; ROW[i] = i >> 5; kk[i] = 0.62 + r() * 0.76; cR[i] = INK[0]; cG[i] = INK[1]; cB[i] = INK[2]; }
})();
const ORD_COL = [...Array(N).keys()].sort((a, b) => COL[a] - COL[b] || ROW[a] - ROW[b]);
const ORD_CEN = [...Array(N).keys()].sort((a, b) => {
  const da = Math.hypot(COL[a] - 15.5, ROW[a] - 15.5), db = Math.hypot(COL[b] - 15.5, ROW[b] - 15.5);
  return da - db || Math.atan2(ROW[a] - 15.5, COL[a] - 15.5) - Math.atan2(ROW[b] - 15.5, COL[b] - 15.5);
});
const PERM = (() => { const a = [...Array(N).keys()], r = rnd(7); for (let i = N - 1; i > 0; i--) { const j = (r() * (i + 1)) | 0; const t = a[i]; a[i] = a[j]; a[j] = t; } return a; })();

function set(i, X, Y, R, A, C, d) {
  if (d > 0 && !RM) { nx[i] = X; ny[i] = Y; nr[i] = R; na[i] = A; nc[i] = C; at[i] = now + d; }
  else { tx[i] = X; ty[i] = Y; tr[i] = R; ta[i] = A; tc[i] = C; at[i] = 0; }
}
function sty(i, R, A, C) { tr[i] = R; ta[i] = A; tc[i] = C; if (at[i]) { nr[i] = R; na[i] = A; nc[i] = C; } }
function rest(i, A, d) { set(i, hx[i], hy[i], rd * 0.8, A === undefined ? 0.07 : A, C_INK, d || 0); tl[i] = 0; }

function physics() {
  const h = dt / 2;
  for (let i = 0; i < N; i++) {
    if (at[i] && now >= at[i]) { tx[i] = nx[i]; ty[i] = ny[i]; tr[i] = nr[i]; ta[i] = na[i]; tc[i] = nc[i]; at[i] = 0; }
    if (RM) { px[i] = tx[i]; py[i] = ty[i]; rr[i] = tr[i]; aa[i] = ta[i]; const c = PAL[tc[i]]; cR[i] = c[0]; cG[i] = c[1]; cB[i] = c[2]; lit[i] = tl[i]; continue; }
    const k = stiff * kk[i], c = 2 * Math.sqrt(k) * 0.84, X = tx[i], Y = ty[i];
    let x = px[i], y = py[i], u = vx[i], v = vy[i];
    u += (k * (X - x) - c * u) * h; v += (k * (Y - y) - c * v) * h; x += u * h; y += v * h;
    u += (k * (X - x) - c * u) * h; v += (k * (Y - y) - c * v) * h; x += u * h; y += v * h;
    px[i] = x; py[i] = y; vx[i] = u; vy[i] = v;
    rr[i] += (tr[i] - rr[i]) * Math.min(1, dt * 9);
    aa[i] += (ta[i] - aa[i]) * Math.min(1, dt * 7);
    const p = PAL[tc[i]], e = Math.min(1, dt * 8);
    cR[i] += (p[0] - cR[i]) * e; cG[i] += (p[1] - cG[i]) * e; cB[i] += (p[2] - cB[i]) * e;
    lit[i] += (tl[i] - lit[i]) * Math.min(1, dt * 7);
  }
}

/* ---------- text on the canvas ---------- */
const FONT = '-apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", "Segoe UI", Roboto, "Helvetica Neue", Arial, system-ui, sans-serif';
function T(s, x, y, o) {
  o = o || {};
  ctx.font = (o.w || 500) + ' ' + ((o.s || 13) * TS).toFixed(2) + 'px ' + FONT;
  ctx.textAlign = o.al || 'left'; ctx.textBaseline = o.bl || 'alphabetic';
  if (o.h) { halo(o); ctx.strokeText(s, x, y); }
  ctx.fillStyle = o.c || rgba(INK, o.a === undefined ? 1 : o.a);
  ctx.fillText(s, x, y);
}
/* a background-coloured halo: lines or dots behind a label do not merge with the letters */
function halo(o) { ctx.lineJoin = 'round'; ctx.lineWidth = o.h; ctx.strokeStyle = 'rgba(9,11,12,' + clamp(o.ha === undefined ? 1 : o.ha).toFixed(3) + ')'; }
let TS = 1;
function TW(s, o) { ctx.font = (o.w || 500) + ' ' + ((o.s || 13) * TS).toFixed(2) + 'px ' + FONT; return ctx.measureText(s).width; }
/* tabular figures: each digit in a cell as wide as '0' */
function TN(s, x, y, o) {
  o = o || {};
  ctx.font = (o.w || 600) + ' ' + ((o.s || 13) * TS).toFixed(2) + 'px ' + FONT;
  const w0 = ctx.measureText('0').width; let tot = 0; const ws = [];
  for (let i = 0; i < s.length; i++) { const ch = s[i]; const w = (ch >= '0' && ch <= '9') ? w0 : ctx.measureText(ch).width; ws.push(w); tot += w; }
  let cx = x - (o.al === 'right' ? tot : o.al === 'center' ? tot / 2 : 0);
  ctx.textAlign = 'center'; ctx.textBaseline = o.bl || 'alphabetic';
  if (o.h) { halo(o); let hx_ = cx; for (let i = 0; i < s.length; i++) { ctx.strokeText(s[i], hx_ + ws[i] / 2, y); hx_ += ws[i]; } }
  ctx.fillStyle = o.c || rgba(INK, o.a === undefined ? 1 : o.a);
  for (let i = 0; i < s.length; i++) { ctx.fillText(s[i], cx + ws[i] / 2, y); cx += ws[i]; }
  return tot;
}
function rrect(x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
function seg(x0, y0, x1, y1, c, w, dash) { ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.strokeStyle = c; ctx.lineWidth = w || 1; if (dash) ctx.setLineDash(dash); ctx.stroke(); if (dash) ctx.setLineDash([]); }
function dot(x, y, r, c) { ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fillStyle = c; ctx.fill(); }
function ring(x, y, r, c, w, dash) { ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.strokeStyle = c; ctx.lineWidth = w || 1; if (dash) ctx.setLineDash(dash); ctx.stroke(); if (dash) ctx.setLineDash([]); }
function glow(x, y, r, c, a) { const gr = ctx.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, rgba(c, a)); gr.addColorStop(1, rgba(c, 0)); ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fill(); }
/* a label on a dark plate, readable over dots */
function tag(s, x, y, o) {
  o = o || {}; const sz = o.s || 12, w = TW(s, { s: sz, w: o.w || 600 }), pad = o.pad === undefined ? 7 : o.pad, hh = sz * TS + 9;
  const xx = o.al === 'right' ? x - w - pad * 2 : o.al === 'center' ? x - w / 2 - pad : x;
  rrect(xx, y - hh / 2, w + pad * 2, hh, hh / 2); ctx.fillStyle = 'rgba(9,11,12,' + (0.86 * (o.a === undefined ? 1 : o.a)).toFixed(3) + ')'; ctx.fill();
  if (o.stroke) { ctx.strokeStyle = o.stroke; ctx.lineWidth = 1; ctx.stroke(); }
  T(s, xx + pad, y + 0.5, { s: sz, w: o.w || 600, bl: 'middle', c: o.c || rgba(INK, o.a === undefined ? 1 : o.a) });
  return w + pad * 2;
}

/* ---------- flying marks (claims, pull requests) ---------- */
const parts = [];
function emit(x0, y0, x1, y1, dur, c, bend, size, cb) { if (RM || parts.length > 420) return; parts.push({ x0, y0, x1, y1, t0: now, d: dur, c, b: bend || 0, s: size || 1.6, cb }); }
function drawParts() {
  for (let i = parts.length - 1; i >= 0; i--) {
    const p = parts[i], u = (now - p.t0) / p.d;
    if (u >= 1) { parts.splice(i, 1); if (p.cb) p.cb(p); continue; }
    const e = eio(u), q = 1 - e, mx = (p.x0 + p.x1) / 2 + (p.y1 - p.y0) * p.b, my = (p.y0 + p.y1) / 2 - (p.x1 - p.x0) * p.b;
    const x = q * q * p.x0 + 2 * q * e * mx + e * e * p.x1, y = q * q * p.y0 + 2 * q * e * my + e * e * p.y1;
    ctx.fillStyle = rgba(p.c, Math.min(1, Math.sin(Math.PI * clamp(u)) * 1.6));
    ctx.beginPath(); ctx.arc(x, y, p.s, 0, 6.2832); ctx.fill();
  }
}

/* ---------- agents ---------- */
const SIX = [15 * 32 + 15, 15 * 32 + 16, 15 * 32 + 17, 16 * 32 + 15, 16 * 32 + 16, 16 * 32 + 17];
const isSix = new Int8Array(N).fill(-1); SIX.forEach((i, k) => { isSix[i] = k; });
function drawBig(i, x, y, r, a) {
  const k = isSix[i], L = lit[i];
  if (L > 0.02) glow(x, y, r * 2.5, EM, 0.2 * L * a);
  ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832);
  if (k >= 0) { ctx.fillStyle = 'rgba(' + (lerp(19, 95, L) | 0) + ',' + (lerp(25, 227, L) | 0) + ',' + (lerp(26, 179, L) | 0) + ',' + a.toFixed(3) + ')'; }
  else { ctx.fillStyle = 'rgba(' + (lerp(16, 26, L) | 0) + ',' + (lerp(21, 84, L) | 0) + ',' + (lerp(22, 66, L) | 0) + ',' + a.toFixed(3) + ')'; }
  ctx.fill();
  ctx.lineWidth = 1.5;
  ctx.strokeStyle = k >= 0 ? rgba(L > 0.5 ? EM : INK, a * lerp(0.3, 0.95, L)) : rgba(L > 0.2 ? EM : INK, a * lerp(0.2, 0.6, L));
  ctx.stroke();
  if (k >= 0 && !(k === 4 && hero.sub >= 1)) { const la = clamp((r - 9) / 8) * a; if (la > 0.02) T(String(k + 1), x, y + r * 0.03, { s: r * 0.7, w: 600, al: 'center', bl: 'middle', c: L > 0.5 ? 'rgba(5,32,24,' + la.toFixed(3) + ')' : rgba(INK, la * 0.94) }); }
}
function drawAgents() {
  for (let i = 0; i < N; i++) {
    const a = aa[i]; if (a < 0.012) continue;
    const r = rr[i], x = px[i], y = py[i];
    if (x < -70 || x > W + 70 || y < -70 || y > H + 70) continue;
    if (r > 7 && vis[0] > 0.02) { drawBig(i, x, y, r, a); continue; }
    ctx.fillStyle = 'rgba(' + (cR[i] | 0) + ',' + (cG[i] | 0) + ',' + (cB[i] | 0) + ',' + a.toFixed(2) + ')';
    if (r < 1.3) ctx.fillRect(x - r, y - r, r * 2, r * 2);
    else { ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fill(); }
  }
}

/* ---------- scenes and scrolling ---------- */
const SC = [];
const vis = new Float32Array(8);
const NAMES = L.names;
const stepEls = [...D.querySelectorAll('.step')];
const steps = stepEls.map(el => ({ el, sc: +el.dataset.sc, st: +el.dataset.st, top: 0, ctop: 0, card: el.querySelector('.card'), long: el.classList.contains('long') }));
let curSc = 0, curSt = 0, key = -1, stepIdx = -2, docH = 1;
const whereEl = $('where'), progEl = $('prog'), langEl = $('lang'), langBase = langEl ? langEl.getAttribute('href') : '';
let place = '';

function measure() {
  const sy = scrollY;
  for (const s of steps) {
    const r = s.el.getBoundingClientRect(); s.top = r.top + sy;
    if (mob) s.ctop = s.top; else if (s.long) s.ctop = s.top + H * 0.15; else s.ctop = s.card.getBoundingClientRect().top + sy;
    if (s.sc === 1 && s.st === 0 && !mob) s.ctop -= H * 0.16;
  }
  docH = Math.max(1, root.scrollHeight - H);
}
function activeStep() {
  const sy = scrollY, trig = mob ? H - 96 : H * 0.8; let a = -1;
  for (let i = 0; i < steps.length; i++) { if (steps[i].ctop - sy < trig) a = i; else break; }
  return a;
}
function go(sc, st) {
  const fresh = sc !== curSc || key < 0;
  curSc = sc; curSt = st; key = sc * 100 + st;
  SC[sc].st = st; SC[sc].t0 = now;
  if (mob) setStage();
  SC[sc].enter(st, fresh);
  if (sc > 0) { whereEl.innerHTML = '<b>' + sc + ' / 7</b>' + NAMES[sc]; whereEl.classList.add('on'); } else whereEl.classList.remove('on');
}
function update() {
  const a = activeStep();
  if (a !== stepIdx || key < 0) {
    stepIdx = a;
    for (let i = 0; i < steps.length; i++) steps[i].el.classList.toggle('on', i === a);
    go(a < 0 ? 0 : steps[a].sc, a < 0 ? 0 : steps[a].st);
  }
  progEl.style.transform = 'scaleX(' + clamp(scrollY / docH).toFixed(4) + ')';
  if (langEl) { const pl = stepIdx >= 0 ? 's' + steps[stepIdx].sc + '-' + steps[stepIdx].st : scrollY > H * 0.6 ? 's0-1' : 's0'; if (pl !== place) { place = pl; langEl.href = langBase + '#' + pl; } }
}
const T_OF = sc => RM ? 999 : now - SC[sc].t0;

/* ---------- hovering the dots (scale and map) ---------- */
const mouse = { x: -9, y: -9, on: false, ui: false, touch: false, moved: -99 };
/* a tap is followed by compatibility mouse events; within a second of a touch they do not switch the page to pointer mode */
let touchT = -1e9, tStart = null;
let hov = -1, hovSet = null, hovPin = false;
const tipEl = $('tip'), tipT = tipEl.querySelector('.t'), tipM = tipEl.querySelector('.m'), tipTh = tipEl.querySelector('.th'), tipA = tipEl.querySelector('a');
function showTip(info, x, y, touch) {
  tipT.textContent = info.t; tipM.textContent = info.m;
  if (info.th) { tipTh.style.display = ''; tipTh.querySelector('span').textContent = info.th; tipTh.querySelector('i').style.background = info.c; } else tipTh.style.display = 'none';
  tipA.href = info.url; tipEl.classList.toggle('touch', !!touch); tipEl.classList.add('on');
  const w = tipEl.offsetWidth, hgt = tipEl.offsetHeight;
  let lx = x + 16, ly = y - hgt - 14;
  if (lx + w > W - 10) lx = x - w - 16; if (lx < 10) lx = 10; if (ly < 58) ly = y + 18; if (ly + hgt > H - 8) ly = H - hgt - 8;
  tipEl.style.left = lx + 'px'; tipEl.style.top = ly + 'px';
}
function hideTip() { tipEl.classList.remove('on'); }
function pick(x, y, rad) {
  if (!hovSet) return -1; let best = -1, bd = rad * rad; const ids = hovSet.ids;
  for (let j = 0; j < ids.length; j++) { const i = ids[j]; if (aa[i] < 0.15) continue; const dx = px[i] - x, dy = py[i] - y, d = dx * dx + dy * dy; if (d < bd) { bd = d; best = j; } }
  return best;
}
addEventListener('mousemove', e => { if (performance.now() - touchT < 1000) return; mouse.x = e.clientX; mouse.y = e.clientY; mouse.on = true; mouse.touch = false; mouse.moved = now; mouse.ui = !!(e.target.closest && e.target.closest('a,button,.legend,.tip')); if (RM) kick(); }, { passive: true });
D.addEventListener('mouseleave', () => { mouse.on = false; });
D.addEventListener('click', e => {
  if (e.target.closest && e.target.closest('a,button,.tip')) return;
  if (mouse.touch) { const j = pick(e.clientX, e.clientY, 22); hov = j; hovPin = j >= 0; if (j >= 0) showTip(hovSet.info(j), e.clientX, e.clientY, true); else hideTip(); return; }
  if (hov >= 0 && hovSet) { const u = hovSet.info(hov).url; if (u) window.open(u, '_blank', 'noopener'); }
});
addEventListener('touchstart', e => { mouse.touch = true; mouse.on = false; touchT = performance.now(); const t = e.touches[0]; tStart = t && e.touches.length === 1 ? { x: t.clientX, y: t.clientY, t: touchT } : null; }, { passive: true });
/* a short tap without movement pins the tooltip here: some browsers (WebKit, iOS) send no click to elements without their own handler */
addEventListener('touchend', e => {
  touchT = performance.now(); const t = e.changedTouches[0], s = tStart; tStart = null;
  if (!s || !t || Math.hypot(t.clientX - s.x, t.clientY - s.y) > 10 || touchT - s.t > 600) return;
  if (e.target.closest && e.target.closest('a,button,.tip,.legend')) return;
  const j = pick(t.clientX, t.clientY, 22); hov = j; hovPin = j >= 0; if (j >= 0) showTip(hovSet.info(j), t.clientX, t.clientY, true); else hideTip();
}, { passive: true });
function hoverFrame() {
  if (!hovSet) { if (hov >= 0 || tipEl.classList.contains('on')) { hov = -1; hovPin = false; hideTip(); root.style.cursor = ''; } return; }
  if (mouse.touch) return;
  const j = (mouse.on && !mouse.ui) ? pick(mouse.x, mouse.y, hovSet.rad || 12) : -1;
  if (j !== hov) { const was = hov; hov = j; root.style.cursor = j >= 0 ? 'pointer' : ''; if (j < 0 && (was >= 0 || !hovSet.auto)) hideTip(); }   /* left the dot: the tooltip fades */
  if (j >= 0) showTip(hovSet.info(j), mouse.x, mouse.y, false);
}

/* ============ Scene 0: six agents, four schemes, delivered vs read, camera pull-out ============ */
const HEX = [[-0.866, -0.5], [0, -1], [0.866, -0.5], [-0.866, 0.5], [0, 1], [0.866, 0.5]];
const INF = 99;
const MODES = [
  { dur: 7.6, lit: [3.0, INF, 0.7, INF, 4.2, INF], chip: [[2, 0.7, L.chip.found], [0, 3.0, L.chip.redo], [4, 4.2, L.chip.redo]] },
  { dur: 6.6, lit: [3.4, INF, 0.8, INF, 3.4, INF], chip: [[2, 0.8, L.chip.found], [0, 3.4, L.chip.got], [4, 3.4, L.chip.got]], tok: [[1.2, 2.1, 2, -1], [2.5, 3.4, -1, 0], [2.5, 3.4, -1, 4]] },
  { dur: 7.8, lit: [3.9, INF, 0.8, INF, 5.4, INF], chip: [[2, 0.8, L.chip.found], [2, 2.0, L.chip.pub], [0, 3.9, L.chip.search], [4, 5.4, L.chip.search]], tok: [[1.2, 2.0, 2, -1], [2.7, 3.25, 0, -1, 1], [3.3, 3.9, -1, 0], [4.2, 4.75, 4, -1, 1], [4.8, 5.4, -1, 4]] },
  { dur: 7.0, lit: [2.1, 1.45, 0.8, 2.75, 2.1, 1.45], chip: [[2, 0.8, L.chip.found], [0, 2.1, L.chip.nbr], [4, 2.1, L.chip.nbr]] }
];
const PATCH = []; for (let i = 0; i < N; i++) if (Math.abs(COL[i] - 16) <= 2 && ROW[i] >= 14 && ROW[i] <= 17) PATCH.push(i);
const inPatch = new Uint8Array(N); PATCH.forEach(i => { inPatch[i] = 1; });
const hopOf = i => Math.abs(COL[i] - 17) + Math.abs(ROW[i] - 15);

const hero = { m: 0, mt: 0, sub: 0, fade: [1, 0, 0, 0], ta: 0, pA: 0, pZ: 0, C: { x: 0, y: 0 }, R: 100, rA: 20, CA: { x: 0, y: 0 }, RA: 80, chipA: new Float32Array(6) };
const copyEl = $('hCopy'), capEl = $('hCap'), aEl = $('hA'), cueEl = $('cue');
const tabEls = [...D.querySelectorAll('.tab')], modeEls = [...D.querySelectorAll('.mode')];
function setMode(m) {
  hero.m = m; hero.mt = RM ? 6.4 : 0;
  tabEls.forEach((e, i) => { e.classList.toggle('on', i === m); e.setAttribute('aria-selected', i === m ? 'true' : 'false'); if (i !== m) e.querySelector('.pb').style.transform = 'scaleX(0)'; });
  modeEls.forEach((e, i) => e.classList.toggle('on', i === m));
}
tabEls.forEach((e, i) => e.addEventListener('click', () => { setMode(i); kick(); }));
$('hCap').querySelector('.tabs').addEventListener('keydown', e => { const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0; if (!d) return; e.preventDefault(); const m = (hero.m + d + 4) % 4; setMode(m); tabEls[m].focus(); kick(); });

function heroGeom() {
  const y0 = mob ? copyEl.offsetTop + copyEl.offsetHeight + 2 : 108, y1 = capEl.offsetTop - (mob ? 4 : 30);
  hero.C.x = S.cx; hero.C.y = (y0 + y1) / 2;
  hero.R = Math.min(S.w * 0.30, (y1 - y0) * (mob ? 0.40 : 0.36), S.w / 3.75); hero.rA = hero.R * 0.21;
  hero.CA.x = S.cx; hero.CA.y = S.y + S.h * (mob ? 0.30 : 0.32); hero.RA = Math.min(S.w * 0.25, S.h * (mob ? 0.235 : 0.245));
}
function mpos(m, k) { if (m === 0) return [(k - 2.5) * (mob ? 0.64 : 0.6) + (mob ? 0 : 0.12), -0.5]; if (m === 3) return [((k % 3) - 1) * 0.8, k < 3 ? -0.4 : 0.4]; return HEX[k]; }
const P6 = k => { const i = SIX[k]; return { x: px[i], y: py[i], r: rr[i] }; };
function bez(a, b, c, d, t) { const q = 1 - t; return q * q * q * a + 3 * q * q * t * b + 3 * q * t * t * c + t * t * t * d; }

/* the finding: a diamond with a trail */
function token(x, y, ux, uy, f, query) {
  const L = mob ? 16 : 26;
  const gr = ctx.createLinearGradient(x - ux * L, y - uy * L, x, y); gr.addColorStop(0, rgba(EM, 0)); gr.addColorStop(1, rgba(EM, 0.75 * f));
  ctx.strokeStyle = gr; ctx.lineWidth = query ? 1.25 : 2; if (query) ctx.setLineDash([3, 4]);
  ctx.beginPath(); ctx.moveTo(x - ux * L, y - uy * L); ctx.lineTo(x, y); ctx.stroke(); ctx.setLineDash([]);
  if (query) { ring(x, y, mob ? 3 : 4, rgba(EM, f), 1.5); return; }
  glow(x, y, mob ? 11 : 17, EM, 0.4 * f);
  const s = mob ? 3.6 : 5.2; ctx.save(); ctx.translate(x, y); ctx.rotate(0.7854); ctx.fillStyle = rgba([226, 255, 243], f); ctx.fillRect(-s, -s, s * 2, s * 2); ctx.restore();
}
function travel(A, B, u, f, query) {
  const dx = B.x - A.x, dy = B.y - A.y, d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d;
  const x0 = A.x + ux * (A.r + 7), y0 = A.y + uy * (A.r + 7), x1 = B.x - ux * (B.r + 7), y1 = B.y - uy * (B.r + 7), e = eio(u);
  token(lerp(x0, x1, e), lerp(y0, y1, e), ux, uy, f * Math.min(1, Math.sin(Math.PI * clamp(u)) * 3), query);
}
function link(A, B, c, w, dash) {
  const dx = B.x - A.x, dy = B.y - A.y, d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d;
  if (d < A.r + B.r + 12) return;
  seg(A.x + ux * (A.r + 6), A.y + uy * (A.r + 6), B.x - ux * (B.r + 6), B.y - uy * (B.r + 6), c, w, dash);
}
function chip(s, x, y, f, solid) {
  const sz = mob ? 10.5 : 12.5, w = TW(s, { s: sz, w: 600 }), pad = mob ? 7 : 9, hh = sz + (mob ? 8 : 10);
  rrect(x - w / 2 - pad, y - hh / 2, w + pad * 2, hh, hh / 2);
  ctx.fillStyle = solid ? rgba([12, 40, 31], f) : 'rgba(9,11,12,' + (0.9 * f).toFixed(3) + ')'; ctx.fill();
  ctx.strokeStyle = rgba(EM, (solid ? 0.75 : 0.4) * f); ctx.lineWidth = 1; ctx.stroke();
  T(s, x, y + 0.5, { s: sz, w: 600, al: 'center', bl: 'middle', c: rgba(EM, f) });
}

function heroLanes(f, mt) {
  const C = hero.C, R = hero.R, yb = C.y + 0.36 * R, vy_ = C.y + 0.84 * R;
  const vw = mob ? 98 : 132, vh = mob ? 24 : 32, found = { 0: 1, 2: 1, 4: 1 };
  for (let k = 0; k < 6; k++) {
    const p = P6(k), x = p.x, y0 = p.y + p.r + 9, xe = C.x + (k - 2.5) * (vw / 7.5);
    ctx.strokeStyle = rgba(INK, 0.17 * f); ctx.lineWidth = 1.25;
    ctx.beginPath(); ctx.moveTo(x, y0); ctx.lineTo(x, yb); ctx.bezierCurveTo(x, yb + (vy_ - yb) * 0.62, xe, vy_ - (vy_ - yb) * 0.6, xe, vy_ - vh / 2 - 3); ctx.stroke();
    const end = k === 2 ? 0.7 : MODES[0].lit[k] < INF ? MODES[0].lit[k] : 4.7;
    if (mt > 0.25 && mt < end + 0.25) {
      const fa = Math.min(1, (mt - 0.25) * 3) * clamp((end + 0.25 - mt) * 4) * f, an = mt * 3.4 + k * 1.7;
      ctx.strokeStyle = rgba(EM, 0.75 * fa); ctx.lineWidth = 2; ctx.lineCap = 'round'; ctx.beginPath(); ctx.arc(p.x, p.y, p.r + 7, an, an + 1.5); ctx.stroke(); ctx.lineCap = 'butt';
    }
    if (mt > 4.9 && mt < 6.05) {
      const u = (mt - 4.9) / 1.15; let ax, ay;
      if (u < 0.4) { ax = x; ay = lerp(y0, yb, u / 0.4); }
      else { const v = (u - 0.4) / 0.6; ax = bez(x, x, xe, xe, v); ay = bez(yb, yb + (vy_ - yb) * 0.62, vy_ - (vy_ - yb) * 0.6, vy_ - vh / 2 - 3, v); }
      if (found[k]) { glow(ax, ay, mob ? 8 : 12, EM, 0.4 * f); dot(ax, ay, mob ? 2.6 : 3.6, rgba(EM, f)); } else dot(ax, ay, mob ? 2.4 : 3.2, rgba(INK3, 0.9 * f));
    }
  }
  const vl = mt > 6.0 ? eo((mt - 6.0) / 0.4) : 0;
  rrect(C.x - vw / 2, vy_ - vh / 2, vw, vh, vh / 2); ctx.fillStyle = rgba([lerp(14, 12, vl), lerp(18, 40, vl), lerp(19, 31, vl)].map(Math.round), f); ctx.fill();
  ctx.strokeStyle = rgba(vl > 0.5 ? EM : INK, lerp(0.26, 0.8, vl) * f); ctx.lineWidth = 1.25; ctx.stroke();
  T(L.vote, C.x, vy_ + 0.5, { s: mob ? 10.5 : 13, w: 600, al: 'center', bl: 'middle', c: rgba(vl > 0.5 ? EM : INK2, f) });
}
function heroHub(m, f, mt) {
  const C = hero.C, R = hero.R, hr = R * (m === 1 ? 0.2 : 0.24), hub = { x: C.x, y: C.y, r: hr };
  for (let k = 0; k < 6; k++) link(hub, P6(k), rgba(INK, 0.18 * f), 1.25, m === 2 ? [4, 6] : null);
  const tok = MODES[m].tok;
  let hl = 0;
  if (m === 1) { hl = ss((mt - 2.0) / 0.3) * (1 - ss((mt - 3.5) / 0.5)); if (mt > 50) hl = 0; }
  if (hl > 0.02) glow(C.x, C.y, hr * 2.6, EM, 0.22 * hl * f);
  if (m === 1) {
    ctx.beginPath(); ctx.arc(C.x, C.y, hr, 0, 6.2832); ctx.fillStyle = rgba([14, 18, 19], f); ctx.fill();
    ctx.strokeStyle = rgba(hl > 0.5 ? EM : INK, lerp(0.42, 0.95, hl) * f); ctx.lineWidth = 1.5; ctx.stroke();
    ring(C.x, C.y, hr * 0.46, rgba(hl > 0.5 ? EM : INK, lerp(0.3, 0.8, hl) * f), 1.25); dot(C.x, C.y, hr * 0.14, rgba(hl > 0.5 ? EM : INK, lerp(0.6, 1, hl) * f));
    T(L.coord, C.x, C.y + hr + (mob ? 13 : 19), { s: mob ? 10.5 : 13, w: 600, al: 'center', c: rgba(INK2, f) });
  } else {
    const s = hr * 1.9, rec = mt >= 2.0 ? eo((mt - 2.0) / 0.4) : 0;
    rrect(C.x - s / 2, C.y - s / 2, s, s, s * 0.2); ctx.fillStyle = rgba([14, 18, 19], f); ctx.fill(); ctx.strokeStyle = rgba(INK, 0.4 * f); ctx.lineWidth = 1.5; ctx.stroke();
    const lw = s * 0.56, n = 4, gap = s * 0.17;
    for (let q = 0; q < n; q++) {
      const yy = C.y - gap * 1.5 + q * gap, isNew = q === 1;
      if (isNew) { if (rec > 0.02) { glow(C.x, yy, s * 0.5, EM, 0.2 * rec * f); seg(C.x - lw / 2, yy, C.x - lw / 2 + lw * rec, yy, rgba(EM, f), mob ? 2 : 3); } else seg(C.x - lw / 2, yy, C.x + lw / 2, yy, rgba(INK, 0.07 * f), mob ? 2 : 3); }
      else seg(C.x - lw / 2, yy, C.x - lw / 2 + lw * (q === 3 ? 0.62 : q === 0 ? 0.85 : 1), yy, rgba(INK, 0.22 * f), mob ? 2 : 3);
    }
    T(L.mem, C.x, C.y + s / 2 + (mob ? 13 : 19), { s: mob ? 10.5 : 13, w: 600, al: 'center', c: rgba(INK2, f) });
  }
  for (const k of [0, 4]) { if (mt < MODES[m].lit[k]) { const p = P6(k); ring(p.x, p.y, p.r + 7, rgba(INK, 0.4 * f), 1.25, [3, 5]); } }
  if (mt < 50) for (const tk of tok) { if (mt >= tk[0] && mt <= tk[1]) travel(tk[2] < 0 ? hub : P6(tk[2]), tk[3] < 0 ? hub : P6(tk[3]), (mt - tk[0]) / (tk[1] - tk[0]), f, tk[4]); }
}
function heroLocal(f, mt) {
  for (const i of PATCH) {
    const A = { x: px[i], y: py[i], r: rr[i] };
    for (const j of [i + 1, i + 32]) {
      if (j >= N || !inPatch[j] || (j === i + 1 && COL[j] !== COL[i] + 1)) continue;
      const B = { x: px[j], y: py[j], r: rr[j] }, both = isSix[i] >= 0 && isSix[j] >= 0, al = Math.min(aa[i], aa[j]);
      link(A, B, rgba(INK, (both ? 0.3 : 0.12) * f * al), 1.25);
      if (mt < 50) {
        const hi = hopOf(i), hj = hopOf(j); if (hi === hj) continue;
        const from = hi < hj ? A : B, to = hi < hj ? B : A, h = Math.min(hi, hj), t0 = 0.9 + 0.65 * h, t1 = 0.8 + 0.65 * (h + 1);
        if (mt >= t0 && mt <= t1) travel(from, to, (mt - t0) / (t1 - t0), f * al * (both ? 1 : 0.55));
      }
    }
  }
  for (const k of [0, 4]) { if (mt < MODES[3].lit[k]) { const p = P6(k); ring(p.x, p.y, p.r + 7, rgba(INK, 0.4 * f), 1.25, [3, 5]); } }
}

/* A: the message arrived, but it is not in the context */
const A_ROWS = [[L.aRows[0], 94, 99, 1], [L.aRows[1], 47, 67, 1], [L.aRows[2], 56, 68, 0], [L.aRows[3], 19, 36, 0]];
const A_IN = { 0: 0, 2: 1, 5: 2 }, A_SEND = [0, 1, 2, 3, 5];
function heroA(f) {
  const tA = RM ? 5.2 : (now - hero.ta) % 9, pc = P6(4), fadeLoop = RM ? 1 : (1 - ss((tA - 8.3) / 0.6)) * ss(tA / 0.4);
  for (const k of A_SEND) link(pc, P6(k), rgba(INK, 0.16 * f), 1.25);
  const cap = tA < 1.9 ? '' : tA < 3.4 ? L.aCap[0] : tA < 4.3 ? L.aCap[1] : L.aCap[2];
  T(mob ? L.aOrder[0] : L.aOrder[1], pc.x, pc.y + pc.r + (mob ? 15 : 24), { s: mob ? 10.5 : 13, w: 600, al: 'center', c: rgba(INK2, f) });
  if (cap) T(cap, pc.x, pc.y + pc.r + (mob ? 29 : 43), { s: mob ? 10.5 : 13, w: 500, al: 'center', c: rgba(tA >= 4.3 ? EM : INK3, f * fadeLoop) });
  /* ranges */
  const bx0 = S.x + (mob ? 2 : 36), bx1 = S.x + S.w - (mob ? 78 : 168), by0 = S.y + S.h * (mob ? 0.655 : 0.675), stp = mob ? 30 : 46, tE = RM ? 9 : now - hero.ta;
  T(L.aShare, bx0, by0 - (mob ? 24 : 38), { s: mob ? 9.5 : 11.5, c: rgba(INK4, f) });
  A_ROWS.forEach((r, q) => {
    const y = by0 + q * stp, gq = eo((tE - 0.35 - 0.22 * q) / 0.9), X = v => bx0 + (bx1 - bx0) * v / 100;
    T(r[0], bx0, y - (mob ? 7 : 10), { s: mob ? 10.5 : 13, c: rgba(INK2, f) });
    seg(bx0, y, bx1, y, rgba(INK, 0.13 * f), 1);
    const xa = X(r[1]), xb = lerp(xa, X(r[2]), gq), hh = mob ? 5 : 7, xs = lerp(bx0, xa, gq);
    rrect(xs, y - hh / 2, Math.max(hh, xb - xs), hh, hh / 2); ctx.fillStyle = rgba(r[3] ? EM : INK, (r[3] ? 0.95 : 0.7) * f * gq); ctx.fill();
    TN(r[1] + '–' + r[2] + '%', S.x + S.w - (mob ? 0 : 20), y + (mob ? 4 : 6), { s: mob ? 15 : 22, w: 600, al: 'right', c: rgba(r[3] ? EM : INK, f * gq) });
  });
  const yl = by0 + 3 * stp + (mob ? 13 : 19);
  [0, 50, 100].forEach(v => { const x = bx0 + (bx1 - bx0) * v / 100; seg(x, yl - (mob ? 11 : 15), x, yl - (mob ? 8 : 11), rgba(INK, 0.3 * f), 1); TN(v + '%', x, yl, { s: mob ? 9.5 : 11, w: 500, al: v === 0 ? 'left' : v === 100 ? 'right' : 'center', c: rgba(INK4, f) }); });
}
function heroAover(f) {
  const tA = RM ? 5.2 : (now - hero.ta) % 9, pc = P6(4), ord = tA > 4.3 ? eo((tA - 4.3) / 0.5) : 0, fadeLoop = RM ? 1 : (1 - ss((tA - 8.3) / 0.6)) * ss(tA / 0.4);
  ring(pc.x, pc.y, pc.r * 0.72, rgba(INK, 0.3 * f), 1, [2, 5]);
  if (ord > 0 && tA < 6) { const u = (tA - 4.3) / 1.2; ring(pc.x, pc.y, pc.r + 6 + u * pc.r * 1.1, rgba(EM, (1 - clamp(u)) * 0.6 * f), 1.5); }
  A_SEND.forEach((k, j) => {
    const ps = P6(k), dx = ps.x - pc.x, dy = ps.y - pc.y, d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d;
    const dep = 0.5 + 0.14 * j, arr = dep + 0.9, rimx = pc.x + ux * (pc.r + 10), rimy = pc.y + uy * (pc.r + 10), sz = mob ? 3 : 4.6, ff = f * fadeLoop;
    if (tA < dep) return;
    if (tA < arr) { travel(ps, { x: pc.x, y: pc.y, r: pc.r + 4 }, (tA - dep) / 0.9, ff); return; }
    let x = rimx, y = rimy, inside = 0;
    if (A_IN[k] !== undefined) { const ti = 2.5 + 0.28 * A_IN[k]; inside = eio((tA - ti) / 0.6); x = lerp(rimx, pc.x + ux * pc.r * 0.3, inside); y = lerp(rimy, pc.y - pc.r * 0.08 + uy * pc.r * 0.3, inside); }
    if (A_IN[k] !== undefined && inside > 0.5) glow(x, y, sz * 3.6, EM, 0.35 * ff);
    ctx.save(); ctx.translate(x, y); ctx.rotate(0.7854);
    if (A_IN[k] !== undefined) { ctx.fillStyle = rgba(inside > 0.5 ? [226, 255, 243] : EM, ff); ctx.fillRect(-sz, -sz, sz * 2, sz * 2); }
    else { ctx.fillStyle = 'rgba(9,11,12,' + ff.toFixed(3) + ')'; ctx.fillRect(-sz, -sz, sz * 2, sz * 2); ctx.strokeStyle = rgba(ord > 0.5 ? INK3 : EM, lerp(0.95, 0.8, ord) * ff); ctx.lineWidth = 1.5; ctx.strokeRect(-sz, -sz, sz * 2, sz * 2); }
    ctx.restore();
  });
  if (tA > 3.2) { const fl_ = f * fadeLoop * ss((tA - 3.2) / 0.4); T(L.inCtx, pc.x, pc.y + pc.r * 0.52, { s: mob ? 8.5 : 11, al: 'center', c: rgba(INK2, fl_) }); }
}

SC[0] = {
  st: 0, t0: 0,
  enter() { heroGeom(); hovSet = null; },
  tick() {
    const sy = scrollY / H, pA = ss((sy - 0.10) / 0.36), pZ = clamp((sy - 1.72) / 1.12);
    hero.pA = pA; hero.pZ = pZ;
    const sub = pZ > 0.001 ? 2 : pA > 0.5 ? 1 : 0;
    if (sub !== hero.sub) { if (sub === 1 && hero.sub === 0) hero.ta = now; hero.sub = sub; }
    const o1 = 1 - ss((sy - 0.03) / 0.26);
    copyEl.style.opacity = o1.toFixed(3); copyEl.style.transform = 'translateY(' + (-36 * (1 - o1)).toFixed(1) + 'px)';
    capEl.style.opacity = o1.toFixed(3); capEl.style.transform = 'translateY(' + (-18 * (1 - o1)).toFixed(1) + 'px)';
    capEl.style.pointerEvents = o1 < 0.5 ? 'none' : ''; cueEl.style.opacity = o1.toFixed(3);
    const oA = ss((sy - 0.34) / 0.2) * (1 - ss((sy - 1.5) / 0.2));
    aEl.style.opacity = oA.toFixed(3); aEl.classList.toggle('live', oA > 0.5);
    stiff = sub === 2 ? 190 : 72;
    if (sub === 0 && !RM) { hero.mt += dt; if (hero.mt > MODES[hero.m].dur) setMode((hero.m + 1) % 4); tabEls[hero.m].querySelector('.pb').style.transform = 'scaleX(' + clamp(hero.mt / MODES[hero.m].dur).toFixed(4) + ')'; }
    for (let m = 0; m < 4; m++) hero.fade[m] += ((sub === 0 && m === hero.m ? 1 : 0) - hero.fade[m]) * (RM ? 1 : Math.min(1, dt * 7));
    if (sub === 0) {
      const m = hero.m, C = hero.C, R = hero.R, rA = hero.rA, sp = 0.8 * R, mt = hero.mt, L = MODES[m].lit;
      for (let i = 0; i < N; i++) {
        const k = isSix[i]; at[i] = 0; tc[i] = C_INK;
        if (k >= 0) { const p = mpos(m, k); tx[i] = C.x + p[0] * R; ty[i] = C.y + p[1] * R; tr[i] = (m === 0 ? 0.9 : 1) * rA; ta[i] = 1; tl[i] = mt >= L[k] ? 1 : 0; }
        else { const dx = COL[i] - 16, dy = ROW[i] - 15.5; tx[i] = C.x + dx * sp; ty[i] = C.y + dy * sp; tr[i] = rA * 0.88; const ip = m === 3 && inPatch[i]; ta[i] = ip ? 1 : 0; tl[i] = ip && mt >= 0.8 + 0.65 * hopOf(i) ? 0.55 : 0; }
      }
    } else if (sub === 1) {
      const C = hero.CA, R = hero.RA, sp = 0.9 * R;
      for (let i = 0; i < N; i++) {
        const k = isSix[i]; at[i] = 0; tc[i] = C_INK; tl[i] = 0;
        if (k === 4) { tx[i] = C.x; ty[i] = C.y; tr[i] = R * 0.3; ta[i] = 1; }
        else if (k >= 0) { tx[i] = C.x + HEX[k][0] * R; ty[i] = C.y + HEX[k][1] * R; tr[i] = R * 0.17; ta[i] = 1; }
        else { tx[i] = C.x + (COL[i] - 16) * sp; ty[i] = C.y + (ROW[i] - 15.5) * sp; tr[i] = R * 0.17; ta[i] = 0; }
      }
    } else {
      const CA = hero.CA, RA = hero.RA, e = eio(pZ), K0 = RA * 0.9 / g, k = Math.exp(Math.log(K0) * (1 - e));
      const gB = mob ? Math.min((W - 36) / 31, (H - 170) / 31) : Math.min((H - 196) / 31, W * 0.8 / 31), gz = lerp(g, gB, e), rdB = mob ? 1.5 : 2.5;
      const cx = lerp(CA.x, W / 2, e), cy = lerp(CA.y, H / 2 + (mob ? 4 : 26), e), fx = lerp(16, 15.5, e), rAA = RA * 0.17;
      const gam = Math.log(rAA / rdB) / Math.log(K0), rz = rdB * Math.pow(k, gam), rho = 1.3 + 27 * Math.pow(e, 1.2), b = ss(pZ / 0.3);
      hero.gz = gz; hero.zc = [cx, cy];
      for (let i = 0; i < N; i++) {
        const s6 = isSix[i], X = cx + (COL[i] - fx) * gz * k, Y = cy + (ROW[i] - 15.5) * gz * k; at[i] = 0;
        if (s6 >= 0) {
          const ax = s6 === 4 ? CA.x : CA.x + HEX[s6][0] * RA, ay = s6 === 4 ? CA.y : CA.y + HEX[s6][1] * RA, ar = s6 === 4 ? RA * 0.3 : rAA;
          tx[i] = lerp(ax, X, b); ty[i] = lerp(ay, Y, b); tr[i] = Math.max(lerp(ar, rz, b), rdB * 1.5); ta[i] = 1; tc[i] = pZ > 0.25 ? C_EM : C_INK; tl[i] = pZ > 0.12 ? 1 : 0;
        } else {
          const d = Math.hypot(COL[i] - 16, ROW[i] - 15.5), q = rho - d, front = q > 0 && q < 2.6 && pZ < 0.985;
          tx[i] = X; ty[i] = Y; tr[i] = rz; ta[i] = clamp(q / 1.5) * (rz > 7 ? 1 : 0.62); tc[i] = front ? C_EM : C_INK; tl[i] = front ? 0.6 : 0;
        }
      }
    }
  },
  under(a) {
    const oh = (1 - ss(hero.pA / 0.5)) * a;
    for (let m = 0; m < 4; m++) {
      const f = hero.fade[m] * oh; if (f < 0.01) continue; const mt = m === hero.m ? hero.mt : 99;
      if (m === 0) heroLanes(f, mt); else if (m === 3) heroLocal(f, mt); else heroHub(m, f, mt);
    }
    const oA = ss((hero.pA - 0.5) / 0.5) * (1 - ss(hero.pZ / 0.22)) * a;
    if (oA > 0.01) heroA(oA);
  },
  overA(a) { const oA = ss((hero.pA - 0.5) / 0.5) * (1 - ss(hero.pZ / 0.22)) * a; if (oA > 0.01 && hero.sub >= 1) heroAover(oA); },
  over(a) {
    const oh = (1 - ss(hero.pA / 0.5)) * a;
    if (oh > 0.01 && hero.sub === 0) {
      const m = hero.m, mt = hero.mt, f = hero.fade[m] * oh, last = {};
      for (const c of MODES[m].chip) if (mt >= c[1]) last[c[0]] = c;
      for (const k in last) { const c = last[k], p = P6(+k), fa = Math.min(1, (mt - c[1]) * 4) * f; chip(c[2], p.x, p.y - p.r - (mob ? 14 : 19), fa, +k === 2); }
    }
    this.overA(a);
    const lz = ss((hero.pZ - 0.74) / 0.2) * a;
    if (lz > 0.01 && hero.sub === 2) {
      const x = px[0] - 2, y = py[0] - (mob ? 14 : 24);
      const w = TN(fmt(1024), x, y, { s: mob ? 17 : 26, w: 600, c: rgba(INK, lz) });
      T(L.zoomAgents, x + w + (mob ? 6 : 10), y, { s: mob ? 12 : 15, c: rgba(INK3, lz) });
      const bx = px[SIX[2]] + (mob ? 8 : 14), byy = (py[SIX[2]] + py[SIX[5]]) / 2;
      seg(bx, byy, bx + (mob ? 14 : 30), byy, rgba(EM, 0.6 * lz), 1);
      tag(L.zoomSix, bx + (mob ? 16 : 34), byy, { s: mob ? 10.5 : 12.5, c: rgba(EM, lz), a: lz });
    }
  }
};

/* ============ Scene 1: the scale axis ============ */
const SCALE = DATA.scale;
const s1 = { role: new Int16Array(N).fill(-1), who: new Int16Array(99), pts: [], x0: 0, x1: 0, ppd: 1, yb: 0, rw: 4, lv: SCALE.map(r => r[0] >= 10000 ? 4 : r[0] >= 1000 ? 3 : r[0] >= 100 ? 2 : r[0] >= 10 ? 1 : 0), id: {} };
SCALE.forEach((r, j) => { s1.id[r[4]] = j; });
(function () { const sub = PERM.slice(0, 99).sort((a, b) => COL[a] - COL[b] || ROW[a] - ROW[b]); sub.forEach((i, j) => { s1.who[j] = i; s1.role[i] = j; }); })();
const xS = v => s1.x0 + Math.log10(v) * s1.ppd;
function s1geom() {
  s1.x0 = S.x + (mob ? 8 : 22); s1.x1 = S.x + S.w - (mob ? 6 : 12); s1.ppd = (s1.x1 - s1.x0 - (mob ? 44 : 150)) / 4.6;
  s1.k = mob ? clamp(S.h / 370, 0.9, 1.45) : 1;
  s1.yb = mob ? S.y + Math.max(S.h * 0.5 + 18 * s1.k, 42 + 150 * s1.k) : S.y + S.h * 0.615; s1.rw = mob ? 2.5 * s1.k : 6.1; s1.xm = s1.x1 - (mob ? 8 : 14);
  const d = s1.rw * 2 + (mob ? 0.9 : 1.6), pts = [];
  for (let j = 0; j < 99; j++) {
    const x = xS(SCALE[j][0]); let yy = 0, moved = true, guard = 0;
    while (moved && guard++ < 400) { moved = false; for (const p of pts) { const dx = Math.abs(p.x - x); if (dx < d) { const need = Math.sqrt(d * d - dx * dx); if (Math.abs(p.o - yy) < need - 0.01) { yy = p.o + need; moved = true; } } } }
    pts.push({ x, o: yy, y: s1.yb - s1.rw - 1.5 - yy });
  }
  s1.pts = pts; let top = s1.yb; for (const p of pts) if (p.x < xS(9.5)) top = Math.min(top, p.y - s1.rw); s1.top = top;
}
function s1topAt(x) { let m = s1.yb; for (const p of s1.pts) if (Math.abs(p.x - x) < s1.rw * 2.4) m = Math.min(m, p.y - s1.rw); return m; }
/* label rows: the further right a landmark, the lower its row, so leader lines never cross text */
const LM = [
  { id: 'anthropic-institute-pace', lv: 0, st: 3 },
  { id: 'openai-navier-stokes', lv: 1, st: 3 },
  { id: 'agensh-1024', lv: 2, st: 5 },
  { v: 1000, lv: 3, st: 4 },
  { id: 'deepmind-cheating-whistleblowing', lv: 4, st: 5 },
  { id: 'anthropic-patterns', lv: 5, st: 5 },
  { v: 50, lv: 6, st: 5 }
].map((m, k) => Object.assign(m, { a: L.lm[k][0], b: L.lm[k][1], m: L.lm[k][2] }));
const s1info = j => ({ t: SCALE[j][1], m: (SCALE[j][2] ? SCALE[j][2] + ' · ' : '') + L.s1agents + fmt(SCALE[j][0]), url: SCALE[j][3] });
SC[1] = {
  st: 0, t0: 0,
  enter(st, fresh) {
    stiff = 62; s1geom();
    for (let i = 0; i < N; i++) { const j = s1.role[i]; if (j < 0) rest(i, 0.075, fresh ? hash(i) * 0.5 : 0); else { set(i, s1.pts[j].x, s1.pts[j].y, s1.rw, 0.9, C_INK, fresh ? 0.1 + j * 0.011 : 0); tl[i] = 0; } }
    hovSet = { ids: Array.from(s1.who), info: s1info, rad: mob ? 14 : 12 };
  },
  tick(t, st) {
    const rev = Math.min(4, 1 + Math.floor(t / 1.0)), fin = t > 4.5;
    for (let j = 0; j < 99; j++) {
      const i = s1.who[j], lv = s1.lv[j], id = SCALE[j][4]; let c = C_INK, a = 0.9, r = s1.rw;
      if (st === 2) { if (lv === 0) a = 0.4; else if (fin) { c = C_EM; a = 0.5 + 0.12 * lv; } else if (lv >= rev) { c = C_EM; a = 1; } else if (lv >= 1) { c = C_EM; a = 0.42; } }
      else if (st >= 3) {
        const isLive = id === 'openai-navier-stokes' || id === 'anthropic-institute-pace', isLm = id === 'agensh-1024' || id === 'deepmind-cheating-whistleblowing' || id === 'anthropic-patterns';
        if (isLive) { c = C_EM; a = 1; r = s1.rw * (st === 3 ? 1.3 : 1.1); } else if (isLm && st >= 5) { c = C_EM; a = 1; r = s1.rw * 1.1; } else a = lv ? 0.5 : 0.36;
      }
      if (hov === j && hovSet && curSc === 1) { r = s1.rw * 1.5; a = 1; }
      sty(i, r, a, c);
    }
  },
  under(a) {
    const st = this.st, t = T_OF(1), x0 = s1.x0, yb = s1.yb, xe = xS(30000) + (mob ? 7 : 14), xm = s1.xm;
    const hf = a * (!mob && st >= 5 && s1.yb - 400 < S.y + 46 ? (st > 5 ? 0 : 1 - ss(t / 0.5)) : 1);
    if (hf > 0.01) { T(L.s1h[0], x0, S.y + (mob ? 12 : 20), { s: mob ? 11 : 13, w: 600, c: rgba(INK2, hf) }); T(L.s1h[1], x0, S.y + (mob ? 27 : 39), { s: mob ? 10.5 : 12.5, c: rgba(INK4, hf) }); }
    seg(x0 - 4, yb, xe, yb, rgba(INK, 0.3 * a), 1);
    for (let d = 0; d <= 4; d++) { const x = x0 + d * s1.ppd; seg(x, yb, x, yb + 5, rgba(INK, 0.3 * a), 1); TN(fmt(Math.pow(10, d)), x, yb + (mob ? 17 : 21), { s: mob ? 10 : 12.5, w: 500, al: 'center', c: rgba(INK3, a) }); }
    /* median */
    {
      const f = a * (st === 0 ? ss((t - 0.9) / 0.5) : 0.9), x = xS(7), top = s1.top - (mob ? 8 : 16);
      seg(x, yb + 1, x, top + 4, rgba(EM, 0.6 * f), 1, [2, 4]);
      TN('7', x, top - (mob ? 3 : 6), { s: mob ? 30 : 68, w: 600, al: 'center', c: rgba(INK, f) });
      if (mob) T(L.median, x - 13, top - 6, { s: 11, w: 500, al: 'right', c: rgba(INK3, f) }); else T(L.median, x + 29, top - 10, { s: 14, w: 500, c: rgba(INK3, f) });
    }
    /* thresholds */
    if (st >= 2) {
      const TH = [[10, 42], [100, 15], [1000, 7], [10000, 4]].map((h, k) => h.concat(L.th[k])), dim = st === 2 ? 1 : 0.5;
      TH.forEach((h, k) => {
        const r = st > 2 ? 1 : eo((t - k * 1.0) / 0.7); if (r < 0.005) return;
        const xs = xS(h[0]), yk = yb + (mob ? 40 + k * 25 * s1.k : 60 + k * 43), f = a * dim;
        seg(xs, yb + (mob ? 22 : 27), xs, yk, rgba(INK, 0.16 * f * r), 1);
        seg(xs, yk, lerp(xs, xe, r), yk, rgba(EM, 0.75 * f), mob ? 1.5 : 2); dot(xs, yk, mob ? 2 : 2.8, rgba(EM, f));
        const wn = TN(String(Math.round(h[1] * r)), xs + (mob ? 7 : 11), yk - (mob ? 6 : 9), { s: mob ? 15 : 25, w: 600, c: rgba(INK, f * r) });
        T(mob ? h[3] : h[2] + ' · ' + h[3], xs + (mob ? 7 : 11) + wn + (mob ? 5 : 9), yk - (mob ? 6 : 9), { s: mob ? 10.5 : 13, c: rgba(INK3, f * r) });
      });
    }
    /* axis break and Moltbook: not a swarm size */
    if (st === 6) {
      const f = a * ss(t / 0.6), y = yb - (mob ? 9 : 14);
      seg(xe + (mob ? 5 : 9), yb, xm - (mob ? 9 : 16), yb, rgba(INK, 0.3 * f), 1, [2, 5]);
      for (const o of [0, mob ? 4 : 6]) seg(xe + (mob ? 2 : 3) + o - 3, yb + 5, xe + (mob ? 2 : 3) + o + 3, yb - 5, rgba(INK, 0.5 * f), 1);
      ring(xm, y, mob ? 6 : 10, rgba(INK, 0.8 * f), 1.25, [2.5, 3.5]);
      TN(L.molt[0], xm, yb + (mob ? 17 : 21), { s: mob ? 10 : 12.5, w: 500, al: 'center', c: rgba(INK3, f) });
      const ML = mob ? L.molt[1] : L.molt[2], lh = mob ? 12 : 17, yT = y - (mob ? 12 : 20) - (ML.length - 1) * lh;
      ML.forEach((l, q) => T(l, xm + (mob ? 7 : 11), yT + q * lh, { s: mob ? 10 : q ? 12.5 : 13.5, w: q ? 500 : 600, al: 'right', c: rgba(q ? INK3 : INK, f) }));
    }
  },
  over(a) {
    const st = this.st, t = T_OF(1); if (st < 3) return;
    for (const m of LM) {
      if (st < m.st) continue;
      const hot = st === m.st, f = a * (hot ? ss(t / 0.5) : 0.78);
      let x, y;
      if (m.id) { const i = s1.who[s1.id[m.id]]; x = px[i]; y = py[i] - rr[i] - 3; }
      else { x = xS(m.v) - (m.v === 1000 ? s1.rw * 0.2 : 0); y = s1topAt(x) - (mob ? 5 : 9); if (hot) glow(x, y, mob ? 9 : 16, EM, 0.4 * f); ring(x, y, mob ? 2.6 : 5, rgba(EM, f), 1.5); y -= (mob ? 4 : 7); }
      const yt = s1.yb - (mob ? (50 + m.lv * 14.5) * s1.k : 126 + m.lv * 43);
      seg(x, y - 2, x, yt, rgba(EM, 0.5 * f), 1);
      if (mob) { const right = x > S.x + S.w * 0.62; T(m.m, x + (right ? -4 : 4), yt + 4, { s: 10.5, w: 600, al: right ? 'right' : 'left', c: rgba(hot ? EM : INK, f) }); }
      else { T(m.a, x + 8, yt + 4, { s: 13.5, w: 600, c: rgba(hot && !m.id ? EM : INK, f) }); T(m.b, x + 8, yt + 20, { s: 12.5, c: rgba(INK3, f) }); }
    }
  }
};

/* ============ Scene 2: the Agensh curve, a hundred agents three ways, N^λ and Avalon-M1 ============ */
const TEAM = [1, 8, 32, 128, 1024], SCORE = [33.89, 41.75, 43.11, 50.94, 55.06], TEAM_L = L.teamL;
const AV = [['FrontierScience', 55.9, 63.5, 55.5, L.avNote[0]], ['SWE-Bench Pro', 21.6, 23.5, 37.3, L.avNote[1]], ['IMO-ProofBench', 29.8, 37.5, 37.7, L.avNote[2]]];
const s2 = { stage: -1, cp: 0, G: {} };
function s2geom() {
  const G = s2.G;
  G.cx0 = S.x + (mob ? 30 : 62); G.cx1 = S.x + S.w - (mob ? 64 : 132); G.cy0 = S.y + (mob ? 74 : 132); G.cy1 = S.y + S.h - (mob ? 40 : 66);
  G.c = mob ? 1.8 : 3.55; G.rdot = mob ? 1.05 : 2;
  G.X = n => G.cx0 + Math.log2(n) / 10 * (G.cx1 - G.cx0); G.Y = v => G.cy1 - (v - 30) / 28 * (G.cy1 - G.cy0); G.Yd = d => G.cy1 - d / 10 * (G.cy1 - G.cy0);
  /* the N^λ fan: a margin on the right is kept for the line labels */
  G.fx1 = S.x + S.w - (mob ? 104 : 148); G.Xf = n => G.cx0 + Math.log2(n) / 10 * (G.fx1 - G.cx0);
  G.pt = TEAM.map((n, j) => [G.X(n), G.Y(SCORE[j])]);
  const P = G.pt, cur = [];
  for (let k = 0; k < 4; k++) {
    const p0 = P[Math.max(0, k - 1)], p1 = P[k], p2 = P[k + 1], p3 = P[Math.min(4, k + 2)];
    for (let q = 0; q < 40; q++) { const u = q / 40, u2 = u * u, u3 = u2 * u; cur.push([0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * u + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3), 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * u + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3)]); }
  }
  cur.push(P[4]); G.curve = cur;
  /* Avalon-M1 bars */
  G.p = mob ? Math.min(5.1, (S.w - 46) / 66) : Math.min(10.8, S.w * 0.84 / 66); G.bl = S.x + (mob ? 4 : 30);
  G.gt = mob ? 24 : 42; G.gi = mob ? 6 : 12; G.go = mob ? 18 : 46; G.gh = 8 * G.p + G.gi + G.gt + G.go;
  G.gy0 = S.y + (S.h - 3 * G.gh + G.go) / 2 + (mob ? 22 : 30);
  /* three ways to spend a hundred agents: three rows */
  const top = mob ? 42 : 66; G.rh = Math.min((S.h - top) / 3, mob ? 132 : 222); G.fs = G.rh * (mob ? 0.84 : 0.88); G.hp = G.fs / 10;
  G.hy0 = S.y + top + (S.h - top - 3 * G.rh) / 2; G.hx = S.x + (mob ? 4 : 18) + G.fs / 2;
}
function s2team(j) {
  const G = s2.G, n = TEAM[j], P = G.pt[j];
  for (let q = 0; q < N; q++) {
    const i = ORD_CEN[q];
    if (q < n) { const rad = n === 1 ? 0 : G.c * Math.sqrt(q + 0.5), an = q * 2.39996; set(i, P[0] + rad * Math.cos(an), P[1] + rad * Math.sin(an), n === 1 ? G.rdot * 2 : G.rdot, 0.95, C_EM, 0); tl[i] = 0; }
    else rest(i, 0.08, 0);
  }
}
function s2hundred() {
  const G = s2.G, p = G.hp, rdt = Math.max(mob ? 1.5 : 2.4, p * 0.2);
  for (let q = 0; q < N; q++) {
    const i = ORD_CEN[q];
    if (q >= 300) { rest(i, 0.05, 0); continue; }
    const grp = q < 100 ? 1 : q < 200 ? 0 : 2, k = q % 100, cx = G.hx, cy = G.hy0 + (grp + 0.5) * G.rh; let x, y;
    if (grp === 0) { x = cx + ((k % 10) - 4.5) * p; y = cy + (Math.floor(k / 10) - 4.5) * p; }
    else if (grp === 1) { const t = Math.floor(k / 10), m = k % 10, row = t < 3 ? 0 : t < 7 ? 1 : 2, col = t < 3 ? t - 1 : t < 7 ? t - 4.5 : t - 8, rad = m === 0 ? 0 : p * 0.86, an = m * 0.698; x = cx + col * p * 2.9 + rad * Math.cos(an); y = cy + (row - 1) * p * 3.1 + rad * Math.sin(an); }
    else { const rad = p * 0.5 * Math.sqrt(k + 0.5), an = k * 2.39996; x = cx + rad * Math.cos(an); y = cy + rad * Math.sin(an); }
    set(i, x, y, rdt, grp === 1 ? 0.98 : 0.8, grp === 1 ? C_EM : C_INK, hash(q) * 0.2); tl[i] = 0;
  }
}
function s2wedge() {
  const G = s2.G;
  for (let q = 0; q < N; q++) { const i = ORD_COL[q], xd = 10 * Math.sqrt((q + 0.5) / N), lam = 0.48 + 0.2 * frac(q * 0.61803398875 + 0.13); set(i, G.cx0 + xd / 10 * (G.fx1 - G.cx0), G.Yd(lam * xd), G.rdot * 0.92, 0.5, C_EM, hash(q) * 0.2); tl[i] = 0; }
}
function s2bars() {
  const G = s2.G; let q0 = 0;
  for (let k = 0; k < 3; k++) for (let s = 0; s < 2; s++) {
    const n = Math.round(AV[k][2 + s] * 4), top = G.gy0 + k * G.gh + G.gt + s * (4 * G.p + G.gi);
    const chunk = []; for (let q = q0; q < q0 + n; q++) chunk.push(q); chunk.sort((a, b) => COL[a] - COL[b] || ROW[a] - ROW[b]);
    chunk.forEach((i, q) => { set(i, G.bl + (q >> 2) * G.p + G.p * 0.5, top + (q & 3) * G.p + G.p * 0.5, G.p * 0.36, s === 0 ? 0.95 : 0.78, s === 0 ? C_EM : C_INK, hash(i) * 0.25); tl[i] = 0; });
    q0 += n;
  }
  for (let i = q0; i < N; i++) rest(i, 0, 0);
}
function tally(x, y, n, k, f) {
  const sz = mob ? 7 : 11, gap = mob ? 3 : 5; let xx = x;
  for (let q = 0; q < n; q++) { rrect(xx, y, sz, sz, 2.5); if (q < k) { ctx.fillStyle = rgba(EM, f); ctx.fill(); } else { ctx.strokeStyle = rgba(INK, 0.5 * f); ctx.lineWidth = 1; ctx.stroke(); } xx += sz + gap; }
}
SC[2] = {
  st: 0, t0: 0,
  enter(st, fresh) {
    stiff = 66; s2geom(); hovSet = null; s2.stage = -1;
    if (st <= 2) { if (fresh) s2.cp = 0; } else if (st === 3) s2hundred(); else if (st === 4) s2wedge(); else s2bars();
  },
  tick(t, st) {
    if (st <= 2) {
      /* the curve is drawn under the title already: the figure is ready when the paragraph is read */
      const stage = st === 0 ? clamp(Math.floor((t - 0.35) / 0.62) + 1, 0, 4) : 4;
      if (stage !== s2.stage) { s2.stage = stage; s2.ts = now; s2team(stage); }
      s2.cp += (stage - s2.cp) * (RM ? 1 : Math.min(1, dt * 4.5));
    }
  },
  axes(a, mode) {
    const G = s2.G, x1 = mode ? G.fx1 : G.cx1, X = mode ? G.Xf : G.X;
    seg(G.cx0, G.cy1, x1, G.cy1, rgba(INK, 0.28 * a), 1); seg(G.cx0, G.cy1, G.cx0, G.cy0 - (mob ? 14 : 30), rgba(INK, 0.16 * a), 1);
    TEAM.forEach(n => { const x = X(n); seg(x, G.cy1, x, G.cy1 + 5, rgba(INK, 0.3 * a), 1); TN(fmt(n), x, G.cy1 + (mob ? 17 : 22), { s: mob ? 10 : 12, w: 500, al: 'center', c: rgba(INK3, a) }); });
    T(mode === 0 ? L.ax[0] : L.ax[1], x1 + (mob ? 14 : 22), G.cy1 + (mob ? 31 : 42), { s: mob ? 10 : 12, al: 'right', c: rgba(INK4, a) });
  },
  head(a, l1, l2, em) {
    const x = S.x + (mob ? 4 : 18);
    T(l1, x, S.y + (mob ? 12 : 20), { s: mob ? 11 : 13, w: 600, c: rgba(INK2, a) });
    if (l2) T(l2, x, S.y + (mob ? 27 : 40), { s: mob ? 10.5 : 12.5, c: rgba(em ? EM : INK4, a) });
  },
  under(a) {
    const st = this.st, G = s2.G;
    if (st <= 2) {
      this.axes(a, 0);
      this.head(a, L.s2a[0], st === 2 ? L.s2a[1] : L.s2a[2], st === 2);
      for (const v of [35, 40, 45, 50, 55]) { const y = G.Y(v); seg(G.cx0, y, G.cx1 + (mob ? 50 : 100), y, rgba(INK, 0.05 * a), 1); TN(String(v), G.cx0 - (mob ? 6 : 10), y + 4, { s: mob ? 10 : 12, w: 500, al: 'right', c: rgba(INK3, a) }); }
      const n = Math.floor(clamp(s2.cp / 4) * (G.curve.length - 1));
      if (n > 0) { ctx.beginPath(); ctx.moveTo(G.curve[0][0], G.curve[0][1]); for (let q = 1; q <= n; q++) ctx.lineTo(G.curve[q][0], G.curve[q][1]); ctx.strokeStyle = rgba(EM, 0.75 * a); ctx.lineWidth = mob ? 1.5 : 2.25; ctx.lineJoin = 'round'; ctx.stroke(); }
    } else if (st === 3) {
      this.head(a, L.s2b[0], L.s2b[1]);
    } else if (st === 4) {
      this.axes(a, 1);
      this.head(a, L.s2c[0], L.s2c[1]);
      for (const d of [0, 2, 4, 6, 8, 10]) { const y = G.Yd(d); seg(G.cx0, y, G.fx1, y, rgba(INK, 0.05 * a), 1); TN('×' + fmt(Math.pow(2, d)), G.cx0 - (mob ? 5 : 10), y + 4, { s: mob ? 9.5 : 12, w: 500, al: 'right', c: rgba(INK3, a) }); }
      seg(G.cx0, G.cy1, G.fx1, G.cy0, rgba(INK, 0.2 * a), 1, [3, 6]);
      T('×N', G.fx1 + 8, G.cy0 + 4, { s: mob ? 10 : 12.5, c: rgba(INK3, a) });
    } else {
      const lg = [[L.avLg[0], EM, 0], [L.avLg[1], INK, 0], [L.avLg[2], INK3, 1]];
      let lx = G.bl, ly = S.y + (mob ? 12 : 20);
      const col = mob || lg.reduce((w, l) => w + TW(l[0], { s: 12.5 }) + 34, 0) > S.x + S.w - G.bl;
      lg.forEach(l => {
        if (l[2]) seg(lx + 3, ly - 10, lx + 3, ly + 3, rgba(INK, 0.8 * a), 1.5); else dot(lx + 3, ly - 4, mob ? 3 : 4, rgba(l[1], a));
        T(l[0], lx + 12, ly, { s: mob ? 10.5 : 12.5, c: rgba(INK2, a) });
        if (col) ly += mob ? 15 : 18; else lx += TW(l[0], { s: 12.5 }) + 34;
      });
      AV.forEach((r, k) => {
        const yT = G.gy0 + k * G.gh, top = yT + G.gt;
        T(r[0], G.bl, yT + (mob ? 14 : 22), { s: mob ? 12.5 : 17, w: 600, c: rgba(INK, a) });
        T(r[4], G.bl + TW(r[0], { s: mob ? 12.5 : 17, w: 600 }) + (mob ? 8 : 14), yT + (mob ? 14 : 22), { s: mob ? 10.5 : 13.5, c: rgba(k === 0 ? EM : INK3, a) });
        const xs = G.bl + r[1] * G.p;
        seg(xs, top - 3, xs, top + 8 * G.p + G.gi + 3, rgba(INK, 0.6 * a), 1.5);
        TN(dec(r[1]), xs, top + 8 * G.p + G.gi + (mob ? 13 : 18), { s: mob ? 9.5 : 12, w: 500, al: 'center', c: rgba(INK3, a) });
      });
    }
  },
  over(a) {
    const st = this.st, G = s2.G, t = T_OF(2);
    if (st <= 2) {
      const stage = s2.stage < 0 ? 0 : s2.stage;
      for (let j = 0; j <= stage; j++) {
        const P = G.pt[j], rad = TEAM[j] === 1 ? G.rdot * 2 : G.c * Math.sqrt(TEAM[j]), f = a * (j === stage && !RM ? ss((now - (s2.ts || 0) - 0.2) / 0.4) : 1);
        if (j < stage) { ring(P[0], P[1], rad + 2.5, rgba(EM, 0.55 * a), 1.25); if (j > 0) dot(P[0], P[1], mob ? 1.6 : 2.4, rgba(EM, 0.9 * a)); }
        const big = mob ? 13.5 : 21, sm = mob ? 10 : 12.5, hw = mob ? 3.5 : 4.5;
        const num = (s, x, y, al, sz) => TN(s, x, y, { s: sz || big, w: 600, al, c: rgba(INK, f), h: hw, ha: f });
        const sub = (s, x, y, al) => T(s, x, y, { s: sm, al, c: rgba(INK3, f), h: hw, ha: f });
        if (j === 0) { num(dec(SCORE[j], 2), P[0] + (mob ? 7 : 12), P[1] + (mob ? 16 : 28), 'left'); sub(TEAM_L[j], P[0] + (mob ? 7 : 12), P[1] + (mob ? 28 : 46), 'left'); }
        else if (j === 4) { const x = P[0] - rad * 0.9 - (mob ? 8 : 18), y = P[1] - rad * 0.6; num(dec(SCORE[j], 2), x, y, 'right', mob ? 18 : 36); sub(TEAM_L[j], x, y + (mob ? 12 : 20), 'right'); }
        else if (j === 3 || (mob && j === 2)) { /* right of and below the point: free space under the curve */ const x = P[0] + (mob ? (j === 2 ? 9 : 5) : 10), y = P[1] + rad + (mob ? (j === 2 ? 21 : 17) : 32); num(dec(SCORE[j], 2), x, y, 'left'); sub(TEAM_L[j], x, y + (mob ? 12 : 18), 'left'); }
        else { /* left of and above the point: over the curve coming into it */ const x = P[0] - 4, y = P[1] - rad - (mob ? 25 : 32); num(dec(SCORE[j], 2), x, y, 'right'); sub(TEAM_L[j], x, y + (mob ? 12 : 18), 'right'); }
      }
    } else if (st === 3) {
      const f = a * ss((t - 0.4) / 0.5), x = G.hx + G.fs / 2 + (mob ? 16 : 46);
      const R3 = [[L.r3[0][0], 12, 10, L.r3[0][mob ? 1 : 2], INK], [L.r3[1][0], 0, 0, L.r3[1][mob ? 1 : 2], EM], [L.r3[2][0], 4, 4, L.r3[2][mob ? 1 : 2], INK]];
      R3.forEach((r, q) => {
        const cy = G.hy0 + (q + 0.5) * G.rh;
        T(r[0], x, cy - (mob ? 12 : 22), { s: mob ? 14 : 24, w: 600, c: rgba(r[4], f) });
        if (r[1]) { tally(x, cy - (mob ? 3 : 4), r[1], r[2], f); T(r[3], x, cy + (mob ? 22 : 36), { s: mob ? 10 : 13.5, c: rgba(INK3, f) }); }
        else T(r[3], x, cy + (mob ? 6 : 8), { s: mob ? 10 : 13.5, c: rgba(EM, f * 0.9) });
      });
    } else if (st === 4) {
      const f = a * ss((t - 0.4) / 0.5), LAM = [[0.68, 'BrowseComp'], [0.57, 'SEC-Bench Pro'], [0.48, 'Terminal-Bench 2.1']], hw = mob ? 3.5 : 4.5;
      for (const l of LAM) seg(G.cx0, G.cy1, G.fx1, G.Yd(l[0] * 10), rgba(l[0] === 0.57 ? INK : EM, (l[0] === 0.57 ? 0.9 : 0.55) * f), l[0] === 0.57 ? 1.75 : 1.25);
      /* labels in the margin right of the fan: each at the end of its line and at least one step from its neighbour */
      const ye = LAM.map(l => G.Yd(l[0] * 10)), gap = mob ? 27 : 38, yl = [Math.min(ye[0], ye[1] - gap), ye[1], Math.max(ye[2], ye[1] + gap)], lx0 = G.fx1 + (mob ? 8 : 14);
      LAM.forEach((l, q) => {
        if (Math.abs(yl[q] - ye[q]) > 1.5) seg(G.fx1 + 2, ye[q], lx0 - 3, yl[q], rgba(INK, 0.3 * f), 1);
        TN('λ = ' + dec(l[0], 2), lx0, yl[q] - (mob ? 1 : 2), { s: mob ? 11 : 15, w: 600, c: rgba(INK, f) });
        T(l[1], lx0, yl[q] + (mob ? 11 : 15), { s: mob ? 9.5 : 12, c: rgba(INK3, f) });
      });
      /* 16 agents: label right of and below the point, under the fan, clear of lines and dashes */
      const x = G.Xf(16), y = G.Yd(0.57 * 4), cap = mob ? 11 : 21, l2 = mob ? 13 : 22, l3 = mob ? 25 : 40, hi = G.cy1 - l3 - (mob ? 11 : 12);
      const yAt = xx => G.Yd(4.8 * (xx - G.cx0) / (G.fx1 - G.cx0)), wN = TW(L.s2d[0], { s: mob ? 14 : 26, w: 600 });
      let lx = x + (mob ? 13 : 24);
      while (yAt(lx) + 7 + cap > hi && lx + wN + 6 < S.x + S.w) lx += 6;
      const by = Math.min(hi, yAt(lx) + 7 + cap + (mob ? 5 : 9));
      seg(x, G.cy1, x, y, rgba(INK, 0.5 * f), 1, [2, 4]); seg(G.cx0, y, x, y, rgba(INK, 0.5 * f), 1, [2, 4]);
      dot(x, y, mob ? 3 : 4.5, 'rgba(9,11,12,' + f.toFixed(3) + ')'); ring(x, y, mob ? 3 : 4.5, rgba(INK, f), 1.75);
      TN(L.s2d[0], lx, by, { s: mob ? 14 : 26, w: 600, c: rgba(INK, f), h: hw, ha: f });
      T(L.s2d[1], lx, by + l2, { s: mob ? 9.5 : 13, c: rgba(INK3, f), h: hw, ha: f });
      T(L.s2d[2], lx, by + l3, { s: mob ? 9.5 : 13, c: rgba(INK3, f), h: hw, ha: f });
    } else {
      const f = a * ss((t - 0.5) / 0.5);
      AV.forEach((r, k) => {
        const top = G.gy0 + k * G.gh + G.gt;
        for (let s = 0; s < 2; s++) { const v = r[2 + s], y = top + s * (4 * G.p + G.gi) + 2 * G.p; TN(dec(v), G.bl + Math.ceil(v) * G.p + (mob ? 6 : 12), y + (mob ? 5 : 9), { s: mob ? 14 : 24, w: 600, c: rgba(s === 0 ? EM : INK, f) }); }
      });
    }
  }
};

/* ============ Scene 3: self-organization ============ */
const s3 = { G: {}, fill: 0, dA: 0, stage: -1, phase: -1, sp: 0, sq: 0, rnd: rnd(31) };
const INTEG = [2, 6, 11, 15, 20, 25, 29].map(r => r * 32 + 31);
const isInt = new Int8Array(N).fill(-1); INTEG.forEach((i, j) => { isInt[i] = j; });
const in8 = i => ROW[i] >= 15 && ROW[i] <= 16 && COL[i] >= 14 && COL[i] <= 17;
const in128 = i => ROW[i] >= 12 && ROW[i] <= 19 && COL[i] >= 8 && COL[i] <= 23;
const B8 = []; for (let i = 0; i < N; i++) if (in8(i)) B8.push(i);
const REV = []; for (let i = 0; i < N; i++) if (in128(i) && hash(i + 3) < 0.1) REV.push(i);
const TREE_N = [18, 36, 54, 73, 91, 109, 127, 145, 163, 183];
const TREE_LEAD = 15;
const s3help = []; for (let i = 0; i < N && s3help.length < 999; i++) if (i !== TREE_LEAD) s3help.push(i);
const s3go = new Uint8Array(N); (function () { const r = rnd(5), a = s3help.slice(); for (let i = a.length - 1; i > 0; i--) { const j = (r() * (i + 1)) | 0; const t = a[i]; a[i] = a[j]; a[j] = t; } for (let q = 0; q < 750; q++) s3go[a[q]] = 1; })();
const NF = 0.014 + 0.86 * 0.427;

function s3geom() {
  const G = s3.G;
  /* board on top, the 32×32 lattice on the left, integrators and main on the right */
  G.tw = mob ? 3.2 : 5.6; G.th = mob ? 2.2 : 3.4; G.tpx = mob ? 4.6 : 8; G.tpy = mob ? 4.2 : 6.6; G.pad = mob ? 7 : 13; G.head = mob ? 21 : 36;
  const bh = mob ? 52 : 132, gapT = mob ? 12 : 28, below = mob ? 50 : 4;
  G.gl = Math.min((S.h - bh - gapT - below - 6) / 31, S.w * (mob ? 0.72 : 0.6) / 31); G.L = 31 * G.gl;
  const oy = Math.max(0, (S.h - (bh + gapT + G.L + below + 6)) / 2);
  G.brd = { x: S.x, y: S.y + (mob ? 2 : 4) + oy, w: S.w, h: bh };
  G.tc = Math.floor((G.brd.w - G.pad * 2) / G.tpx); G.trw = Math.floor((bh - G.head - (mob ? 5 : 9)) / G.tpy); G.cells = G.tc * G.trw;
  G.lx = S.x + (mob ? 4 : 10); G.ly = G.brd.y + bh + gapT; G.rl = Math.max(mob ? 1.35 : 2.6, G.gl * 0.19);
  const rx = G.lx + G.L, rw = S.x + S.w - rx;
  G.xI = rx + rw * (mob ? 0.36 : 0.3); G.xM = S.x + S.w - (mob ? 9 : 36); G.yI0 = G.ly + (mob ? 4 : 184); G.yI1 = G.ly + G.L - (mob ? 4 : 8); G.rx = rx + (mob ? 14 : 44);
  /* task tree */
  G.tp = Math.min(mob ? 2.8 : 6.4, S.w * 0.56 / 61); G.tg = mob ? 7 : 19; G.tx = S.x + S.w * (mob ? 0.35 : 0.33);
  G.ty = S.y + Math.max(mob ? 62 : 126, (S.h - 10 * (3 * G.tp + G.tg)) / 2 + (mob ? 6 : 10));
  G.tcx = S.x + S.w * (mob ? 0.82 : 0.8); G.tcc = mob ? 1.5 : 3.4;
  G.tcy = G.ty + 9 * (3 * G.tp + G.tg) + 3 * G.tp - G.tcc * Math.sqrt(750) * 0.72;
  /* two ParallACT waffles */
  G.wp = Math.min(30, (S.w - (mob ? 30 : 130)) / 21, (S.h - (mob ? 130 : 240)) / 10); G.wy = S.y + S.h * 0.5 + (mob ? 4 : 2);
  /* s³ blocks: two rows of thirteen */
  G.up = Math.min((S.w - (mob ? 6 : 20)) / (14 * 3.55), (S.h - (mob ? 170 : 262)) / 29); G.uy = S.y + (mob ? 74 : 128) + Math.max(0, (S.h - (mob ? 170 : 262) - 29 * G.up) / 2);
  /* Avalon-M1 plans */
  G.gs = Math.min(S.w * (mob ? 1 : 0.69), S.h * (mob ? 0.8 : 0.86)) / 10; G.gx = S.x + (mob ? (S.w - 10 * G.gs) / 2 : 6); G.gy = S.y + (mob ? 26 : (S.h - 10 * G.gs) / 2 + 14);
}
const s3cell = q => { const G = s3.G, c = Math.floor(q / G.trw), r = q % G.trw; return [G.brd.x + G.pad + c * G.tpx, G.brd.y + G.head + r * G.tpy]; };
const s3fail = (q, tot) => hash(q + 17) < (q / tot < 0.14 ? 0.1 : 0.427);
const s3yI = j => s3.G.yI0 + (j + 0.5) * (s3.G.yI1 - s3.G.yI0) / 7;
function s3lat(d) {
  const G = s3.G;
  for (let i = 0; i < N; i++) { set(i, G.lx + COL[i] * G.gl, G.ly + ROW[i] * G.gl, G.rl, 0.6, C_INK, d ? hash(i) * d : 0); tl[i] = 0; }
}
function s3tree() {
  const G = s3.G, P = s3.phase; let q0 = 0, gone = 0;
  set(TREE_LEAD, G.tx, G.ty - (mob ? 12 : 28), mob ? 3.4 : 7, 1, C_EM, 0);
  for (let l = 0; l < 10; l++) {
    const n = TREE_N[l], cols = Math.ceil(n / 3), chunk = s3help.slice(q0, q0 + n).sort((a, b) => COL[a] - COL[b] || ROW[a] - ROW[b]);
    chunk.forEach((i, q) => {
      if (P === 1 && s3go[i]) { const k = gone++, rad = G.tcc * Math.sqrt(k + 0.5), an = k * 2.39996; set(i, G.tcx + rad * Math.cos(an), G.tcy + rad * Math.sin(an), mob ? 1.05 : 2.1, 0.95, C_EM, hash(i) * 0.8); }
      else { const c = Math.floor(q / 3), r = q % 3; set(i, G.tx + (c - (cols - 1) / 2) * G.tp, G.ty + l * (3 * G.tp + G.tg) + r * G.tp, mob ? 1 : 2.1, P === 1 ? 0.5 : 0.88, C_INK, P === 1 ? 0 : hash(i) * 0.3); }
      tl[i] = 0;
    });
    q0 += n;
  }
  for (let i = 1000; i < N; i++) rest(i, 0, 0);
}
function s3par() {
  const G = s3.G, p = G.wp, vals = [62, 16], used = new Uint8Array(N);
  for (let w = 0; w < 2; w++) {
    const ids = (w === 0 ? ORD_COL.slice(0, 100) : ORD_COL.slice(N - 100)).sort((a, b) => ROW[a] - ROW[b] || COL[a] - COL[b]), cx = S.x + S.w * (w === 0 ? 0.26 : 0.74);
    ids.forEach((i, q) => { used[i] = 1; const ok = q < vals[w]; set(i, cx + ((q % 10) - 4.5) * p, G.wy + (Math.floor(q / 10) - 4.5) * p, p * 0.31, ok ? 0.98 : 0.5, ok ? C_EM : C_WARM, hash(i) * 0.3); tl[i] = 0; });
  }
  for (let i = 0; i < N; i++) if (!used[i]) rest(i, 0.04, 0);
}
function s3unitPos(q) {
  const G = s3.G, p = G.up, b = Math.floor(q / 39), k = q % 39, row = b < 13 ? 0 : 1, c = b < 13 ? b : b - 13;
  return [S.x + (mob ? 3 : 10) + c * 3.55 * p + (row === 0 && c > 0 ? p * 0.5 : 0) + (k % 3) * p, G.uy + row * (13 * p + (mob ? 30 : 46)) + Math.floor(k / 3) * p];
}
function s3unit() {
  const G = s3.G;
  for (let q = 0; q < N; q++) { const i = ORD_COL[q], pos = s3unitPos(q), base = q < 39, part = q >= 1014; set(i, pos[0], pos[1], G.up * 0.33, base ? 0.8 : part ? 0.75 - (q - 1014) * 0.06 : 0.95, base ? C_INK : C_EM, hash(q) * 0.25 + q * 0.0003); tl[i] = 0; }
}
const GT_BEFORE = k => k < 71 ? 0 : k < 87 ? 1 : 2, GT_AFTER = k => k < 31 ? 0 : k < 85 ? 1 : 2;
function s3plans() {
  const G = s3.G, gs = G.gs, u = gs * 0.34, after = s3.phase === 1;
  for (let i = 0; i < N; i++) {
    if (i >= 900) { rest(i, 0, 0); continue; }
    const k = Math.floor(i / 9), m = i % 9, ty_ = after ? GT_AFTER(k) : GT_BEFORE(k), cx = G.gx + (k % 10 + 0.5) * gs, cy = G.gy + (Math.floor(k / 10) + 0.5) * gs; let x, y, r = gs * 0.052, a = 0.78, c = C_INK;
    if (ty_ === 0) { const cl = Math.floor(m / 3), an = -1.5708 + cl * 2.0944, an2 = 1.5708 + (m % 3) * 2.0944; x = cx + u * (0.62 * Math.cos(an) + 0.27 * Math.cos(an2)); y = cy + u * (0.62 * Math.sin(an) + 0.27 * Math.sin(an2)); }
    else if (ty_ === 1) { c = C_EM; if (m === 0) { x = cx; y = cy; r = gs * 0.085; a = 1; } else { const an = (m - 1) * 0.7854; x = cx + u * 0.84 * Math.cos(an); y = cy + u * 0.84 * Math.sin(an); a = 0.8; } }
    else { x = cx + u * 0.58 * ((m % 3) - 1); y = cy + u * 0.58 * (Math.floor(m / 3) - 1); a = 0.26; }
    const ch = GT_BEFORE(k) !== GT_AFTER(k);
    set(i, x, y, Math.max(r, mob ? 0.95 : 1.5), a, c, ch ? (k - 31) * 0.022 + hash(i) * 0.15 : hash(i) * 0.2); tl[i] = 0;
  }
}
SC[3] = {
  st: 0, t0: 0,
  enter(st, fresh) {
    stiff = 66; s3geom(); hovSet = null; s3.stage = -1; s3.phase = -1;
    if (st <= 3) { s3lat(fresh ? 0.3 : 0); if (fresh && st === 0) s3.fill = 0; }
    else if (st === 5) s3par(); else if (st === 6) s3unit();
  },
  tick(t, st) {
    const G = s3.G, R = s3.rnd;
    s3.dA += ((st <= 3 ? 1 : 0) - s3.dA) * (RM ? 1 : Math.min(1, dt * 5));
    if (st <= 3) {
      /* the board fills at once: by the time the paragraph is read, claims are already on it */
      const target = [0.2, 0.45, 0.65, 1][st];
      s3.fill = RM ? target : st === 3 ? Math.max(s3.fill, lerp(0.65, 1, eo(t / 4.5))) : s3.fill + (target - s3.fill) * Math.min(1, dt * 1.5);
      if (st < 3 && s3.fill > target + 0.02) s3.fill = target;
      const stage = st < 2 ? 0 : st === 3 ? 3 : RM ? 3 : t < 2.2 ? 1 : t < 4.4 ? 2 : 3;
      s3.stage = stage;
      for (let i = 0; i < N; i++) {
        let c = C_INK, a = 0.6, r = G.rl; const ii = isInt[i];
        if (fl[i] > now) { c = flc[i]; a = 1; }
        if (stage === 1) { if (in8(i)) { c = C_EM; a = 1; r = G.rl * 1.25; } else a = 0.22; }
        else if (stage === 2) { if (in128(i)) { a = 0.9; if (hash(i + 3) < 0.1) { c = C_EM; a = 1; r = G.rl * 1.25; } } else a = 0.22; }
        if (ii >= 0) {
          at[i] = 0;
          if (stage === 3) { tx[i] = G.xI; ty[i] = s3yI(ii); c = C_EM; a = 1; r = mob ? 3.4 : 7; }
          else { tx[i] = G.lx + COL[i] * G.gl; ty[i] = G.ly + ROW[i] * G.gl; }
        }
        sty(i, r, a, c);
      }
      if (!RM) {
        const front = Math.floor(s3.fill * G.cells), rate = [18, 16, 8, 26][st];
        s3.sp += rate * dt;
        while (s3.sp >= 1) { s3.sp -= 1; const i = (R() * N) | 0; if (isInt[i] >= 0 && stage === 3) continue; const q = Math.max(0, front - ((R() * 8) | 0)), ce = s3cell(q), bad = st <= 1 ? R() < 0.1 : R() < 0.42; emit(px[i], py[i], ce[0] + G.tw / 2, ce[1], 0.7 + R() * 0.3, bad ? WARM : EM, (R() - 0.5) * 0.3, mob ? 1.3 : 2.2); fl[i] = now + 0.45; flc[i] = bad ? C_WARM : C_EM; }
        if (st === 3) {
          s3.sq += 30 * dt;
          while (s3.sq >= 1) {
            s3.sq -= 1; const i = (R() * N) | 0; if (isInt[i] >= 0) continue;
            let bj = 0, bd = 1e9; for (let j = 0; j < 7; j++) { const d = Math.abs(s3yI(j) - py[i]); if (d < bd) { bd = d; bj = j; } }
            const Y = s3yI(bj), xI = G.xI, xM = G.xM, yE = G.yI1 + (mob ? 8 : 16);
            emit(px[i], py[i], xI - (mob ? 5 : 10), Y, 0.7 + R() * 0.3, INK, (R() - 0.5) * 0.2, mob ? 1.2 : 2, () => {
              if (Math.random() < 0.252) emit(xI + (mob ? 5 : 10), Y, xM, Y + (mob ? 8 : 16), 0.5, EM, -0.12, mob ? 1.5 : 2.5, p => emit(xM, p.y1, xM, yE, 0.5 + (yE - p.y1) / 420, EM, 0, mob ? 1.5 : 2.5));
              else emit(xI - (mob ? 5 : 10), Y, xI - (mob ? 16 : 34), Y + (Math.random() - 0.5) * (mob ? 20 : 40), 0.4, INK3, 0, mob ? 1 : 1.5);
            });
          }
        }
      }
    } else if (st === 4) {
      const ph = RM || t > 2.4 ? 1 : 0; if (ph !== s3.phase) { s3.phase = ph; s3.tp0 = now; s3tree(); }
    } else if (st === 7) {
      const ph = RM ? 1 : (t % 8.4) < 2.6 ? 0 : 1; if (ph !== s3.phase) { s3.phase = ph; s3.tp0 = now; s3plans(); }
    }
  },
  under(a) {
    const st = this.st, G = s3.G, t = T_OF(3), f = a * s3.dA;
    if (f > 0.01) {
      const B = G.brd, tot = G.cells, n = Math.floor(s3.fill * tot), yh = B.y + (mob ? 14 : 23);
      rrect(B.x, B.y, B.w, B.h, mob ? 9 : 14); ctx.fillStyle = 'rgba(238,242,239,' + (0.024 * f).toFixed(3) + ')'; ctx.fill(); ctx.strokeStyle = rgba(INK, 0.14 * f); ctx.lineWidth = 1; ctx.stroke();
      T(L.board, B.x + G.pad, yh, { s: mob ? 11 : 13.5, w: 600, c: rgba(INK, f) });
      const ent = 148079 * s3.fill, fails = 56472 * (s3.fill <= 0.14 ? s3.fill * 0.1 : 0.014 + (s3.fill - 0.14) * 0.427) / NF;
      let xr = B.x + B.w - G.pad;
      xr -= T_R('FAIL', xr, yh, { s: mob ? 10 : 12.5, w: 600, c: rgba(WARM, f) }) + 5;
      xr -= TN(fmt(fails), xr, yh, { s: mob ? 11 : 13.5, w: 600, al: 'right', c: rgba(WARM, f) }) + (mob ? 10 : 18);
      xr -= T_R(L.entries, xr, yh, { s: mob ? 10 : 12.5, w: 500, c: rgba(INK3, f) }) + 5;
      TN(fmt(ent), xr, yh, { s: mob ? 11 : 13.5, w: 600, al: 'right', c: rgba(INK, f) });
      ctx.fillStyle = rgba(EM, 0.62 * f); for (let q = 0; q < n; q++) { if (s3fail(q, tot)) continue; const c = s3cell(q); ctx.fillRect(c[0], c[1], G.tw, G.th); }
      ctx.fillStyle = rgba(WARM, 0.9 * f); for (let q = 0; q < n; q++) { if (!s3fail(q, tot)) continue; const c = s3cell(q); ctx.fillRect(c[0], c[1], G.tw, G.th); }
      /* steps of organization and the run's totals */
      const LAD = [[fmt(8)].concat(L.lad[0]), [fmt(128)].concat(L.lad[1]), [fmt(1024)].concat(L.lad[2])], cur = s3.stage;
      if (st === 2) {
        LAD.forEach((l, k) => {
          const on = cur === k + 1, al = (on ? 1 : cur > k + 1 ? 0.7 : 0.36) * f;
          if (mob) { const y = G.ly + G.L + 20 + k * 15; TN(l[0], S.x + 40, y, { s: 11.5, w: 600, al: 'right', c: rgba(on ? EM : INK, al) }); T(l[1] + ' ' + l[2], S.x + 47, y, { s: 10.5, c: rgba(on ? EM : INK3, al) }); }
          else { const y = G.ly + 20 + k * 48; TN(l[0], G.rx + 54, y, { s: 19, w: 600, al: 'right', c: rgba(on ? EM : INK, al) }); T(l[1], G.rx + 66, y - 3, { s: 13, c: rgba(on ? EM : INK2, al) }); T(l[2], G.rx + 66, y + 15, { s: 13, c: rgba(on ? EM : INK2, al) }); }
        });
      }
      if (st === 3) {
        const e = RM ? 1 : eo(t / 4.5);
        if (mob) { const y = G.ly + G.L + 22; let x = S.x + 4; x += TN(fmt(11111 * e), x, y, { s: 15, w: 600, c: rgba(INK, f) }) + 5; x += TW(L.pr[0], { s: 10.5 }) + 5; T(L.pr[0], x - TW(L.pr[0], { s: 10.5 }) - 5, y, { s: 10.5, c: rgba(INK3, f) }); TN(fmt(2800 * e), x, y, { s: 15, w: 600, c: rgba(EM, f) }); }
        else {
          const y = G.ly + 34; TN(fmt(11111 * e), G.rx, y, { s: 34, w: 600, c: rgba(INK, f) }); T(L.pr[1], G.rx, y + 22, { s: 13, c: rgba(INK3, f) });
          TN(fmt(2800 * e), G.rx, y + 76, { s: 34, w: 600, c: rgba(EM, f) }); T(L.pr[2], G.rx, y + 98, { s: 13, c: rgba(INK3, f) });
        }
      }
      if (st === 2 && s3.stage === 1) { ctx.strokeStyle = rgba(EM, 0.35 * f); ctx.lineWidth = 1; ctx.beginPath(); for (let p = 0; p < 8; p++) for (let q = p + 1; q < 8; q++) { ctx.moveTo(px[B8[p]], py[B8[p]]); ctx.lineTo(px[B8[q]], py[B8[q]]); } ctx.stroke(); }
      if (st === 2 && s3.stage === 2) for (const i of REV) ring(px[i], py[i], rr[i] + (mob ? 2 : 4), rgba(EM, 0.75 * f), 1.25);
      /* integrators and main */
      const fi = f * (s3.stage === 3 ? 1 : 0);
      if (fi > 0.01) { for (const j of INTEG) glow(px[j], py[j], mob ? 12 : 24, EM, 0.18 * fi); if (!mob) T(L.integ, G.xI, G.yI0 - 10, { s: 12.5, w: 600, al: 'center', c: rgba(EM, fi) }); }
      const fm = f * (st === 3 ? 1 : st === 2 && s3.stage === 3 ? 0.6 : 0.2), yE = G.yI1 + (mob ? 8 : 16);
      seg(G.xM, G.yI0, G.xM, yE, rgba(INK, 0.32 * fm), 1.25);
      ctx.beginPath(); ctx.moveTo(G.xM - 4, yE - 6); ctx.lineTo(G.xM, yE); ctx.lineTo(G.xM + 4, yE - 6); ctx.strokeStyle = rgba(INK, 0.4 * fm); ctx.lineWidth = 1.25; ctx.stroke();
      T('main', G.xM, G.yI0 - (mob ? 5 : 10), { s: mob ? 10 : 12.5, w: 600, al: 'center', c: rgba(INK2, fm) });
    }
    if (st === 4) {
      const ph = s3.phase, fp = a * ss((t - 0.2) / 0.5);
      for (let l = 0; l < 10; l++) { const cols = Math.ceil(TREE_N[l] / 3), y = G.ty + l * (3 * G.tp + G.tg) + G.tp, hw = (cols - 1) / 2 * G.tp + 4; seg(G.tx - hw, y, G.tx + hw, y, rgba(INK, 0.07 * a), 3 * G.tp + 2); TN(String(l + 1), G.tx - hw - (mob ? 6 : 12), y + 4, { s: mob ? 8.5 : 11.5, w: 500, al: 'right', c: rgba(INK4, fp) }); }
      const xr = G.tx + (Math.ceil(183 / 3) - 1) / 2 * G.tp + 4, yl = G.ty + 9 * (3 * G.tp + G.tg) + G.tp;
      if (ph === 1) {
        const e = RM ? 1 : ss((now - s3.tp0) / 0.8), R750 = G.tcc * Math.sqrt(750);
        dot(xr + (mob ? 5 : 10), yl, mob ? 2.2 : 3.6, rgba(INK, a * e)); seg(xr + (mob ? 5 : 10), yl, lerp(xr + 10, G.tcx - R750 - 4, e), lerp(yl, G.tcy + R750 * 0.55, e), rgba(INK, 0.4 * a * e), 1, [2, 4]);
        ctx.beginPath(); ctx.moveTo(px[TREE_LEAD] + 9, py[TREE_LEAD]); ctx.quadraticCurveTo(G.tcx, py[TREE_LEAD] - 2, lerp(px[TREE_LEAD], G.tcx, e), lerp(py[TREE_LEAD], G.tcy - R750 - 8, e)); ctx.strokeStyle = rgba(EM, 0.55 * a * e); ctx.lineWidth = 1.25; ctx.setLineDash([3, 5]); ctx.stroke(); ctx.setLineDash([]);
      }
    }
  },
  over(a) {
    const st = this.st, G = s3.G, t = T_OF(3), hx_ = S.x + (mob ? 2 : 10);
    if (st === 4) {
      const f = a * ss((t - 0.2) / 0.5);
      T(L.tree[0], hx_, S.y + (mob ? 12 : 20), { s: mob ? 11 : 13, w: 600, c: rgba(INK2, a) });
      T(L.tree[1], hx_, S.y + (mob ? 27 : 40), { s: mob ? 10.5 : 12.5, c: rgba(INK4, a) });
      tag(L.tree[2], px[TREE_LEAD] + (mob ? 8 : 15), py[TREE_LEAD], { s: mob ? 10.5 : 12.5, c: rgba(EM, f), a: f });
      if (s3.phase === 1) {
        const e = RM ? 1 : ss((now - s3.tp0 - 0.6) / 0.6), R750 = G.tcc * Math.sqrt(750), y = G.tcy + R750 + (mob ? 18 : 38);
        TN('≈750', G.tcx, y + (mob ? 4 : 8), { s: mob ? 18 : 36, w: 600, al: 'center', c: rgba(INK, a * e) });
        T(L.tree[3], G.tcx, y + (mob ? 18 : 30), { s: mob ? 10 : 13, al: 'center', c: rgba(INK3, a * e) });
        T(mob ? L.tree[4] : L.tree[5], G.tcx, y + (mob ? 31 : 49), { s: mob ? 10 : 13, al: 'center', c: rgba(INK3, a * e) });
      }
    } else if (st === 5) {
      const f = a * ss((t - 0.4) / 0.5), p = G.wp, vals = [62, 16], LB = L.parLB, e = RM ? 1 : eo((t - 0.4) / 1.0);
      T(L.par[0], hx_, S.y + (mob ? 12 : 20), { s: mob ? 11 : 13, w: 600, c: rgba(INK2, a) });
      T(mob ? L.par[1] : L.par[2], hx_, S.y + (mob ? 27 : 40), { s: mob ? 10.5 : 12.5, c: rgba(INK4, a) });
      for (let w = 0; w < 2; w++) {
        const x0 = S.x + S.w * (w === 0 ? 0.26 : 0.74) - 4.5 * p - p * 0.3, yb = G.wy + 5 * p + (mob ? 20 : 34);
        TN(Math.round(vals[w] * e) + '%', x0, G.wy - 5 * p - (mob ? 7 : 16), { s: mob ? 26 : 56, w: 600, c: rgba(w === 0 ? EM : INK, f) });
        T(LB[w][0], x0, yb, { s: mob ? 11.5 : 17, w: 600, c: rgba(INK, f) }); T(LB[w][1], x0, yb + (mob ? 14 : 22), { s: mob ? 10 : 13.5, c: rgba(INK3, f) });
      }
    } else if (st === 6) {
      const f = a * ss((t - 0.5) / 0.5), p = G.up, x1 = s3unitPos(39)[0], y0 = G.uy;
      T(L.s3u[0], hx_, S.y + (mob ? 12 : 20), { s: mob ? 11 : 13, w: 600, c: rgba(INK2, a) });
      T(L.s3u[1], hx_, S.y + (mob ? 27 : 40), { s: mob ? 10.5 : 12.5, c: rgba(INK4, a) });
      const wn = TN('×25', x1, y0 - (mob ? 9 : 16), { s: mob ? 26 : 54, w: 600, c: rgba(EM, f) });
      T(L.s3u[2], x1 + wn + (mob ? 8 : 14), y0 - (mob ? 21 : 38), { s: mob ? 11 : 16, w: 600, c: rgba(EM, f) }); T(L.s3u[3], x1 + wn + (mob ? 8 : 14), y0 - (mob ? 9 : 18), { s: mob ? 10 : 13, c: rgba(INK3, f) });
      T(mob ? L.s3u[4] : L.s3u[5], S.x + (mob ? 3 : 10), y0 + 13 * p + (mob ? 12 : 20), { s: mob ? 9.5 : 12, c: rgba(INK3, f) });
      const y3 = y0 + 26 * p + (mob ? 30 : 46) + (mob ? 22 : 40);
      if (mob) T(L.s3u[6], S.x + 3, y3, { s: 10.5, c: rgba(INK2, f) });
      else { const w1 = TN('≈−50%', S.x + 10, y3, { s: 24, w: 600, c: rgba(INK, f) }); T(L.s3u[7], S.x + 10 + w1 + 12, y3 - 2, { s: 13, c: rgba(INK3, f) }); }
    } else if (st === 7) {
      const f = a * ss((t - 0.4) / 0.5), after = s3.phase === 1, gs = G.gs;
      T(mob ? L.plans[0] : L.plans[1], hx_, S.y + (mob ? 12 : 20), { s: mob ? 10.5 : 13, w: 600, c: rgba(INK2, a) });
      const rows = [[L.plans[2], L.plans[3], 71, 31, INK], [L.plans[4], L.plans[5], 16, 54, EM]];
      if (mob) {
        const y0 = G.gy + 10 * gs + 22;
        rows.forEach((r, k) => { const x = S.x + 4 + k * (S.w / 2); const w = TN(r[2] + '%', x, y0, { s: 17, w: 600, c: rgba(r[4], f * (after ? 0.4 : 1)) }); T('→', x + w + 4, y0 - 1, { s: 12, c: rgba(INK4, f) }); TN(r[3] + '%', x + w + 20, y0, { s: 17, w: 600, c: rgba(r[4], f * (after ? 1 : 0.4)) }); T(r[0] + ' ' + r[1], x, y0 + 14, { s: 10, c: rgba(INK3, f) }); });
        T(after ? L.plans[7] : L.plans[6], S.x + S.w, S.y + 12, { s: 10.5, w: 600, al: 'right', c: rgba(EM, f) });
      } else {
        const x = G.gx + 10 * gs + 36, y0 = G.gy + gs * 1.1;
        [[L.plans[6], !after], [L.plans[7], after]].forEach((c, k) => { T(c[0], x, y0 + k * 24, { s: 14, w: 600, c: rgba(c[1] ? EM : INK4, f) }); if (c[1]) dot(x - 12, y0 + k * 24 - 5, 3, rgba(EM, f)); });
        T(L.plans[8], x, y0 + 46, { s: 12.5, c: rgba(INK4, f) });
        rows.forEach((r, k) => {
          const y = y0 + 134 + k * 140;
          const w = TN(r[2] + '%', x, y, { s: 34, w: 600, c: rgba(r[4], f * (after ? 0.35 : 1)) }); T('→', x + w + 8, y - 3, { s: 20, c: rgba(INK4, f) }); TN(r[3] + '%', x + w + 40, y, { s: 34, w: 600, c: rgba(r[4], f * (after ? 1 : 0.35)) });
          T(r[0], x, y + 26, { s: 13.5, c: rgba(INK2, f) }); T(r[1], x, y + 45, { s: 13.5, c: rgba(INK2, f) });
        });
      }
    }
  }
};
function T_R(s, x, y, o) { o.al = 'right'; T(s, x, y, o); return ctx.measureText(s).width; }

/* ============ Scene 4: memory ============ */
const s4 = { G: {}, m: 0, gf: 0, ring: [], idx: new Int16Array(N).fill(-1), gone: new Uint8Array(128), recs: [], links: [], indeg: new Uint8Array(128), top: [] };
(function () {
  const ang = [...Array(N).keys()].sort((a, b) => Math.atan2(ROW[a] - 15.5, COL[a] - 15.5) - Math.atan2(ROW[b] - 15.5, COL[b] - 15.5));
  for (let j = 0; j < 128; j++) { const i = ang[j * 8 + ((hash(j) * 8) | 0)]; s4.ring.push(i); s4.idx[i] = j; }
  const r = rnd(19);
  for (let j = 0; j < 128; j++) s4.gone[j] = 0;
  const pm = [...Array(128).keys()]; for (let i = 127; i > 0; i--) { const j = (r() * (i + 1)) | 0; const t = pm[i]; pm[i] = pm[j]; pm[j] = t; }
  for (let q = 0; q < 64; q++) s4.gone[pm[q]] = 1;
  /* links point to nearby earlier records, preferring the ones already cited more often */
  for (let j = 1; j < 128; j++) {
    const nl = r() < 0.4 ? 2 : 1, cj = j % 13, rj = Math.floor(j / 13);
    for (let q = 0; q < nl; q++) {
      const cand = []; let tot = 0;
      for (let k = 0; k < j; k++) { const dc = Math.abs(k % 13 - cj), dr = Math.abs(Math.floor(k / 13) - rj); if (dc <= 3 && dr <= 2 && !(dc === 0 && dr === 0)) { const w = s4.indeg[k] * 2 + 1; cand.push([k, w]); tot += w; } }
      if (!cand.length) cand.push([j - 1, 1]), tot = 1;
      let pick = r() * tot, k = cand[cand.length - 1][0]; for (const c of cand) { pick -= c[1]; if (pick <= 0) { k = c[0]; break; } }
      if (!s4.links.some(l => l[0] === j && l[1] === k)) { s4.links.push([j, k]); s4.indeg[k]++; }
    }
  }
  s4.top = [...Array(128).keys()].sort((a, b) => s4.indeg[b] - s4.indeg[a]);
})();
const MC = [0, 32, 64, 96];
/* Three conditions of one ScaleMAS experiment: the same 128 agents gathered into three rings.
   An arc of the big ring folds into a small one, so on the next step the three rings unfold into one. */
const S4ROWS = [6, 7, 8, 8, 7, 6], s4mini = [], s4ml = [];
(function () {
  let o = 0;
  for (let r = 0; r < 6; r++) {
    const n = S4ROWS[r];
    for (let c = 0; c < n; c++) { s4mini.push([c - (n - 1) / 2, r - 2.5]); if (c < n - 1) s4ml.push([o + c, o + c + 1]); }
    if (r < 5) { const n2 = S4ROWS[r + 1]; for (let c = 0; c < n; c++) { const x = c - (n - 1) / 2; let b = 0, bd = 99; for (let q = 0; q < n2; q++) { const d = Math.abs(q - (n2 - 1) / 2 - x - 0.01); if (d < bd) { bd = d; b = q; } } s4ml.push([o + c, o + n + b]); } }
    o += n;
  }
})();
function s4map(rot) {   /* rot = 0: rings in a row (left arc, top and bottom, right arc); rot = 90: in a column */
  const g = new Uint8Array(128), phi = new Float32Array(128), k = new Uint8Array(128), cnt = [0, 0, 0], norm = d => ((d + 540) % 360) - 180;
  for (let j = 0; j < 128; j++) {
    const th = norm(-180 + (j + 0.5) * 2.8125 - rot); let gg, c, kk;
    if (Math.abs(th) > 120) { gg = 0; c = 180; kk = (360 / 42) / 2.8125; }
    else if (Math.abs(th) <= 60) { gg = 2; c = 0; kk = (360 / 42) / 2.8125; }
    else { gg = 1; c = th < 0 ? -90 : 90; kk = (180 / 22) / 2.8125; }
    g[j] = gg; phi[j] = (rot + c + kk * norm(th - c)) * Math.PI / 180; k[j] = cnt[gg]++;
  }
  return { g, phi, k };
}
const S4M = [s4map(0), s4map(90)];
function s4geom() {
  const G = s4.G;
  G.cx = S.cx; G.R = mob ? Math.min(S.w, S.h) * 0.37 : Math.min(Math.min(S.w, S.h) * 0.37, (S.h - 172) / 2); G.ra = mob ? 1.7 : 3.3;
  G.cy = mob ? S.y + S.h * 0.455 : Math.max(S.y + S.h * 0.445, S.y + 62 + G.R);
  G.rp = Math.min(G.R * 1.36 / 13, mob ? 12.5 : 27); G.rs = mob ? 2.5 : 4.6;
  /* three rings: in a row on a wide screen, in a column on a narrow one */
  const vert = mob || S.w < 560, top = S.y + (mob ? 38 : 58); G.vert = vert; G.po = mob ? 7 : 13; G.map = S4M[vert ? 1 : 0];
  if (vert) { const rh = (S.y + S.h - top) / 3; G.tr = Math.min(rh / 2 - G.po - 10, S.w * 0.17); G.tc = [0, 1, 2].map(g => [S.x + G.tr + G.po + 8, top + rh * (g + 0.5)]); }
  else { const tp = S.w / 3; G.tr = Math.min(tp / 2 - 28, S.h * 0.22); const ty = top + Math.max(0, (S.y + S.h - top - 2 * (G.tr + G.po) - 112) / 2) + G.tr + G.po; G.tc = [0, 1, 2].map(g => [S.x + tp * (g + 0.5), ty]); }
  G.tq = G.tr * 1.28 / 8;
}
const s4ang = j => -Math.PI + (j + 0.5) / 128 * 6.28319;
const s4agent = j => { const G = s4.G, a = s4ang(j); return [G.cx + G.R * Math.cos(a), G.cy + G.R * Math.sin(a)]; };
const s4cell = j => { const G = s4.G, c = j % 13, r = Math.floor(j / 13), n = r === 9 ? 11 : 13; return [G.cx + (c - (n - 1) / 2) * G.rp, G.cy + (r - 4.5) * G.rp]; };
/* an agent on its small ring */
const s4tri = j => { const G = s4.G, M = G.map, c = G.tc[M.g[j]], a = M.phi[j]; return [c[0] + G.tr * Math.cos(a), c[1] + G.tr * Math.sin(a)]; };
/* where a record lives before the shared store: nowhere (with the agent), next to its author, in the small grid */
function s4start(j) {
  const G = s4.G, M = G.map, g = M.g[j], c = G.tc[g];
  if (g === 2) { const q = s4mini[M.k[j]]; return [c[0] + q[0] * G.tq, c[1] + q[1] * G.tq]; }
  const a = M.phi[j], r = G.tr + (g === 1 ? G.po : 0); return [c[0] + r * Math.cos(a), c[1] + r * Math.sin(a)];
}
function s4rec(j) { const u = clamp(s4.m * 1.7 - (j / 128) * 0.7), e = eio(u), a = s4start(j), b = s4cell(j); return [lerp(a[0], b[0], e), lerp(a[1], b[1], e), e]; }
function s4layout(st) {
  const G = s4.G;
  for (let i = 0; i < N; i++) {
    const j = s4.idx[i];
    if (j < 0) { rest(i, st === 5 ? 0 : 0.045, 0); continue; }
    const p = st <= 1 ? s4tri(j) : s4agent(j);
    if (st === 5) { const q = MC.indexOf(j); if (q >= 0) { const an = -2.356 + q * 1.5708; set(i, G.cx + G.R * 0.8 * Math.cos(an), G.cy + G.R * 0.8 * Math.sin(an), mob ? 5 : 9, 1, C_EM, 0); } else set(i, p[0], p[1], G.ra, 0, C_INK, 0); }
    else set(i, p[0], p[1], G.ra, 0.9, C_INK, 0);
    tl[i] = 0;
  }
}
SC[4] = {
  st: 0, t0: 0,
  enter(st) { stiff = 64; s4geom(); hovSet = null; s4layout(st); s4.dead = [0, 0, 0, 0]; s4.nd = 0; },
  tick(t, st) {
    const G = s4.G;
    s4.m += ((st >= 2 ? 1 : 0) - s4.m) * (RM ? 1 : Math.min(1, dt * 1.6));
    const tv = RM ? 3 : t % 8.5, goneNow = (st <= 1 && tv > 1.6 && tv < 6.2) || st === 3 || st === 6;
    s4.goneNow = goneNow;
    s4.gf += ((goneNow && st <= 1 ? 1 : 0) - s4.gf) * (RM ? 1 : Math.min(1, dt * 5));
    if (st === 5) {
      const p = RM ? 1 : eo(t / 8);
      if (!RM) { const due = p < 0.999 ? 0.5 : 1.9; if (now - s4.nd > due) { s4.nd = now; s4.dead[(Math.random() * 4) | 0] = now; } }
      MC.forEach((j, q) => { const i = s4.ring[j], d = now - s4.dead[q]; if (RM || d > 1.2) sty(i, mob ? 5 : 9, 1, C_EM); else if (d < 0.3) sty(i, mob ? 6 : 11, 1, C_WARM); else if (d < 0.65) sty(i, mob ? 5 : 9, 0.05, C_WARM); else sty(i, mob ? 5 : 9, 1, C_EM); });
      return;
    }
    for (let j = 0; j < 128; j++) {
      const i = s4.ring[j]; let a = st === 4 ? 0.32 : 0.9, c = C_INK, r = G.ra;
      if (goneNow && s4.gone[j]) a = 0;
      sty(i, r, a, c);
    }
    /* operations on the store */
    if ((st === 2 || st === 3 || st === 6) && (RM || t > 1.2)) {
      const t2 = RM ? t : t - 1.2, per = st === 2 ? 7.2 : 3.4, cyc = Math.floor(t2 / per), u = t2 - cyc * per;
      const op = st === 2 ? (u < 2.4 ? 0 : u < 4.8 ? 1 : 2) : 1, uo = st === 2 ? u - op * 2.4 : u;
      let ag = (cyc * 37 + 11 + op * 29) % 128; if (st !== 2) { while (s4.gone[ag]) ag = (ag + 1) % 128; }
      const cand = []; for (let q = 0; q < 16; q++) cand.push(s4.top[(cyc * 7 + q * 5) % 40]);
      let found = [...new Set(cand)].slice(0, 3);
      if (st !== 2) { const gk = s4.top.find(k => s4.gone[k] && found.indexOf(k) < 0); if (!found.some(k => s4.gone[k])) found[2] = gk; }
      s4.op = { op, u: RM ? 1.6 : uo, ag, found, pub: (cyc * 53 + 90) % 128 };
      if (op !== 0 && !(goneNow && s4.gone[ag])) sty(s4.ring[ag], G.ra * 1.5, 1, C_EM);
      if (op === 0) sty(s4.ring[s4.op.pub], G.ra * 1.5, 1, C_EM);
    } else s4.op = null;
  },
  under(a) {
    const st = this.st, G = s4.G, t = T_OF(4), op = s4.op, gn = s4.goneNow;
    const LBL = L.s4lbl;
    const hx_ = S.x + (mob ? 2 : 6);
    if (st <= 1) { T(LBL[0], hx_, S.y + (mob ? 12 : 20), { s: mob ? 11 : 13, w: 600, c: rgba(INK2, a) }); T(LBL[1], hx_, S.y + (mob ? 27 : 39), { s: mob ? 10.5 : 12.5, c: rgba(INK4, a) }); }
    else if (st === 2 || st === 3) {
      const ops = L.s4ops; let x = hx_;
      T(mob ? L.s4opsH[0] : L.s4opsH[1], x, S.y + (mob ? 12 : 20), { s: mob ? 11 : 13, w: 600, c: rgba(INK2, a) });
      ops.forEach((o, k) => { const on = op && op.op === k; T(o, x, S.y + (mob ? 27 : 41), { s: mob ? 10.5 : 13.5, w: 600, c: rgba(on ? EM : INK4, a) }); const w = TW(o, { s: mob ? 10.5 : 13.5, w: 600 }); if (on) seg(x, S.y + (mob ? 31 : 47), x + w, S.y + (mob ? 31 : 47), rgba(EM, a), 1.5); x += w + (mob ? 12 : 26); });
    } else if (st === 4) { T(mob ? L.cmH[0] : L.cmH[1], hx_, S.y + (mob ? 12 : 20), { s: mob ? 10.5 : 13, w: 600, c: rgba(INK2, a) }); }
    else if (st === 6) { T(mob ? L.oai[0] : L.oai[1], hx_, S.y + (mob ? 12 : 20), { s: mob ? 11 : 13, w: 600, c: rgba(INK2, a) }); T(mob ? L.oai[2] : L.oai[3], hx_, S.y + (mob ? 27 : 39), { s: mob ? 10.5 : 12.5, c: rgba(INK4, a) }); }
    else { T(L.mc[0], hx_, S.y + (mob ? 12 : 20), { s: mob ? 11 : 13, w: 600, c: rgba(INK2, a) }); T(L.mc[1], hx_, S.y + (mob ? 27 : 39), { s: mob ? 10.5 : 12.5, c: rgba(INK4, a) }); }
    /* links */
    const dim = st === 4 ? 0.22 : 1, lm = clamp((s4.m - 0.75) * 4);
    if (lm > 0.01) {
      ctx.strokeStyle = rgba(INK, 0.16 * a * lm * dim); ctx.lineWidth = 1; ctx.beginPath();
      for (const l of s4.links) { if (op && op.op === 0 && l[0] === op.pub && op.u < 1.0) continue; const p = s4cell(l[0]), q = s4cell(l[1]); ctx.moveTo(p[0], p[1]); ctx.lineTo(q[0], q[1]); }
      ctx.stroke();
    }
    /* three rings: the small grid of the shared store and the condition labels */
    const M = G.map, pre = 1 - clamp(s4.m * 3);
    if (pre > 0.01) {
      const c2 = G.tc[2]; ctx.strokeStyle = rgba(INK, 0.2 * a * pre); ctx.lineWidth = 1; ctx.beginPath();
      for (const l of s4ml) { const p = s4mini[l[0]], q = s4mini[l[1]]; ctx.moveTo(c2[0] + p[0] * G.tq, c2[1] + p[1] * G.tq); ctx.lineTo(c2[0] + q[0] * G.tq, c2[1] + q[1] * G.tq); }
      ctx.stroke();
      const LB = L.s4lb, V = [38.0, 46.8, 55.1], CP = L.s4cp, fa = a * pre, fg = fa * s4.gf;
      for (let g = 0; g < 3; g++) {
        const c = G.tc[g], cn = rgba(g === 2 ? EM : INK, fa), cl = rgba(g === 2 ? INK : INK2, fa), cc = rgba(g === 2 ? EM : INK3, fg);
        if (G.vert) {
          const x = c[0] + G.tr + G.po + (mob ? 22 : 30);
          T(LB[g], x, c[1] - (mob ? 14 : 19), { s: mob ? 11 : 14, w: 600, c: cl });
          TN(dec(V[g]) + '%', x, c[1] + (mob ? 12 : 18), { s: mob ? 24 : 34, w: 600, c: cn });
          if (fg > 0.01) T(CP[g], x, c[1] + (mob ? 29 : 40), { s: mob ? 10 : 12.5, c: cc });
        } else {
          const y = c[1] + G.tr + G.po + 32;
          T(LB[g], c[0], y, { s: 14, w: 600, al: 'center', c: cl });
          TN(dec(V[g]) + '%', c[0], y + 42, { s: 34, w: 600, al: 'center', c: cn });
          if (fg > 0.01) T(CP[g], c[0], y + 66, { s: 12.5, al: 'center', c: cc });
        }
      }
    }
    /* records */
    for (let j = 0; j < 128; j++) {
      const p = s4rec(j), ag = s4.ring[j], g = M.g[j]; let sz = G.rs * (1 + p[2] * 0.2 * Math.min(5, s4.indeg[j])), c = INK, hl = 0;
      /* without a store there is no record, a private one lives with its author, a shared one stays */
      let al = g === 0 ? p[2] : g === 1 ? lerp(Math.min(1, aa[ag] / 0.9), 1, p[2]) : 1;
      const keep = g === 2 && s4.gone[j] ? s4.gf * pre : 0;
      if (op && op.op === 0 && j === op.pub) { al = op.u < 0.9 ? 0 : eo((op.u - 0.9) / 0.4); if (op.u >= 0.9) { c = EM; hl = 1 - clamp((op.u - 1.6) / 0.8); } }
      if (op && op.op >= 1 && op.found.indexOf(j) >= 0 && op.u > 0.6) { c = EM; hl = clamp((op.u - 0.6) * 4) * (op.op === 2 && j !== op.found[0] ? 0.4 : 1); }
      if (op && op.op === 2 && op.u > 1.2) { const l = s4.links.find(l => l[0] === op.found[0]) || s4.links.find(l => l[1] === op.found[0]); if (l && (j === l[0] || j === l[1])) { c = EM; hl = 1; } }
      al *= a * dim * (st === 5 ? 0.85 : 0.8); if (al < 0.01) continue;
      if (hl > 0.02) glow(p[0], p[1], sz * 3.2, EM, 0.28 * hl * a);
      if (keep > 0.02) { c = [lerp(238, 95, keep) | 0, lerp(242, 227, keep) | 0, lerp(239, 179, keep) | 0]; sz *= 1 + 0.25 * keep; }
      const wgt = lerp(0.74, 0.5 + 0.1 * Math.min(5, s4.indeg[j]), p[2]) + 0.4 * keep;
      ctx.fillStyle = rgba(c, hl > 0.3 ? a : al * wgt); ctx.fillRect(p[0] - sz / 2, p[1] - sz / 2, sz, sz);
    }
    /* actions */
    if (op && a > 0.5) {
      const A = s4agent(op.ag), agGone = gn && s4.gone[op.ag];
      if (op.op === 0) {
        const P = s4agent(op.pub), Cc = s4cell(op.pub);
        if (op.u < 0.9) { const e = eio(op.u / 0.9), x = lerp(P[0], Cc[0], e), y = lerp(P[1], Cc[1], e); seg(P[0], P[1], x, y, rgba(EM, 0.5 * a), 1.25); const s = G.rs * 1.2; glow(x, y, s * 3, EM, 0.35 * a); ctx.fillStyle = rgba(EM, a); ctx.fillRect(x - s / 2, y - s / 2, s, s); }
        else { const e = eo((op.u - 0.9) / 0.6); ctx.strokeStyle = rgba(EM, 0.75 * a * (1 - clamp((op.u - 1.7) / 0.6))); ctx.lineWidth = 1.25; ctx.beginPath(); for (const l of s4.links) if (l[0] === op.pub) { const q = s4cell(l[1]); ctx.moveTo(Cc[0], Cc[1]); ctx.lineTo(lerp(Cc[0], q[0], e), lerp(Cc[1], q[1], e)); } ctx.stroke(); }
      } else if (!agGone) {
        if (op.u < 0.6) { const e = op.u / 0.6; ring(lerp(A[0], G.cx, e * 0.55), lerp(A[1], G.cy, e * 0.55), mob ? 2.5 : 4, rgba(EM, a), 1.5); seg(A[0], A[1], lerp(A[0], G.cx, e * 0.55), lerp(A[1], G.cy, e * 0.55), rgba(EM, 0.45 * a), 1, [3, 4]); }
        else { const e = eo((op.u - 0.6) / 0.5), f = a * (op.op === 2 ? 0.35 : 1) * (1 - clamp((op.u - (st === 3 ? 2.8 : 2.0)) / 0.4)); ctx.strokeStyle = rgba(EM, 0.6 * f); ctx.lineWidth = 1.25; ctx.beginPath(); for (const k of op.found) { const q = s4cell(k); ctx.moveTo(q[0], q[1]); ctx.lineTo(lerp(q[0], A[0], e), lerp(q[1], A[1], e)); } ctx.stroke(); }
        if (op.op === 2 && op.u > 0.8) { const l = s4.links.find(l => l[0] === op.found[0]) || s4.links.find(l => l[1] === op.found[0]); if (l) { const from = s4cell(op.found[0]), to = s4cell(l[0] === op.found[0] ? l[1] : l[0]), e = eio((op.u - 0.8) / 0.8); seg(from[0], from[1], lerp(from[0], to[0], e), lerp(from[1], to[1], e), rgba(EM, a), 2); } }
      }
    }
    /* state labels: a record found after its author is gone (ScaleMAS; the OpenAI runs), and the ScaleMAS result */
    if (st === 3 || st === 6) {
      const k = op && op.found.find(q => s4.gone[q]);
      if (op && k !== undefined && op.u > 0.9) { const p = s4cell(k), f = a * clamp((op.u - 0.9) * 3) * (1 - clamp((op.u - 2.8) / 0.4)); ring(p[0], p[1], G.rs * 2.1, rgba(EM, f), 1.25); tag(L.s4found, p[0] + G.rs * 2.6, p[1] - G.rs * 3.2, { s: mob ? 10 : 12.5, c: rgba(EM, f), a: f }); }
      if (st === 3) { const rows = [[L.s4lb[2], 55.1, 1], [L.s4lb[1], 46.8, 0], [L.s4lb[0], 38.0, 0]], y0 = G.cy + G.R + (mob ? 24 : 46), stp = mob ? 17 : 27, bx0 = S.x + (mob ? 104 : 190), bx1 = S.x + S.w - (mob ? 54 : 110), e = RM ? 1 : eo((t - 0.4) / 1.1);
      rows.forEach((r, q) => {
        const y = y0 + q * stp, hh = mob ? 5 : 7, w = (bx1 - bx0) * r[1] / 60 * e;
        T(r[0], S.x + (mob ? 2 : 6), y + 4, { s: mob ? 10.5 : 13, w: r[2] ? 600 : 500, c: rgba(r[2] ? INK : INK3, a) });
        rrect(bx0, y - hh / 2, Math.max(hh, w), hh, hh / 2); ctx.fillStyle = rgba(r[2] ? EM : INK, (r[2] ? 0.95 : 0.4) * a); ctx.fill();
        TN(dec(r[1] * e) + '%', S.x + S.w - (mob ? 0 : 6), y + (mob ? 4 : 6), { s: mob ? 13 : 19, w: 600, al: 'right', c: rgba(r[2] ? EM : INK, a) });
      }); }
    }
    if (st === 4) {
      const cs = mob ? 62 : 112, f = a * ss((t - 0.2) / 0.6), OPS = L.cmOps;
      const act = RM ? -1 : Math.floor(t / 0.9) % 6;
      OPS.forEach((o, k) => {
        const an = -1.5708 + k * 1.0472, r1 = G.R * 0.6, x = G.cx + r1 * Math.cos(an), y = G.cy + r1 * Math.sin(an), on = act === k;
        seg(G.cx + cs * 0.56 * Math.cos(an), G.cy + cs * 0.56 * Math.sin(an), x, y, rgba(on ? EM : INK, (on ? 0.8 : 0.2) * f), 1.25);
        if (on) glow(x, y, mob ? 12 : 20, EM, 0.3 * f);
        dot(x, y, mob ? 3 : 5, 'rgba(9,11,12,' + f.toFixed(3) + ')'); ring(x, y, mob ? 3 : 5, rgba(on ? EM : INK, (on ? 1 : 0.6) * f), 1.5);
        const up = Math.sin(an) < -0.2, al = 'center', ox = 0, oy = up ? -(mob ? 21 : 33) : (mob ? 15 : 25);
        T(o[0], x + ox, y + oy, { s: mob ? 10.5 : 14, w: 600, al, c: rgba(on ? EM : INK, f) }); T(o[1], x + ox, y + oy + (mob ? 12 : 17), { s: mob ? 9.5 : 12, al, c: rgba(INK4, f) });
      });
      rrect(G.cx - cs / 2, G.cy - cs / 2, cs, cs, cs * 0.2); ctx.fillStyle = 'rgba(13,17,18,' + f.toFixed(3) + ')'; ctx.fill(); ctx.strokeStyle = rgba(EM, 0.6 * f); ctx.lineWidth = 1.5; ctx.stroke();
      TN(dec(69.6) + '%', G.cx, G.cy + (mob ? 2 : 4), { s: mob ? 15 : 26, w: 600, al: 'center', c: rgba(INK, f) });
      T(mob ? L.cmProbes[0] : L.cmProbes[1], G.cx, G.cy + (mob ? 15 : 24), { s: mob ? 9 : 12, al: 'center', c: rgba(INK3, f) });
    }
    if (st === 5) {
      const p = RM ? 1 : eo(t / 8), R = G.R * 1.04, f = a;
      ring(G.cx, G.cy, R, rgba(INK, 0.1 * f), 1);
      ctx.beginPath(); ctx.arc(G.cx, G.cy, R, -1.5708, -1.5708 + 6.28319 * p); ctx.strokeStyle = rgba(EM, 0.85 * f); ctx.lineWidth = mob ? 1.5 : 2; ctx.stroke();
      for (let h = 0; h < 27; h++) { const an = -1.5708 + h / 27.2333 * 6.28319; seg(G.cx + (R - 3) * Math.cos(an), G.cy + (R - 3) * Math.sin(an), G.cx + (R + 3) * Math.cos(an), G.cy + (R + 3) * Math.sin(an), rgba(INK, (h / 27.2333 <= p ? 0.5 : 0.18) * f), 1); }
      const hrs = 27 + 14 / 60, cur = hrs * p, hh = Math.floor(cur), mm = Math.floor((cur - hh) * 60 + 0.001);
      const y0 = G.cy + R + (mob ? 22 : 44);
      TN(hh + L.hm[0] + (mm < 10 ? '0' : '') + mm + L.hm[1], S.x + (mob ? 2 : 6), y0, { s: mob ? 15 : 24, w: 600, c: rgba(INK, f) });
      T(L.mc[2], S.x + (mob ? 2 : 6), y0 + (mob ? 13 : 20), { s: mob ? 10 : 12.5, c: rgba(INK3, f) });
      TN(fmt(2783 * p), S.cx + (mob ? 30 : 60), y0, { s: mob ? 15 : 24, w: 600, al: 'right', c: rgba(EM, f) }); T(L.mc[3], S.cx + (mob ? 30 : 60), y0 + (mob ? 13 : 20), { s: mob ? 10 : 12.5, al: 'right', c: rgba(INK3, f) });
      TN(fmt(605 * p), S.x + S.w - (mob ? 0 : 6), y0, { s: mob ? 15 : 24, w: 600, al: 'right', c: rgba(WARM, f) }); T(L.mc[4], S.x + S.w - (mob ? 0 : 6), y0 + (mob ? 13 : 20), { s: mob ? 10 : 12.5, al: 'right', c: rgba(INK3, f) });
      MC.forEach((j, q) => { const d = now - s4.dead[q]; if (!RM && d > 0.65 && d < 1.5) { const i = s4.ring[j], e = clamp((d - 0.65) / 0.5); seg(G.cx, G.cy, lerp(G.cx, px[i], e), lerp(G.cy, py[i], e), rgba(EM, 0.6 * (1 - clamp((d - 1.2) / 0.3)) * f), 1.25, [3, 4]); } });
    }
  },
  over() {}
};

/* ============ Scene 5: beliefs ============ */
const s5 = { G: {}, sp: [], cas: [], cc: [], lead: 0, cnt: 0, tq: new Float32Array(N) };
(function () {
  for (let q = 0; q < N; q++) s5.tq[q] = q < 717 ? 0.5 + 4.2 * Math.pow(q / 717, 0.9) + (hash(q + 5) - 0.5) * 0.3 : 1e9;
  const r = rnd(45), cnt = [0, 0, 0, 0, 0, 0, 0, 0];
  for (let n = 0; n < N; n++) { const w = cnt.map(c => Math.pow(c + 1, 1.3)); let tot = 0; for (const x of w) tot += x; let p = r() * tot, k = 0; for (; k < 8; k++) { p -= w[k]; if (p <= 0) break; } k = Math.min(k, 7); s5.cas.push([k, cnt[k]]); cnt[k]++; }
  s5.cc = cnt; s5.lead = cnt.indexOf(Math.max.apply(null, cnt));
})();
const W5 = [77, 20, 3], COLL = [0, 100, 100, 100];
function s5geom() {
  const G = s5.G;
  G.cx = S.cx - (mob ? 0 : 50); G.cy = S.cy + (mob ? 12 : 8); G.R = Math.min(S.w, S.h) / 2 - (mob ? 20 : 40); G.a = mob ? 30 : 62; G.turn = mob ? 12.5 : 24; G.r = mob ? 1.7 : 3;
  const b = G.turn / 6.28319, L = Math.PI * (G.R * G.R - G.a * G.a) / G.turn, ds = L / 1023; s5.sp = [];
  for (let q = 0; q < N; q++) { const th = (-G.a + Math.sqrt(G.a * G.a + 2 * b * q * ds)) / b, rad = G.a + b * th; s5.sp.push([G.cx + rad * Math.cos(th - 1.5708), G.cy + rad * Math.sin(th - 1.5708)]); }
  /* cascade: eight options */
  G.pc = Math.min(mob ? 2.9 : 5.8, (S.h - (mob ? 86 : 150)) / 96); G.cg = mob ? 12 : 34; G.cw = 8 * G.pc; G.cx0 = S.cx - (8 * G.cw + 7 * G.cg) / 2; G.cyb = S.y + S.h - (mob ? 30 : 60);
  /* columns of a hundred runs: 5 × 20 */
  G.wq = Math.min(mob ? 12 : 23, (S.h - (mob ? 124 : 250)) / 20, S.w / (mob ? 17 : 20)); G.wyb = S.cy + 9.5 * G.wq + (mob ? 6 : 8);
  G.kq = Math.min(mob ? 11 : 21, (S.h - (mob ? 124 : 250)) / 20, S.w / (mob ? 24 : 26)); G.kyb = S.cy + 9.5 * G.kq + (mob ? 0 : 0);
}
const W5X = w => S.x + S.w * (0.2 + w * 0.3), K5X = w => S.x + S.w * (mob ? 0.12 + w * 0.255 : 0.105 + w * 0.243);
function s5spiral(d) { const G = s5.G; for (let q = 0; q < N; q++) { const i = ORD_CEN[q]; set(i, s5.sp[q][0], s5.sp[q][1], G.r, 0.62, C_INK, d ? hash(q) * 0.2 + q * 0.0003 : 0); tl[i] = 0; } }
function s5cascade() {
  const G = s5.G;
  for (let n = 0; n < N; n++) { const i = PERM[n], c = s5.cas[n][0], lv = s5.cas[n][1], lead = c === s5.lead; set(i, G.cx0 + c * (G.cw + G.cg) + (lv % 8 + 0.5) * G.pc, G.cyb - (Math.floor(lv / 8) + 0.5) * G.pc, G.pc * 0.36, lead ? 0.95 : 0.55, C_INK, 0.15 + 3.2 * Math.pow(n / N, 0.9)); tl[i] = 0; }
}
function s5cols(n, X, q5, yb, vals, colOn, kind) {
  const used = new Uint8Array(N);
  for (let w = 0; w < n; w++) {
    const ids = ORD_COL.slice(Math.round(w * (N - 100) / (n - 1)), Math.round(w * (N - 100) / (n - 1)) + 100).sort((a, b) => ROW[b] - ROW[a] || COL[a] - COL[b]), cx = X(w);
    ids.forEach((i, q) => {
      used[i] = 1; const on = q < vals[w]; let a = on ? 0.98 : 0, c = on ? colOn : C_INK, r = q5 * 0.3;
      if (kind === 0 && w === 2 && on) a = 0.5; if (kind === 1) { if (!on) a = 0.17; if (w === 3) { a = 0.85; r = q5 * 0.24; } }
      set(i, cx + ((q % 5) - 2) * q5, yb - Math.floor(q / 5) * q5, r, a, c, 0.1 + w * 0.25 + q * 0.004); tl[i] = 0;
    });
  }
  for (let i = 0; i < N; i++) if (!used[i]) rest(i, 0.04, 0);
}
function s5page(f, warn) {
  const G = s5.G, w = mob ? 27 : 54, h = mob ? 35 : 68, x = G.cx - w / 2, y = G.cy - h / 2;
  rrect(x, y, w, h, mob ? 4 : 7); ctx.fillStyle = 'rgba(13,17,18,' + f.toFixed(3) + ')'; ctx.fill(); ctx.strokeStyle = rgba(INK, 0.4 * f); ctx.lineWidth = 1.25; ctx.stroke();
  const lw = [0.78, 0.62, 0.78, 0.7, 0.5, 0.66], pad = w * 0.16;
  for (let q = 0; q < 6; q++) { const yy = y + h * (0.17 + q * 0.133), isW = q === 2; if (isW && warn > 0.02) { glow(G.cx, yy, w * 0.9, EM, 0.3 * warn * f); seg(x + pad, yy, x + pad + (w - pad * 2) * warn, yy, rgba(EM, f), mob ? 2 : 3); } else if (!isW) seg(x + pad, yy, x + pad + (w - pad * 2) * lw[q], yy, rgba(INK, 0.3 * f), mob ? 1.5 : 2.5); }
}
SC[5] = {
  st: 0, t0: 0,
  enter(st, fresh) {
    stiff = 64; s5geom(); hovSet = null; const G = s5.G;
    if (st <= 2) s5spiral(fresh); else if (st === 3) s5cascade(); else if (st === 4) s5cols(3, W5X, G.wq, G.wyb, W5, C_EM, 0); else s5cols(4, K5X, G.kq, G.kyb, COLL, C_WARM, 1);
  },
  tick(t, st) {
    const G = s5.G;
    if (st > 2) return;
    let cnt = 0;
    for (let q = 0; q < N; q++) {
      const i = ORD_CEN[q]; let inf = false, hot = false;
      if (st === 1) { inf = RM ? q < 717 : t > s5.tq[q]; hot = inf && t - s5.tq[q] < 0.28; }
      else if (st === 2) { if (RM) inf = q < 10; else if (t < 0.9) inf = q < 717 && t < 0.75 * (q / 717); else { const t2 = 1.5 + q * 0.18; inf = q < 10 && t > t2; hot = inf && t - t2 < 0.3; } }
      if (inf) { cnt++; sty(i, hot ? G.r * 1.7 : G.r * 1.08, 0.98, C_WARM); } else sty(i, G.r, 0.5, C_INK);
    }
    s5.cnt = cnt;
  },
  under(a) {
    const st = this.st, G = s5.G, t = T_OF(5), hx_ = S.x + (mob ? 2 : 10);
    if (st <= 2) {
      T(L.mv[0], hx_, S.y + (mob ? 12 : 20), { s: mob ? 11 : 13, w: 600, c: rgba(INK2, a) });
      if (st >= 1) {
        const pct = Math.round(s5.cnt / N * 100), xr = mob ? S.x + 2 : S.x + S.w - 2, al = mob ? 'left' : 'right', y = S.y + (mob ? 62 : 156);
        TN(pct + '%', xr, y, { s: mob ? 34 : 88, w: 600, al, c: rgba(st === 2 && t > 0.9 ? EM : WARM, a) });
        const l1 = st === 1 ? L.mv[1] : L.mv[3], l2 = st === 1 ? L.mv[2] : L.mv[4];
        T(l1, xr, y + (mob ? 15 : 28), { s: mob ? 10.5 : 14, al, c: rgba(INK3, a) }); T(l2, xr, y + (mob ? 28 : 47), { s: mob ? 10.5 : 14, al, c: rgba(INK3, a) });
      }
    } else if (st === 3) {
      T(L.ml[0], hx_, S.y + (mob ? 12 : 20), { s: mob ? 11 : 13, w: 600, c: rgba(INK2, a) });
      T(L.ml[1], hx_, S.y + (mob ? 27 : 40), { s: mob ? 10.5 : 12.5, c: rgba(INK4, a) });
      seg(G.cx0 - 8, G.cyb + 1, G.cx0 + 8 * G.cw + 7 * G.cg + 8, G.cyb + 1, rgba(INK, 0.25 * a), 1);
      T(L.ml[2], S.cx, G.cyb + (mob ? 15 : 23), { s: mob ? 10 : 12.5, al: 'center', c: rgba(INK4, a) });
      const f = a * (RM ? 1 : ss((t - 2.2) / 0.7)), x = G.cx0 + s5.lead * (G.cw + G.cg) + G.cw / 2, top = G.cyb - Math.ceil(s5.cc[s5.lead] / 8) * G.pc, right = s5.lead < 4, ox = (G.cw / 2 + (mob ? 8 : 18)) * (right ? 1 : -1);
      if (f > 0.01) { T(L.ml[3], x + ox, top + (mob ? 16 : 30), { s: mob ? 17 : 32, w: 600, al: right ? 'left' : 'right', c: rgba(INK, f) }); T(mob ? L.ml[4] : L.ml[5], x + ox, top + (mob ? 30 : 54), { s: mob ? 10 : 13.5, al: right ? 'left' : 'right', c: rgba(INK3, f) }); T(mob ? L.ml[6] : L.ml[7], x + ox, top + (mob ? 43 : 73), { s: mob ? 10 : 13.5, al: right ? 'left' : 'right', c: rgba(INK3, f) }); }
    } else if (st === 4) {
      const f = a * ss((t - 0.2) / 0.5), LB = L.cyStages, NM = ['77%', '20%', '0–3%'], q5 = G.wq, top = G.wyb - 19 * q5;
      T(L.cy[0], hx_, S.y + (mob ? 12 : 20), { s: mob ? 11 : 13, w: 600, c: rgba(INK2, a) });
      T(mob ? L.cy[1] : L.cy[2], hx_, S.y + (mob ? 27 : 40), { s: mob ? 10.5 : 12.5, c: rgba(INK4, a) });
      for (let w = 0; w < 3; w++) {
        const cx = W5X(w), fq = f * ss((t - 0.3 - w * 0.3) / 0.5), x0 = cx - 2 * q5 - q5 * 0.36;
        ctx.strokeStyle = rgba(INK, 0.3 * fq); ctx.lineWidth = 1; ctx.beginPath(); for (let q = 0; q < 100; q++) { const x = cx + ((q % 5) - 2) * q5, y = G.wyb - Math.floor(q / 5) * q5; ctx.moveTo(x + q5 * 0.36, y); ctx.arc(x, y, q5 * 0.36, 0, 6.2832); } ctx.stroke();
        TN(NM[w], x0, top - (mob ? 12 : 24), { s: mob ? 21 : 42, w: 600, c: rgba(EM, fq) });
        T(LB[w], x0, G.wyb + (mob ? 19 : 32), { s: mob ? 10.5 : 14, w: 600, c: rgba(INK2, fq) });
        if (w < 2) T('→', (W5X(w) + W5X(w + 1)) / 2, G.wyb - 9.5 * q5 + 6, { s: mob ? 14 : 24, al: 'center', c: rgba(INK4, f) });
      }
      const yl = G.wyb + (mob ? 38 : 62);
      dot(hx_ + 4, yl - 4, mob ? 3 : 4.4, rgba(EM, f)); T(L.cy[3], hx_ + 13, yl, { s: mob ? 10 : 12.5, c: rgba(INK2, f) });
      const x2 = hx_ + (mob ? 108 : 160); ring(x2 + 4, yl - 4, mob ? 3 : 4.4, rgba(INK, 0.6 * f), 1); T(mob ? L.cy[4] : L.cy[5], x2 + 13, yl, { s: mob ? 10 : 12.5, c: rgba(INK2, f) });
    } else {
      const f = a * ss((t - 0.2) / 0.5), NM = ['0%', '100%', '100%', '86%'], LB = [mob ? 'Sonnet 4.5' : 'Claude Sonnet 4.5', 'GPT-4.1', mob ? 'Gemini 2.5' : 'Gemini 2.5 Flash', mob ? L.col[0] : L.col[1]], q5 = G.kq, top = G.kyb - 19 * q5;
      T(mob ? L.col[2] : L.col[3], hx_, S.y + (mob ? 12 : 20), { s: mob ? 11 : 13, w: 600, c: rgba(INK2, a) });
      if (!mob) T(L.col[4], hx_, S.y + 40, { s: 12.5, c: rgba(INK4, a) });
      for (let w = 0; w < 4; w++) {
        const cx = K5X(w), x0 = cx - 2 * q5 - q5 * 0.3, fq = f * ss((t - 0.25 - w * 0.25) / 0.5);
        TN(NM[w], x0, top - (mob ? 12 : 24), { s: mob ? 17 : 38, w: 600, c: rgba(w === 0 ? INK : w === 3 ? EM : WARM, fq) });
        T(LB[w], x0, G.kyb + (mob ? 19 : 32), { s: mob ? 9 : 13.5, w: 600, c: rgba(INK2, fq) });
        if (w === 3) {
          T(mob ? L.col[5] : L.col[6], x0, G.kyb + (mob ? 31 : 51), { s: mob ? 9 : 12, c: rgba(INK4, fq) }); if (!mob) { T('DeepSeek-V4-Flash,', x0, G.kyb + 68, { s: 12, c: rgba(INK4, fq) }); T(L.col[7], x0, G.kyb + 85, { s: 12, c: rgba(INK4, fq) }); }
          ctx.strokeStyle = rgba(EM, 0.95 * fq); ctx.lineWidth = mob ? 1 : 1.5; ctx.beginPath(); for (let q = 0; q < 86; q++) { const x = cx + ((q % 5) - 2) * q5, y = G.kyb - Math.floor(q / 5) * q5; ctx.moveTo(x + q5 * 0.4, y); ctx.arc(x, y, q5 * 0.4, 0, 6.2832); } ctx.stroke();
        }
      }
      const xd = (K5X(2) + K5X(3)) / 2; seg(xd, top - (mob ? 30 : 60), xd, G.kyb + (mob ? 34 : 70), rgba(INK, 0.12 * f), 1);
    }
  },
  over(a) {
    const st = this.st, G = s5.G, t = T_OF(5); if (st > 2) return;
    const fw = st === 2 ? (RM ? 1 : ss((t - 0.8) / 0.5)) : 0;
    s5page(a, fw);
    if (st === 2 && fw > 0.02) { const px_ = G.cx + (mob ? 16 : 31), py_ = G.cy - (mob ? 5 : 9), ex = G.cx + G.a + (mob ? 26 : 64), ey = py_ - (mob ? 34 : 70); seg(px_, py_, ex, ey, rgba(EM, 0.7 * fw * a), 1.25); tag(mob ? L.mv[5] : L.mv[6], ex, ey, { s: mob ? 10 : 12.5, c: rgba(EM, fw * a), a: fw * a, stroke: rgba(EM, 0.4 * fw * a) }); }
  }
};

/* ============ Scene 6: the full-frame map of works ============ */
const WORKS = DATA.works, NW = WORKS.length;
/* notable works: they sit on top of their month columns and lead the idle tour */
const NOTES = [["2508.17536", 0], ["wiz.io", 0], ["2608.10218", 1], ["2609.26781", 1], ["navier-stokes", 1], ["2610.16120", 1], ["safely-scaling", 1], ["avalonm1", 1]].map(n => ({ w: WORKS.findIndex(x => x[5].indexOf(n[0]) >= 0), side: n[1] })).filter(n => n.w >= 0);
const isNote = new Uint8Array(NW); NOTES.forEach(n => { isNote[n.w] = 1; });
const s6 = { G: {}, who: new Int16Array(NW), role: new Int16Array(N).fill(-1), col: new Int16Array(NW), k: new Int16Array(NW), hl: -1, tk: -1, tw: -1, cnt: new Array(25).fill(0), ground: [] };
(function () {
  const colOf = m => m === -1 ? 0 : m === -2 ? 1 : m + 2;
  const order = [...Array(NW).keys()].sort((a, b) => colOf(WORKS[a][3]) - colOf(WORKS[b][3]) || isNote[a] - isNote[b] || WORKS[a][4] - WORKS[b][4] || a - b);
  for (const w of order) { const c = colOf(WORKS[w][3]); s6.col[w] = c; s6.k[w] = s6.cnt[c]++; }
  const sub = PERM.slice(120, 120 + NW).sort((a, b) => COL[a] - COL[b] || ROW[a] - ROW[b]);
  order.forEach((w, q) => { s6.who[w] = sub[q]; s6.role[sub[q]] = w; });
  for (const i of ORD_COL) if (s6.role[i] < 0) s6.ground.push(i);
  const th = new Array(10).fill(0); let fr = 0; for (const w of WORKS) { th[w[4]]++; if (w[6]) fr++; }
  const lg = $('legend'); lg.textContent = '';
  THEMES.forEach((t, k) => { const li = D.createElement('li'); li.style.setProperty('--c', 'rgb(' + t[1].join(',') + ')'); li.innerHTML = '<i></i><span>' + t[0] + '</span><em>' + th[k] + '</em>'; li.dataset.k = k; li.tabIndex = 0; lg.appendChild(li); });
  const lf = D.createElement('li'); lf.className = 'fresh'; lf.innerHTML = '<i></i><span>' + L.freshLegend + '</span><em>' + fr + '</em>'; lf.dataset.k = 99; lf.tabIndex = 0; lg.appendChild(lf);
  const setHl = k => { s6.hl = k; lg.classList.toggle('hl', k >= 0); [...lg.children].forEach(li => li.classList.toggle('on', +li.dataset.k === k)); kick(); };
  [...lg.children].forEach(li => {
    li.addEventListener('mouseenter', () => { if (!mouse.touch) setHl(+li.dataset.k); }); li.addEventListener('mouseleave', () => { if (!mouse.touch) setHl(-1); });
    li.addEventListener('focus', () => setHl(+li.dataset.k)); li.addEventListener('blur', () => setHl(-1));
    li.addEventListener('click', () => { if (mouse.touch) setHl(s6.hl === +li.dataset.k ? -1 : +li.dataset.k); });
  });
})();
const TOUR = NOTES.filter(n => n.side === 1).map(n => n.w);
const s6info = w => ({ t: WORKS[w][0], m: (WORKS[w][1] ? WORKS[w][1] + ' · ' : '') + WORKS[w][2], th: THEMES[WORKS[w][4]][0], c: 'rgb(' + THEMES[WORKS[w][4]][1].join(',') + ')', url: WORKS[w][5] });
function s6geom() {
  const G = s6.G;
  if (mob) { G.x0 = S.x; G.wd = S.w; G.yb = S.y + S.h - 38; G.per = 2; }
  else { G.x0 = Math.max(48, (W - 1280) / 2 + 16); G.wd = W - G.x0 - Math.max(40, G.x0 - 40); G.yb = H - 92; G.per = 3; }
  G.cw = G.wd / 26.6; G.gi = G.cw * 0.12; G.p = (G.cw - G.gi) / G.per; G.r = G.p * 0.42;
  G.cx = c => G.x0 + (c === 0 ? 0 : c === 1 ? 1 : c + 1.6) * G.cw;
  let mx = 0; for (let c = 2; c < 25; c++) mx = Math.max(mx, s6.cnt[c]); G.tall = Math.ceil(mx / G.per) * G.p;
}
const s6pos = w => { const G = s6.G, c = s6.col[w], k = s6.k[w], per = c === 1 ? G.per * 2 : G.per; return [G.cx(c) + G.gi / 2 + G.p / 2 + (k % per) * G.p, G.yb - G.p / 2 - Math.floor(k / per) * G.p - 2]; };
SC[6] = {
  st: 0, t0: 0,
  enter(st, fresh) {
    stiff = 60; s6geom(); const G = s6.G;
    for (let w = 0; w < NW; w++) { const p = s6pos(w), i = s6.who[w]; set(i, p[0], p[1], G.r, 0.95, C_TH + WORKS[w][4], fresh ? 0.05 + s6.col[w] * 0.022 + s6.k[w] * 0.004 : 0); tl[i] = 0; }
    const rows = mob ? 3 : 2, per = Math.ceil(s6.ground.length / rows), gw = G.wd / per;
    s6.ground.forEach((i, q) => { set(i, G.x0 + (q % per + 0.5) * gw, G.yb + (mob ? 4 : 7) + Math.floor(q / per) * (mob ? 2.3 : 3.6), mob ? 0.75 : 1.2, 0.22, C_INK, fresh ? hash(i) * 0.5 : 0); tl[i] = 0; });
    hovSet = { ids: Array.from(s6.who), info: s6info, rad: mob ? 16 : 12, auto: true }; s6.tk = -1;
  },
  tick(t) {
    const G = s6.G, hl = s6.hl;
    const idle = mouse.touch ? !hovPin : (now - mouse.moved > 3.2 && hov < 0);
    let tw = -1;
    if (!RM && idle && t > 2.6 && TOUR.length && hl < 0) { const k = Math.floor((t - 2.6) / 3.2) % TOUR.length; tw = TOUR[k]; if (k !== s6.tk) { s6.tk = k; const i = s6.who[tw]; if (!mob) showTip(s6info(tw), px[i], py[i] + 46, false); } }
    else if (s6.tk >= 0) { s6.tk = -1; if (hov < 0 && !hovPin) hideTip(); }
    s6.tw = tw;
    for (let w = 0; w < NW; w++) {
      const i = s6.who[w]; let a = 0.95, r = G.r;
      if (hl >= 0 && (hl === 99 ? !WORKS[w][6] : WORKS[w][4] !== hl)) a = 0.12;
      if (w === hov || w === tw) { r = G.r * 1.5; a = 1; }
      sty(i, r, a, C_TH + WORKS[w][4]);
    }
  },
  under(a) {
    const G = s6.G, MN = L.mn, yl = G.yb + (mob ? 22 : 34);
    if (mob) T(fmt(NW) + L.mapMob, S.x + 2, S.y + 12, { s: 11, w: 600, c: rgba(INK2, a) });
    for (let m = 0; m < 23; m++) {
      const x = G.cx(m + 2) + G.cw / 2, mm = m % 12;
      if (mob ? mm % 6 === 0 : true) T(MN[mm], x, yl, { s: mob ? 9.5 : 11.5, al: 'center', c: rgba(mm % 3 === 0 || mob ? INK3 : INK4, a) });
      if (mm === 0) { T(String(2025 + Math.floor(m / 12)), x, yl + (mob ? 13 : 19), { s: mob ? 10 : 13, w: 600, al: 'center', c: rgba(INK2, a) }); if (m > 0) seg(G.cx(m + 2) - G.gi / 2, G.yb - G.tall * 0.6, G.cx(m + 2) - G.gi / 2, G.yb - 4, rgba(INK, 0.1 * a), 1, [2, 4]); }
    }
    if (!mob) { T(L.pre2025[0], G.cx(0) + G.cw / 2, yl, { s: 11.5, al: 'center', c: rgba(INK4, a) }); T(L.pre2025[1], G.cx(0) + G.cw / 2, yl + 16, { s: 11.5, al: 'center', c: rgba(INK4, a) }); }
    T(L.noDate[0], G.cx(1) + G.cw, yl, { s: mob ? 8.5 : 11.5, al: 'center', c: rgba(INK4, a) }); T(L.noDate[1], G.cx(1) + G.cw, yl + (mob ? 11 : 16), { s: mob ? 8.5 : 11.5, al: 'center', c: rgba(INK4, a) });
    /* fresh works: a bracket under October and November */
    const xa = G.cx(23) + G.gi / 2, xb = G.cx(24) + G.cw - G.gi / 2, yf = yl + (mob ? 7 : 9);
    ctx.beginPath(); ctx.moveTo(xa, yf - 3); ctx.lineTo(xa, yf); ctx.lineTo(xb, yf); ctx.lineTo(xb, yf - 3); ctx.strokeStyle = rgba(WARM, 0.75 * a); ctx.lineWidth = 1; ctx.stroke();
    T(L.fresh, (xa + xb) / 2, yf + (mob ? 11 : 14), { s: mob ? 9 : 11.5, al: 'center', c: rgba(INK2, a) });
  },
  over(a) {
    const hl = s6.hl;
    for (let w = 0; w < NW; w++) {
      if (!WORKS[w][6]) continue; const i = s6.who[w]; if (aa[i] < 0.3 && hl !== 99) continue;
      ring(px[i], py[i], rr[i] + (mob ? 1.5 : 2.6), rgba(WARM, 0.95 * a), mob ? 1 : 1.4);
    }
    const sel = hov >= 0 && curSc === 6 ? hov : s6.tw;
    if (sel >= 0 && sel !== undefined && curSc === 6) { const i = s6.who[sel]; ring(px[i], py[i], rr[i] + (mob ? 3.5 : 5.5), rgba(INK, a), 1.5); }
  }
};

/* ============ Scene 7: finale ============ */
const DIG = [['00100', '01100', '00100', '00100', '00100', '00100', '01110'], ['01110', '10001', '00001', '00010', '00100', '01000', '11111'], ['11110', '00001', '00001', '01110', '00001', '00001', '11110'], ['00010', '00110', '01010', '10010', '11111', '00010', '00010']];
const VOID = [[3, 3], [20, 3], [3, 18], [20, 18]];
const s7 = { m: new Int8Array(N) };
(function () { for (let i = 0; i < N; i++) { const c = COL[i], r = ROW[i]; VOID.forEach((v, k) => { if (c >= v[0] && c < v[0] + 9 && r >= v[1] && r < v[1] + 11) { const dc = c - v[0] - 2, dr = r - v[1] - 2; s7.m[i] = (dc >= 0 && dc < 5 && dr >= 0 && dr < 7 && DIG[k][dr][dc] === '1') ? 2 : 1; } }); } })();
SC[7] = {
  st: 0, t0: 0,
  enter(st, fresh) {
    stiff = 48; hovSet = null;
    for (let i = 0; i < N; i++) { const m = s7.m[i]; set(i, hx[i], hy[i], m === 2 ? rd * 1.45 : rd, m === 2 ? 1 : m === 1 ? 0 : 0.45, m === 2 ? C_EM : C_INK, fresh ? hash(i) * 0.4 : 0); tl[i] = 0; }
  },
  tick(t) {
    if (RM) return;
    for (let i = 0; i < N; i++) { const m = s7.m[i]; if (m === 0) { ta[i] = 0.42 + 0.12 * Math.sin(t * 0.7 + (COL[i] + ROW[i]) * 0.22); if (at[i]) na[i] = ta[i]; } }
  },
  under(a) {
    VOID.forEach(v => { const x = hx[0] + (v[0] - 0.5) * g, y = hy[0] + (v[1] - 0.5) * g; rrect(x, y, 9 * g, 11 * g, g * 0.9); ctx.strokeStyle = rgba(EM, 0.24 * a); ctx.lineWidth = 1; ctx.stroke(); });
  },
  over() {}
};

/* ============ Frame assembly ============ */
/* desired figure height on a phone, as a fraction of width: per scene and step */
const MH = [[1.08], [1.2], [1.15, 1.15, 1.15, 1.22, 1.15, 0.98], [1.04, 1.04, 1.1, 1.04, 0.92, 0.9, 1.0, 1.2], [1.14], [1.12, 1.12, 1.12, 1.1, 1.08, 1.08, 1.1], [0.86], [1.05]];
function setStage() {
  if (mob) {
    /* on a phone the figure takes all the space between the header and the current step's card */
    const ch = stepIdx >= 0 ? steps[stepIdx].card.offsetHeight : (aEl.offsetHeight || 280), free = H - 62 - ch - 26;
    const sc = stepIdx >= 0 ? steps[stepIdx].sc : 0, st = stepIdx >= 0 ? steps[stepIdx].st : 0, want = (MH[sc][st] || MH[sc][0]) * (W - 28);
    S.x = 14; S.w = W - 28; S.y = 60; S.h = Math.round(clamp(Math.min(free, want), H * 0.3, H * 0.62));
    root.style.setProperty('--ct', (S.y + S.h + 12) + 'px');
  } else {
    const left = Math.max(48, (W - 1280) / 2 + 16), colw = clamp(W * 0.27, 300, 388), gap = clamp(W * 0.03, 28, 44);
    S.x = Math.round(left + colw + gap); S.w = Math.round(W - S.x - Math.max(40, left - 40)); S.y = 92; S.h = H - 92 - 64;
  }
  S.cx = S.x + S.w / 2; S.cy = S.y + S.h / 2; g = Math.min(S.w, S.h) / 33.5; rd = mob ? 1.25 : 2.0;
  for (let i = 0; i < N; i++) { hx[i] = S.cx + (COL[i] - 15.5) * g; hy[i] = S.cy + (ROW[i] - 15.5) * g; }
}
function resize() {
  W = innerWidth; H = innerHeight; mob = W < 760; TS = mob ? 1.05 : 1.1;
  DPR = Math.min(devicePixelRatio || 1, 2); cv.width = Math.round(W * DPR); cv.height = Math.round(H * DPR);
  setStage();
  root.style.setProperty('--sx', S.x + 'px'); root.style.setProperty('--sw', S.w + 'px');
  measure();
  if (key >= 0) { SC[curSc].enter(curSt, false); }
  kick();
}
function frame(ts) {
  raf = 0; now = ts / 1000; dt = clamp(now - last, 0.001, 0.05); last = now;
  update();
  const sc = curSc;
  SC[sc].tick(T_OF(sc), curSt);
  for (let i = 0; i < 8; i++) vis[i] = RM ? (i === sc ? 1 : 0) : vis[i] + ((i === sc ? 1 : 0) - vis[i]) * Math.min(1, dt * 5.5);
  physics(); hoverFrame();
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0); ctx.clearRect(0, 0, W, H);
  for (let i = 0; i < 8; i++) if (vis[i] > 0.01) SC[i].under(vis[i]);
  drawAgents(); drawParts();
  for (let i = 0; i < 8; i++) if (vis[i] > 0.01) SC[i].over(vis[i]);
  if (!RM && !D.hidden) raf = requestAnimationFrame(frame);
}
function kick() { if (!raf) raf = requestAnimationFrame(frame); }
(function start() {
  W = innerWidth; H = innerHeight;
  resize();
  for (let i = 0; i < N; i++) { px[i] = tx[i] = hx[i]; py[i] = ty[i] = hy[i]; rr[i] = tr[i] = rd; aa[i] = 0; ta[i] = 0; }
  if (RM) setMode(0);
  let rt = 0;
  addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(resize, 120); });
  addEventListener('scroll', kick, { passive: true });
  addEventListener('load', () => { measure(); kick(); });
  D.addEventListener('visibilitychange', () => { if (D.hidden) { if (raf) cancelAnimationFrame(raf); raf = 0; } else { last = performance.now() / 1000; kick(); } });
  if (D.fonts && D.fonts.ready) D.fonts.ready.then(() => { measure(); kick(); });
  kick();
})();

})();