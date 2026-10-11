#!/usr/bin/env python3
"""Regression checks for the defects named in the final reviews of the single page (R1–R4) and their polish items.
Each check drives the built site the way a reader does (typing, clicks, taps, keys, resizes, a changed motion
preference) and fails on the old behaviour.

  python scripts/qa_regress.py [OUTDIR] [--only=R1,R2,R3,R4,P]   # default qa/regress/; Playwright with Chromium and WebKit

R1  atlas → language: after a search, a topic filter or a reset, the language link carries the row being read, also
    when the new rows are exactly as tall as the old ones (nothing resizes) and with no ResizeObserver at all
R2  HiddenBench and the mind-virus chain: reduced motion switched on while packets fly, with a breakpoint change on
    either side, leaves every responsive variant in its end state (no waiting slot, no packet left); the loophole
    timeline keeps its end state across a breakpoint under reduced motion; playback, Pause and reduced → normal move
R3  the theme control: mouse click, touch tap and keyboard (Tab, Space) at a deep place switch the theme and keep the
    place, under normal and reduced motion; the native checkbox is the focus target and sits on the visible button;
    Shift+Tab onto the skip link keeps the place too
R4  every address a former page forwards with JavaScript has a labelled no-JS entry with the same target; the old
    full.html#index-s-1 works without JavaScript
P   λ chart: the two curve labels never overlap (every choice, the automatic story, both sizes) and the data marks are
    where the formula puts them; the loophole legend on a phone keeps each item to at most two lines; no-JS zoom
    entries are named apart from their figures
Writes OUTDIR/REGRESS.md, OUTDIR/regress.json and screenshots in OUTDIR/shots/; exits 1 if a check fails.
"""
import html as H, json, os, re, sys, time
# Playwright uses its platform default, or the caller's explicit PLAYWRIGHT_BROWSERS_PATH.
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
ONLY = next((a.split("=", 1)[1].upper().split(",") for a in sys.argv[1:] if a.startswith("--only=")), None)   # e.g. --only=R1,P
OUT = os.path.abspath(ARGS[0] if ARGS else os.path.join(ROOT, "qa", "regress"))
SHOTS = os.path.join(OUT, "shots"); os.makedirs(SHOTS, exist_ok=True)
ENGINES, LANGS = ("chromium", "webkit"), ("en", "ru")
DESK, PHONE = {"width": 1240, "height": 844}, {"width": 390, "height": 844}
R = []

def url(lang, page="index", frag=""): return "file://" + os.path.join(SITE, lang, page + ".html") + frag

def rec(group, engine, name, ok, detail=None):
    R.append(dict(group=group, engine=engine, check=name, ok=bool(ok), detail=detail))
    print(("PASS " if ok else "FAIL ") + f"{group} {engine} {name}" + ("" if ok else "  " + json.dumps(detail, ensure_ascii=False)[:600]), flush=True)

def shot(pg, name, sel=None):
    p = os.path.join(SHOTS, name + ".png")
    try:
        (pg.locator(sel).first.screenshot(path=p) if sel else pg.screenshot(path=p))
    except Exception as e:   # a missing shot must not hide a result
        print("  (no screenshot", name, str(e)[:120], ")")

def jump(pg, sel, block="center"):
    """Scroll an element into place at once, then give the page back its own scroll behaviour."""
    pg.evaluate("""([s, b]) => { const r = document.documentElement, sb = r.style.scrollBehavior; r.style.scrollBehavior = 'auto';
      document.querySelector(s).scrollIntoView({block: b}); r.style.scrollBehavior = sb; }""", [sel, block])

def page(b, viewport, motion="reduce", js=True, touch=False, init=None):
    ctx = b.new_context(viewport=viewport, reduced_motion=motion, java_script_enabled=js, has_touch=touch)
    if init: ctx.add_init_script(init)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.errs = errs
    return ctx, pg

