#!/usr/bin/env python3
"""Real-browser QA of the built site (site/): Chromium (installed Google Chrome if present, else Playwright's) and WebKit.

  python scripts/qa_browser.py [OUTDIR] [--shots]      # default qa/

For each engine × viewport (phone 390×844, desktop 1240×722, wide 1600×900) and language:
  * the single page loads over file:// with no console or page errors
  * every <img> finishes loading with naturalWidth > 0 (lazy images are switched to eager first)
  * no page-level horizontal overflow; no visible element sticks out of the viewport
  * no Cyrillic text on the English page (outside elements marked lang="ru")
  * every former page (ch01 … full) forwards to the single page with its fragment
With JavaScript DISABLED (phone, both engines):
  * the theme checkbox switches the background; a figure opens in the :target lightbox
  * an atlas filter hides non-matching rows; the scale dashboard tabs switch layers
  * the contents sheet opens and its link moves within the page; the prologue shows a static figure for each scheme
    and the scale beside its whole text (the sticky stage needs JavaScript)
  * a former page lists its places and highlights the addressed one
Writes qa/report.json and qa/REPORT.md; screenshots in qa/screens/ with --shots.
"""
import json, os, pwd, sys, time
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
OUT = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith("--")), os.path.join(ROOT, "qa")))   # optional OUTDIR
for _c in (os.path.expanduser("~/Library/Caches/ms-playwright"), os.path.join(pwd.getpwuid(os.getuid()).pw_dir, "Library/Caches/ms-playwright")):
    if os.path.isdir(_c) and "PLAYWRIGHT_BROWSERS_PATH" not in os.environ: os.environ["PLAYWRIGHT_BROWSERS_PATH"] = _c
STUBS = [f"ch{n:02d}" for n in range(1, 12)] + ["atlas", "glossary", "sources", "about", "full"]
VIEWS = {"phone": dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, has_touch=True),
         "desktop": dict(viewport={"width": 1240, "height": 722}, device_scale_factor=1),
         "wide": dict(viewport={"width": 1600, "height": 900}, device_scale_factor=1)}

def url(path): return "file://" + os.path.join(SITE, path)

PROBE = """async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const imgs = [...document.querySelectorAll('img')];
  imgs.forEach(i => { i.loading = 'eager'; });
  const t0 = Date.now();
  while (Date.now() - t0 < 25000 && imgs.some(i => !i.complete)) await sleep(150);
  const bad = imgs.filter(i => !(i.complete && i.naturalWidth > 0)).map(i => i.getAttribute('src'));
  const overflow = document.documentElement.scrollWidth - document.documentElement.clientWidth;
  const vw = document.documentElement.clientWidth;
  const wide = [];
  for (const e of document.querySelectorAll('main *')) {
    if (wide.length > 5) break;
    const r = e.getBoundingClientRect();
    if (!r.width || r.right <= vw + 2) continue;
    if (e.closest('.table-wrap, .lightbox, svg, .sk-plot, .filters .opts, dialog')) continue;
    const cs = getComputedStyle(e); if (cs.position === 'fixed' || cs.visibility === 'hidden') continue;
    wide.push(e.tagName + '.' + String(e.className).slice(0, 40) + ' ' + Math.round(r.right));
  }
  const c = document.body.cloneNode(true); c.querySelectorAll('[lang=ru], script, style').forEach(e => e.remove());
  return { imgs: imgs.length, bad_imgs: bad, h_overflow_px: overflow, overflowing_elems: wide, height: document.documentElement.scrollHeight,
           scenes: document.querySelectorAll('[data-scene]').length, figures: document.querySelectorAll('figure.fig').length,
           cards: document.querySelectorAll('article.case, section.note').length, ids: document.querySelectorAll('[id]').length,
           has_theme: !!document.querySelector('label.themebtn'), has_lang: !!document.querySelector('a.langbtn'), has_menu: !!document.querySelector('details.mtoc'),
           cyr_in_en: document.documentElement.lang === 'en' ? (c.textContent.match(/[А-Яа-яЁё]/g) || []).length : null };
}"""

