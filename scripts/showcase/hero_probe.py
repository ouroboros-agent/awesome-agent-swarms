#!/usr/bin/env python3
"""Measure and photograph the first screen of the Field page: the six-agent figure between the intro and the tabs.

  python scripts/showcase/hero_probe.py OUT --page ru=site/ru/index.html --page en=site/en/index.html [--label NAME]
         [--engines webkit,chromium] [--sizes NAME,NAME] [--modes 0,1,2,3] [--states] [--strict]

For every engine, language and screen size the page is opened from its file with the deterministic clock of
scripts/showcase/vclock.js, each of the four schemes is selected and run to the moment all its labels are shown, and
one frame is photographed and measured. On a screen where the first screen is taller than the window (--hx > 0 in the
page), the frame is also taken after scrolling that excess, where the figure and its caption are both in view.

What is measured in each frame (CSS px, in the viewport):
  node_r      radius of the six agents' circles (median of the filled circles the page draws)
  ink         bounding box of what the canvas really shows (alpha above ~12%)
  gap         the space between the last line of the intro and the tab row
  over_intro  how far canvas ink reaches above the bottom of the intro text (0 = clear)
  over_tabs   how far canvas ink reaches below the top of the tab row (0 = clear)
  clashes     pairs of canvas labels whose boxes intersect, and labels that touch an agent's circle

  ink_on_intro, ink_on_caption   canvas ink behind the page's own text lines (intro; tabs and caption), px²
  text_on_text  pairs of intro lines and tab or caption lines that overlap each other

--states adds the first screen in reduced motion, after turning the phone and back, with a browser bar that hides, on
arrival at the address of its second state, without JavaScript, and under the keyboard where its sheet is taller than the
window: Tab to the tabs and the caption's source link moves the page, never the pin alone (real time, no clock).
--strict exits 1 unless every judged frame keeps node_r >= 14, has no canvas ink behind text, no text over text, no
clashing labels, no error and a running animation, and every state check passes.
Output: OUT/<label>/shots/*.png, OUT/<label>/hero_probe.json, OUT/<label>/HERO_PROBE.md.
"""
import argparse
import json
import os
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stage  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

# name: (width, height, device scale, phone?)   visible browser windows, not screen sizes
SIZES = {
    "iphone15pro-393x659": (393, 659, 3, True),     # Playwright's "iPhone 15 Pro": Safari with its bars shown
    "owner-378x575": (378, 575, 3, True),           # estimated from the owner's screenshot of 15 November 2026
    "iphone-se-375x548": (375, 548, 2, True),
    "android-360x640": (360, 640, 3, True),
    "inapp-390x664": (390, 664, 3, True),           # the size scripts/qa_field.py calls the in-app browser of Telegram
    "full-390x844": (390, 844, 3, True),
    "promax-430x739": (430, 739, 3, True),
    "narrow-320x568": (320, 568, 2, True),
    "short-375x480": (375, 480, 2, True),
    "fold-280x653": (280, 653, 3, True),            # narrower than any current phone but a folded Galaxy Fold: measured, not judged
    "land-667x375": (667, 375, 2, True),            # a phone held sideways, narrower than 760 px
    "land-734x343": (734, 343, 3, True),            # Playwright's "iPhone 15 landscape": the published page stops drawing here
    "land-844x390": (844, 390, 3, True),            # a phone held sideways, 760 px or wider (the published page uses its desktop layout)
    "land-932x430": (932, 430, 3, True),
    "desk-760x500": (760, 500, 1, False),           # the smallest window that still gets the desktop layout
    "desk-1024x520": (1024, 520, 1, False),
    "desk-760x900": (760, 900, 1, False),           # the narrowest desktop layout, tall
    "ipad-768x1024": (768, 1024, 2, False),         # tablets upright and on their side: the desktop layout at its narrowest
    "ipad-820x1180": (820, 1180, 2, False),
    "ipad-1024x768": (1024, 768, 2, False),
    "ipad-1180x820": (1180, 820, 2, False),
    "desk-1280x720": (1280, 720, 1, False),
    "desk-1440x900": (1440, 900, 1, False),
}
UNJUDGED = ("fold-280x653",)      # at 280 px the width limits the figure: its longest chip still reaches a neighbouring circle
# seconds into each scheme at which all of its labels are on screen (the schemes last 7.6, 6.6, 7.8 and 7.0 s)
SHOW = (6.5, 3.8, 5.7, 3.0)