# ---------------------------------------------------------------- R1: atlas rows and the language switch
PAIR = """() => {   // two atlas rows of exactly equal height, each the only row its own title finds
  const rows = [...document.querySelectorAll('.worklist li.w')], texts = rows.map(e => e.textContent.toLowerCase()), seen = {};
  for (let i = 0; i < rows.length; i++) {
    const t = rows[i].querySelector('.wt'); if (!t) continue;
    const title = t.textContent.trim(), ws = title.toLowerCase().split(/\\s+/).filter(Boolean);
    if (texts.filter(x => ws.every(w => x.includes(w))).length !== 1) continue;
    const h = rows[i].getBoundingClientRect().height;
    if (seen[h]) return [seen[h], {id: rows[i].id, title, h}];
    seen[h] = {id: rows[i].id, title, h};
  }
  return null; }"""
LANDED = """(id) => { const e = document.getElementById(id); if (!e) return {exists: false};
  const r = e.getBoundingClientRect(); return {exists: true, rendered: e.getClientRects().length > 0, top: Math.round(r.top), vh: innerHeight}; }"""
VISIBLE_ROWS = "() => [...document.querySelectorAll('.worklist li.w')].filter(x => x.getClientRects().length).map(x => x.id)"

def switch_and_check(pg, engine, name, expected, extra):
    href = pg.evaluate("document.querySelector('.langbtn').getAttribute('href')")
    with pg.expect_navigation():
        pg.locator(".langbtn").click()
    pg.wait_for_timeout(900)
    got = pg.url.split("#", 1)[1] if "#" in pg.url else ""
    land = pg.evaluate(LANDED, expected)
    ok = got == expected and land.get("exists") and land.get("rendered") and 0 <= land["top"] < land["vh"] * 0.6
    rec("R1", engine, name, ok, dict(expected=expected, landed=got, href_before_click=href, place=land, **extra))

def r1(p):
    for engine in ENGINES:
        b = getattr(p, engine).launch()
        # the reported path: two searches whose single rows are exactly as tall, then the language link (both ways)
        for lang in LANGS:
            for vp in (DESK, PHONE):
                ctx, pg = page(b, vp)
                pg.goto(url(lang)); pg.wait_for_timeout(500)
                pair = pg.evaluate(PAIR)
                if not pair:
                    rec("R1", engine, f"{lang} {vp['width']} equal-height pair", False, "no pair found"); ctx.close(); continue
                for it in pair:
                    pg.locator("#atlas-q").fill(it["title"]); pg.wait_for_timeout(350)
                    jump(pg, "#" + it["id"], "start"); pg.wait_for_timeout(350)
                switch_and_check(pg, engine, f"{lang}→other {vp['width']} search A then B (equal height {pair[0]['h']})", pair[1]["id"],
                                 dict(pair=[x["id"] for x in pair]))
                ctx.close()
        # no ResizeObserver: the list must still be re-measured after a topic filter and after a reset
        for vp in (DESK, PHONE):
            ctx, pg = page(b, vp, init="delete window.ResizeObserver")
            pg.goto(url("en")); pg.wait_for_timeout(500)
            jump(pg, ".fpanel", "start"); pg.wait_for_timeout(200)
            if not pg.evaluate("document.querySelector('.fpanel').open"): pg.locator(".fpanel > summary").click()
            pg.locator('label[for="ft-memory"]').click(); pg.wait_for_timeout(350)
            rows = pg.evaluate(VISIBLE_ROWS)
            target = rows[min(4, len(rows) - 1)]
            jump(pg, "#" + target, "start"); pg.wait_for_timeout(350)
            switch_and_check(pg, engine, f"en→ru {vp['width']} topic filter, no ResizeObserver", target, dict(visible=len(rows)))
            ctx.close()
            ctx, pg = page(b, vp, init="delete window.ResizeObserver")
            pg.goto(url("en")); pg.wait_for_timeout(500)
            pair = pg.evaluate(PAIR)
            pg.locator("#atlas-q").fill(pair[0]["title"]); pg.wait_for_timeout(300)
            jump(pg, "#" + pair[0]["id"], "start"); pg.wait_for_timeout(300)
            pg.set_viewport_size({"width": vp["width"] + 1, "height": vp["height"]}); pg.wait_for_timeout(250)   # a turn of the phone
            pg.set_viewport_size(vp); pg.wait_for_timeout(350)
            pg.locator("#atlas-reset").click(); pg.wait_for_timeout(350)
            rows = pg.evaluate(VISIBLE_ROWS)
            target = rows[40]
            jump(pg, "#" + target, "start"); pg.wait_for_timeout(350)
            switch_and_check(pg, engine, f"en→ru {vp['width']} search, resize, reset, no ResizeObserver", target, dict(visible=len(rows)))
            ctx.close()
        b.close()

