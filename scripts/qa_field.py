#!/usr/bin/env python3
"""Real-browser checks of the Field edition, opened as files (file://, no server), in Chromium and WebKit.

  python scripts/qa_field.py [OUTDIR]          # default qa/field; writes OUTDIR/qa_field.json, QA_FIELD.md, shots/, sheets/
  python scripts/qa_field.py OUTDIR --fast     # fewer frames per sweep
  python scripts/qa_field.py OUTDIR --groups=map,site   # only some groups (sweep widths nojs rm resize map schemes focus site)

Each delivery file is copied alone into an empty folder (OUTDIR/isolated/<lang>/) and opened from there. Network is
refused: any request other than file: / data: / about: is recorded as a failure (and aborted). Checks:
  sweep      every step at 1100x750 and 390x844 in both languages (Chromium; every third step and the map in WebKit): no console or page errors, no horizontal
             scroll, the step's card is the active one, the frame is not empty; frames and contact sheets saved
  widths     the first screen and the map (and the curve in Chromium) at intermediate sizes, 600–1728 px wide; phones
             390x844 and 390x664 (the in-app browser of Telegram): every pinned card ends on screen, the s³ units of
             scene 3 step 6 are drawn, the first screen and the tallest scenes keep their figure; short landscape phones
             667x375 (also 740x360 and 640x360 in Chromium): every card's first and last line and the first screen's panel
             can be read in full while their step is active
  focus      keyboard and taps where text moves inside a box (390x664, English): from the top, Tab through the first screen
             lands only on visible stops (the hidden panel's clipped link is not one); with the panel shown, Tab to its
             source link shows it inside the panel; Tab and a tap on the last source link of step 1-4 keep that step active
             with its card pinned and the link inside it; a walk over every Tab stop (1126x681 and 390x664; WebKit with
             Option+Tab, as in Safari) finds each one visible, opaque, on screen and under the pointer
  nojs       without JavaScript: the hero text, the four schemes, every step's text, the map legend; no canvas; every
             source link is the element under the pointer, and a click on each link of the first screen opens its source
  rm         reduced motion: static frames, no continuous animation loop, hover still answers
  resize     desktop → phone → desktop on one page without reloading: layout switches, nothing overflows, no errors
  map        hover shows a work's title, lab, date and theme; click opens its source in a new tab; touch tap pins a tooltip
             with a link (on a phone titles appear only on a tap); the idle tour shows notable works on a desktop; hovering or
             focusing the legend highlights a theme
  keyboard   Tab reaches the scheme tabs with a visible focus ring; arrow keys change the scheme
  schemes    the first screen switches schemes by itself; a click on a tab selects that scheme
  site       repository layout: the language link carries the current scene and step and the other language opens there;
             on a phone, arriving that way at a card whose text moves inside its box starts at its first line;
             an address of the 19 October single page (index.html#ch04) lands on the dated survey; the survey link works
"""
import json
import math
import os
import shutil
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_field as F

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(ROOT, "qa", "field"))
FAST = "--fast" in sys.argv
GROUPS = next((a.split("=", 1)[1].split(",") for a in sys.argv[1:] if a.startswith("--groups=")), None)   # e.g. --groups=map,site
SHOTS = os.path.join(OUT, "shots")
ENGINES = ("chromium", "webkit")
DESK = dict(viewport={"width": 1100, "height": 750}, device_scale_factor=1)
PHONE = dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, has_touch=True, is_mobile=True)
R = []


def rec(group, engine, name, ok, detail=None):
    R.append(dict(group=group, engine=engine, check=name, ok=bool(ok), detail=detail))
    with open(os.path.join(OUT, "qa_field.jsonl"), "a", encoding="utf-8") as f:   # kept even if a run is interrupted
        f.write(json.dumps(R[-1], ensure_ascii=False) + "\n")
    print(("PASS " if ok else "FAIL ") + f"{group} {engine} {name}" + ("" if ok else "  " + json.dumps(detail, ensure_ascii=False)[:500]), flush=True)


def isolate():
    """Each export alone in an empty folder."""
    paths = {}
    for lang in F.LANGS:
        d = os.path.join(OUT, "isolated", lang)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        src = os.path.join(ROOT, "delivery", F.DELIVERY[lang])
        shutil.copy2(src, d)
        paths[lang] = os.path.join(d, F.DELIVERY[lang])
        assert os.listdir(d) == [F.DELIVERY[lang]]
    return paths


def open_page(b, opts, path, js=True, rm=False, frag=""):
    kw = dict(opts)
    if engine_of(b) != "chromium":
        kw.pop("is_mobile", None)
    if rm:
        kw["reduced_motion"] = "reduce"
    ctx = b.new_context(java_script_enabled=js, **kw)
    ctx.set_default_timeout(30000)          # a blocked browser call fails the check instead of stopping the run
    errors, net = [], []
    ctx.route("**/*", lambda route: (net.append(route.request.url), route.abort()) if not route.request.url.startswith(("file:", "data:", "about:", "blob:")) else route.continue_())
    pg = ctx.new_page()
    pg.on("console", lambda m: errors.append("console: " + m.text[:200]) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)[:200]))
    pg.goto("file://" + path + frag, wait_until="load")
    return ctx, pg, errors, net


ENGINE_OF = {}


def engine_of(b):
    return ENGINE_OF[id(b)]


def shot(pg, name):
    os.makedirs(SHOTS, exist_ok=True)
    p = os.path.join(SHOTS, name + ".png")
    pg.screenshot(path=p)
    return p