HOOK = r"""(() => {
  const C = CanvasRenderingContext2D.prototype, P = window.__probe = { cur: { arcs: [], texts: [] }, last: { arcs: [], texts: [] } };
  const k = c => c.canvas.width / Math.max(1, c.canvas.clientWidth);
  const cr = C.clearRect; C.clearRect = function (x, y, w, h) { if (w * k(this) >= this.canvas.width - 2) { P.last = P.cur; P.cur = { arcs: [], texts: [] }; P.frames = (P.frames || 0) + 1; } return cr.apply(this, arguments); };
  const bp = C.beginPath; C.beginPath = function () { this.__arc = null; return bp.apply(this, arguments); };
  const ar = C.arc; C.arc = function (x, y, r) { const m = this.getTransform(), s = k(this); this.__arc = [(m.a * x + m.c * y + m.e) / s, (m.b * x + m.d * y + m.f) / s, r * Math.hypot(m.a, m.b) / s]; return ar.apply(this, arguments); };
  const fl = C.fill; C.fill = function () { if (this.__arc && this.__arc[2] >= 1 && typeof this.fillStyle === 'string') P.cur.arcs.push(this.__arc.map(v => Math.round(v * 100) / 100)); return fl.apply(this, arguments); };
  const ft = C.fillText; C.fillText = function (s, x, y) {
    const m = this.getTransform(), sc = k(this), w = this.measureText(s).width, fs = parseFloat(this.font.match(/([\d.]+)px/)[1]);
    const l = this.textAlign === 'right' ? x - w : this.textAlign === 'center' ? x - w / 2 : x;
    const t = this.textBaseline === 'middle' ? y - fs * 0.5 : y - fs * 0.78, b = this.textBaseline === 'middle' ? y + fs * 0.5 : y + fs * 0.22;
    const al = /rgba\([^)]*,\s*([\d.]+)\)$/.exec(String(this.fillStyle)); const a = al ? +al[1] : 1;
    const px = this.textBaseline === 'middle' ? 7 * sc : 0, py = this.textBaseline === 'middle' ? 4 * sc : 0;
    if (a >= 0.25 && !m.b && !m.c) P.cur.texts.push({ s: String(s), l: (m.a * l + m.e - px) / sc, t: (m.d * t + m.f - py) / sc, r: (m.a * (l + w) + m.e + px) / sc, b: (m.d * b + m.f + py) / sc });
    return ft.apply(this, arguments);
  };
})()"""

