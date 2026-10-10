#!/usr/bin/env python3
"""Feature QA of the built site, complementing scripts/qa_browser.py (page loads, images, overflow, no-JS basics).

  python scripts/qa_features.py [OUTDIR]      # default qa/features/; needs Playwright with Chromium and WebKit

Static: card/section/figure ID parity RU↔EN, every registry figure on the site, README image paths.
Browser (Chromium = Playwright build, WebKit; desktop 1440×900, phone 390×844):
  scene movement and auto-advance, pause, manual mode, offscreen pause, reduced motion, no-JS mode switch,
  theme switch + persistence, language switch keeps the section, viewer (open, next, zoom, Esc, focus back),
  expand-all, card hash opens its details, atlas search/reset, contents sheet, light-theme chart variants.
Writes OUTDIR/coverage.json and OUTDIR/COVERAGE.md; screenshots in OUTDIR/shots/.
"""
import json, os, pwd, re, sys, time
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", os.path.join(pwd.getpwuid(os.getuid()).pw_dir, "Library/Caches/ms-playwright"))
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "qa", "features"))
SHOTS = os.path.join(OUT, "shots"); os.makedirs(SHOTS, exist_ok=True)
PAGES = ["index"] + [f"ch{n:02d}" for n in range(1, 12)] + ["atlas", "glossary", "sources", "about", "full"]
VIEWS = {"desktop": dict(viewport={"width": 1440, "height": 900}, device_scale_factor=1),
         "phone": dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, has_touch=True, is_mobile=True)}
R = {"static": {}, "browser": [], "shots": []}
def url(lang, page, frag=""): return "file://" + os.path.join(SITE, lang, page + ".html") + frag
def read(lang, page): return open(os.path.join(SITE, lang, page + ".html"), encoding="utf-8").read()

# ---------------------------------------------------------------- static checks
def static():
    s = {}
    figs = json.load(open(os.path.join(ROOT, "data", "figures.json"), encoding="utf-8"))["figures"]
    files = [f["file"] for f in figs]
    for lang in ("ru", "en"):
        html_all = "".join(read(lang, p) for p in PAGES if p != "full")
        missing = []
        for f in files:
            if f.startswith("dash_"):
                base = f.replace("_dark.png", "")
                if f"{base}_{lang}_dark.png" not in html_all: missing.append(f)
            elif f not in html_all: missing.append(f)
        s[f"figures_on_site_{lang}"] = {"expected": len(files), "missing": missing}
        assets_missing = [f for f in files if not os.path.exists(os.path.join(SITE, "assets", "charts" if f.startswith("dash_") else "figures", f))]
        s[f"figure_assets_missing"] = assets_missing
    par = {}
    for p in PAGES:
        ru, en = read("ru", p), read("en", p)
        ids_ru = set(re.findall(r'\sid="((?:w|s|fig|a|src|p)-[^"]+)"', ru)); ids_en = set(re.findall(r'\sid="((?:w|s|fig|a|src|p)-[^"]+)"', en))
        par[p] = {"ru": len(ids_ru), "en": len(ids_en), "only_ru": sorted(ids_ru - ids_en)[:10], "only_en": sorted(ids_en - ids_ru)[:10]}
    s["id_parity"] = par
    # card ids from the content files must exist as anchors on their page
    lost = []
    for lang in ("ru", "en"):
        for p in PAGES[:-1]:
            md = os.path.join(ROOT, "content", lang, p + ".md")
            if not os.path.exists(md): continue
            h = read(lang, p)
            for cid in re.findall(r"^:::(?:card|short)\s+(\S+)", open(md, encoding="utf-8").read(), re.M):
                if f'id="w-{cid}"' not in h: lost.append(f"{lang}/{p}:{cid}")
    s["card_anchors_missing"] = lost
    rd = {}
    for name in ("README.md", "README.ru.md"):
        t = open(os.path.join(ROOT, name), encoding="utf-8").read()
        paths = [a or b for a, b in re.findall(r'(?:src|srcset)="([^"]+)"|\]\(((?!https?:)[^)#]+)', t)]
        rd[name] = {"images": len(re.findall(r"<img ", t)), "links_local": len(paths), "missing": [x for x in paths if not os.path.exists(os.path.join(ROOT, x))],
                    "chars": len(t), "private_disclaimers": len(re.findall(r"(?i)private candidate|приватн|not an ACL|не является публикацией ACL|arXiv submission|не подавался", t))}
    s["readme"] = rd
    R["static"] = s