def nonblank(path):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    im = im.resize((im.width // 4, im.height // 4))
    px = list(im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata())
    return sum(1 for r, g, b in px if abs(r - 9) + abs(g - 11) + abs(b - 12) > 40) / len(px)


def sheet(paths, out, cols):
    from PIL import Image
    if not paths:
        return
    ims = [Image.open(p).convert("RGB") for p in paths]
    w0, h0 = ims[0].size
    tw = 520 if w0 > h0 else 200
    th = round(h0 * tw / w0)
    rows = math.ceil(len(ims) / cols)
    sh = Image.new("RGB", (cols * tw + (cols + 1) * 8, rows * th + (rows + 1) * 8), (60, 60, 60))
    for i, im in enumerate(ims):
        r, c = divmod(i, cols)
        sh.paste(im.resize((tw, th), Image.LANCZOS), (8 + c * (tw + 8), 8 + r * (th + 8)))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sh.save(out)


def steps(pg):
    return pg.evaluate("[...document.querySelectorAll('.step')].map(e => [e.dataset.sc + '-' + e.dataset.st, Math.round(e.getBoundingClientRect().top + scrollY)])")


def scroll_to(pg, y, settle):
    pg.evaluate(f"window.scrollTo(0, {max(0, y - 240)})")
    pg.wait_for_timeout(120)
    pg.evaluate(f"window.scrollTo(0, {y})")
    pg.wait_for_timeout(settle)


HSCROLL = "document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"


def sweep(b, eng, lang, vname, opts, path, fast=False):
    ctx, pg, errors, net = open_page(b, opts, path)
    pg.wait_for_timeout(1500)
    H = pg.evaluate("innerHeight")
    frames, bad_active, empty = [], [], []
    p0 = shot(pg, f"sweep-{eng}-{lang}-{vname}-h0")
    frames.append(p0)
    for k, y in (("h1", H), ("h2", int(H * 2.6))):
        scroll_to(pg, y, 1400)
        frames.append(shot(pg, f"sweep-{eng}-{lang}-{vname}-{k}"))
    st = steps(pg)
    for i, (k, y) in enumerate(st):
        if (FAST or fast) and i % 3 and k not in ("6-0", "7-0"):
            continue
        scroll_to(pg, y, 1100 if eng == "chromium" else 900)
        act = pg.evaluate("(document.querySelector('.step.on') || {dataset: {}}).dataset.sc + '-' + (document.querySelector('.step.on') || {dataset: {}}).dataset.st")
        if act != k:
            bad_active.append([k, act])
        f = shot(pg, f"sweep-{eng}-{lang}-{vname}-s{k}")
        frames.append(f)
        nb = nonblank(f)
        if nb < 0.03:
            empty.append([k, round(nb, 3)])
    hs = pg.evaluate(HSCROLL)
    docH = pg.evaluate("document.documentElement.scrollHeight")
    rec("sweep", eng, f"{lang} {vname}: {len(frames)} frames, no errors or requests, no horizontal scroll, active step = scrolled step, no empty frame",
        not errors and not net and not hs and not bad_active and not empty,
        dict(errors=errors[:4], net=net[:4], hscroll=hs, wrong_active=bad_active[:6], empty=empty, doc_height=docH))
    sheet(frames, os.path.join(OUT, "sheets", f"{eng}-{lang}-{vname}.png"), 4 if vname == "desktop" else 8)
    ctx.close()


def widths(b, eng, paths):
    sizes = [(600, 960), (760, 900), (900, 700), (1280, 800), (1440, 900), (1728, 1117)] if eng == "chromium" else [(760, 900), (1440, 900)]
    for lang in F.LANGS:
        for w, h in sizes:
            ctx, pg, errors, net = open_page(b, dict(viewport={"width": w, "height": h}, device_scale_factor=1), paths[lang])
            pg.wait_for_timeout(1200)
            names = [shot(pg, f"width-{eng}-{lang}-{w}x{h}-h0")]
            st = dict(steps(pg))
            for k in (("2-2", "6-0") if eng == "chromium" else ("6-0",)):
                scroll_to(pg, st[k], 1300)
                names.append(shot(pg, f"width-{eng}-{lang}-{w}x{h}-s{k}"))
            hs = pg.evaluate(HSCROLL)
            rec("widths", eng, f"{lang} {w}x{h}: no errors, no horizontal scroll (first screen, curve, map)", not errors and not net and not hs, dict(errors=errors[:3], net=net[:3], hscroll=hs))
            ctx.close()
    for lang in F.LANGS:
        for w, h in ((390, 844), (390, 664)):
            phone_fit(b, eng, lang, w, h, paths[lang])
        for w, h in ((667, 375), (740, 360), (640, 360)) if eng == "chromium" else ((667, 375),):
            phone_read(b, eng, lang, w, h, paths[lang])


# Counts the dots one frame draws (arcs and squares big and opaque enough to see): s³ units of zero size draw nothing.
DOTS = """(() => { const C = CanvasRenderingContext2D.prototype, P = window.__dots = { cur: 0, last: 0 };
  const al = (s, g) => { if (typeof s !== 'string') return 0; const m = /^rgba?\\(([^)]+)\\)$/.exec(s); return (m && m[1].split(',').length > 3 ? +m[1].split(',')[3] : 1) * g; };
  const cr = C.clearRect; C.clearRect = function (x, y, w, h) { if (w * (this.canvas.width / Math.max(1, this.canvas.clientWidth)) >= this.canvas.width - 2) { P.last = P.cur; P.cur = 0; } return cr.apply(this, arguments); };
  const ar = C.arc; C.arc = function (x, y, r) { if (r >= 0.4) this.__a = 1; return ar.apply(this, arguments); };
  const bp = C.beginPath; C.beginPath = function () { this.__a = 0; return bp.apply(this, arguments); };
  const fl = C.fill; C.fill = function () { if (this.__a && al(this.fillStyle, this.globalAlpha) >= 0.25) P.cur++; return fl.apply(this, arguments); };
  const fr = C.fillRect; C.fillRect = function (x, y, w, h) { if (Math.abs(w) >= 0.8 && al(this.fillStyle, this.globalAlpha) >= 0.25) P.cur++; return fr.apply(this, arguments); };
})()"""
PINNED = """(k) => { const s = [...document.querySelectorAll('.step')].find(e => e.dataset.sc + '-' + e.dataset.st === k), c = s.querySelector('.card');
  const top = s.getBoundingClientRect().top + scrollY, pin = parseFloat(getComputedStyle(c).top) || 0;
  return [top, pin, s.offsetHeight, c.offsetHeight]; }"""


def phone_fit(b, eng, lang, w, h, path):
    """A phone at w x h: every step's card, once pinned, ends on screen (a longer text moves inside the card); the
    s³ units are drawn; the first screen, the scale, s³, the Avalon-M1 bars and the map are photographed."""
    opts = dict(PHONE, viewport={"width": w, "height": h})
    kw = dict(opts)
    if eng != "chromium":
        kw.pop("is_mobile", None)
    ctx = b.new_context(**kw)
    ctx.set_default_timeout(30000)
    ctx.add_init_script(DOTS)
    errors, net = [], []
    ctx.route("**/*", lambda route: (net.append(route.request.url), route.abort()) if not route.request.url.startswith(("file:", "data:", "about:", "blob:")) else route.continue_())
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)[:200]))
    pg.goto("file://" + path, wait_until="load")
    pg.wait_for_timeout(1200)
    shot(pg, f"width-{eng}-{lang}-{w}x{h}-h0")
    cut, dots = [], None
    for k, *_ in steps(pg):
        top, pin, sh, ch = pg.evaluate(PINNED, k)
        scroll_to(pg, top - h * 0.5, 250)              # the step becomes active: on a phone its card's pinned top (--ct) is set then
        top, pin, sh, ch = pg.evaluate(PINNED, k)
        y = top - pin + min(60, max(0, (sh - ch) / 3))
        scroll_to(pg, y, 1300 if k in ("1-5", "3-6", "5-4", "6-0") else 350)
        act, box = pg.evaluate("(() => { const s = document.querySelector('.step.on'), r = s && s.querySelector('.card').getBoundingClientRect(); return [s ? s.dataset.sc + '-' + s.dataset.st : null, r ? [r.top, r.bottom] : null]; })()")
        if act != k or box[0] < 47.5 or box[1] > h + 0.5:
            cut.append([k, act, [round(v) for v in box] if box else None])
        if k == "3-6":
            pg.wait_for_timeout(1500)
            dots = pg.evaluate("window.__dots.last")
        if k in ("1-5", "3-6", "5-4", "6-0"):
            shot(pg, f"width-{eng}-{lang}-{w}x{h}-s{k}")
    hs = pg.evaluate(HSCROLL)
    rec("widths", eng, f"{lang} {w}x{h}: every pinned card ends on screen (36 steps), s³ draws its units, no errors or overflow",
        not cut and dots is not None and dots >= 1000 and not errors and not net and not hs, dict(cut=cut[:6], s3_dots=dots, errors=errors[:3], net=net[:3], hscroll=hs))
    ctx.close()


