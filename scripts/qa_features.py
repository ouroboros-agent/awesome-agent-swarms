#!/usr/bin/env python3
"""Feature QA of the single page, complementing scripts/qa_browser.py (loads, images, overflow, no-JS basics).

  python scripts/qa_features.py [OUTDIR]      # default qa/features/; needs Playwright with Chromium and WebKit

Browser (Chromium = Playwright build, WebKit; desktop 1240×722, phone 390×844):
  prologue moves by itself and advances schemes; pause holds it; it stops off screen
  every scene: idle before it is seen, moves when on screen (an intermediate state is captured), stops off screen,
    its pause holds it; reduced motion shows the end state and never moves
  part statements light up with the scroll (--p rises); chapter plates pin and get covered (--c rises)
  the top bar names the chapter being read; the contents sheet opens on it
  the language switch keeps the place (a section deep in a chapter, a card) and the other page lands there
  in-page links and Back: a chapter reference jumps, history.back() returns to the place
  figure viewer: opens fitted, pages with →, zooms, Esc closes and returns focus; Back closes it too
  atlas: search narrows the list; a topic × evidence cell (Fig. 1.6 and the atlas map) filters it; reset restores
  the scale dashboard: tabs switch quantities; a dot shows its work; theme switch persists across reload and language
Static: every registry figure is on the page, README image paths exist, then README rendered light/dark.
Writes OUTDIR/FEATURES.md and OUTDIR/features.json; screenshots in OUTDIR/shots/.
"""
import json, os, pwd, re, sys, time
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", os.path.join(pwd.getpwuid(os.getuid()).pw_dir, "Library/Caches/ms-playwright"))
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "qa", "features"))
SHOTS = os.path.join(OUT, "shots"); os.makedirs(SHOTS, exist_ok=True)
VIEWS = {"desktop": dict(viewport={"width": 1240, "height": 722}, device_scale_factor=1),
         "phone": dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, has_touch=True)}
SCENES = ["#ch01-fig-1", "#sc-lambda", "#sc-hidden", "#sc-virus", "#sc-loophole", "#sc-echo", "#sc-consensus", "#sc-moltbook"]
R = {"static": {}, "browser": [], "shots": []}

def url(lang, frag=""): return "file://" + os.path.join(SITE, lang, "index.html") + frag

def rec(engine, view, name, ok, detail=None):
    R["browser"].append({"engine": engine, "view": view, "check": name, "ok": bool(ok), "detail": detail})

def shot(pg, name):
    p = os.path.join(SHOTS, name + ".png"); pg.screenshot(path=p); R["shots"].append(os.path.relpath(p, OUT))

def jump(pg, sel, block="center"):
    pg.evaluate("([s, b]) => { document.documentElement.style.scrollBehavior = 'auto'; const e = document.querySelector(s); if (e) e.scrollIntoView({block: b}); }", [sel, block])

STATE = """(sel) => { const e = document.querySelector(sel); if (!e) return null;
  const h = s => { let x = 2166136261; for (let i = 0; i < s.length; i++) { x ^= s.charCodeAt(i); x = Math.imul(x, 16777619); } return (x >>> 0).toString(36); };
  const parts = [...e.querySelectorAll('.lx-tr i, .lx-trs, .lx-tb i, .op, .pc, .ad, .nd, .ed, .fx *, .rib circle, .rib path, .slot, .fm-col, .beats li, .ec-meter b, .sv2, .mk.live, canvas, .verdict')]
    .map(x => (x.getAttribute('style') || '') + (x.getAttribute('class') || '') + (x.getAttribute('cx') || '') + (x.getAttribute('cy') || '') + (x.getAttribute('transform') || '') + (x.getAttribute('opacity') || '') + (x.tagName === 'B' ? x.textContent : '') + (x.tagName === 'CANVAS' ? x.width + 'x' + x.height + (x.toDataURL ? x.toDataURL().length : '') : ''));
  return {beat: e.getAttribute('data-beat'), shown: e.classList.contains('shown'), ended: e.classList.contains('ended'), paused: e.classList.contains('paused'),
          phase: e.getAttribute('data-phase'), sig: h(parts.join('|'))}; }"""