# ---------------------------------------------------------------- R2: scenes settle in every responsive variant
HB = """() => { const e = document.querySelector('#sc-hidden'), s = e.__scene;
  const v = c => { const g = e.querySelector('.hb-svg.' + c), slots = [...g.querySelectorAll('.slot')];
    return {wait: g.querySelectorAll('.slot.wait').length, slots: slots.length,
            shown: slots.filter(x => getComputedStyle(x).display !== 'none' && +getComputedStyle(x).opacity > 0.5).length,
            packets: g.querySelectorAll('.fx > *').length, verdict: getComputedStyle(g.querySelector('.v-ok')).display,
            moves: [...g.querySelectorAll('.fx > *')].map(x => x.getAttribute('transform')).join('|')}; };
  return {phase: e.dataset.phase, static: document.documentElement.classList.contains('static'), ended: e.classList.contains('ended'),
          paused: e.classList.contains('paused'), active: s ? s.active() : null, t: s ? +s.t.toFixed(2) : null, n: v('hb-n'), w: v('hb-w')}; }"""
MV = """() => { const e = document.querySelector('#sc-virus');
  const v = c => { const g = e.querySelector('.mv-svg.' + c), pk = [...g.querySelectorAll('.fx > *')];
    return {packets: pk.length, visible: pk.filter(x => +(x.getAttribute('opacity') || 1) > 0.05).length}; };
  return {armed: e.classList.contains('armed'), static: document.documentElement.classList.contains('static'), n: v('mv-n'), w: v('mv-w')}; }"""
LH = """() => { const e = document.querySelector('#sc-loophole'), g = e.querySelector('.lh-svg.lh-w'), f = g.querySelector('.tl-fill'), ph = g.querySelector('.tl-ph');
  const ax = g.querySelector('.tl-ax'); return {fill: f.style.transform || '(markup)', fillW: Math.round(f.getBoundingClientRect().width),
  axW: Math.round(ax.getBoundingClientRect().width), ph: +ph.getAttribute('x'), axEnd: +ax.getAttribute('x2'), armed: e.classList.contains('armed')}; }"""

def end_state(v): return v["wait"] == 0 and v["packets"] == 0 and v["shown"] == v["slots"] and v["verdict"] == "block"