# Sweeps one card (or the first screen's panel, k='hA') through its scroll range. While its step is active (the panel: while
# it is opaque): is its first line, and its last line, each fully readable at some position (below the header, above the
# bottom edge, inside the box when the text moves inside one)? Is a box whose text moves inside the screen while pinned?
READ = """async ([k, stride]) => {
  const raf = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const H = innerHeight, hdr = innerWidth < 760 ? 48 : 56, hero = k === 'hA';
  const el = hero ? null : [...document.querySelectorAll('.step')].find(e => e.dataset.sc + '-' + e.dataset.st === k);
  const card = hero ? document.getElementById('hA') : el.querySelector('.card'), ci = card.querySelector('.ci') || card;
  const kids = [...ci.children].filter(x => x.offsetHeight > 0), first = kids[0], last = kids[kids.length - 1];
  const vis = (e, lo, hi) => { const r = e.getBoundingClientRect(); return r.top >= lo - 0.5 && r.bottom <= hi + 0.5; };
  const a = hero ? 0 : el.getBoundingClientRect().top + scrollY - H, b = hero ? 1.6 * H : el.getBoundingClientRect().bottom + scrollY;
  const ov = card.classList.contains('ov');
  let active = 0, f = false, l = false, outside = null, yOn = null;
  for (let y = Math.max(0, Math.round(a)); y <= b; y += stride) {
    scrollTo(0, y); await raf();
    if (hero ? +getComputedStyle(card).opacity < 0.9 : !el.classList.contains('on')) continue;
    active++; if (yOn === null) yOn = y;
    const cr = card.getBoundingClientRect(), lo = Math.max(hdr, ov ? cr.top : -1e9), hi = Math.min(H, ov ? cr.bottom : 1e9);
    f = f || vis(first, lo, hi); l = l || vis(last, lo, hi);
    const pin = hero ? cr.top : parseFloat(getComputedStyle(card).top);
    if (ov && !outside && Math.abs(cr.top - pin) < 1 && (cr.top < hdr - 0.5 || cr.bottom > H + 0.5)) outside = [Math.round(cr.top), Math.round(cr.bottom), y];
    if (f && l && !ov) break;
  }
  return { k, ov, active, first: f, last: l, outside, yOn };
}"""


def phone_read(b, eng, lang, w, h, path):
    """A short landscape phone (w x h): under the figure a card has no room for a readable box, so it is not clipped and
    moves as a whole. Every card's first and last line, and the first screen's panel, can each be read in full while the
    step is active; s³ draws its units; no errors or horizontal overflow."""
    opts = dict(PHONE, viewport={"width": w, "height": h})
    kw = dict(opts)
    if eng != "chromium":
        kw.pop("is_mobile", None)
    ctx = b.new_context(**kw)
    ctx.set_default_timeout(120000)
    ctx.add_init_script(DOTS)
    errors, net = [], []
    ctx.route("**/*", lambda route: (net.append(route.request.url), route.abort()) if not route.request.url.startswith(("file:", "data:", "about:", "blob:")) else route.continue_())
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)[:200]))
    pg.goto("file://" + path, wait_until="load")
    pg.wait_for_timeout(1200)
    shot(pg, f"land-{eng}-{lang}-{w}x{h}-h0")
    bad, dots, keys = [], None, ["hA"] + [k for k, _ in steps(pg)]
    for k in keys:
        r = pg.evaluate(READ, [k, 32])
        if not (r["active"] and r["first"] and r["last"] and not r["outside"]):
            bad.append(r)
        if r["yOn"] is not None and k in ("hA", "1-4", "2-5", "3-6", "5-4", "6-0"):
            scroll_to(pg, h if k == "hA" else r["yOn"] + 48, 1500 if k in ("3-6", "6-0") else 700)
            if k == "3-6" and pg.evaluate("(s => s ? s.dataset.sc + '-' + s.dataset.st : null)(document.querySelector('.step.on'))") == "3-6":
                dots = pg.evaluate("window.__dots.last")
            shot(pg, f"land-{eng}-{lang}-{w}x{h}-s{k}")
    hs = pg.evaluate(HSCROLL)
    rec("widths", eng, f"{lang} {w}x{h} landscape: all {len(keys) - 1} cards and the first screen's panel can be read in full while active, s³ draws its units, no errors or overflow",
        not bad and dots is not None and dots >= 1000 and not errors and not net and not hs, dict(unreadable=bad[:6], s3_dots=dots, errors=errors[:3], net=net[:3], hscroll=hs))
    ctx.close()