def scene_checks(pg, engine, view, lang):
    for sel in SCENES:
        name = sel.strip("#")
        jump(pg, "#top", "start"); pg.wait_for_timeout(250)
        idle = pg.evaluate(STATE, sel)
        jump(pg, sel); pg.wait_for_timeout(1400)
        a = pg.evaluate(STATE, sel)
        pg.wait_for_timeout(1300)
        b = pg.evaluate(STATE, sel)
        if view == "desktop" and lang == "en": shot(pg, f"{engine}-{view}-{lang}-{name}-mid")
        moving = a and b and (a["beat"] != b["beat"] or a["sig"] != b["sig"])
        rec(engine, view, f"{lang}: {name} idle until seen, then moves on screen (intermediate state captured)",
            idle and not idle["shown"] and a["shown"] and moving, {"idle": idle, "t1.4s": a, "t2.7s": b})
        # pause holds it
        btn = pg.locator(sel + " .sc-pp")
        if btn.count() and not b["ended"]:
            btn.first.click(); pg.wait_for_timeout(150)
            p0 = pg.evaluate(STATE, sel); pg.wait_for_timeout(900); p1 = pg.evaluate(STATE, sel)
            held = p0["paused"] and p0["beat"] == p1["beat"] and p0["sig"] == p1["sig"]
            btn.first.click(); pg.wait_for_timeout(100)
            rec(engine, view, f"{lang}: {name} pause holds the scene", held, {"p0": p0, "p1": p1})
        # off screen it stops
        jump(pg, "#atlas", "start"); pg.wait_for_timeout(500)
        o0 = pg.evaluate(STATE, sel); pg.wait_for_timeout(1000); o1 = pg.evaluate(STATE, sel)
        rec(engine, view, f"{lang}: {name} stops off screen", o0["beat"] == o1["beat"] and o0["sig"] == o1["sig"], {"o0": o0, "o1": o1})