def r2(p):
    for engine in ENGINES:
        b = getattr(p, engine).launch()
        for lang in LANGS:
            # phone, packets in flight; wide; reduced motion; phone again (the review's sequence, conditioned on the real phase)
            ctx, pg = page(b, PHONE, motion="no-preference", touch=True)
            pg.goto(url(lang)); pg.wait_for_timeout(400)
            jump(pg, "#sc-hidden")
            pg.wait_for_function("""() => { const e = document.querySelector('#sc-hidden'); return e.dataset.phase === 'talk'
              && e.querySelectorAll('.hb-n .slot.wait').length >= 4 && e.querySelectorAll('.hb-n .fx > *').length >= 1; }""", timeout=20000)
            before = pg.evaluate(HB)
            pg.set_viewport_size(DESK); pg.wait_for_timeout(250)
            pg.emulate_media(reduced_motion="reduce"); pg.wait_for_timeout(250)
            pg.set_viewport_size(PHONE); pg.wait_for_timeout(250)
            jump(pg, "#sc-hidden .hb-n"); pg.wait_for_timeout(700)
            after = pg.evaluate(HB)
            rec("R2", engine, f"{lang} HiddenBench talk on phone → wide → reduced → phone", after["static"] and end_state(after["n"]) and end_state(after["w"]),
                dict(before=before, after=after))
            shot(pg, f"r2-{engine}-{lang}-hidden-phone-after-reduce", "#sc-hidden")
            # reduced → normal: the scene plays again from its start, packets move, Pause holds it
            pg.emulate_media(reduced_motion="no-preference"); pg.wait_for_timeout(300)
            try:
                pg.wait_for_function("() => document.querySelectorAll('#sc-hidden .hb-n .fx > *').length >= 1", timeout=12000)
                a = pg.evaluate(HB); pg.wait_for_timeout(200); b2 = pg.evaluate(HB)
                moving = a["n"]["moves"] != b2["n"]["moves"] or a["t"] != b2["t"]
            except Exception as e:
                a = b2 = {"error": str(e)[:200]}; moving = False
            rec("R2", engine, f"{lang} HiddenBench reduced → normal plays again", moving and not b2.get("static", True), dict(a=a, b=b2))
            ctx.close()
        # the forced reveal: reduced motion while its packets fly (wide)
        ctx, pg = page(b, DESK, motion="no-preference")
        pg.goto(url("en")); pg.wait_for_timeout(400)
        jump(pg, "#sc-hidden")
        pg.wait_for_function("""() => { const e = document.querySelector('#sc-hidden'); return e.dataset.phase === 'swap'
          && e.querySelectorAll('.hb-w .fx > *').length >= 1; }""", timeout=25000)
        before = pg.evaluate(HB)
        pg.emulate_media(reduced_motion="reduce"); pg.wait_for_timeout(700)
        after = pg.evaluate(HB)
        rec("R2", engine, "en HiddenBench reduced motion during the forced reveal", end_state(after["w"]) and end_state(after["n"]), dict(before=before, after=after))
        shot(pg, f"r2-{engine}-en-hidden-reveal-reduce", "#sc-hidden")
        ctx.close()
        # normal playback, Pause, natural end
        ctx, pg = page(b, PHONE, motion="no-preference", touch=True)
        pg.goto(url("en")); pg.wait_for_timeout(400)
        jump(pg, "#sc-hidden")
        pg.wait_for_function("() => document.querySelectorAll('#sc-hidden .hb-n .fx > *').length >= 1", timeout=20000)
        a = pg.evaluate(HB); pg.wait_for_timeout(150); m = pg.evaluate(HB)
        pg.locator("#sc-hidden .sc-pp").click(); pg.wait_for_timeout(100)
        p1 = pg.evaluate(HB); pg.wait_for_timeout(700); p2 = pg.evaluate(HB)
        pg.locator("#sc-hidden .sc-pp").click()
        try:
            pg.wait_for_function("() => document.querySelector('#sc-hidden').classList.contains('ended')", timeout=25000)
            pg.wait_for_timeout(600); end = pg.evaluate(HB)
        except Exception as e:
            end = {"error": str(e)[:200], "n": {"wait": -1, "packets": -1, "shown": 0, "slots": 1, "verdict": "none"}}
        ok = (a["n"]["moves"] != m["n"]["moves"]) and p1["paused"] and p1["n"]["moves"] == p2["n"]["moves"] and p1["t"] == p2["t"] and end_state(end["n"])
        rec("R2", engine, "en HiddenBench plays, Pause holds the packets, the natural end is complete", ok, dict(moving=[a["t"], m["t"]], paused=[p1["t"], p2["t"]], end=end))
        ctx.close()
        # the mind-virus chain: the same sequence with its packets
        ctx, pg = page(b, PHONE, motion="no-preference", touch=True)
        pg.goto(url("en")); pg.wait_for_timeout(400)
        jump(pg, "#sc-virus")
        pg.wait_for_function("() => [...document.querySelectorAll('#sc-virus .mv-n .fx > *')].some(x => x.getAttribute('opacity') === '1')", timeout=20000)
        before = pg.evaluate(MV)
        pg.set_viewport_size(DESK); pg.wait_for_timeout(250)
        pg.emulate_media(reduced_motion="reduce"); pg.wait_for_timeout(250)
        pg.set_viewport_size(PHONE); pg.wait_for_timeout(250)
        jump(pg, "#sc-virus .mv-n"); pg.wait_for_timeout(600)
        after = pg.evaluate(MV)
        rec("R2", engine, "en mind-virus chain on phone → wide → reduced → phone", after["static"] and not after["armed"] and after["n"]["packets"] == 0 and after["w"]["packets"] == 0,
            dict(before=before, after=after))
        shot(pg, f"r2-{engine}-en-virus-phone-after-reduce", "#sc-virus")
        ctx.close()
        ctx, pg = page(b, DESK, motion="no-preference")
        pg.goto(url("en")); pg.wait_for_timeout(400)
        jump(pg, "#sc-virus")
        pg.wait_for_function("() => [...document.querySelectorAll('#sc-virus .mv-w .fx > *')].some(x => x.getAttribute('opacity') === '1')", timeout=20000)
        before = pg.evaluate(MV)
        pg.emulate_media(reduced_motion="reduce"); pg.wait_for_timeout(600)
        after = pg.evaluate(MV)
        rec("R2", engine, "en mind-virus chain: reduced motion while packets fly", after["w"]["packets"] == 0 and after["n"]["packets"] == 0 and not after["armed"], dict(before=before, after=after))
        ctx.close()
        # the loophole timeline under reduced motion: a breakpoint change keeps the end state
        ctx, pg = page(b, PHONE, motion="reduce", touch=True)
        pg.goto(url("en")); pg.wait_for_timeout(400)
        jump(pg, "#sc-loophole"); pg.wait_for_timeout(300)
        pg.set_viewport_size(DESK); pg.wait_for_timeout(400)
        jump(pg, "#sc-loophole"); pg.wait_for_timeout(300)
        st = pg.evaluate(LH)
        rec("R2", engine, "en loophole timeline, reduced motion, phone → wide", abs(st["fillW"] - st["axW"]) <= 8 and abs(st["ph"] - st["axEnd"]) <= 1, st)
        shot(pg, f"r2-{engine}-en-loophole-wide-after-resize", "#sc-loophole")
        ctx.close()
        b.close()