def nojs(b, eng, paths):
    for lang in F.LANGS:
        C = F.read_json("field", f"{lang}.json")
        for vname, opts in (("desktop", DESK), ("phone", PHONE)):
            ctx, pg, errors, net = open_page(b, opts, paths[lang], js=False)
            text = pg.evaluate("document.body.innerText")
            import html as _h, re as _re
            pl = lambda s: _re.sub(r"\s+", " ", _h.unescape(_re.sub(r"<[^>]+>", "", s))).strip()
            norm = _re.sub(r"\s+", " ", text)
            need = [pl(C["hero"]["h1"]), pl(C["hero"]["modes"][3]["mech"]), pl(C["hero"]["aside"]["p"][1])] + \
                   [pl(s["p"][0]) for sc in C["scenes"] for s in sc["steps"] if s.get("p")] + [pl(C["scenes"][-1]["steps"][0]["qs"][3])]
            missing = [x[:60] for x in need if x not in norm]
            canvas = pg.evaluate("getComputedStyle(document.getElementById('field')).display")
            legend = pg.evaluate("document.querySelectorAll('#legend li').length")
            hs = pg.evaluate(HSCROLL)
            pg.set_viewport_size(opts["viewport"])
            full = os.path.join(SHOTS, f"nojs-{eng}-{lang}-{vname}.png")
            os.makedirs(SHOTS, exist_ok=True)
            pg.screenshot(path=full, full_page=True)
            rec("nojs", eng, f"{lang} {vname}: all text readable without JavaScript ({len(need)} probes), legend of 11 themes, canvas hidden, no overflow",
                not missing and canvas == "none" and legend == 11 and not hs and not errors and not net, dict(missing=missing[:5], canvas=canvas, legend=legend, hscroll=hs, errors=errors[:3]))
            # every source link is the element a pointer reaches; a click on each link of the first screen opens its source
            hits = pg.evaluate("""() => [...document.querySelectorAll('.src a')].map(a => { a.scrollIntoView({ block: 'center' }); const r = a.getClientRects()[0], e = document.elementFromPoint(r.left + Math.min(r.width / 2, 24), r.top + r.height / 2); return [a.href, !!e && (e === a || a.contains(e)), !!a.closest('.h-cap,.h-a')]; })""")
            blocked = [x[0] for x in hits if not x[1]]
            opened, failed = [], []
            for i, (href, _, hero) in enumerate(hits):
                if not hero:
                    continue
                loc = pg.locator('.src a').nth(i)
                before = len(net)
                try:
                    with ctx.expect_page(timeout=6000) as pop:
                        loc.click(timeout=6000)
                    pop.value.wait_for_timeout(300)
                    got = net[before:]
                    (opened if got and got[0].rstrip('/') == href.rstrip('/') else failed).append([href, got[:1]])
                    pop.value.close()
                except Exception as e:
                    failed.append([href, str(e).splitlines()[0][:120]])
            rec("nojs", eng, f"{lang} {vname}: without JavaScript all {len(hits)} source links can be clicked; the {len(opened) + len(failed)} links of the first screen open their sources",
                hits and not blocked and opened and not failed, dict(blocked=blocked[:5], failed=failed[:5], opened=len(opened)))
            ctx.close()


COUNT_RAF = """(() => { window.__raf = 0; const o = window.requestAnimationFrame.bind(window); window.requestAnimationFrame = f => { window.__raf++; return o(f); }; })()"""


def reduced(b, eng, paths):
    for lang in F.LANGS:
        for vname, opts in (("desktop", DESK), ("phone", PHONE)):
            ctx, pg, errors, net = open_page(b, opts, paths[lang], rm=True)
            pg.wait_for_timeout(600)
            rm = pg.evaluate("document.documentElement.classList.contains('rm')")
            pg.evaluate(COUNT_RAF)
            pg.wait_for_timeout(1500)
            idle = pg.evaluate("window.__raf")
            st = dict(steps(pg))
            frames = []
            for k in ("1-2", "3-3", "5-1", "6-0"):
                scroll_to(pg, st[k], 450)
                frames.append(shot(pg, f"rm-{eng}-{lang}-{vname}-s{k}"))
            empty = [os.path.basename(f) for f in frames if nonblank(f) < 0.03]
            rec("rm", eng, f"{lang} {vname}: reduced motion draws static frames on demand (no loop while idle), none empty, no errors",
                rm and idle <= 2 and not empty and not errors and not net, dict(rm_class=rm, raf_while_idle=idle, empty=empty, errors=errors[:3]))
            sheet(frames, os.path.join(OUT, "sheets", f"rm-{eng}-{lang}-{vname}.png"), 4)
            if vname == "desktop":
                # hover answers in reduced motion: the pointer asks for a frame
                scroll_to(pg, st["6-0"], 500)
                found = hover_scan(pg, 1100, 750)
                rec("rm", eng, f"{lang}: map hover shows a tooltip in reduced motion", bool(found), found)
            ctx.close()


def hover_scan(pg, W, H):
    """Move the pointer over the map's columns until the tooltip shows a work."""
    for y in range(H - 100, H - 300, -6):
        for x in range(60, W - 40, 7):
            pg.mouse.move(x, y)
            pg.wait_for_timeout(16)
            t = pg.evaluate("(() => { const t = document.getElementById('tip'); return t.classList.contains('on') && !t.classList.contains('touch') ? [t.querySelector('.t').textContent, t.querySelector('.m').textContent, t.querySelector('.th span').textContent] : null; })()")
            if t and t[0]:
                return dict(x=x, y=y, title=t[0][:80], meta=t[1][:80], theme=t[2])
    return None