def run_engine(p, engine):
    b = p.chromium.launch() if engine == "chromium" else p.webkit.launch()
    ver = b.version
    for view, vopt in VIEWS.items():
        ctx = b.new_context(**vopt); pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        # --- prologue
        pg.goto(url("ru")); pg.wait_for_timeout(300)
        s0 = pg.evaluate("({mode: document.getElementById('how').dataset.mode, beat: document.querySelector('.narr').dataset.beat})")
        pg.wait_for_timeout(2900)
        s1 = pg.evaluate("""() => ({mode: document.getElementById('how').dataset.mode, beat: document.querySelector('.narr').dataset.beat,
                 fx: [...document.querySelectorAll('svg.tp')].find(s => s.getClientRects().length).querySelectorAll('.fx .pk').length})""")
        rec(engine, view, "ru: prologue moves by itself (beat 0→≥1, packets)", s0["beat"] == "0" and s1["beat"] != "0" and s1["fx"] > 0, {"t0": s0, "t3s": s1})
        if view == "desktop":
            t0 = time.time(); mode = "ind"
            while time.time() - t0 < 14 and mode == "ind":
                pg.wait_for_timeout(500); mode = pg.evaluate("document.getElementById('how').dataset.mode")
            rec(engine, view, "ru: prologue advances to the next scheme without a Start button", mode == "coord", {"after_s": round(time.time() - t0, 1)})
        pg.locator("#how .pp").click(); b0 = pg.evaluate("document.querySelector('.narr').dataset.beat"); pg.wait_for_timeout(2000)
        b1 = pg.evaluate("document.querySelector('.narr').dataset.beat"); pg.locator("#how .pp").click()
        rec(engine, view, "ru: prologue pause holds", b0 == b1, [b0, b1])
        jump(pg, "#ch03", "start"); pg.wait_for_timeout(600)
        rec(engine, view, "ru: prologue stops off screen", pg.evaluate("document.getElementById('how').classList.contains('offscreen')"))
        # --- scenes
        for lang in (("en", "ru") if view == "desktop" else ("en",)):
            pg.goto(url(lang)); pg.wait_for_timeout(400)
            scene_checks(pg, engine, view, lang)
        # --- part statements and plates: scroll-linked values
        pg.goto(url("en")); pg.wait_for_timeout(300)
        # two reading positions: the statement's top at 90 %, then at 30 % of the viewport (independent of the section's height,
        # which an end/start alignment is not: a statement taller than the viewport reverses that comparison)
        P2 = "parseFloat(getComputedStyle(document.getElementById('part-2')).getPropertyValue('--p'))"
        pg.evaluate("f => { document.documentElement.style.scrollBehavior = 'auto'; const e = document.getElementById('part-2'); scrollTo(0, e.getBoundingClientRect().top + scrollY - innerHeight * f); }", 0.9); pg.wait_for_timeout(400); pa = pg.evaluate(P2)
        pg.evaluate("f => { document.documentElement.style.scrollBehavior = 'auto'; const e = document.getElementById('part-2'); scrollTo(0, e.getBoundingClientRect().top + scrollY - innerHeight * f); }", 0.3); pg.wait_for_timeout(400); pb = pg.evaluate(P2)
        rec(engine, view, "part statement: --p rises as it is read (word highlight follows the scroll)", pa < pb, [pa, pb])
        jump(pg, "#ch04", "start"); pg.wait_for_timeout(400)
        pin = pg.evaluate("document.querySelector('#ch04 .plate').classList.contains('pin')")
        c0 = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('#ch04 .plate')).getPropertyValue('--c')) || 0")
        pg.evaluate("window.scrollBy(0, innerHeight * 0.6)"); pg.wait_for_timeout(400)
        c1 = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('#ch04 .plate')).getPropertyValue('--c')) || 0")
        top = pg.evaluate("Math.round(document.querySelector('#ch04 .plate').getBoundingClientRect().top)")
        rec(engine, view, "chapter plate pins and the sheet covers it (--c rises)", (pin and c1 > c0 and abs(top) <= 2) or (not pin and view == "phone"), {"pin": pin, "c": [c0, c1], "plate_top": top})
        if view == "desktop": shot(pg, f"{engine}-{view}-en-ch04-plate-covered")
        # --- top bar names the chapter; the contents sheet opens on it
        jump(pg, "#ch07-s-4", "start"); pg.wait_for_timeout(600)
        here = pg.evaluate("document.querySelector('.here-n').textContent + '|' + document.querySelector('.here-t').textContent")
        rec(engine, view, "top bar names the chapter being read", here.startswith("7|"), here)
        if view == "desktop":
            pg.locator("details.mtoc summary").click(); pg.wait_for_timeout(400)
            cur = pg.evaluate("(document.querySelector('.outline li.cur') || {}).dataset ? document.querySelector('.outline li.cur').dataset.k : ''")
            vis = pg.evaluate("(() => { const s = document.querySelector('.outline li.cur .secs'); return !!s && getComputedStyle(s).display !== 'none'; })()")
            shot(pg, f"{engine}-{view}-en-contents-ch07"); pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
            rec(engine, view, "contents sheet opens on the current chapter with its sections", cur == "ch07" and vis, cur)
        # --- language switch keeps the place, deep in a chapter and on a card
        for target in ("#ch07-s-4", "#w-agensh-1024", "#ch01-fig-2"):
            pg.goto(url("en")); pg.wait_for_timeout(300)
            jump(pg, target, "start"); pg.wait_for_timeout(500)
            bb = pg.locator("a.langbtn").bounding_box()          # a real click: no automatic scrolling to the sticky button first
            pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2); pg.wait_for_load_state("load"); pg.wait_for_timeout(900)
            landed = pg.url.split("/site/")[-1]
            ok_top = pg.evaluate("(id) => { const e = document.getElementById(id); if (!e) return null; const r = e.getBoundingClientRect(); return Math.round(r.top); }", target[1:])
            rec(engine, view, f"language switch keeps the place: {target}", landed == "ru/index.html" + target and ok_top is not None and -10 < ok_top < 260, {"landed": landed, "target_top": ok_top})
        # --- in-page link and Back
        pg.goto(url("en")); pg.wait_for_timeout(300)
        jump(pg, "#w-ord-swarm-scaling", "start"); pg.wait_for_timeout(500)
        y0 = pg.evaluate("Math.round(scrollY)")
        link = pg.locator("#ch04 a.chref[href='#ch05']").first
        link.scroll_into_view_if_needed(); y_before = pg.evaluate("Math.round(scrollY)")
        link.click(); pg.wait_for_timeout(1400)
        jumped = pg.evaluate("Math.abs(document.getElementById('ch05').getBoundingClientRect().top) < 140")
        pg.go_back(); pg.wait_for_timeout(1400)
        y_back = pg.evaluate("Math.round(scrollY)")
        rec(engine, view, "in-page chapter link jumps; Back returns to the place", jumped and abs(y_back - y_before) < 160, {"before": y_before, "back": y_back})
        # --- figure viewer
        pg.goto(url("en")); pg.wait_for_timeout(300)
        jump(pg, "#w-kim-scaling-agent-systems .fig", "center"); pg.wait_for_timeout(400)
        pg.locator("#w-kim-scaling-agent-systems a.zoom").first.click(); pg.wait_for_timeout(1300)
        v = pg.evaluate("""() => { const d = document.querySelector('dialog.viewer'); const i = d && d.querySelector('.vw-img'); const r = i && i.getBoundingClientRect(); const s = d && d.querySelector('.vw-stage').getBoundingClientRect();
            return d ? {open: d.open, nat: i.naturalWidth, count: d.querySelector('.vw-count').textContent, fits: r.top >= s.top - 1 && r.bottom <= s.bottom + 1 && r.left >= s.left - 1 && r.right <= s.right + 1} : null; }""")
        if view == "desktop": shot(pg, f"{engine}-{view}-en-viewer")
        pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(400)
        c2 = pg.evaluate("document.querySelector('dialog.viewer .vw-count').textContent")
        pg.locator("dialog.viewer .vw-zoom").click(); pg.wait_for_timeout(400)
        z = pg.evaluate("document.querySelector('dialog.viewer .vw-img').style.transform")
        pg.keyboard.press("Escape"); pg.wait_for_timeout(500)
        closed = pg.evaluate("!document.querySelector('dialog.viewer').open"); foc = pg.evaluate("!!document.activeElement && document.activeElement.matches('a.zoom')")
        pg.locator("#w-kim-scaling-agent-systems a.zoom").first.click(); pg.wait_for_timeout(800)
        pg.go_back(); pg.wait_for_timeout(700)
        closed_back = pg.evaluate("!document.querySelector('dialog.viewer').open")
        rec(engine, view, "viewer: fitted, → pages, zooms, Esc closes with focus back, Back closes",
            v and v["open"] and v["nat"] > 0 and v["fits"] and c2 != v["count"] and "scale(1)" not in z and closed and foc and closed_back,
            {"open": v, "next": c2, "zoom": z, "closed": closed, "focus": foc, "back_closes": closed_back})
        # --- atlas: search, matrix filters, reset
        pg.goto(url("ru", "#atlas")); pg.wait_for_timeout(500)
        c0 = pg.evaluate("document.getElementById('atlas-count').textContent")
        pg.fill("#atlas-q", "pandoc"); pg.wait_for_timeout(300); c1 = pg.evaluate("document.getElementById('atlas-count').textContent")
        pg.locator("#atlas-reset").click(); pg.wait_for_timeout(300); c3 = pg.evaluate("document.getElementById('atlas-count').textContent")
        rec(engine, view, "ru: atlas search narrows, reset restores", c1 != c0 and c3 == c0, [c0, c1, c3])
        if view == "desktop":
            cell = pg.locator(".atlasmap .tm-v[data-ft='memory'][data-fe='live_experiment']")
            cell.scroll_into_view_if_needed(); cell.click(); pg.wait_for_timeout(400)
            vis = pg.evaluate("[...document.querySelectorAll('.worklist .w')].filter(e => e.offsetParent !== null).length")
            want = int(pg.evaluate("document.querySelector(\".atlasmap .tm-v[data-ft='memory'][data-fe='live_experiment'] span\").textContent"))
            rec(engine, view, "ru: atlas map cell filters the list to its count", vis == want, {"visible": vis, "cell": want})
            pg.locator("#atlas-reset").click(); pg.wait_for_timeout(200)
            pg.goto(url("en", "#ch01-fig-6")); pg.wait_for_timeout(700)
            cell = pg.locator("#ch01-fig-6 .tm-v[data-ft='safety_alignment'][data-fe='incident']"); cell.scroll_into_view_if_needed(); cell.click(); pg.wait_for_timeout(1500)
            vis = pg.evaluate("[...document.querySelectorAll('.worklist .w')].filter(e => e.offsetParent !== null).length")
            near = pg.evaluate("Math.abs(document.querySelector('#atlas .atlas').getBoundingClientRect().top) < 200")
            rec(engine, view, "en: a Fig. 1.6 cell takes the reader to the atlas filtered to that cell", vis == 5 and near and pg.url.endswith("#atlas"), {"visible": vis, "near": near})
        # --- scale dashboard: tabs and a dot
        pg.goto(url("en", "#ch01-fig-2")); pg.wait_for_timeout(1200)
        pg.locator("#ch01-fig-2 label.sk-tab").nth(2).click(); pg.wait_for_timeout(400)
        lay = pg.evaluate("getComputedStyle(document.querySelector('.sk-lay-cap')).display")
        pg.locator("#ch01-fig-2 label.sk-tab").nth(0).click(); pg.wait_for_timeout(800)
        dot = pg.locator(".sk-lay-sim svg:visible a.dot.hl").first
        if view == "desktop":
            dot.hover(); pg.wait_for_timeout(300)
        else:
            dot.tap(); pg.wait_for_timeout(300)
        tip = pg.evaluate("(() => { const t = document.querySelector('.sk-tip'); return t.classList.contains('on') ? t.textContent.slice(0, 80) : ''; })()")
        if view == "desktop": shot(pg, f"{engine}-{view}-en-scale-tooltip")
        rec(engine, view, "scale dashboard: tabs switch quantities; a dot shows its work", lay == "block" and len(tip) > 10, {"cap_layer": lay, "tip": tip})
        # --- theme persists across reload and language
        pg.goto(url("en")); pg.wait_for_timeout(300)
        bg0 = pg.evaluate("getComputedStyle(document.body).backgroundColor")
        pg.locator("label.themebtn").click(); pg.wait_for_timeout(300)
        bg1 = pg.evaluate("getComputedStyle(document.body).backgroundColor")
        pg.goto(url("ru", "#ch05")); pg.wait_for_timeout(500)
        bg2 = pg.evaluate("getComputedStyle(document.body).backgroundColor"); light = pg.evaluate("document.documentElement.classList.contains('light')")
        if view == "desktop": shot(pg, f"{engine}-{view}-ru-ch05-light")
        pg.locator("label.themebtn").click(); pg.wait_for_timeout(200)
        rec(engine, view, "theme switch persists across reload and language", bg0 != bg1 and bg1 == bg2 and light, [bg0, bg1, bg2])
        rec(engine, view, "no page or console errors during the run", not errs, errs[:5])
        ctx.close()
        # --- reduced motion: end states, nothing moves
        ctx = b.new_context(reduced_motion="reduce", **vopt); pg = ctx.new_page()
        pg.goto(url("en")); pg.wait_for_timeout(600)
        st = pg.evaluate("document.documentElement.classList.contains('static')")
        moved = []
        for sel in SCENES + ["#how"]:
            jump(pg, sel); pg.wait_for_timeout(500); a = pg.evaluate(STATE, sel); pg.wait_for_timeout(800); b2 = pg.evaluate(STATE, sel)
            if a and b2 and a["sig"] != b2["sig"]: moved.append(sel)
        lit = pg.evaluate("[...document.querySelectorAll('.sc-fieldmap .fm-node')].every(n => getComputedStyle(n).opacity === '1')")
        pinned = pg.evaluate("document.querySelectorAll('.plate.pin').length")
        if view == "desktop": jump(pg, "#sc-hidden"); pg.wait_for_timeout(300); shot(pg, f"{engine}-{view}-en-reduced-hidden")
        rec(engine, view, "reduced motion: end states shown, nothing moves, no pinned plates", st and not moved and lit and pinned == 0, {"moved": moved, "fieldmap_lit": lit, "pinned": pinned})
        ctx.close()
    b.close()
    return ver