def nojs_checks(b, lang):
    res = {}
    ctx = b.new_context(java_script_enabled=False, **VIEWS["phone"]); pg = ctx.new_page()
    pg.goto(url(f"{lang}/index.html")); pg.wait_for_timeout(200)
    bg0 = pg.evaluate("getComputedStyle(document.body).backgroundColor")
    pg.locator("label.themebtn").click(); pg.wait_for_timeout(100)
    bg1 = pg.evaluate("getComputedStyle(document.body).backgroundColor")
    res["theme_toggle"] = bg0 != bg1
    pg.locator("label.themebtn").click()
    z = pg.locator("figure.fig a.zoom").first; z.scroll_into_view_if_needed(); z.click(); pg.wait_for_timeout(150)
    res["lightbox_opens"] = pg.evaluate("(() => { const l = document.querySelector('.lightbox:target'); return !!l && getComputedStyle(l).display === 'flex'; })()")
    pg.goto(url(f"{lang}/index.html") + "#atlas"); pg.wait_for_timeout(150)
    n0 = pg.evaluate("[...document.querySelectorAll('.worklist .w')].filter(e => e.offsetParent !== null).length")
    pg.locator("label[for='ft-memory']").click(); pg.wait_for_timeout(100)
    n1 = pg.evaluate("[...document.querySelectorAll('.worklist .w')].filter(e => e.offsetParent !== null).length")
    res["atlas_all"], res["atlas_memory"] = n0, n1
    res["atlas_filter_works"] = 0 < n1 < n0
    lay0 = pg.evaluate("getComputedStyle(document.querySelector('.sk-lay-cum')).display")
    pg.locator(".sc-scale label.sk-tab").nth(1).click(); pg.wait_for_timeout(150)
    lay1 = pg.evaluate("getComputedStyle(document.querySelector('.sk-lay-cum')).display")
    res["scale_tabs"] = lay0 == "none" and lay1 == "block"
    pg.locator("details.mtoc summary").click(); pg.wait_for_timeout(100)
    res["menu_opens"] = pg.locator("details.mtoc nav").is_visible()
    pg.evaluate("(() => { const n = document.querySelector('details.mtoc nav'), a = n.querySelector('a[href=\"#ch05\"]'); n.scrollTop = a.offsetTop - 120; })()")   # the reader scrolls the sheet first
    pg.wait_for_timeout(150)
    pg.locator("details.mtoc nav a[href='#ch05']").first.click(); pg.wait_for_timeout(250)
    res["menu_moves_in_page"] = pg.url.endswith("#ch05") and pg.evaluate("Math.abs(document.getElementById('ch05').getBoundingClientRect().top) < 140")
    pg.goto(url(f"{lang}/index.html") + "#m-coord"); pg.wait_for_timeout(200)
    res["prologue_static"] = pg.evaluate("""() => getComputedStyle(document.querySelector('#how .stage')).display === 'none'
      && [...document.querySelectorAll('#how .static')].filter(f => [...f.querySelectorAll('svg')].some(s => s.getClientRects().length)).length === 4
      && document.querySelectorAll('#how .step').length === 13
      && Math.abs(document.getElementById('m-coord').getBoundingClientRect().top) < 120""")
    pg.goto(url(f"{lang}/ch05.html") + "#w-agensh-1024"); pg.wait_for_timeout(200)
    res["stub_lists_and_targets"] = pg.evaluate("(() => { const t = document.querySelector('li:target'); return !!t && t.querySelector('a').getAttribute('href') === 'index.html#w-agensh-1024'; })()")
    ctx.close()
    return res