def map_checks(b, eng, paths):
    for lang in F.LANGS:
        L = F.read_json("field", f"{lang}.json")["labels"]
        ctx, pg, errors, net = open_page(b, DESK, paths[lang])
        st = dict(steps(pg))
        scroll_to(pg, st["6-0"], 1500)
        # idle tour: a notable work's tooltip appears by itself
        pg.wait_for_timeout(4200)
        tour = pg.evaluate("(() => { const t = document.getElementById('tip'); return t.classList.contains('on') ? t.querySelector('.t').textContent : ''; })()")
        shot(pg, f"map-{eng}-{lang}-tour")
        rec("map", eng, f"{lang} desktop: the idle tour shows a notable work's tooltip without interaction", bool(tour), tour[:80])
        found = hover_scan(pg, 1100, 750)
        shot(pg, f"map-{eng}-{lang}-hover")
        themes_ok = bool(found) and found["theme"] in L["themes"]
        rec("map", eng, f"{lang} desktop: hover shows title, lab and date, and the theme in this language", themes_ok, found)
        if found:
            pg.mouse.move(found["x"], found["y"])
            pg.wait_for_timeout(120)
            before = list(net)
            with ctx.expect_page(timeout=4000) as pop:
                pg.mouse.click(found["x"], found["y"])
            pop.value.wait_for_timeout(600)
            opened = [u for u in net if u not in before]
            rec("map", eng, f"{lang} desktop: click opens the work's source in a new tab (request aborted in QA)", bool(opened) and opened[0].startswith("https://"), opened[:2])
            pop.value.close()
        # legend: hover highlights a theme, focus too
        pg.locator("#legend li").nth(3).hover()
        pg.wait_for_timeout(300)
        hl = pg.evaluate("document.getElementById('legend').classList.contains('hl') && document.querySelector('#legend li.on') !== null")
        shot(pg, f"map-{eng}-{lang}-legend")
        pg.mouse.move(5, 5)
        pg.wait_for_timeout(200)
        pg.locator("#legend li").nth(5).focus()
        pg.wait_for_timeout(200)
        fhl = pg.evaluate("document.querySelector('#legend li.on') && document.querySelector('#legend li.on').dataset.k === '5'")
        rec("map", eng, f"{lang}: legend highlights a theme on hover and on keyboard focus", hl and fhl, dict(hover=hl, focus=fhl))
        rec("map", eng, f"{lang} desktop map: no errors or other requests", not errors and not [u for u in net if not u.startswith("https://")], dict(errors=errors[:3]))
        ctx.close()
        # touch
        ctx, pg, errors, net = open_page(b, PHONE, paths[lang])
        st = dict(steps(pg))
        scroll_to(pg, st["6-0"], 1500)
        H = pg.evaluate("innerHeight")
        box = pg.evaluate("(() => { const c = document.querySelector('#s6 .card').getBoundingClientRect(); return [c.top]; })()")
        pinned = None
        for y in range(int(box[0]) - 52, int(box[0]) - 220, -5):
            for x in range(20, 380, 6):
                pg.touchscreen.tap(x, y)
                pg.wait_for_timeout(40)
                t = pg.evaluate("(() => { const t = document.getElementById('tip'); const a = t.querySelector('a'); return t.classList.contains('on') && t.classList.contains('touch') ? [t.querySelector('.t').textContent, a.href, getComputedStyle(a).display] : null; })()")
                if t:
                    pinned = dict(x=x, y=y, title=t[0][:80], link=t[1], link_display=t[2])
                    break
            if pinned:
                break
        shot(pg, f"map-{eng}-{lang}-tap")
        rec("map", eng, f"{lang} phone: a tap pins a tooltip with a visible link to the source", bool(pinned) and pinned["link"].startswith("https://") and pinned["link_display"] != "none", pinned)
        # on a phone titles appear only on a tap: after the tooltip is released, the idle tour rings dots without text
        pg.touchscreen.tap(195, 120)
        pg.wait_for_timeout(4500)
        tour = pg.evaluate("(() => { const t = document.getElementById('tip'); return t.classList.contains('on') ? t.querySelector('.t').textContent : ''; })()")
        shot(pg, f"map-{eng}-{lang}-phone-idle")
        rec("map", eng, f"{lang} phone: no title is drawn without a tap (the idle tour only rings notable dots)", not tour, tour[:80])
        ctx.close()


def schemes_and_keys(b, eng, paths):
    for lang in F.LANGS:
        ctx, pg, errors, net = open_page(b, DESK, paths[lang])
        sel = "[...document.querySelectorAll('.tab')].findIndex(t => t.getAttribute('aria-selected') === 'true')"
        on = "[...document.querySelectorAll('.mode')].findIndex(m => m.classList.contains('on'))"
        pg.wait_for_timeout(500)
        a0 = pg.evaluate(sel)
        pg.wait_for_timeout(8000)
        a1, m1 = pg.evaluate(sel), pg.evaluate(on)
        shot(pg, f"schemes-{eng}-{lang}-auto")
        rec("schemes", eng, f"{lang}: the first screen moves to the next scheme by itself (0 → 1 after ~8 s)", a0 == 0 and a1 == 1 and m1 == 1, dict(start=a0, after=a1, mode=m1))
        pg.locator(".tab").nth(3).click()
        pg.wait_for_timeout(1200)
        a2, m2 = pg.evaluate(sel), pg.evaluate(on)
        shot(pg, f"schemes-{eng}-{lang}-click4")
        rec("schemes", eng, f"{lang}: a click on scheme 4 selects it", a2 == 3 and m2 == 3, dict(selected=a2, mode=m2))
        if eng == "chromium":
            pg.reload(); pg.wait_for_timeout(600)
            pg.keyboard.press("Tab")
            f = pg.evaluate("(() => { const e = document.activeElement; return [e.className, getComputedStyle(e).outlineStyle, getComputedStyle(e).outlineWidth]; })()")
            pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(500)
            k1 = pg.evaluate(sel)
            pg.keyboard.press("ArrowLeft"); pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(500)
            k2 = pg.evaluate(sel)
            shot(pg, f"keys-{eng}-{lang}")
            rec("keyboard", eng, f"{lang}: Tab reaches the first scheme tab with a focus ring; arrows move the scheme (1 → 2 → 4)",
                "tab" in f[0] and f[1] != "none" and k1 == 1 and k2 == 3, dict(focus=f, after_right=k1, after_two_left=k2))
        rec("schemes", eng, f"{lang}: no errors or requests", not errors and not net, dict(errors=errors[:3], net=net[:3]))
        ctx.close()