def static():
    s = {}
    figs = json.load(open(os.path.join(ROOT, "data", "figures.json"), encoding="utf-8"))["figures"]
    for lang in ("ru", "en"):
        h = open(os.path.join(SITE, lang, "index.html"), encoding="utf-8").read()
        miss = [f["file"] for f in figs if (f["file"].replace("_dark.png", f"_{lang}_dark.png") if f["file"].startswith("dash_") else f["file"]) not in h]
        s[f"figures_on_page_{lang}"] = {"expected": len(figs), "missing": miss}
    rd = {}
    for name in ("README.md", "README.ru.md"):
        t = open(os.path.join(ROOT, name), encoding="utf-8").read()
        paths = [a or b for a, b in re.findall(r'(?:src|srcset)="([^"]+)"|\]\(((?!https?:)[^)#]+)', t)]
        rd[name] = {"images": len(re.findall(r"<img ", t)), "links_local": len(paths), "missing": [x for x in paths if not os.path.exists(os.path.join(ROOT, x))]}
    s["readme"] = rd
    R["static"] = s

def readme_render(p):
    import markdown
    out = {}
    b = p.chromium.launch()
    for name in ("README.md", "README.ru.md"):
        body = markdown.markdown(open(os.path.join(ROOT, name), encoding="utf-8").read(), extensions=["fenced_code", "tables"])
        for scheme in ("light", "dark"):
            bg, fg = ("#ffffff", "#1f2328") if scheme == "light" else ("#0d1117", "#e6edf3")
            h = os.path.join(OUT, f"{name}.{scheme}.html")
            open(h, "w", encoding="utf-8").write(f'<!doctype html><meta charset="utf-8"><base href="file://{ROOT}/"><body style="margin:0;background:{bg};color:{fg};font:16px/1.5 -apple-system,Segoe UI,sans-serif">'
                                                 f'<article style="max-width:880px;margin:0 auto;padding:32px">{body}</article><style>img{{max-width:100%}} a{{color:#4493f8}} pre{{background:rgba(127,127,127,.12);padding:12px;overflow:auto}}</style>')
            ctx = b.new_context(color_scheme=scheme, viewport={"width": 1012, "height": 900}); pg = ctx.new_page()
            pg.goto("file://" + h); pg.wait_for_timeout(500)
            imgs = pg.evaluate("[...document.images].map(i => ({src: (i.currentSrc || i.src).split('/').pop(), ok: i.complete && i.naturalWidth > 0}))")
            path = os.path.join(SHOTS, f"readme-{name.replace('.md', '')}-{scheme}.png"); pg.screenshot(path=path, full_page=True)
            R["shots"].append(os.path.relpath(path, OUT)); out[f"{name}:{scheme}"] = imgs
            ctx.close()
    b.close()
    R["static"]["readme_render"] = out