MEASURE = r"""() => {
  const q = id => document.getElementById(id), copy = q('hCopy'), cap = q('hCap'), pin = q('pin'), cv = q('field');
  const lines = el => { const r = document.createRange(); r.selectNodeContents(el); return [...r.getClientRects()].filter(b => b.width > 1 && b.height > 1); };
  const intro = [...copy.children].flatMap(lines), tabs = cap.querySelector('.tabs').getBoundingClientRect();
  const introBottom = Math.max(...intro.map(b => b.bottom)), introTop = Math.min(...intro.map(b => b.top));
  const on = cap.querySelector('.mode.on'), capText = on ? [...on.querySelectorAll('p')].flatMap(lines) : [];
  /* what the canvas shows */
  const s = cv.width / cv.clientWidth, w = cv.width, h = cv.height, d = cv.getContext('2d').getImageData(0, 0, w, h).data;
  let x0 = w, y0 = h, x1 = -1, y1 = -1, overIntro = 0, overTabs = 0;
  const iB = introBottom * s, tT = tabs.top * s;
  for (let y = 0; y < h; y++) { const o = y * w * 4; for (let x = 0; x < w; x++) { if (d[o + x * 4 + 3] > 30) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; } } }
  const ink = x1 < 0 ? null : [x0 / s, y0 / s, (x1 + 1) / s, (y1 + 1) / s].map(v => Math.round(v * 10) / 10);
  const under = rects => { let n = 0; for (const b of rects) { const xa = Math.max(0, Math.floor(b.left * s)), xb = Math.min(w, Math.ceil(b.right * s)), ya = Math.max(0, Math.floor((b.top + 2) * s)), yb = Math.min(h, Math.ceil((b.bottom - 2) * s)); for (let y = ya; y < yb; y++) { const o = y * w * 4; for (let x = xa; x < xb; x++) if (d[o + x * 4 + 3] > 30) n++; } } return Math.round(n / (s * s)); };
  const tabText = [...cap.querySelectorAll('.tab')].flatMap(lines);
  const P = window.__probe.last, big = P.arcs.map(a => a[2]).sort((a, b) => b - a).slice(0, 6), nodeR = big.length ? big[Math.floor(big.length / 2)] : 0;
  /* canvas labels: a clash is two label boxes that intersect, or a label box that reaches into an agent's circle */
  const T = P.texts.filter(t => !/^\d$/.test(t.s)), clashes = [];
  for (let i = 0; i < T.length; i++) for (let j = i + 1; j < T.length; j++) { const a = T[i], b = T[j]; if (a.l < b.r - 0.5 && b.l < a.r - 0.5 && a.t < b.b - 0.5 && b.t < a.b - 0.5) clashes.push(a.s + ' × ' + b.s); }
  const circ = P.arcs.filter(a => a[2] >= Math.max(3, nodeR * 0.8));
  for (const t of T) for (const c of circ) { const nx = Math.max(t.l, Math.min(c[0], t.r)), ny = Math.max(t.t, Math.min(c[1], t.b)); if (Math.hypot(nx - c[0], ny - c[1]) < c[2] - 0.5) { clashes.push(t.s + ' × circle'); break; } }
  const cs = getComputedStyle(document.documentElement);
  return {
    W: innerWidth, H: innerHeight, dpr: devicePixelRatio, y: scrollY, pinH: pin.offsetHeight, hx: parseFloat(cs.getPropertyValue('--hx')) || 0,
    intro: [Math.round(introTop * 10) / 10, Math.round(introBottom * 10) / 10], tabsTop: Math.round(tabs.top * 10) / 10, tabsBottom: Math.round(tabs.bottom * 10) / 10,
    capTextBottom: capText.length ? Math.round(Math.max(...capText.map(b => b.bottom)) * 10) / 10 : null,
    gap: Math.round((tabs.top - introBottom) * 10) / 10, ink, node_r: Math.round(nodeR * 10) / 10,
    over_intro: ink ? Math.max(0, Math.round((introBottom - ink[1]) * 10) / 10) : 0, over_tabs: ink ? Math.max(0, Math.round((ink[3] - tabs.top) * 10) / 10) : 0,
    ink_on_intro: under(intro), ink_on_caption: under(tabText.concat(capText)), phone_layout: getComputedStyle(cap.querySelector('.mode')).display === 'block',
    text_on_text: intro.reduce((n, a) => n + tabText.concat(capText).filter(b => a.left < b.right - 1 && b.left < a.right - 1 && a.top < b.bottom - 2 && b.top < a.bottom - 2).length, 0),
    clashes: [...new Set(clashes)], labels: T.map(t => t.s), mode: [...cap.querySelectorAll('.tab')].findIndex(t => t.classList.contains('on')),
    hscroll: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    loop_alive: window.__vc ? __vc.pending() > 0 : null, thrown: window.__vc ? __vc.log.slice(0, 2) : [], frames: window.__probe.frames || 0,
    rm: document.documentElement.classList.contains('rm')
  };
}"""


def defect(r):
    """What is wrong in one frame, as a list of words (empty: nothing)."""
    d = []
    if r["node_r"] < 14:
        d.append("small")
    if r["ink_on_intro"] or r["ink_on_caption"]:
        d.append("over text")
    if r["text_on_text"]:
        d.append("text on text")
    if r["clashes"]:
        d.append("labels clash")
    if r["errors"] or r["thrown"]:
        d.append("error")
    if r["loop_alive"] is False:
        d.append("animation stopped")
    if r["hscroll"]:
        d.append("hscroll")
    return d