# ---------------------------------------------------------------- browser checks
def rec(engine, view, name, ok, detail=None):
    R["browser"].append({"engine": engine, "view": view, "check": name, "ok": bool(ok), "detail": detail})

def shot(pg, name):
    p = os.path.join(SHOTS, name + ".png"); pg.screenshot(path=p); R["shots"].append(os.path.relpath(p, OUT))

def scroll_to(pg, sel):
    pg.evaluate("(s) => { const e = document.querySelector(s); if (e) e.scrollIntoView({block: 'center', behavior: 'instant'}); }", sel)
    pg.wait_for_timeout(250)

def run_engine(p, engine):
    b = p.chromium.launch() if engine == "chromium" else p.webkit.launch()
    ver = b.version
    for view, vopt in VIEWS.items():
        ctx = b.new_context(**vopt); pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        # --- scene movement
        for lang in ("ru", "en"):
            pg.goto(url(lang, "index")); pg.wait_for_timeout(300)
            st0 = pg.evaluate("() => ({mode: document.getElementById('how').dataset.mode, beat: document.querySelector('.narr').dataset.beat})")
            pg.wait_for_timeout(2900)
            st1 = pg.evaluate("""() => ({mode: document.getElementById('how').dataset.mode, beat: document.querySelector('.narr').dataset.beat,
                     fx: [...document.querySelectorAll('svg.tp')].find(s => s.getClientRects().length).querySelectorAll('.fx .pk').length,
                     a3: [...document.querySelectorAll('svg.tp')].find(s => s.getClientRects().length).querySelector('.ag[data-n="3"]').getAttribute('class'),
                     now: (document.querySelector('.beats-ind li.now') || {}).textContent || ''})""")
            rec(engine, view, f"{lang}: scene moves by itself (beat 0→≥1, packets, agent 3 finds)", st0["beat"] == "0" and st1["beat"] != "0" and st1["fx"] > 0 and "src" in (st1["a3"] or ""), {"t0": st0, "t3s": st1})
            if lang == "ru": shot(pg, f"{engine}-{view}-ru-index-moving")
        # auto-advance to the next scheme (desktop only to save time)
        if view == "desktop":
            pg.goto(url("en", "index")); pg.wait_for_timeout(200)
            t0 = time.time(); mode = "ind"
            while time.time() - t0 < 14 and mode == "ind":
                pg.wait_for_timeout(500); mode = pg.evaluate("document.getElementById('how').dataset.mode")
            rec(engine, view, "en: scheme advances automatically without a Start button", mode == "coord", {"mode_after_s": round(time.time() - t0, 1), "mode": mode})
            pg.wait_for_timeout(2600); shot(pg, f"{engine}-{view}-en-index-coordinator")
        # pause
        pg.goto(url("ru", "index")); pg.wait_for_timeout(500)
        pg.locator(".pp").click(); b0 = pg.evaluate("document.querySelector('.narr').dataset.beat")
        lab = pg.evaluate("document.querySelector('.pp').getAttribute('aria-label')")
        pg.wait_for_timeout(2600); b1 = pg.evaluate("document.querySelector('.narr').dataset.beat")
        paused = pg.evaluate("document.getElementById('how').classList.contains('paused')")
        pg.locator(".pp").click(); pg.wait_for_timeout(2600); b2 = pg.evaluate("document.querySelector('.narr').dataset.beat")
        rec(engine, view, "ru: pause holds the scene, play resumes", paused and b0 == b1 and lab == "Продолжить" and b2 != b1, {"b0": b0, "b1": b1, "b2": b2, "label": lab})
        # manual choice
        pg.locator("label[for='m-mem']").click(); pg.wait_for_timeout(1800)
        man = pg.evaluate("() => ({mode: document.getElementById('how').dataset.mode, auto: document.getElementById('how').classList.contains('auto')})")
        rec(engine, view, "ru: choosing a scheme switches the scene and stops rotation", man["mode"] == "mem" and not man["auto"], man)
        shot(pg, f"{engine}-{view}-ru-index-memory")
        # offscreen pause
        pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); pg.wait_for_timeout(600)
        off = pg.evaluate("document.getElementById('how').classList.contains('offscreen')")
        rec(engine, view, "ru: scene pauses when scrolled out of view", off)
        # theme switch + persistence
        pg.goto(url("en", "ch05")); pg.wait_for_timeout(300)
        bg0 = pg.evaluate("getComputedStyle(document.body).backgroundColor")
        pg.locator("label.themebtn").click(); pg.wait_for_timeout(300)
        bg1 = pg.evaluate("getComputedStyle(document.body).backgroundColor")
        pg.goto(url("ru", "ch04")); pg.wait_for_timeout(300)
        bg2 = pg.evaluate("getComputedStyle(document.body).backgroundColor"); light = pg.evaluate("document.documentElement.classList.contains('light')")
        rec(engine, view, "theme switch works and is remembered across pages and languages", bg0 != bg1 and bg1 == bg2 and light, {"dark": bg0, "light": bg1, "next_page": bg2})
        scroll_to(pg, "#w-kim-scaling-agent-systems"); pg.wait_for_timeout(400); shot(pg, f"{engine}-{view}-ru-ch04-light")
        pg.goto(url("ru", "ch01")); pg.wait_for_timeout(700)
        cv = pg.evaluate("[...document.querySelectorAll('.frame.chart img')].filter(i => i.offsetParent !== null).map(i => i.getAttribute('src').split('/').pop()).slice(0, 2)")
        rec(engine, view, "light theme shows the light chart variants", all("_light" in x for x in cv) and cv, cv)
        pg.locator("label.themebtn").click(); pg.wait_for_timeout(200)   # back to dark
        # language switch keeps the section being read
        pg.goto(url("en", "ch05")); pg.wait_for_timeout(300)
        sid = pg.evaluate("[...document.querySelectorAll('.prose > h2[id]')][2].id")
        pg.evaluate("(id) => { const h = document.getElementById(id); window.scrollTo({top: h.getBoundingClientRect().top + scrollY - 90, behavior: 'instant'}); }", sid); pg.wait_for_timeout(500)
        pg.locator("a.langbtn").click(); pg.wait_for_load_state("load"); pg.wait_for_timeout(300)
        rec(engine, view, "language switch lands on the same section in the other language", pg.url.endswith("/ru/ch05.html#" + sid), pg.url.split("/site/")[-1])
        # card hash opens its details
        pg.goto(url("en", "ch05", "#w-cursor-scaling")); pg.wait_for_timeout(400)
        op = pg.evaluate("document.querySelector('#w-cursor-scaling details.more').open")
        rec(engine, view, "address #w-<card> opens that card", op)
        # expand all
        pg.goto(url("ru", "ch07")); pg.wait_for_timeout(300)
        n = pg.evaluate("document.querySelectorAll('details.more').length")
        pg.locator(".xall").click(); pg.wait_for_timeout(300)
        on = pg.evaluate("[...document.querySelectorAll('details.more')].every(d => d.open)")
        lab = pg.evaluate("document.querySelector('.xall').textContent")
        rec(engine, view, "ru: expand all opens every card", n > 0 and on and lab == "Свернуть карточки", {"cards": n, "label": lab})
        # viewer
        pg.goto(url("en", "ch04")); pg.wait_for_timeout(300)
        scroll_to(pg, "#w-kim-scaling-agent-systems a.zoom"); pg.locator("#w-kim-scaling-agent-systems a.zoom").first.click(); pg.wait_for_timeout(1200)
        v = pg.evaluate("""() => { const d = document.querySelector('dialog.viewer'); const i = d && d.querySelector('.vw-img');
            const r = i && i.getBoundingClientRect(); const s = d && d.querySelector('.vw-stage').getBoundingClientRect();
            return d ? {open: d.open, nat: i.naturalWidth, src: i.getAttribute('src').split('/').pop(), count: d.querySelector('.vw-count').textContent,
                    fits: r.top >= s.top - 1 && r.bottom <= s.bottom + 1 && r.left >= s.left - 1 && r.right <= s.right + 1, cap: d.querySelector('.vw-cap').textContent.slice(0, 40)} : null; }""")
        shot(pg, f"{engine}-{view}-en-ch04-viewer")
        pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(500)
        c2 = pg.evaluate("document.querySelector('dialog.viewer .vw-count').textContent")
        pg.locator("dialog.viewer .vw-zoom").click(); pg.wait_for_timeout(500)
        z = pg.evaluate("document.querySelector('dialog.viewer .vw-img').style.transform")
        pg.keyboard.press("Escape"); pg.wait_for_timeout(500)
        closed = pg.evaluate("!document.querySelector('dialog.viewer').open")
        foc = pg.evaluate("document.activeElement && document.activeElement.matches('a.zoom')")
        rec(engine, view, "viewer: opens the full figure fitted, pages with →, zooms, closes with Esc, returns focus",
            v and v["open"] and v["nat"] > 0 and v["fits"] and c2 != v["count"] and "scale(1)" not in z and closed and foc, {"open": v, "after_next": c2, "zoom": z, "closed": closed, "focus_back": foc})
        # atlas search
        pg.goto(url("ru", "atlas")); pg.wait_for_timeout(400)
        c0 = pg.evaluate("document.getElementById('atlas-count').textContent")
        pg.fill("#atlas-q", "pandoc"); pg.wait_for_timeout(300)
        c1 = pg.evaluate("document.getElementById('atlas-count').textContent")
        reset_visible = pg.evaluate("!document.getElementById('atlas-reset').hidden")
        pg.locator("#atlas-reset").click(); pg.wait_for_timeout(300)
        c3 = pg.evaluate("document.getElementById('atlas-count').textContent")
        rec(engine, view, "ru: atlas search narrows the list, reset restores it", c1 != c0 and reset_visible and c3 == c0, [c0, c1, c3])
        # contents sheet (phone)
        if view == "phone":
            pg.goto(url("en", "ch08")); pg.wait_for_timeout(300)
            pg.locator("details.mtoc summary").click(); pg.wait_for_timeout(300)
            vis = pg.locator("details.mtoc nav").is_visible(); shot(pg, f"{engine}-{view}-en-ch08-contents")
            pg.locator("details.mtoc nav a[href='ch09.html']").click(); pg.wait_for_load_state("load")
            rec(engine, view, "contents sheet opens and navigates", vis and pg.url.endswith("/en/ch09.html"))
        # page tops for the archive
        for lang, page in (("en", "index"), ("ru", "ch01"), ("en", "ch05"), ("ru", "ch09"), ("en", "atlas"), ("ru", "glossary"), ("en", "about"), ("ru", "full")):
            pg.goto(url(lang, page)); pg.wait_for_timeout(700); shot(pg, f"{engine}-{view}-{lang}-{page}-top")
        rec(engine, view, "no page errors or console errors during the run", not errs, errs[:5])
        ctx.close()
        # reduced motion
        ctx = b.new_context(reduced_motion="reduce", **vopt); pg = ctx.new_page()
        pg.goto(url("en", "index")); pg.wait_for_timeout(1500)
        rm = pg.evaluate("""() => { const svg = [...document.querySelectorAll('svg.tp')].find(s => s.getClientRects().length);
            return {static: document.documentElement.classList.contains('static'), fx: svg.querySelectorAll('.fx .pk').length,
                    a3: svg.querySelector('.ag[data-n="3"]').getAttribute('class'), a1: svg.querySelector('.ag[data-n="1"]').getAttribute('class'),
                    beats: [...document.querySelectorAll('.beats-ind li')].filter(li => getComputedStyle(li).opacity === '1').length}; }""")
        pg.wait_for_timeout(2500); m2 = pg.evaluate("document.getElementById('how').dataset.mode")
        rec(engine, view, "reduced motion: no movement, end state and all steps shown", rm["static"] and rm["fx"] == 0 and "src" in rm["a3"] and "redo" in rm["a1"] and rm["beats"] == 4 and m2 == "ind", {**rm, "mode_later": m2})
        shot(pg, f"{engine}-{view}-en-index-reduced-motion")
        ctx.close()
        # no JavaScript
        ctx = b.new_context(java_script_enabled=False, **vopt); pg = ctx.new_page()
        pg.goto(url("ru", "index")); pg.wait_for_timeout(400)
        nj0 = pg.evaluate("getComputedStyle(document.querySelector('svg.tp' + (innerWidth < 600 ? '.tp-n' : '.tp-w') + ' .layer-ind')).visibility")
        pg.locator("label[for='m-coord']").click(); pg.wait_for_timeout(1200)   # tags fade in over .4s after the .45s layer delay
        nj1 = pg.evaluate("""() => { const s = document.querySelector('svg.tp' + (innerWidth < 600 ? '.tp-n' : '.tp-w'));
            return {coord: getComputedStyle(s.querySelector('.layer-coord')).visibility, ind: getComputedStyle(s.querySelector('.layer-ind')).visibility,
                    got: getComputedStyle(s.querySelector('.ag[data-n="1"] .tg-got')).opacity}; }""")
        rec(engine, view, "no JS: scene shows an end state and the scheme choice still switches it", nj0 == "visible" and nj1["coord"] == "visible" and nj1["ind"] == "hidden" and nj1["got"] == "1", {"before": nj0, "after": nj1})
        shot(pg, f"{engine}-{view}-ru-index-nojs-coordinator")
        pg.goto(url("en", "ch05")); pg.wait_for_timeout(300)
        pg.locator("a.zoom").first.click(); pg.wait_for_timeout(300)
        lb = pg.evaluate("(() => { const l = document.querySelector('.lightbox:target'); return !!l && getComputedStyle(l).display === 'flex'; })()")
        rec(engine, view, "no JS: figure opens in the :target lightbox", lb)
        ctx.close()
    b.close()
    return ver