# ---------------------------------------------------------------- R3: the theme control keeps the place
GEOM = """() => { const c = document.getElementById('theme'), l = document.querySelector('.themebtn'), a = c.getBoundingClientRect(), b = l.getBoundingClientRect();
  return {box: [a.left, a.top, a.width, a.height].map(Math.round), label: [b.left, b.top, b.width, b.height].map(Math.round),
          inside: a.left >= b.left - 1 && a.right <= b.right + 1 && a.top >= b.top - 1 && a.bottom <= b.bottom + 1}; }"""
STATE3 = """() => ({y: Math.round(scrollY), light: document.documentElement.classList.contains('light'), checked: document.getElementById('theme').checked,
  active: (a => a ? (a.id || (a.getAttribute && a.getAttribute('class')) || a.tagName) : null)(document.activeElement),
  ring: getComputedStyle(document.querySelector('.themebtn')).outlineStyle})"""

def deep(pg, frag="#ch07-s-4"):
    pg.goto(url("en", frag=frag)); pg.wait_for_timeout(1200)
    jump(pg, frag, "start"); pg.wait_for_timeout(500)

def r3(p):
    for engine in ENGINES:
        b = getattr(p, engine).launch()
        for motion in ("no-preference", "reduce"):
            for how in ("click", "tap", "keyboard"):
                vp = PHONE if how == "tap" else DESK
                # keyboard: from the contents button (where Escape leaves focus) by Tab to the theme control, then Space.
                # WebKit, like Safari with “Press Tab to highlight each item” off, may pass form controls by on Tab:
                # then the same walk with Option+Tab, on a fresh page, is the one judged.
                for key in ((("Tab", "Alt+Tab") if engine == "webkit" else ("Tab",)) if how == "keyboard" else (None,)):
                    ctx, pg = page(b, vp, motion=motion, touch=how == "tap")
                    deep(pg)
                    s0 = pg.evaluate(STATE3); path = []
                    if how == "click": pg.locator(".themebtn").click()
                    elif how == "tap": pg.locator(".themebtn").tap()
                    else:
                        pg.focus(".mtoc > summary"); s0 = pg.evaluate(STATE3)
                        for _ in range(4):
                            pg.keyboard.press(key); pg.wait_for_timeout(120); st = pg.evaluate(STATE3); path.append([st["active"], st["y"]])
                            if st["active"] == "theme": break
                        if path[-1][0] == "theme":
                            pg.wait_for_timeout(200); path.append(["ring", pg.evaluate(STATE3)["ring"]]); pg.keyboard.press("Space")
                    pg.wait_for_timeout(900)
                    s1 = pg.evaluate(STATE3); g = pg.evaluate(GEOM)
                    ys = [s0["y"]] + [y for a, y in path if a != "ring"] + [s1["y"]]
                    ok = s1["light"] != s0["light"] and max(abs(y - s0["y"]) for y in ys) <= 2
                    reached = any(a == "theme" for a, _ in path)
                    if how == "keyboard": ok = ok and reached and any(a == "ring" and y != "none" for a, y in path)
                    name = f"theme by {how}{' (' + key + ')' if key else ''}, {motion}, {vp['width']} at #ch07-s-4"
                    if key == "Tab" and engine == "webkit" and not reached:   # the browser's own order, recorded; the Option+Tab walk is judged
                        rec("R3", engine, name + ": Tab passes the control by (Safari convention), see Option+Tab", True, dict(tab_path=path))
                    else:
                        rec("R3", engine, name, ok, dict(before=s0, after=s1, tab_path=path, geometry=g))
                    if motion == "no-preference": shot(pg, f"r3-{engine}-{how}{'-' + key.replace('+', '') if key else ''}-{vp['width']}-after")
                    ctx.close()
                    if key == "Tab" and reached: break
        # Shift+Tab from the brand reaches the skip link: the place stays
        ctx, pg = page(b, DESK, motion="no-preference")
        deep(pg)
        pg.focus(".brand"); s0 = pg.evaluate(STATE3)
        pg.keyboard.press("Shift+Tab"); pg.wait_for_timeout(700)
        s1 = pg.evaluate(STATE3)
        rec("R3", engine, "Shift+Tab from the brand onto the skip link keeps the place", abs(s1["y"] - s0["y"]) <= 2, dict(before=s0, after=s1))
        shot(pg, f"r3-{engine}-skip-focused")
        ctx.close()
        # no JavaScript: the label still switches the theme, nothing moves
        ctx, pg = page(b, DESK, js=False)
        pg.goto(url("en", frag="#ch07-s-4")); pg.wait_for_timeout(800)
        y0 = pg.evaluate("Math.round(scrollY)")
        bg0 = pg.evaluate("getComputedStyle(document.body).backgroundColor")
        pg.locator(".themebtn").click(); pg.wait_for_timeout(500)
        y1 = pg.evaluate("Math.round(scrollY)"); bg1 = pg.evaluate("getComputedStyle(document.body).backgroundColor")
        rec("R3", engine, "no-JS theme label switches the theme and keeps the place", bg0 != bg1 and abs(y1 - y0) <= 2, dict(y=[y0, y1], bg=[bg0, bg1]))
        ctx.close()
        b.close()