# The focused control as a reader sees it, and whether the pin has a scroll of its own (it must not: the canvas cannot see one).
STOP = """(() => { const D = document, a = D.activeElement, top = D.querySelector('.top').getBoundingClientRect().bottom, r = a && a !== D.body ? a.getBoundingClientRect() : null;
  let op = 1, vis = true; for (let e = a; e && e !== D.documentElement; e = e.parentElement) { const s = getComputedStyle(e); op *= +s.opacity; if (s.visibility !== 'visible') vis = false; }
  const hit = r ? D.elementFromPoint(Math.min(innerWidth - 2, Math.max(1, r.left + Math.min(r.width / 2, 12))), r.top + r.height / 2) : null;
  return { where: !r ? 'none' : a.closest('#hCap, #hCopy') ? 'sheet' : a.closest('header') ? 'header' : 'out', what: r ? (a.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 30) : '',
    pin: D.getElementById('pin').scrollTop, y: Math.round(scrollY), box: r ? [Math.round(r.top), Math.round(r.bottom)] : null,
    shown: !!r && r.top >= top - 0.5 && r.bottom <= innerHeight + 0.5 && op >= 0.99 && vis && a.matches(':focus-visible') && !!hit && (hit === a || a.contains(hit)) }; })()"""


def states(p, engines, pages, out, shots):
    """The first screen where its sheet is taller than the window, in the states a frame-by-frame matrix does not reach:
    reduced motion, turning the phone and back, a browser bar that hides, the page without JavaScript, and the keyboard.
    Real time, no clock: the page runs exactly as in a browser. -> rows of dict(engine, lang, state, ok, detail)."""
    rows = []

    def rec(eng, lang, state, ok, detail):
        rows.append(dict(engine=eng, lang=lang, state=state, ok=bool(ok), detail=detail))
        print(("PASS " if ok else "FAIL ") + f"states {eng} {lang}: {state}" + ("" if ok else "  " + json.dumps(detail, ensure_ascii=False)[:400]), flush=True)

    def clean(r):
        return not (r["ink_on_intro"] or r["ink_on_caption"] or r["text_on_text"] or r["clashes"] or r["hscroll"]) and r["node_r"] >= 14

    def brief(r):
        return {k: r[k] for k in ("W", "H", "y", "hx", "node_r", "ink_on_intro", "ink_on_caption", "text_on_text", "clashes", "frames", "rm")}

    for eng in engines:
        for lang, path in pages.items():
            # 1. reduced motion on a short phone: one static frame, no loop while idle; scrolling the excess still moves the sheet as one piece
            b, ctx, pg, problems = stage.open_page(p, eng, path, 378, 575, 3, phone=True, reduced=True, clock=False, extra_init=(HOOK,))
            pg.wait_for_timeout(900)
            r0 = pg.evaluate(MEASURE)
            pg.wait_for_timeout(1000)
            idle = pg.evaluate("window.__probe.frames") - r0["frames"]
            pg.screenshot(path=os.path.join(shots, f"state-{eng}-{lang}-reduced-motion-top.png"))
            pg.evaluate(f"scrollTo(0, {r0['hx']})")
            pg.wait_for_timeout(500)
            r1 = pg.evaluate(MEASURE)
            pg.screenshot(path=os.path.join(shots, f"state-{eng}-{lang}-reduced-motion-scrolled.png"))
            rec(eng, lang, "reduced motion, 378x575: a static first screen of full size (no frames drawn while idle), and after scrolling its excess the figure sits with its caption; nothing over text, no errors",
                r0["rm"] and r0["hx"] > 50 and idle == 0 and clean(r0) and clean(r1) and r1["frames"] > r0["frames"] and not problems, dict(idle_frames=idle, top=brief(r0), scrolled=brief(r1), problems=problems[:3]))
            b.close()
            # 2. turning the phone and back, then a browser bar that hides (a taller window): the sheet is measured again each time
            b, ctx, pg, problems = stage.open_page(p, eng, path, 393, 659, 3, phone=True, clock=False, extra_init=(HOOK,))
            pg.wait_for_timeout(1200)
            a0 = pg.evaluate(MEASURE)
            seq = []
            for name, (w, h) in (("landscape", (734, 343)), ("portrait again", (393, 659)), ("bar hidden", (393, 743)), ("bar shown", (393, 659))):
                pg.set_viewport_size({"width": w, "height": h})
                pg.wait_for_timeout(1500)
                r = pg.evaluate(MEASURE)
                f0 = r["frames"]
                pg.wait_for_timeout(500)
                r["running"] = pg.evaluate("window.__probe.frames") - f0
                seq.append((name, r))
                pg.screenshot(path=os.path.join(shots, f"state-{eng}-{lang}-turn-{name.replace(' ', '-')}.png"))
            back = seq[1][1]
            rec(eng, lang, "turn 393x659 to 734x343 and back, then a bar that hides (393x743) and returns: each time the figure keeps its size, nothing lies over text, the animation runs; back in portrait the numbers are the first ones",
                all(clean(r) and r["running"] > 10 for _, r in seq) and seq[0][1]["hx"] > 100 and abs(back["hx"] - a0["hx"]) < 1 and abs(back["node_r"] - a0["node_r"]) < 0.2 and seq[2][1]["hx"] < a0["hx"] and not problems,
                dict(first=brief(a0), **{n: dict(brief(r), running=r["running"]) for n, r in seq}, problems=problems[:3]))
            b.close()
            # 3. the address of the first screen's second state (the language link carries it) on the short phone: the panel is shown
            b, ctx, pg, problems = stage.open_page(p, eng, path, 378, 575, 3, phone=True, clock=False, extra_init=(HOOK,))
            pg.goto("file://" + os.path.abspath(path) + "#s0-1", wait_until="load")
            pg.reload(wait_until="load")
            pg.wait_for_timeout(1500)
            g = pg.evaluate("({y: scrollY, H: innerHeight, hx: parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--hx')) || 0, op: +getComputedStyle(document.getElementById('hA')).opacity,"
                            " href: document.getElementById('lang') ? document.getElementById('lang').getAttribute('href') : '#s0-1', cap: +getComputedStyle(document.getElementById('hCap')).opacity})")
            pg.screenshot(path=os.path.join(shots, f"state-{eng}-{lang}-arrive-second-state.png"))
            rec(eng, lang, "arriving at #s0-1 on 378x575: the page stands past the first screen's excess with the delivered-vs-read panel shown, and the language link keeps that place",
                g["hx"] > 50 and g["y"] > g["hx"] + 0.5 * g["H"] and g["op"] > 0.9 and g["cap"] < 0.05 and g["href"].endswith("#s0-1") and not problems, dict(g, problems=problems[:3]))
            b.close()
            # 4. no JavaScript on the short phone: plain text in order, nothing on top of anything, no canvas
            br = getattr(p, eng).launch()
            kw = dict(viewport={"width": 378, "height": 575}, device_scale_factor=2, has_touch=True, java_script_enabled=False)
            ctx = br.new_context(**kw)
            pg = ctx.new_page()
            pg.goto("file://" + os.path.abspath(path), wait_until="load")
            boxes = [pg.locator(q).nth(i).bounding_box() for q in ("#hCopy > *", "#hCap .tab", "#hCap .mode p") for i in range(pg.locator(q).count())]
            boxes = [x for x in boxes if x and x["height"] > 1]
            over = sum(1 for i in range(len(boxes)) for j in range(i + 1, len(boxes))
                       if boxes[i]["x"] < boxes[j]["x"] + boxes[j]["width"] - 1 and boxes[j]["x"] < boxes[i]["x"] + boxes[i]["width"] - 1
                       and boxes[i]["y"] < boxes[j]["y"] + boxes[j]["height"] - 1 and boxes[j]["y"] < boxes[i]["y"] + boxes[i]["height"] - 1)
            canvas = pg.locator("#field").bounding_box()
            pg.screenshot(path=os.path.join(shots, f"state-{eng}-{lang}-no-js.png"))
            rec(eng, lang, "no JavaScript, 378x575: the intro, the four tabs and every scheme's text are laid out one after another, none over another, and no canvas is shown",
                len(boxes) >= 3 + 4 + 12 and over == 0 and canvas is None, dict(blocks=len(boxes), overlapping_pairs=over, canvas=canvas))
            br.close()
            # 5. the keyboard where the sheet goes on below the window (a phone held sideways, a short phone): Tab reaches the four tabs
            #    and the caption's source link by moving the page, with which the canvas moves too. The pin never scrolls by itself:
            #    that would carry the text up over a figure that stays where it was.
            for w, h in ((844, 390), (378, 575)):
                b, ctx, pg, problems = stage.open_page(p, eng, path, w, h, 2, phone=True, clock=False, extra_init=(HOOK,))
                pg.wait_for_timeout(1000)
                r0 = pg.evaluate(MEASURE)
                stops, bad = [], []
                for _ in range(9):
                    pg.keyboard.press("Tab" if eng == "chromium" else "Alt+Tab")      # WebKit, like Safari, reaches links with Option+Tab
                    pg.wait_for_timeout(350)
                    s = pg.evaluate(STOP)
                    if s["where"] == "header":
                        continue
                    if s["where"] != "sheet":
                        break
                    r = pg.evaluate(MEASURE)
                    s["over_text"] = r["ink_on_intro"] + r["ink_on_caption"] + r["text_on_text"]
                    stops.append(s)
                    if s["pin"] or not s["shown"] or s["over_text"]:
                        bad.append(s)
                pg.screenshot(path=os.path.join(shots, f"state-{eng}-{lang}-keyboard-{w}x{h}-last-stop.png"))
                pg.mouse.move(w / 2, h / 2)
                pg.mouse.wheel(0, -30000)             # and back to the top, as a reader would
                pg.wait_for_timeout(900)
                r1, pin1 = pg.evaluate(MEASURE), pg.evaluate("document.getElementById('pin').scrollTop")
                rec(eng, lang, f"keyboard, {w}x{h}: Tab to the four tabs and the caption's source link, below the window's edge, moves the page and never the pin alone; every stop is shown with its focus ring, "
                               "nothing is drawn behind text, and back at the top the first screen is as it was",
                    r0["hx"] > 50 and len(stops) >= 5 and not bad and max(s["y"] for s in stops) > 0 and r1["y"] == 0 and pin1 == 0 and clean(r1) and abs(r1["tabsTop"] - r0["tabsTop"]) < 1 and not problems,
                    dict(excess=r0["hx"], stops=[[s["what"], s["y"], s["box"]] for s in stops], bad=bad[:3], back=dict(brief(r1), pin=pin1, tabsTop=[r0["tabsTop"], r1["tabsTop"]]), problems=problems[:3]))
                b.close()
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--page", action="append", required=True, help="lang=path (repeatable)")
    ap.add_argument("--label", default="probe")
    ap.add_argument("--engines", default="webkit,chromium")
    ap.add_argument("--sizes", default=",".join(SIZES))
    ap.add_argument("--modes", default="0,1,2,3")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--states", action="store_true", help="also check reduced motion, turning the phone, a hiding browser bar and no JavaScript")
    a = ap.parse_args()
    pages = dict(p.split("=", 1) for p in a.page)
    out = os.path.join(os.path.abspath(a.out), a.label)
    shots = os.path.join(out, "shots")
    os.makedirs(shots, exist_ok=True)
    vclock = open(os.path.join(HERE, "vclock.js"), encoding="utf-8").read()
    modes = [int(m) for m in a.modes.split(",")]
    rows = []
    with sync_playwright() as p:
        for eng in a.engines.split(","):
            b = getattr(p, eng).launch()
            for lang, path in pages.items():
                path = os.path.abspath(path)
                for name in a.sizes.split(","):
                    w, h, dpr, phone = SIZES[name]
                    kw = dict(viewport={"width": w, "height": h}, device_scale_factor=dpr)
                    if phone:
                        kw["has_touch"] = True
                        if eng == "chromium":
                            kw["is_mobile"] = True
                    ctx = b.new_context(**kw)
                    ctx.add_init_script(HOOK)
                    ctx.add_init_script(vclock)
                    errors, net = [], []
                    ctx.route("**/*", lambda route: (net.append(route.request.url), route.abort()) if not route.request.url.startswith(("file:", "data:", "about:", "blob:")) else route.continue_())
                    pg = ctx.new_page()
                    pg.on("console", lambda m: errors.append("console: " + m.text[:200]) if m.type == "error" else None)
                    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)[:200]))
                    pg.goto("file://" + path, wait_until="load")
                    pg.evaluate("__vc.run(30)")
                    for m in modes:
                        pg.evaluate(f"(() => {{ scrollTo(0, 0); document.querySelectorAll('.tab')[{m}].click(); return __vc.run({round(SHOW[m] * 60)}); }})()")
                        base = f"{eng}-{lang}-{name}-m{m + 1}"
                        r = pg.evaluate(MEASURE)
                        r.update(engine=eng, version=b.version, lang=lang, size=name, at="top", shot=base + ".png", errors=errors[:3] + net[:3])
                        pg.screenshot(path=os.path.join(shots, base + ".png"))
                        rows.append(r)
                        if r["hx"] > 0.5:     # the first screen is taller than the window: also where its excess has been scrolled
                            pg.evaluate(f"(() => {{ for (let i = 1; i <= 12; i++) __vc.frame({{ y: {r['hx']} * i / 12 }}); return __vc.t; }})()")
                            r2 = pg.evaluate(MEASURE)
                            r2.update(engine=eng, version=b.version, lang=lang, size=name, at="scrolled", shot=base + "-scrolled.png", errors=errors[:3] + net[:3])
                            pg.screenshot(path=os.path.join(shots, base + "-scrolled.png"))
                            rows.append(r2)
                    ctx.close()
                    print(f"{a.label} {eng} {lang} {name}: " + " | ".join(f"m{r['mode'] + 1}{'s' if r['at'] == 'scrolled' else ''} r={r['node_r']} gap={r['gap']} hx={r['hx']} txt={r['ink_on_intro']}+{r['ink_on_caption']}+{r['text_on_text']} clash={len(r['clashes'])}" for r in rows[-len(modes) * 2:] if r["size"] == name and r["engine"] == eng and r["lang"] == lang), flush=True)
            b.close()
        st = states(p, a.engines.split(","), pages, out, shots) if a.states else []
    json.dump(rows, open(os.path.join(out, "hero_probe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(st, open(os.path.join(out, "hero_states.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # a frame is judged where the figure is meant to be seen whole: at the top, or after the first screen's excess is scrolled
    judged = [r for r in rows if r["size"] not in UNJUDGED]
    bad = [r for r in judged if defect(r)]
    md = [f"# First screen of the Field page: {a.label}", "",
          f"{len(rows)} frames; {len(judged)} judged ({', '.join(UNJUDGED)} is measured but not judged), {len(bad)} with a defect: agent radius under 14 px (small), canvas ink behind the page's text lines (over text), "
          "intro lines over tab or caption lines (text on text), canvas labels whose boxes intersect or reach into a circle (labels clash), a script error, an animation loop that asks for no next frame (animation stopped) or horizontal scroll.", "",
          "| engine | lang | size | scheme | at | agent r | gap | excess | ink behind intro, px² | ink behind tabs and caption, px² | text on text | clashes | defect |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['engine']} {r['version']} | {r['lang']} | {r['size']} | {r['mode'] + 1} | {r['at']} | {r['node_r']} | {r['gap']} | {r['hx']} | {r['ink_on_intro']} | {r['ink_on_caption']} | {r['text_on_text']} | {'; '.join(r['clashes']) or '–'} | {', '.join(defect(r)) or '–'} |")
    if st:
        md += ["", f"## Other states: {sum(1 for x in st if x['ok'])} of {len(st)} passed", "", "| engine | lang | state | result |", "|---|---|---|---|"]
        md += [f"| {x['engine']} | {x['lang']} | {x['state']} | {'pass' if x['ok'] else 'FAIL'} |" for x in st]
    open(os.path.join(out, "HERO_PROBE.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"{a.label}: {len(rows)} frames, {len(bad)} of {len(judged)} judged frames defective -> {out}")
    if a.strict and (bad or [x for x in st if not x["ok"]]):
        sys.exit(1)


if __name__ == "__main__":
    main()