def readme_render(p):
    """Render README.md / README.ru.md to HTML (python-markdown) and show it as GitHub would: dark and light."""
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
            R["shots"].append(os.path.relpath(path, OUT))
            out[f"{name}:{scheme}"] = imgs
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
    st = R["static"]
    sfail = []
    for lang in ("ru", "en"):
        if st[f"figures_on_site_{lang}"]["missing"]: sfail.append(f"figures missing on {lang} site: {st[f'figures_on_site_{lang}']['missing']}")
    if st["figure_assets_missing"]: sfail.append(f"figure assets missing: {st['figure_assets_missing']}")
    for p_, v in st["id_parity"].items():
        if v["only_ru"] or v["only_en"]: sfail.append(f"id parity {p_}: only_ru={v['only_ru']} only_en={v['only_en']}")
    if st["card_anchors_missing"]: sfail.append(f"card anchors missing: {st['card_anchors_missing'][:10]}")
    for k, v in st["readme"].items():
        if v["missing"] or v["private_disclaimers"]: sfail.append(f"{k}: missing={v['missing']} disclaimers={v['private_disclaimers']}")
    for k, v in st["readme_render"].items():
        bad = [i["src"] for i in v if not i["ok"]]
        if bad: sfail.append(f"README render {k}: images failed {bad}")
    R["summary"] = {"browser_checks": len(R["browser"]), "browser_failed": len(fails), "static_failed": sfail, "versions": vers, "shots": len(R["shots"])}
    json.dump(R, open(os.path.join(OUT, "features.json"), "w"), ensure_ascii=False, indent=1)
    lines = ["# Feature QA", "", f"Generated {time.strftime('%Y-%m-%d %H:%M:%S')} by `scripts/qa_features.py` against `site/` over file://.", "",
             f"Engines: {vers}. Views: desktop 1440×900, phone 390×844.", "", f"Browser checks: {len(R['browser'])}, failed: **{len(fails)}**. Static problems: **{len(sfail)}**.", "",
             "| Engine | View | Check | OK |", "|---|---|---|---|"]
    for x in R["browser"]:
        lines.append(f"| {x['engine']} | {x['view']} | {x['check']} | {'yes' if x['ok'] else '**NO** ' + json.dumps(x['detail'], ensure_ascii=False)[:300]} |")
    lines += ["", "## Static", "", f"- Figures from data/figures.json on the RU site: {st['figures_on_site_ru']['expected'] - len(st['figures_on_site_ru']['missing'])}/{st['figures_on_site_ru']['expected']}; EN: {st['figures_on_site_en']['expected'] - len(st['figures_on_site_en']['missing'])}/{st['figures_on_site_en']['expected']}",
              f"- Card anchors missing: {len(st['card_anchors_missing'])}", f"- ID parity RU↔EN problems: {sum(1 for v in st['id_parity'].values() if v['only_ru'] or v['only_en'])} pages",
              f"- README: " + "; ".join(f"{k}: {v['images']} images, {v['links_local']} local links, missing {len(v['missing'])}, process disclaimers {v['private_disclaimers']}" for k, v in st["readme"].items()),
              f"- README render (python-markdown, GitHub-like page, light/dark): " + "; ".join(f"{k}: {sum(1 for i in v if i['ok'])}/{len(v)} images" for k, v in st["readme_render"].items())]
    if sfail: lines += ["", "### Static problems", ""] + [f"- {x}" for x in sfail]
    open(os.path.join(OUT, "FEATURES.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(json.dumps(R["summary"], ensure_ascii=False, indent=1))
    for x in fails: print("FAIL", x["engine"], x["view"], x["check"], json.dumps(x["detail"], ensure_ascii=False)[:400])
    sys.exit(1 if fails or sfail else 0)

if __name__ == "__main__":
    main()