# ---------------------------------------------------------------- R4: former pages without JavaScript
def stub_lists(lang):
    out = {}
    for f in sorted(os.listdir(os.path.join(SITE, lang))):
        if not f.endswith(".html") or f == "index.html": continue
        t = open(os.path.join(SITE, lang, f), encoding="utf-8").read()
        m = re.search(r"var m=(\{.*?\}),d=(\"[^\"]*\")", t)
        if not m: continue
        lis = re.findall(r'<li id="([^"]+)"><a href="index\.html#([^"]*)">(.*?)</a></li>', t)
        out[f] = (json.loads(m.group(1)), [(H.unescape(i), H.unescape(h), H.unescape(re.sub(r"<[^>]+>", "", lab)).strip()) for i, h, lab in lis])
    return out

def r4_static():
    for lang in LANGS:
        missing, nmap, dup_zoom = [], 0, []
        for f, (amap, lis) in stub_lists(lang).items():
            by = {i: (h, lab) for i, h, lab in lis}
            for k, v in amap.items():
                nmap += 1
                if k not in by or by[k][0] != v or not by[k][1]: missing.append(f"{f}#{k}→{v}: {by.get(k)}")
            labels = {}
            for i, h, lab in lis: labels.setdefault(lab, []).append(i)
            for i, h, lab in lis:
                mz = re.match(r"zoom-(\d+)$", i)
                if mz and ("fig-" + mz.group(1) in by and by["fig-" + mz.group(1)][1] == lab or len(labels[lab]) > 1): dup_zoom.append(f"{f}#{i} “{lab}”")
        rec("R4", "static", f"{lang}: every forwarded address has a labelled no-JS entry with the same target", not missing, dict(map_entries=nmap, missing=missing[:20], n_missing=len(missing)))
        rec("P", "static", f"{lang}: no-JS zoom entries are named apart from their figures", not dup_zoom, dict(n=len(dup_zoom), examples=dup_zoom[:6]))