# What a reader sees of the focused element: its opacity with all its ancestors', visibility, focus ring, whether it lies on
# screen below the header (inside its box when text moves inside one) and is the element under the pointer there.
FOCUS_INFO = """(el) => {
  const W = innerWidth, H = innerHeight, hdr = W < 760 ? 48 : 56, r = el.getClientRects()[0] || el.getBoundingClientRect();
  let op = 1; for (let e = el; e && e.nodeType === 1; e = e.parentElement) op *= +getComputedStyle(e).opacity;
  const box = el.closest('.card.ov, .h-a.ov'), br = box && box.getBoundingClientRect();
  const lo = Math.max(hdr, br ? br.top : -1e9), hi = Math.min(H, br ? br.bottom : 1e9);
  const x = Math.min(Math.max(r.left + Math.min(r.width / 2, 24), 1), W - 1), hit = document.elementFromPoint(x, r.top + r.height / 2);
  const on = document.querySelector('.step.on'), st = el.closest('.step'), c = st && st.querySelector('.card'), key = e => e ? e.dataset.sc + '-' + e.dataset.st : null;
  return { what: (el.getAttribute('href') || el.className || el.tagName).slice(0, 70), text: (el.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 40),
           op: Math.round(op * 100) / 100, vis: getComputedStyle(el).visibility, fv: el.matches(':focus-visible'),
           inside: r.top >= lo - 0.5 && r.bottom <= hi + 0.5 && r.left >= -0.5 && r.right <= W + 0.5, hit: !!hit && (hit === el || el.contains(hit)),
           r: [r.left, r.top, r.right, r.bottom].map(Math.round), step: key(st), active: key(on), sy: Math.round(scrollY),
           pinned: c ? Math.abs(c.getBoundingClientRect().top - parseFloat(getComputedStyle(c).top)) < 1 : null };
}"""
STOP_OK = lambda i: i["op"] >= 0.6 and i["vis"] == "visible" and i["fv"] and i["inside"] and i["hit"]
NEXT_KEY = lambda eng: "Tab" if eng == "chromium" else "Alt+Tab"     # WebKit, like Safari, reaches links with Option+Tab


def focus_info(pg):
    return pg.evaluate("(" + FOCUS_INFO + ")(document.activeElement)")


def tab_walk(pg, eng, limit=300, wait=650):
    """Press Tab until focus leaves the page or comes back: every stop must be visible where it is."""
    stops, bad = 0, []
    for _ in range(limit):
        pg.keyboard.press(NEXT_KEY(eng))
        pg.wait_for_timeout(wait)
        tag = pg.evaluate("(() => { const e = document.activeElement; if (!e || e === document.body || e === document.documentElement) return null; if (e.dataset.qaStop) return 'seen'; e.dataset.qaStop = String(window.__qaStops = (window.__qaStops || 0) + 1); return e.dataset.qaStop; })()")
        if tag in (None, "seen"):
            break
        stops += 1
        i = focus_info(pg)
        if not STOP_OK(i):
            bad.append(i)
    return stops, bad


def focus_checks(b, eng, paths):
    ph = dict(PHONE, viewport={"width": 390, "height": 664})
    # 1. the first screen's panel (the reviewers' case): on this phone its text moves inside a clipped box. From the top of the page,
    #    Tab through the first screen must land only on visible stops: the panel's source link, clipped beyond the box while the
    #    panel is hidden, is not a stop then. Once the panel is shown with its text at the first line, Tab reaches that link
    #    (Worse Together) and the page brings it inside the box.
    ctx, pg, errors, net = open_page(b, ph, paths["en"])
    pg.wait_for_timeout(1200)
    H = pg.evaluate("innerHeight")
    hero_stops, bad, reached = 0, [], False
    for _ in range(14):
        pg.keyboard.press(NEXT_KEY(eng))
        pg.wait_for_timeout(650)
        where = pg.evaluate("(() => { const e = document.activeElement; return !e || e === document.body ? 'none' : e.closest('#hA') ? 'panel' : e.closest('#s0, header') ? 'hero' : 'out'; })()")
        if where in ("none", "out"):
            break
        hero_stops += 1
        i = focus_info(pg)
        if not STOP_OK(i):
            bad.append(i)
        if where == "panel":
            reached = True
            break
    shot(pg, f"focus-{eng}-en-390x664-from-top")
    rec("focus", eng, f"en 390x664: from the top, Tab through the first screen lands only on visible stops ({hero_stops}); the hidden panel's clipped source link is not one of them",
        hero_stops >= 4 and not bad and not reached, dict(stops=hero_stops, invisible=bad[:4], reached_hidden_panel=reached))
    ctx.close()
    ctx, pg, errors, net = open_page(b, ph, paths["en"])   # a reader scrolls to the panel, then presses Tab
    pg.wait_for_timeout(1200)
    scroll_to(pg, round(0.45 * H), 900)                # the panel is shown and its text is at its first line: the link lies beyond the box
    link = "document.querySelector('#hA .src a')"
    hidden = not pg.evaluate("(" + FOCUS_INFO + f")({link})")["inside"]
    got = None
    for _ in range(14):
        pg.keyboard.press(NEXT_KEY(eng))
        pg.wait_for_timeout(150)
        if pg.evaluate("!!(document.activeElement.closest && document.activeElement.closest('#hA'))"):
            got = pg.evaluate("document.activeElement.textContent.trim().slice(0, 40)")
            break
    pg.wait_for_timeout(800)
    i = focus_info(pg)
    panel = pg.evaluate("(() => { const a = document.getElementById('hA'); return [a.classList.contains('ov'), +getComputedStyle(a).opacity]; })()")
    shot(pg, f"focus-{eng}-en-390x664-panel-link")
    rec("focus", eng, "en 390x664: with the panel shown and its text at the first line, Tab reaches the panel's source link (Worse Together), clipped beyond the box, and shows it inside the box",
        hidden and bool(got) and got.startswith("Worse Together") and panel[0] and panel[1] > 0.9 and STOP_OK(i), dict(hidden_before=hidden, focused=got, panel_ov_opacity=panel, info=i))
    ctx.close()
    # 2. step 1-4 on the same phone: its text moves inside the pinned card; Tab and a tap on its last source link
    k = "1-4"
    for how in ("tab", "tap"):
        ctx, pg, errors, net = open_page(b, ph, paths["en"])
        pg.wait_for_timeout(1200)
        top, pin, sh, ch = pg.evaluate(PINNED, k)
        scroll_to(pg, top - H * 0.5, 300)
        top, pin, sh, ch = pg.evaluate(PINNED, k)
        sel = f"document.querySelector('.step[data-sc=\"{k[0]}\"][data-st=\"{k[2:]}\"]')"
        ov = pg.evaluate(f"{sel}.querySelector('.card').classList.contains('ov')")
        last = f"{sel}.querySelectorAll('.card .src a')"
        if how == "tab":
            y_start, y_end = top - pin + 0.1 * H, top - pin + 0.1 * H + max(1, sh - ch - 0.22 * H)   # the text at its first line / at its last line
            scroll_to(pg, y_start + 2, 700)
            hidden = not pg.evaluate("(" + FOCUS_INFO + f")([...{last}].pop())")["inside"]   # with a small overflow the link may already show in the fade
            pg.evaluate(f"""(() => {{ const t = [...{last}].pop(), all = [...document.querySelectorAll('a[href], button, [tabindex]:not([tabindex="-1"])')].filter(e => getComputedStyle(e).visibility === 'visible' && e.offsetParent !== null);
                           all[all.indexOf(t) - 1].focus({{ preventScroll: true }}); }})()""")
            pg.wait_for_timeout(700)
            pg.keyboard.press(NEXT_KEY(eng))
            pg.wait_for_timeout(900)
            on_target = pg.evaluate(f"document.activeElement === [...{last}].pop()")
            i = focus_info(pg)
            shot(pg, f"focus-{eng}-en-390x664-s{k}-tab-last-link")
            rec("focus", eng, f"en 390x664: Tab to the last source link of step {k} shows it in the card's box without overshooting: the step stays active, its card pinned, the page no further than the end of the step's text",
                ov and on_target and STOP_OK(i) and i["active"] == k and i["pinned"] and top - pin - 2 <= i["sy"] <= y_end + 2,
                dict(moving=ov, hidden_before=hidden, focused=on_target, scroll_bounds=[round(top - pin), round(y_end)], info=i))
        else:
            # the end of the step's text: the last link is visible in the box; tapping it must not move the page
            range_ = sh - ch - 0.22 * H
            scroll_to(pg, top - pin + 0.1 * H + max(0, range_ - 4), 900)
            t = pg.evaluate("(" + FOCUS_INFO + f")([...{last}].pop())")
            y0 = pg.evaluate("scrollY")
            pop = None
            try:
                with ctx.expect_page(timeout=4000) as pi:
                    pg.touchscreen.tap((t["r"][0] + min(t["r"][2], t["r"][0] + 48)) / 2, (t["r"][1] + t["r"][3]) / 2)
                pop = pi.value
            except Exception:
                pass
            pg.wait_for_timeout(900)
            after = pg.evaluate("(" + FOCUS_INFO + f")([...{last}].pop())")
            y1 = pg.evaluate("scrollY")
            shot(pg, f"focus-{eng}-en-390x664-s{k}-tap-last-link")
            if pop:
                pop.close()
            rec("focus", eng, f"en 390x664: a tap on the last source link of step {k} opens it and moves nothing: the step stays active, its card pinned, the link in place",
                ov and t["inside"] and bool(pop) and abs(y1 - y0) <= 2 and after["active"] == k and after["pinned"] and after["inside"],
                dict(moving=ov, before=t, after=after, scroll=[y0, y1], opened=bool(pop)))
        ctx.close()
    # 3. every Tab stop is visible: a desktop and the short phone, both languages (WebKit: the phone, English)
    views = (("1126x681", dict(viewport={"width": 1126, "height": 681}, device_scale_factor=1)), ("390x664", ph))
    for vname, opts in views:
        for lang in F.LANGS:
            if eng != "chromium" and (vname != "390x664" or lang != "en"):
                continue
            ctx, pg, errors, net = open_page(b, opts, paths[lang])
            pg.wait_for_timeout(1200)
            n, bad = tab_walk(pg, eng)
            rec("focus", eng, f"{lang} {vname}: all {n} Tab stops are visible where they land (opaque, on screen, focus ring, under the pointer)",
                n >= 40 and not bad and not errors, dict(stops=n, invisible=bad[:6], errors=errors[:3]))
            ctx.close()


