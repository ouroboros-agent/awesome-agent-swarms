#!/usr/bin/env python3
"""Regression checks for the defects named in the final reviews of the single page (R1–R5) and their polish items.
Each check drives the built site the way a reader does (typing, clicks, taps, keys, resizes, a changed motion
preference) and fails on the old behaviour.

  python scripts/qa_regress.py [OUTDIR] [--only=R1,R2,R3,R4,R5,P] [--site=DIR]   # default qa/regress/ and site/; Chromium and WebKit

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
R5  edition r5 (B «Контекст»): on the prologue's stage nothing is marked as received, asked or copied, and no journal
    entry or query appears, before the flight that brings it lands; skipping ahead, going back, the motion switch
    (also in mid-flight) and reduced motion leave the state complete with nothing waiting; without JavaScript the
    static figures are complete. Fig. 1.2: every direct label is tied to its own dot (a leader, or beside it) and
    none passes over another highlighted dot without one. Dated segments in the title screen, intro and footer
    («срез 3 октября 2026», "cut-off 3 October 2026") never break inside. The comparison conditions' text is set at normal width, only their heading condensed. The atlas map
    keeps no frame loop. Without JavaScript every figure's close button is on top and closes it. A directly
    addressed source entry or related-work row keeps its place across the language switch.
P   λ chart: the two curve labels never overlap (every choice, the automatic story, both sizes) and the data marks are
    where the formula puts them; the loophole legend on a phone keeps each item to at most two lines; no-JS zoom
    entries are named apart from their figures
Writes OUTDIR/REGRESS.md, OUTDIR/regress.json and screenshots in OUTDIR/shots/; exits 1 if a check fails.
"""
import html as H, json, os, re, sys, time
# Playwright uses its platform default, or the caller's explicit PLAYWRIGHT_BROWSERS_PATH.
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.abspath(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--site=")), os.path.join(ROOT, "site")))   # e.g. a copy of an earlier edition
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

# ---------------------------------------------------------------- R5: edition r5 (stage arrivals, Fig. 1.2, dates, conditions, atlas map, no-JS figures)
def to_step(pg, n, view):
    """Bring prologue step n onto the stage's reading line at once: mid-screen on wide screens, under the stage on phones."""
    pg.evaluate("""([n, f]) => { const r = document.documentElement, sb = r.style.scrollBehavior; r.style.scrollBehavior = 'auto';
      const b = document.getElementById('how-' + n).getBoundingClientRect();
      scrollTo(0, b.top + scrollY + Math.min(b.height / 2, innerHeight * 0.2) - innerHeight * f); r.style.scrollBehavior = sb; }""", [n, 0.485 if view == "desktop" else 0.665])

# Records every frame for ms: the stage state, the flights in the air and how visible each thing is that a flight
# brings. Labels and the journal's queries are found by geometry, so the r5 bytes (no ids on them) measure the same.
STAGE_REC = """([ms]) => {
  const svg = [...document.querySelectorAll('#how .stage svg')].find(s => s.getClientRects().length);
  const v = svg.classList.contains('v-narrow') ? 'narrow' : 'wide', byId = k => document.getElementById(v + '-dyn-' + k);
  const mid = el => { const b = el.getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; };
  const lab = blk => [...svg.querySelectorAll('.k.bl')].find(g => { const t = g.querySelector('text');
    return Math.abs(+t.getAttribute('x') - (+blk.getAttribute('x') + +blk.getAttribute('width') / 2)) < .6
        && Math.abs(+t.getAttribute('y') - (+blk.getAttribute('y') + +blk.getAttribute('height') * .5)) < .6; });
  const T = [], land = {};
  for (const k of ['bC-6', 'b1-5', 'b5-5', 'b1-6', 'b5-6']) { const b = byId(k); if (!b) continue; land[k] = mid(b); T.push([k, b, k]); const l = lab(b); if (l) T.push(['l' + k.slice(1), l, k]); }
  const rec = byId('rec'); if (rec) { land.rec = mid(rec); T.push(['rec', rec.closest('.k'), 'rec']); [...svg.querySelectorAll('.k.beam')].forEach((g, i) => T.push(['q' + i, g, 'rec'])); }
  const S = window.__r5 = [], t0 = performance.now();
  const tick = () => { const now = performance.now();
    S.push({t: Math.round(now - t0), s: svg.getAttribute('data-s'), paused: document.documentElement.classList.contains('paused'),
            fl: [...svg.querySelectorAll('.flight')].map(mid), wait: document.querySelectorAll('#how .wait').length,
            el: T.map(([n, e]) => { const cs = getComputedStyle(e); return [n, cs.visibility === 'visible' ? +(+cs.opacity).toFixed(2) : 0]; })});
    if (now - t0 < ms) requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
  return {variant: v, targets: T.map(([n, , k]) => [n, k]), land};
}"""
COORD = {"bC-6", "lC-6", "b1-5", "l1-5", "b5-5", "l5-5"}
MEM = {"rec", "q0", "q1", "b1-6", "l1-6", "b5-6", "l5-6"}

def arrivals(S, info, state, names):
    """Nothing a flight brings is visible before that flight lands in its block or entry; at the end all of it is."""
    tgt = {n: k for n, k in info["targets"] if n in names}
    t0 = next((x["t"] for x in S if x["s"] == state), None)
    if t0 is None: return False, dict(why="state never shown")
    land, seen = {}, {}
    for x in S:
        if x["t"] < t0: continue
        for k, (cx, cy) in info["land"].items():
            if k not in land and any(abs(fx - cx) < 3 and abs(fy - cy) < 3 for fx, fy in x["fl"]): land[k] = x["t"] - t0
        for n, op in x["el"]:
            if n in tgt and n not in seen and op > .05: seen[n] = x["t"] - t0
    early = {n: dict(seen=seen.get(n), landed=land.get(k)) for n, k in tgt.items()
             if land.get(k) is None or seen.get(n) is None or seen[n] < land[k] - 20}
    end = S[-1]; full = {n: op for n, op in end["el"] if n in tgt}
    ok = not early and all(op >= .99 for op in full.values()) and not end["fl"] and not end["wait"] and len(tgt) == len(names)
    return ok, dict(early=early, landed=land, seen=seen, end=dict(visible=full, flights=len(end["fl"]), waiting=end["wait"]), found=sorted(tgt))

def settled(S, after, names):
    """From `after` ms on: no flight in the air; at the end every named element fully visible and nothing waiting."""
    late = [x for x in S if x["t"] >= after]
    fl = [x["t"] for x in late if x["fl"]]
    end = S[-1]; full = {n: op for n, op in end["el"] if n in names}
    return not fl and all(op >= .99 for op in full.values()) and len(full) == len(names) and not end["wait"], dict(flights_at=fl[:5], end=full, waiting=end["wait"])

def stage_case(pg, view, prep, act, ms=2300):
    for n_ in prep: to_step(pg, n_, view); pg.wait_for_timeout(900)
    info = pg.evaluate(STAGE_REC, [ms])
    act(); pg.wait_for_timeout(ms + 250)
    return pg.evaluate("window.__r5"), info

def r5_stage(p):
    for engine in ENGINES:
        b = getattr(p, engine).launch()
        for view, vp in (("desktop", DESK), ("phone", PHONE)):
            for lang in (("ru", "en") if view == "desktop" else ("ru",)):
                ctx, pg = page(b, vp, motion="no-preference", touch=view == "phone")
                pg.goto(url(lang)); pg.wait_for_timeout(500)
                # forward into the coordinator scheme and into shared memory: arrivals wait for their flights
                S, info = stage_case(pg, view, (5,), lambda: to_step(pg, 6, view))
                ok, d = arrivals(S, info, "coord-2", COORD)
                rec("R5", engine, f"{lang} {view} coordinator: copy and «received» appear only as the flights land; the state ends complete", ok, d)
                S, info = stage_case(pg, view, (8,), lambda: to_step(pg, 9, view))
                ok, d = arrivals(S, info, "mem-2", MEM)
                rec("R5", engine, f"{lang} {view} shared memory: entry, queries and «asked» appear only as the flights land; the state ends complete", ok, d)
                if lang != "ru": ctx.close(); continue
                # mid-flight: the shots show a flight in the air with its landing places still empty, then the landed state
                to_step(pg, 5, view); pg.wait_for_timeout(900); to_step(pg, 6, view); pg.wait_for_timeout(1250)
                shot(pg, f"r5-{engine}-{view}-{lang}-coord-2-in-flight"); pg.wait_for_timeout(900)
                shot(pg, f"r5-{engine}-{view}-{lang}-coord-2-landed")
                # skipping ahead in mid-flight
                def skip():
                    to_step(pg, 6, view); pg.wait_for_timeout(300); to_step(pg, 7, view)
                S, info = stage_case(pg, view, (5,), skip, 1800)
                t1 = next((x["t"] for x in S if x["s"] == "coord-3"), 10 ** 6)
                ok, d = settled(S, t1 + 40, COORD)
                rec("R5", engine, f"{lang} {view} skipping ahead in mid-flight: the flights stop, the next state is complete, nothing waits", ok and t1 < 10 ** 6, d)
                # going back
                S, info = stage_case(pg, view, (7,), lambda: to_step(pg, 6, view), 1200)
                t1 = next((x["t"] for x in S if x["s"] == "coord-2"), 10 ** 6)
                ok, d = settled(S, t1, COORD)
                rec("R5", engine, f"{lang} {view} going back: no flight, the state complete", ok and t1 < 10 ** 6, d)
                # the motion switch in mid-flight
                def pause():
                    to_step(pg, 6, view); pg.wait_for_timeout(350); pg.locator("button.mtg").click()
                S, info = stage_case(pg, view, (5,), pause, 1400)
                tp = next((x["t"] for x in S if x["paused"]), 10 ** 6)
                ok, d = settled(S, tp + 50, COORD)
                rec("R5", engine, f"{lang} {view} the motion switch in mid-flight: the flight stops, the state is complete at once", ok and tp < 10 ** 6, dict(paused_at=tp, **d))
                # paused before: the state changes, nothing flies, everything is there at once
                S, info = stage_case(pg, view, (8,), lambda: to_step(pg, 9, view), 900)
                t1 = next((x["t"] for x in S if x["s"] == "mem-2"), 10 ** 6)
                ok, d = settled(S, t1, MEM)
                full = all(op >= .99 for x in S if x["t"] >= t1 + 60 for n, op in x["el"] if n in MEM)
                rec("R5", engine, f"{lang} {view} paused: the state changes with no flight and is complete at once", ok and full and t1 < 10 ** 6, d)
                pg.locator("button.mtg").click(); pg.wait_for_timeout(200)
                # reduced motion switched on in mid-flight, then off again
                to_step(pg, 8, view); pg.wait_for_timeout(900); to_step(pg, 9, view); pg.wait_for_timeout(300)
                pg.emulate_media(reduced_motion="reduce"); pg.wait_for_timeout(400)
                st = pg.evaluate("""() => ({static: document.documentElement.classList.contains('static'), stage: getComputedStyle(document.querySelector('#how .stage')).display,
                  figs: [...document.querySelectorAll('#how figure.static')].filter(f => f.getClientRects().length).length})""")
                pg.emulate_media(reduced_motion="no-preference"); pg.wait_for_timeout(500)
                info = pg.evaluate(STAGE_REC, [300]); pg.wait_for_timeout(450); S = pg.evaluate("window.__r5")
                ok, d = settled(S, 0, MEM)
                rec("R5", engine, f"{lang} {view} reduced motion in mid-flight: static figures, then back to motion with the state complete",
                    ok and st["static"] and st["stage"] == "none" and st["figs"] == 4, dict(reduced=st, **d))
                ctx.close()
        # without JavaScript, and with reduced motion, the static figures carry every arrival
        for js, motion in ((False, "no-preference"), (True, "reduce")):
            for lang in LANGS:
                ctx, pg = page(b, DESK, motion=motion, js=js)
                pg.goto(url(lang)); pg.wait_for_timeout(400)
                fig = pg.evaluate("""() => { const out = {};
                  for (const s of ['coord-3', 'mem-3']) { const svg = [...document.querySelectorAll('#how figure.static svg')].find(x => x.getAttribute('data-s') === s && x.getClientRects().length);
                    if (!svg) { out[s] = null; continue; }
                    const vis = e => { const c = getComputedStyle(e); return c.visibility === 'visible' && +c.opacity > .99; };
                    out[s] = {labels: [...svg.querySelectorAll('.k.bl')].filter(vis).map(g => g.textContent.trim()), copies: [...svg.querySelectorAll('rect.bk')].filter(r => (r.getAttribute('data-copy') || '').includes(s) && vis(r)).length,
                              entry: [...svg.querySelectorAll('.k.rec')].filter(vis).length, queries: [...svg.querySelectorAll('.k.beam')].filter(vis).length}; }
                  return out; }""")
                c3, m3 = fig.get("coord-3"), fig.get("mem-3")
                ok = bool(c3 and m3) and len(c3["labels"]) >= 4 and c3["copies"] == 2 and len(m3["labels"]) >= 3 and m3["copies"] == 2 and m3["entry"] == 1 and m3["queries"] == 2
                rec("R5", engine, f"{lang} {'no JS' if not js else 'reduced motion'}: the static figures carry every copy, label, entry and query", ok, fig)
                ctx.close()
        b.close()

# Fig. 1.2: each direct label is tied to its own dot. Measured on the rendered SVG (getBBox), per quantity tab.
FIG12 = """() => [...document.querySelectorAll('#ch01 svg.sk-svg')].filter(s => s.getClientRects().length).map(svg => {
  const dots = [...svg.querySelectorAll('a.dot')].map(a => { const c = a.querySelector('circle.mk'); return {w: a.dataset.w, hl: a.classList.contains('hl'),
    v: (a.dataset.v || '').replace(/\\D/g, ''), x: +c.getAttribute('cx'), y: +c.getAttribute('cy'), r: +c.getAttribute('r')}; });
  const labels = [...svg.querySelectorAll('text.dl')].map(t => {
    const b = t.getBBox(), txt = t.textContent, num = txt.split('·').pop().replace(/\\D/g, '');
    const own = (t.dataset.w && dots.find(d => d.w === t.dataset.w)) || dots.find(d => d.hl && d.v && d.v === num) || null;
    if (!own) return {txt, own: null};
    const mid = b.y + b.height / 2, near = t.getAttribute('text-anchor') === 'end' ? own.x - (b.x + b.width) : b.x - own.x;
    const ln = [...svg.querySelectorAll('line.dll')].find(l => l.dataset.w === own.w);
    let leader = false;
    if (ln) { const x1 = +ln.getAttribute('x1'), ys = [+ln.getAttribute('y1'), +ln.getAttribute('y2')];
      const dotEnd = ys.reduce((a, y) => Math.abs(Math.abs(y - own.y) - own.r) < Math.abs(Math.abs(a - own.y) - own.r) ? y : a);
      const txtEnd = ys.find(y => y !== dotEnd);
      leader = Math.abs(x1 - own.x) < .6 && Math.abs(Math.abs(dotEnd - own.y) - own.r) <= 3 && txtEnd >= b.y - 1 && txtEnd <= b.y + b.height + 1 && near >= 0 && near <= 9; }
    const beside = Math.abs(mid - own.y) <= 4 && near >= own.r && near <= own.r + 9;
    const over = dots.filter(d => d.hl && d.w !== own.w && d.x >= b.x - d.r && d.x <= b.x + b.width + d.r && Math.abs(d.y - mid) <= b.height / 2 + 2 * d.r).map(d => d.w);
    return {txt, own: own.w, leader, beside, over};
  });
  return {chart: (svg.classList.contains('sk-w') ? 'w' : 'n') + ':' + svg.closest('.sk-lay').dataset.lay, labels};
})"""
R5_LABELS = {"w:sim": 5, "n:sim": 3, "w:cum": 4, "n:cum": 1, "w:cap": 4, "n:cap": 2}   # as many labels as edition r5 placed

def r5_fig12(p):
    for engine in ENGINES:
        b = getattr(p, engine).launch()
        for lang in LANGS:
            for vp in (DESK, PHONE):
                ctx, pg = page(b, vp)
                pg.goto(url(lang)); pg.wait_for_timeout(400)
                res = []
                for i, lay in enumerate(("sim", "cum", "cap")):
                    pg.locator("#ch01-fig-2 .sk-tab").nth(i).click(); pg.wait_for_timeout(150)
                    jump(pg, "#ch01-fig-2 .sk-lay-" + lay + " svg.sk-" + ("w" if vp is DESK else "n")); pg.wait_for_timeout(150)
                    res += pg.evaluate(FIG12)
                    if lay == "sim": shot(pg, f"r5-{engine}-{lang}-{vp['width']}-fig-1-2-sim")
                bad = [dict(chart=c["chart"], **l) for c in res for l in c["labels"] if not l.get("own") or not (l["leader"] or l["beside"]) or (l["over"] and not l["leader"])]
                few = {c["chart"]: len(c["labels"]) for c in res if len(c["labels"]) < R5_LABELS.get(c["chart"], 0)}
                rec("R5", engine, f"{lang} {vp['width']} Fig. 1.2: every label tied to its own dot (leader or beside it), none over another highlighted dot without one",
                    not bad and not few and len(res) == 3, dict(bad=bad, fewer_than_r5=few, charts=[c["chart"] for c in res]))
                pg.locator("#ch01-fig-2 .sk-tab").nth(0).click()
                ctx.close()
        b.close()

# Dated segments in the title screen, the intro and the footer never break inside (the line breaks between segments)
DATES = """() => { const rx = /\\d{1,2}[ \\u00a0](?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря|January|February|March|April|May|June|July|August|September|October|November|December)[ \\u00a0]\\d{4}/g;
  const out = [];
  for (const [name, el] of [['hero kicker', document.querySelector('.hero .kicker')], ['hero byline', document.querySelector('.hero .meta')],
                            ['intro label', document.querySelector('#survey .label')], ['footer byline', document.querySelector('.foot-in > div:first-child > p:last-child')]]) {
    if (!el) { out.push({name, missing: true}); continue; }
    const node = [...el.childNodes].find(n => n.nodeType === 3), text = node ? node.textContent : '';
    let pos = 0;
    for (const seg of text.split(/[ \\u00a0]·[ \\u00a0]/)) {   // a dated segment («срез 3 октября 2026», "cut-off 3 October 2026") stays on one line
      const i = text.indexOf(seg, pos); pos = i + seg.length; rx.lastIndex = 0;
      if (!rx.test(seg)) continue;
      const r = document.createRange(); r.setStart(node, i); r.setEnd(node, i + seg.length);
      const tops = new Set([...r.getClientRects()].filter(x => x.width > 0).map(x => Math.round(x.top)));
      out.push({name, date: seg.replace(/\\u00a0/g, ' ').replace(/\\u2011/g, '-'), lines: tops.size}); }
    out.push({name, fits: el.scrollWidth <= el.clientWidth + 1, lines: Math.round(el.getBoundingClientRect().height / parseFloat(getComputedStyle(el).lineHeight || '18'))});
  }
  return {items: out, overflow: document.documentElement.scrollWidth > innerWidth + 1}; }"""

def r5_dates(p):
    for engine in ENGINES:
        b = getattr(p, engine).launch()
        for lang in LANGS:
            for vp in ({"width": 320, "height": 568}, PHONE, DESK, {"width": 1440, "height": 900}):
                ctx, pg = page(b, vp)
                pg.goto(url(lang)); pg.wait_for_timeout(300)
                d = pg.evaluate(DATES)
                broken = [x for x in d["items"] if x.get("missing") or ("date" in x and x["lines"] != 1) or x.get("fits") is False]
                dates = sum(1 for x in d["items"] if "date" in x)
                rec("R5", engine, f"{lang} {vp['width']} dated segments never break inside (title screen, intro, footer); no overflow", not broken and dates == 8 and not d["overflow"], dict(broken=broken, dates=dates, overflow=d["overflow"]))
                if vp["width"] in (320, 390): shot(pg, f"r5-{engine}-{lang}-{vp['width']}-title")
                if vp is DESK:
                    jump(pg, "#survey", "start"); pg.wait_for_timeout(300); shot(pg, f"r5-{engine}-{lang}-{vp['width']}-intro")
                ctx.close()
        b.close()

def r5_misc(p):
    for engine in ENGINES:
        b = getattr(p, engine).launch()
        for lang in LANGS:
            # the comparison conditions: body text at normal width, the heading condensed
            ctx, pg = page(b, DESK)
            pg.goto(url(lang)); pg.wait_for_timeout(300)
            jump(pg, ".cond"); pg.wait_for_timeout(200)
            fs = pg.evaluate("""() => { const f = s => getComputedStyle(document.querySelector(s)).fontStretch; return {h: f('.cond :is(h3, h4)'), dt: f('.cond dt'), dd: f('.cond dd'), body: f('.cond')}; }""")
            normal = lambda v: v in ("100%", "normal"); condensed = lambda v: v in ("62.5%", "extra-condensed")
            rec("R5", engine, f"{lang} comparison conditions: text at normal width, heading condensed", normal(fs["dd"]) and normal(fs["dt"]) and condensed(fs["h"]), fs)
            shot(pg, f"r5-{engine}-{lang}-cond")
            ctx.close()
            # the atlas map plays nothing, so it keeps no frame loop; its cells still filter the atlas
            ctx, pg = page(b, DESK, motion="no-preference", init="(() => { const o = window.requestAnimationFrame.bind(window); window.__raf = 0; window.requestAnimationFrame = f => { window.__raf++; return o(f); }; })()")
            pg.goto(url(lang)); pg.wait_for_timeout(400)
            jump(pg, ".atlasmap"); pg.wait_for_timeout(1500)
            pg.evaluate("window.__raf = 0"); pg.wait_for_timeout(1500)
            n_raf = pg.evaluate("window.__raf")
            before = pg.evaluate("[...document.querySelectorAll('.worklist li.w')].filter(e => e.getClientRects().length).length")
            pg.locator(".atlasmap .tm-v").first.click(); pg.wait_for_timeout(300)
            after = pg.evaluate("[...document.querySelectorAll('.worklist li.w')].filter(e => e.getClientRects().length).length")
            rec("R5", engine, f"{lang} atlas map in view: no frame loop while nothing plays; a cell still filters the atlas", n_raf <= 3 and 0 < after < before, dict(raf_in_1_5s=n_raf, rows=[before, after]))
            ctx.close()
            # without JavaScript an opened figure covers the top bar: its close button is on top and closes it
            for vp in (DESK, PHONE):
                ctx, pg = page(b, vp, js=False)
                pg.goto(url(lang)); pg.wait_for_timeout(300)
                ids = pg.evaluate("[...document.querySelectorAll('.lightbox[id]')].map(e => e.id)")
                hidden = []
                for i, lid in enumerate(ids):
                    pg.goto(url(lang, frag="#" + lid)); pg.wait_for_timeout(60)
                    hit = pg.evaluate("""(id) => { const c = document.querySelector('#' + CSS.escape(id) + ' .lb-close'), b = c.getBoundingClientRect();
                      const e = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2); return e === c || c.contains(e) ? null : (e ? e.tagName + '.' + e.className : 'none'); }""", lid)
                    if hit: hidden.append([lid, hit])
                    if i in (0, len(ids) // 2, len(ids) - 1):
                        if i == 0: shot(pg, f"r5-{engine}-{lang}-{vp['width']}-nojs-lightbox")
                        bb = pg.locator(f"#{lid} .lb-close").bounding_box()
                        pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2); pg.wait_for_timeout(120)
                        if pg.locator(f"#{lid}").is_visible(): hidden.append([lid, "still open after a click on ×"])
                rec("R5", engine, f"{lang} {vp['width']} no JS: every figure's close button is on top and closes it ({len(ids)} figures)", ids and not hidden, dict(n=len(ids), bad=hidden[:6], n_bad=len(hidden)))
                ctx.close()
        b.close()

def r5_lang(p):
    """A direct address of a source entry or a related-work row (short rows): the language link carries it both ways, on a
    fresh load and once an in-page jump to it has settled (the page scrolls there smoothly)."""
    for engine in ENGINES:
        b = getattr(p, engine).launch()
        for lang in LANGS:
            other = "en" if lang == "ru" else "ru"
            for vp in ({"width": 1440, "height": 960}, PHONE):
                for frag in ("s-multi-agent-transactive-memory", "w-safety-of-latent-communication"):
                    for how in ("fresh load", "in-page jump"):
                        ctx, pg = page(b, vp, motion="no-preference")
                        if how == "fresh load": pg.goto(url(lang, frag="#" + frag))
                        else: pg.goto(url(lang)); pg.wait_for_timeout(500); pg.evaluate("f => { location.hash = f; }", frag)
                        last = None
                        for _ in range(40):   # until the window rests
                            pg.wait_for_timeout(150); y = pg.evaluate("Math.round(scrollY)")
                            if y == last: break
                            last = y
                        with pg.expect_navigation():
                            pg.locator("a.langbtn").click()
                        pg.wait_for_timeout(700)
                        got = pg.url.split("#", 1)[1] if "#" in pg.url else ""
                        land = pg.evaluate(LANDED, frag)
                        ok = got == frag and land.get("rendered") and 0 <= land["top"] < land["vh"] * 0.6
                        rec("R5", engine, f"{lang}→{other} {vp['width']} {how} #{frag}: the language link keeps the entry", ok, dict(landed=got, place=land))
                        ctx.close()
        b.close()

def r5(p):
    for f in (r5_stage, r5_fig12, r5_dates, r5_misc, r5_lang):
        try: f(p)
        except Exception as e:
            rec("R5", "-", f"{f.__name__} crashed", False, repr(e)[:800])

def main():
    t0 = time.time()
    want = lambda g: ONLY is None or g in ONLY
    if want("R4") or want("P"): r4_static()
    with sync_playwright() as p:
        for f in [f for g, f in (("R1", r1), ("R2", r2), ("R3", r3), ("R4", r4_browser), ("R5", r5), ("P", polish)) if want(g)]:
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