def main():
    shots = "--shots" in sys.argv
    os.makedirs(os.path.join(OUT, "screens"), exist_ok=True)
    report = {"generated": time.strftime("%Y-%m-%d %H:%M:%S"), "runs": [], "stubs": [], "nojs": []}
    with sync_playwright() as p:
        def chrome():
            try: return p.chromium.launch(channel="chrome"), "chromium (Google Chrome)"
            except Exception: return p.chromium.launch(), "chromium (Playwright)"
        for launch in (chrome, lambda: (p.webkit.launch(), "webkit")):
            b, name = launch(); ver = b.version
            for vname, vopt in VIEWS.items():
                ctx = b.new_context(**vopt); pg = ctx.new_page(); errors = []
                pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
                pg.on("pageerror", lambda e: errors.append(str(e)))
                for lang in ("ru", "en"):
                    errors.clear(); t0 = time.time()
                    pg.goto(url(f"{lang}/index.html"), wait_until="load")
                    r = pg.evaluate(PROBE)
                    r.update(engine=name, version=ver, view=vname, lang=lang, page="index", console_errors=list(errors), secs=round(time.time() - t0, 2))
                    report["runs"].append(r)
                    if shots:
                        pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(300)
                        pg.screenshot(path=os.path.join(OUT, "screens", f"{name.split()[0]}-{vname}-{lang}-top.png"))
                ctx.close()
            # former pages forward (desktop)
            ctx = b.new_context(**VIEWS["desktop"]); pg = ctx.new_page()
            for lang in ("ru", "en"):
                for s in STUBS:
                    pg.goto(url(f"{lang}/{s}.html")); pg.wait_for_timeout(250)
                    report["stubs"].append({"engine": name, "lang": lang, "page": s, "landed": pg.url.split("/site/")[-1], "ok": pg.url.split("/site/")[-1].startswith(f"{lang}/index.html#")})
            for root_page in ("index.html", "404.html"):
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(url(root_page)); pg.wait_for_timeout(200)
                report["stubs"].append({"engine": name, "lang": "-", "page": root_page, "landed": pg.url.split("/site/")[-1],
                                        "ok": pg.locator(".choose a").count() == 2 and not errs})
            ctx.close()
            for lang in ("ru", "en"):
                try: r = nojs_checks(b, lang)
                except Exception as e: r = {"error": str(e)[:300]}
                r.update(engine=name, version=ver, lang=lang); report["nojs"].append(r)
            b.close()
    runs = report["runs"]
    fails = [r for r in runs if r["bad_imgs"] or r["h_overflow_px"] > 1 or r["overflowing_elems"] or r["console_errors"] or (r["cyr_in_en"] or 0) > 0
             or not (r["has_theme"] and r["has_lang"] and r["has_menu"])]
    stub_fail = [s for s in report["stubs"] if not s["ok"]]
    keys = ("theme_toggle", "lightbox_opens", "atlas_filter_works", "scale_tabs", "menu_opens", "menu_moves_in_page", "prologue_static", "stub_lists_and_targets")
    nojs_fail = [r for r in report["nojs"] if not all(r.get(k) for k in keys)]
    report["summary"] = dict(page_loads=len(runs), engines=sorted({r["engine"] + " " + r["version"] for r in runs}), images_checked=sum(r["imgs"] for r in runs),
                             failing_loads=len(fails), stub_checks=len(report["stubs"]), stub_failing=len(stub_fail), nojs_runs=len(report["nojs"]), nojs_failing=len(nojs_fail))
    json.dump(report, open(os.path.join(OUT, "report.json"), "w"), ensure_ascii=False, indent=1)
    lines = ["# Browser QA report", "", f"Generated {report['generated']} by `scripts/qa_browser.py` against `site/` over file://.", "",
             f"- Engines: {', '.join(report['summary']['engines'])}", f"- Single-page loads: {len(runs)} (RU/EN × phone 390×844 / desktop 1240×722 / wide 1600×900 × 2 engines)",
             f"- Images checked for successful decode: {report['summary']['images_checked']}",
             f"- Loads with a failure (broken image, horizontal overflow, element outside the viewport, console error, Cyrillic on EN page, missing controls): **{len(fails)}**",
             f"- Former pages forwarding to the single page (+ root and 404): {len(report['stubs'])}, failing: **{len(stub_fail)}**",
             f"- No-JS interaction runs (phone): {len(report['nojs'])}, failing: **{len(nojs_fail)}**", "",
             "| Engine | View | Lang | Images | Bad | H-overflow px | Outside viewport | Scenes | Figures | Cards | Height px | Console errors | Load s |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in runs:
        lines.append(f"| {r['engine'].split()[0]} | {r['view']} | {r['lang']} | {r['imgs']} | {len(r['bad_imgs'])} | {r['h_overflow_px']} | {len(r['overflowing_elems'])} | {r['scenes']} | {r['figures']} | {r['cards']} | {r['height']} | {len(r['console_errors'])} | {r['secs']} |")
    lines += ["", "## No-JS interactions (JavaScript disabled, phone)", "", "| Engine | Lang | " + " | ".join(keys) + " |", "|---|---|" + "---|" * len(keys)]
    for r in report["nojs"]:
        lines.append(f"| {r['engine'].split()[0]} | {r['lang']} | " + " | ".join(str(r.get(k)) for k in keys) + " |" + (f" error: {r['error']}" if r.get("error") else ""))
    if fails or stub_fail:
        lines += ["", "## Failures", ""] + [f"- {r['engine']} {r['view']} {r['lang']}: bad_imgs={r['bad_imgs'][:3]} overflow={r['h_overflow_px']} elems={r['overflowing_elems'][:3]} console={r['console_errors'][:2]} cyr={r['cyr_in_en']}" for r in fails] \
                 + [f"- forwarding {s['engine']} {s['lang']}/{s['page']} -> {s['landed']}" for s in stub_fail]
    open(os.path.join(OUT, "REPORT.md"), "w").write("\n".join(lines) + "\n")
    print(json.dumps(report["summary"], indent=1))
    for r in fails: print("FAIL", r["engine"][:8], r["view"], r["lang"], r["h_overflow_px"], r["overflowing_elems"][:3], r["bad_imgs"][:2], r["console_errors"][:2], r["cyr_in_en"])
    for s in stub_fail: print("STUB FAIL", s)
    for r in nojs_fail: print("NOJS FAIL", r)
    sys.exit(1 if fails or stub_fail or nojs_fail else 0)

if __name__ == "__main__":
    main()