def resize(b, eng, paths):
    for lang in F.LANGS:
        ctx, pg, errors, net = open_page(b, DESK, paths[lang])
        st = dict(steps(pg))
        scroll_to(pg, st["2-3"], 1200)
        pg.set_viewport_size({"width": 390, "height": 844})
        pg.wait_for_timeout(1500)
        st = dict(steps(pg))
        scroll_to(pg, st["2-3"], 1200)
        ct = pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--ct')")
        hs1 = pg.evaluate(HSCROLL)
        a = shot(pg, f"resize-{eng}-{lang}-to-phone")
        pg.set_viewport_size({"width": 1100, "height": 750})
        pg.wait_for_timeout(1500)
        st = dict(steps(pg))
        scroll_to(pg, st["4-2"], 1300)
        hs2 = pg.evaluate(HSCROLL)
        c = shot(pg, f"resize-{eng}-{lang}-back-desktop")
        rec("resize", eng, f"{lang}: desktop → phone → desktop without reload: phone layout engages, no overflow, frames drawn, no errors",
            bool(ct.strip()) and not hs1 and not hs2 and nonblank(a) > 0.03 and nonblank(c) > 0.03 and not errors and not net, dict(ct=ct, hscroll=[hs1, hs2], errors=errors[:3]))
        ctx.close()


ARRIVE = """(k) => { const s = document.getElementById('s' + k), c = s.querySelector('.card'), ci = c.querySelector('.ci') || c, f = [...ci.children].find(x => x.offsetHeight > 0);
  const on = document.querySelector('.step.on'), cr = c.getBoundingClientRect(), fr = f.getBoundingClientRect(), H = innerHeight;
  return { landed: location.hash, active: on ? on.id : null, ov: c.classList.contains('ov'), sy: Math.round(scrollY),
           first: fr.top >= Math.max(48, cr.top) - 0.5 && fr.bottom <= Math.min(H, cr.bottom) + 0.5, first_box: [Math.round(fr.top), Math.round(fr.bottom)],
           pinned_inside: Math.abs(cr.top - parseFloat(getComputedStyle(c).top)) < 1 && cr.top >= 47.5 && cr.bottom <= H + 0.5, card: [Math.round(cr.top), Math.round(cr.bottom)] }; }"""