def main():
    static()
    with sync_playwright() as p:
        vers = {e: run_engine(p, e) for e in ("chromium", "webkit")}
        readme_render(p)
    R["versions"] = vers
    fails = [x for x in R["browser"] if not x["ok"]]
    st = R["static"]; sfail = []
    for lang in ("ru", "en"):
        if st[f"figures_on_page_{lang}"]["missing"]: sfail.append(f"figures missing on {lang}: {st[f'figures_on_page_{lang}']['missing']}")
    for k, v in st["readme"].items():
        if v["missing"]: sfail.append(f"{k}: missing {v['missing']}")
    for k, v in st["readme_render"].items():
        bad = [i["src"] for i in v if not i["ok"]]
        if bad: sfail.append(f"README render {k}: images failed {bad}")
    R["summary"] = {"browser_checks": len(R["browser"]), "browser_failed": len(fails), "static_failed": sfail, "versions": vers, "shots": len(R["shots"])}
    json.dump(R, open(os.path.join(OUT, "features.json"), "w"), ensure_ascii=False, indent=1)
    lines = ["# Feature QA", "", f"Generated {time.strftime('%Y-%m-%d %H:%M:%S')} by `scripts/qa_features.py` against `site/` over file://.", "",
             f"Engines: {vers}. Views: desktop 1240×722, phone 390×844.", "", f"Browser checks: {len(R['browser'])}, failed: **{len(fails)}**. Static problems: **{len(sfail)}**.", "",
             "| Engine | View | Check | OK |", "|---|---|---|---|"]
    for x in R["browser"]:
        lines.append(f"| {x['engine']} | {x['view']} | {x['check']} | {'yes' if x['ok'] else '**NO** ' + json.dumps(x['detail'], ensure_ascii=False)[:300]} |")
    lines += ["", "## Static", "", f"- Registry figures on the RU page: {st['figures_on_page_ru']['expected'] - len(st['figures_on_page_ru']['missing'])}/{st['figures_on_page_ru']['expected']}; EN: {st['figures_on_page_en']['expected'] - len(st['figures_on_page_en']['missing'])}/{st['figures_on_page_en']['expected']}",
              "- README: " + "; ".join(f"{k}: {v['images']} images, {v['links_local']} local links, missing {len(v['missing'])}" for k, v in st["readme"].items()),
              "- README render (python-markdown, GitHub-like page, light/dark): " + "; ".join(f"{k}: {sum(1 for i in v if i['ok'])}/{len(v)} images" for k, v in st["readme_render"].items())]
    if sfail: lines += ["", "### Static problems", ""] + [f"- {x}" for x in sfail]
    open(os.path.join(OUT, "FEATURES.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(json.dumps(R["summary"], ensure_ascii=False, indent=1))
    for x in fails: print("FAIL", x["engine"], x["view"], x["check"], json.dumps(x["detail"], ensure_ascii=False)[:500])
    sys.exit(1 if fails or sfail else 0)

if __name__ == "__main__":
    main()