def r4_browser(p):
    for engine in ENGINES:
        b = getattr(p, engine).launch()
        for lang in LANGS:
            ctx, pg = page(b, DESK, js=False)
            pg.goto(url(lang, "full", "#index-s-1")); pg.wait_for_timeout(400)
            t = pg.evaluate("() => { const t = document.querySelector(':target'); const a = t && t.querySelector('a'); return t ? {id: t.id, href: a && a.getAttribute('href'), text: a && a.textContent.trim()} : null; }")
            shot(pg, f"r4-{engine}-{lang}-full-index-s-1-nojs")
            landed = None
            if t and t.get("href"):
                with pg.expect_navigation(): pg.locator(":target a").click()
                pg.wait_for_timeout(400)
                landed = pg.evaluate("() => { const t = document.querySelector(':target'); return {url: location.href.split('/').slice(-2).join('/'), target: t && t.id, text: t && t.textContent.trim().slice(0, 60)}; }")
            ok = bool(t and t["id"] == "index-s-1" and t["href"] == "index.html#s-1" and t["text"] and landed and landed["target"] == "s-1")
            rec("R4", engine, f"{lang} no-JS full.html#index-s-1 lists its place and the link lands on #s-1", ok, dict(target=t, landed=landed))
            ctx.close()
            ctx, pg = page(b, DESK)
            pg.goto(url(lang, "full", "#index-s-1")); pg.wait_for_timeout(900)
            rec("R4", engine, f"{lang} with JS full.html#index-s-1 forwards to index.html#s-1", pg.url.endswith(f"/{lang}/index.html#s-1"), pg.url.split("/")[-1])
            ctx.close()
        b.close()

# ---------------------------------------------------------------- polish: λ labels, loophole legend
LXM = """() => { const c = document.querySelector('#sc-lambda .lx-chart'), s = c.querySelector('.cl-s'), k = c.querySelector('.cl-c');
  const a = s.getBoundingClientRect(), b = k.getBoundingClientRect(), lx = document.querySelector('#sc-lambda .lx');
  return {ov: +(Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top)).toFixed(2), sy: +s.getAttribute('y'), cy: +k.getAttribute('y'),
          ms: +c.querySelector('.m-s').getAttribute('cy'), mc: +c.querySelector('.m-c').getAttribute('cy'), cs: c.querySelector('.c-s').getAttribute('d').split(' L').pop(),
          read: document.querySelector('#sc-lambda .lx-read').textContent}; }"""

def Yf(f):
    import math
    return 196 - math.log2(f) / 4 * 176

def lam_ok(m, N, L):
    """No overlap; the marks sit where the formula puts them; each label stays beside the end of its own curve."""
    data = abs(m["ms"] - Yf(N ** L)) < 0.06 and abs(m["mc"] - Yf(N ** (1 - L))) < 0.06 and abs(float(m["cs"].split()[1]) - Yf(16 ** L)) < 0.06
    near = abs(m["sy"] - Yf(16 ** L)) <= 9 and abs(m["cy"] - Yf(16 ** (1 - L))) <= 9
    order = L == 0.5 or (m["sy"] < m["cy"]) == (L > 0.5)   # the label of the higher curve stays above
    return m["ov"] <= 0 and data and near and order