def site_checks(b, eng):
    base = os.path.join(ROOT, "site")
    for lang, other in (("ru", "en"), ("en", "ru")):
        ctx, pg, errors, net = open_page(b, DESK, os.path.join(base, lang, "index.html"))
        st = dict(steps(pg))
        scroll_to(pg, st["3-2"], 1300)
        href = pg.evaluate("document.getElementById('lang').getAttribute('href')")
        pg.locator("#lang").click()
        pg.wait_for_load_state("load")
        pg.wait_for_timeout(1500)
        landed = pg.url.split("/site/")[-1]
        act = pg.evaluate("(() => { const s = document.querySelector('.step.on'); return s ? s.id : null; })()")
        shot(pg, f"site-{eng}-{lang}-to-{other}-s3-2")
        rec("site", eng, f"{lang} → {other}: the language link keeps scene 3 step 2 and the other page opens there",
            href.endswith("#s3-2") and landed == f"{other}/index.html#s3-2" and act == "s3-2", dict(href=href, landed=landed, active=act))
        # the hero's second state
        pg.goto("file://" + os.path.join(base, lang, "index.html")); pg.wait_for_timeout(800)
        H = pg.evaluate("innerHeight")
        scroll_to(pg, H, 1200)
        href2 = pg.evaluate("document.getElementById('lang').getAttribute('href')")
        pg.locator("#lang").click(); pg.wait_for_load_state("load"); pg.wait_for_timeout(1500)
        y = pg.evaluate("scrollY")
        op = pg.evaluate("parseFloat(getComputedStyle(document.getElementById('hA')).opacity)")
        shot(pg, f"site-{eng}-{lang}-to-{other}-s0-1")
        rec("site", eng, f"{lang} → {other}: from the delivered-vs-read panel the other language opens on the same panel",
            href2.endswith("#s0-1") and abs(y - H) < 40 and op > 0.5, dict(href=href2, scrollY=y, H=H, panel_opacity=op))
        # an address of the 19 October single page
        pg.goto("file://" + os.path.join(base, lang, "index.html") + "#ch04"); pg.wait_for_timeout(1500)
        landed = pg.url.split("/site/")[-1]
        rec("site", eng, f"{lang}: index.html#ch04 (address of the 19 October single page) lands on the dated survey", landed == f"{lang}/{F.SURVEY_PAGE}#ch04", landed)
        # the survey link at the end
        pg.goto("file://" + os.path.join(base, lang, "index.html")); pg.wait_for_timeout(600)
        st = dict(steps(pg))
        scroll_to(pg, st["7-0"], 1300)
        shot(pg, f"site-{eng}-{lang}-final")
        pg.locator(f'p.more a[href="{F.SURVEY_PAGE}"]').click(); pg.wait_for_load_state("load"); pg.wait_for_timeout(500)
        landed = pg.url.split("/site/")[-1]
        rec("site", eng, f"{lang}: the final scene links to the dated detailed survey", landed == f"{lang}/{F.SURVEY_PAGE}", landed)
        rec("site", eng, f"{lang}: no errors on the Field pages (the survey page's own checks are make qa / qa-features)", not [e for e in errors if "survey" not in e], errors[:3])
        ctx.close()
    # a phone arrives by the language link at a step whose text moves inside its card: the text starts at its first line
    for (w, h), k in (((390, 844), "3-6"), ((390, 664), "5-4")):
        for lang, other in (("ru", "en"), ("en", "ru")):
            ctx, pg, errors, net = open_page(b, dict(PHONE, viewport={"width": w, "height": h}), os.path.join(base, lang, "index.html"))
            pg.wait_for_timeout(1000)
            top, pin, sh, ch = pg.evaluate(PINNED, k)
            scroll_to(pg, top - h * 0.5, 300)
            top, pin, sh, ch = pg.evaluate(PINNED, k)
            scroll_to(pg, top - pin + min(60, max(0, (sh - ch) / 3)), 900)
            href = pg.evaluate("document.getElementById('lang').getAttribute('href')")
            pg.locator("#lang").click()
            pg.wait_for_load_state("load")
            pg.wait_for_timeout(1500)
            r = pg.evaluate(ARRIVE, k)
            shot(pg, f"site-{eng}-{lang}-to-{other}-{w}x{h}-s{k}")
            rec("site", eng, f"{lang} → {other}, {w}x{h} phone: arriving at step {k}, whose text moves inside its card, the step is active and its text starts at the first line",
                href.endswith(f"#s{k}") and r["landed"] == f"#s{k}" and r["active"] == f"s{k}" and r["ov"] and r["first"] and r["pinned_inside"], dict(href=href, **r))
            ctx.close()
    ctx, pg, errors, net = open_page(b, DESK, os.path.join(base, "index.html"))
    pg.locator(".choose a[data-lang='en']").click(); pg.wait_for_load_state("load")
    landed = pg.url.split("/site/")[-1]
    rec("site", eng, "site/index.html: the English choice opens the Field page", landed == "en/index.html", landed)
    ctx.close()


def main():
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "qa_field.jsonl"), "w").close()
    paths = isolate()
    t0 = time.time()
    with sync_playwright() as p:
        for eng in ENGINES:
            b = getattr(p, eng).launch()
            ENGINE_OF[id(b)] = eng
            run = lambda g: GROUPS is None or g in GROUPS
            if run("sweep"):
                for lang in F.LANGS:
                    sweep(b, eng, lang, "desktop", DESK, paths[lang], fast=eng != "chromium")
                    sweep(b, eng, lang, "phone", PHONE, paths[lang], fast=eng != "chromium")
            if run("widths"): widths(b, eng, paths)
            if run("nojs"): nojs(b, eng, paths)
            if run("rm"): reduced(b, eng, paths)
            if run("resize"): resize(b, eng, paths)
            if run("map"): map_checks(b, eng, paths)
            if run("schemes"): schemes_and_keys(b, eng, paths)
            if run("focus"): focus_checks(b, eng, paths)
            if run("site"): site_checks(b, eng)
            R.append(dict(group="meta", engine=eng, check="browser version", ok=True, detail=b.version))
            b.close()
    fails = [r for r in R if not r["ok"]]
    meta = dict(generated=time.strftime("%Y-%m-%d %H:%M:%S"), seconds=round(time.time() - t0), checks=len(R), failed=len(fails),
                files={lang: dict(path=os.path.relpath(paths[lang], ROOT), bytes=os.path.getsize(paths[lang])) for lang in paths})
    with open(os.path.join(OUT, "qa_field.json"), "w", encoding="utf-8") as f:
        json.dump(dict(meta=meta, results=R), f, ensure_ascii=False, indent=1)
    lines = [f"# Field QA — {meta['generated']}", "", f"{len(R) - len(fails)} passed, {len(fails)} failed, {meta['seconds']} s.", ""]
    lines += [f"- {'PASS' if r['ok'] else 'FAIL'} · {r['group']} · {r['engine']} · {r['check']}" + ("" if r["ok"] else f" — `{json.dumps(r['detail'], ensure_ascii=False)[:300]}`") for r in R]
    with open(os.path.join(OUT, "QA_FIELD.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\n{len(R) - len(fails)} passed, {len(fails)} failed → {OUT}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