def polish(p):
    for engine in ENGINES:
        b = getattr(p, engine).launch()
        for lang in LANGS:
            for vp in (DESK, PHONE):
                ctx, pg = page(b, vp)
                pg.goto(url(lang)); pg.wait_for_timeout(400)
                jump(pg, "#sc-lambda"); pg.wait_for_timeout(300)
                bad = []
                for N in (4, 16):
                    pg.locator(f'#sc-lambda .opt[data-n="{N}"]').click()
                    for L in (0.48, 0.5, 0.57, 0.68, 1.0):
                        pg.locator(f'#sc-lambda .opt[data-l="{L}"]').click(); pg.wait_for_timeout(60)
                        m = pg.evaluate(LXM)
                        if not lam_ok(m, N, L): bad.append(dict(N=N, L=L, **m))
                        if N == 16 and L in (0.48, 0.5): shot(pg, f"p-{engine}-{lang}-{vp['width']}-lambda-{L}", "#sc-lambda .lx-side")
                rec("P", engine, f"{lang} {vp['width']} λ labels apart, marks on the formula (10 choices)", not bad, bad[:3])
                ctx.close()
        # the automatic story passes through λ = 0.48
        ctx, pg = page(b, DESK, motion="no-preference")
        pg.goto(url("en")); pg.wait_for_timeout(400)
        jump(pg, "#sc-lambda")
        pg.wait_for_function("() => /λ = 0\\.48/.test(document.querySelector('#sc-lambda .lx-read').textContent)", timeout=20000)
        m = pg.evaluate(LXM)
        rec("P", engine, "en story beat at λ = 0.48: labels apart", lam_ok(m, 16, 0.48), m)
        shot(pg, f"p-{engine}-en-lambda-story-0.48", "#sc-lambda .lx-side")
        ctx.close()
        # the loophole legend on phones
        for lang in LANGS:
            for w in (390, 360):
                ctx, pg = page(b, {"width": w, "height": 844}, touch=True)
                pg.goto(url(lang)); pg.wait_for_timeout(400)
                jump(pg, "#sc-loophole .lh-leg-n"); pg.wait_for_timeout(300)
                leg = pg.evaluate("""() => { const ul = document.querySelector('#sc-loophole .lh-leg-n'), u = ul.getBoundingClientRect();
                  return [...ul.querySelectorAll('li')].map(li => { const tops = new Set();
                    for (const n of li.childNodes) { if (n.nodeType !== 3 || !n.textContent.trim()) continue;   // the words; the icon and the number sit beside them
                      const r = document.createRange(); r.selectNodeContents(n); for (const x of r.getClientRects()) if (x.width > 1) tops.add(Math.round(x.top)); }
                    const b = li.getBoundingClientRect(); return {text: li.textContent.trim(), lines: tops.size, inside: b.left >= u.left - 1 && b.right <= u.right + 1}; }); }""")
                worst = max(x["lines"] for x in leg)
                rec("P", engine, f"{lang} {w} loophole legend: at most two lines an item", worst <= 2 and all(x["inside"] for x in leg), leg)
                shot(pg, f"p-{engine}-{lang}-{w}-loophole-legend", "#sc-loophole .lh-n")
                ctx.close()
        b.close()

def main():
    t0 = time.time()
    want = lambda g: ONLY is None or g in ONLY
    if want("R4") or want("P"): r4_static()
    with sync_playwright() as p:
        for f in [f for g, f in (("R1", r1), ("R2", r2), ("R3", r3), ("R4", r4_browser), ("P", polish)) if want(g)]:
            try: f(p)
            except Exception as e:   # one broken group must not hide the others
                rec(f.__name__.split("_")[0].upper(), "-", f"{f.__name__} crashed", False, repr(e)[:800])
    bad = [x for x in R if not x["ok"]]
    json.dump(dict(results=R, failed=len(bad), passed=len(R) - len(bad), seconds=round(time.time() - t0)), open(os.path.join(OUT, "regress.json"), "w"), ensure_ascii=False, indent=1)
    lines = [f"# Regression checks — {len(R) - len(bad)} passed, {len(bad)} failed ({round(time.time() - t0)} s)", ""]
    for x in R: lines.append(f"- {'PASS' if x['ok'] else 'FAIL'} · {x['group']} · {x['engine']} · {x['check']}")
    open(os.path.join(OUT, "REGRESS.md"), "w").write("\n".join(lines) + "\n")
    print(f"passed {len(R) - len(bad)}, failed {len(bad)}; {OUT}")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
