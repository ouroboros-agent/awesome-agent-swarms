#!/usr/bin/env python3
"""Real-browser QA of the built site (site/), Chromium (installed Google Chrome) and WebKit via Playwright.

  python scripts/qa_browser.py [--pages all|quick] [--shots]

For every page × engine × viewport (phone 390×844, desktop 1280×900):
  * page loads over file://, no console errors / page errors
  * every <img> on the page finishes loading with naturalWidth > 0 (lazy images forced by scrolling)
  * no page-level horizontal overflow (wide tables must scroll inside their own box)
  * the theme/lang buttons and the menu are present
With JavaScript DISABLED (phone, both engines) on index, a chapter and the atlas:
  * opening a card's <details> reveals its body
  * the theme checkbox switches the page background
  * an atlas filter hides non-matching entries
  * a figure's zoom link opens the :target lightbox
Writes qa/report.json and qa/REPORT.md; screenshots in qa/screens/ with --shots.
"""
import json, os, sys, time
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
OUT = os.path.join(ROOT, "qa")
import pwd
for _c in (os.path.expanduser("~/Library/Caches/ms-playwright"), os.path.join(pwd.getpwuid(os.getuid()).pw_dir, "Library/Caches/ms-playwright")):
    if os.path.isdir(_c) and "PLAYWRIGHT_BROWSERS_PATH" not in os.environ: os.environ["PLAYWRIGHT_BROWSERS_PATH"] = _c
PAGES = ["index"] + [f"ch{n:02d}" for n in range(1, 12)] + ["atlas", "glossary", "sources", "about", "full"]
VIEWS = {"phone": dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, has_touch=True),
         "desktop": dict(viewport={"width": 1280, "height": 900}, device_scale_factor=1)}

def url(lang, page): return "file://" + os.path.join(SITE, lang, page + ".html")

PROBE = """async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const H = () => document.documentElement.scrollHeight;
  for (let y = 0; y < H(); y += Math.max(600, innerHeight)) { window.scrollTo(0, y); await sleep(25); }
  const imgs = [...document.querySelectorAll('img')];
  imgs.forEach(i => { i.loading = 'eager'; });
  const t0 = Date.now();
  while (Date.now() - t0 < 15000 && imgs.some(i => !i.complete)) await sleep(100);
  const visible = el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  const bad = imgs.filter(i => !(i.complete && i.naturalWidth > 0)).map(i => i.getAttribute('src'));
  const overflow = document.documentElement.scrollWidth - document.documentElement.clientWidth;
  const wide = [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); return visible(e) && r.right > document.documentElement.clientWidth + 2 && !e.closest('.table-wrap') && !e.closest('.lightbox') && getComputedStyle(e).position !== 'fixed'; })
     .slice(0, 5).map(e => e.tagName + '.' + (e.className || '') );
  const tw = [...document.querySelectorAll('.table-wrap')];
  return { imgs: imgs.length, bad_imgs: bad, h_overflow_px: overflow, overflowing_elems: wide,
           tables: tw.length, tables_scrollable: tw.filter(w => w.scrollWidth > w.clientWidth + 2).length,
           tables_hint_shown: tw.filter(w => w.classList.contains('is-scrollable')).length,
           cards: document.querySelectorAll('article.card').length, details: document.querySelectorAll('details.more').length,
           figures: document.querySelectorAll('figure.fig').length, has_theme: !!document.querySelector('label.themebtn'),
           has_lang: !!document.querySelector('a.langbtn'), height: H(), cyr_in_en: document.documentElement.lang === 'en' ? (() => { const c = document.body.cloneNode(true); c.querySelectorAll('[lang=ru]').forEach(e => e.remove()); return (c.textContent.match(/[А-Яа-яЁё]/g) || []).length; })() : null };
}"""

def nojs_checks(pg, lang):
    res = {}
    pg.goto(url(lang, "ch04")); pg.wait_for_timeout(200)
    d = pg.locator("details.more").first
    before = d.locator(".cbody").first.is_visible()
    d.locator("summary").click(); pg.wait_for_timeout(100)
    res["details_open"] = (not before) and d.locator(".cbody").first.is_visible()
    bg0 = pg.evaluate("getComputedStyle(document.body).backgroundColor")
    pg.locator("label.themebtn").click(); pg.wait_for_timeout(100)
    bg1 = pg.evaluate("getComputedStyle(document.body).backgroundColor")
    res["theme_toggle"] = bg0 != bg1; res["theme_bg"] = [bg0, bg1]
    z = pg.locator("a.zoom").first; z.scroll_into_view_if_needed(); z.click(); pg.wait_for_timeout(150)
    res["lightbox_opens"] = pg.evaluate("(() => { const l = document.querySelector('.lightbox:target'); return !!l && getComputedStyle(l).display === 'flex'; })()")
    pg.goto(url(lang, "atlas")); pg.wait_for_timeout(200)
    n0 = pg.evaluate("[...document.querySelectorAll('.worklist .w')].filter(e => e.offsetParent !== null).length")
    pg.locator("label[for='ft-memory']").click(); pg.wait_for_timeout(100)
    n1 = pg.evaluate("[...document.querySelectorAll('.worklist .w')].filter(e => e.offsetParent !== null).length")
    pg.locator("label[for='fl-related']").click(); pg.wait_for_timeout(100)
    n2 = pg.evaluate("[...document.querySelectorAll('.worklist .w')].filter(e => e.offsetParent !== null).length")
    res["atlas_all"] = n0; res["atlas_memory"] = n1; res["atlas_memory_and_related"] = n2
    res["atlas_filter_works"] = 0 < n1 < n0 and n2 <= n1
    pg.goto(url(lang, "index")); pg.wait_for_timeout(100)
    m = pg.locator("details.mtoc")
    m.locator("summary").click(); pg.wait_for_timeout(100)
    res["mobile_menu_opens"] = pg.locator("details.mtoc nav").is_visible()
    pg.locator("details.mtoc nav a[href='ch05.html']").first.click(); pg.wait_for_timeout(200)
    res["menu_navigates"] = pg.url.endswith("/ch05.html")
    return res

def main():
    quick = "--pages" in sys.argv and sys.argv[sys.argv.index("--pages") + 1] == "quick"
    shots = "--shots" in sys.argv
    pages = ["index", "ch04", "ch09", "atlas"] if quick else PAGES
    os.makedirs(os.path.join(OUT, "screens"), exist_ok=True)
    report = {"generated": time.strftime("%Y-%m-%d %H:%M:%S"), "runs": [], "nojs": []}
    with sync_playwright() as p:
        engines = [("chromium (Google Chrome)", lambda: p.chromium.launch(channel="chrome")), ("webkit", lambda: p.webkit.launch())]
        for name, launch in engines:
            b = launch(); ver = b.version
            for vname, vopt in VIEWS.items():
                ctx = b.new_context(**vopt); pg = ctx.new_page()
                errors = []
                pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
                pg.on("pageerror", lambda e: errors.append(str(e)))
                for lang in ("ru", "en"):
                    for page in pages:
                        errors.clear(); t0 = time.time()
                        pg.goto(url(lang, page), wait_until="load")
                        r = pg.evaluate(PROBE)
                        r.update(engine=name, version=ver, view=vname, lang=lang, page=page, console_errors=list(errors), secs=round(time.time() - t0, 2))
                        report["runs"].append(r)
                        if shots and page in ("index", "ch04", "atlas", "ch09"):
                            pg.evaluate("window.scrollTo(0,0)")
                            pg.screenshot(path=os.path.join(OUT, "screens", f"{name.split()[0]}-{vname}-{lang}-{page}.png"))
                ctx.close()
            # no-JS interaction checks on the phone viewport
            for lang in ("ru", "en"):
                ctx = b.new_context(java_script_enabled=False, **VIEWS["phone"]); pg = ctx.new_page()
                try: r = nojs_checks(pg, lang)
                except Exception as e: r = {"error": str(e)[:300]}
                r.update(engine=name, version=ver, lang=lang); report["nojs"].append(r); ctx.close()
            b.close()
    # summary
    runs = report["runs"]
    fails = [r for r in runs if r["bad_imgs"] or r["h_overflow_px"] > 1 or r["console_errors"] or (r["cyr_in_en"] or 0) > 0 or not r["has_theme"] or not r["has_lang"]]
    nojs_fail = [r for r in report["nojs"] if not all(r.get(k) for k in ("details_open", "theme_toggle", "lightbox_opens", "atlas_filter_works", "mobile_menu_opens", "menu_navigates"))]
    report["summary"] = dict(page_loads=len(runs), engines=sorted({r["engine"] + " " + r["version"] for r in runs}), images_checked=sum(r["imgs"] for r in runs),
                             failing_loads=len(fails), nojs_runs=len(report["nojs"]), nojs_failing=len(nojs_fail))
    json.dump(report, open(os.path.join(OUT, "report.json"), "w"), ensure_ascii=False, indent=1)
    lines = ["# Browser QA report", "", f"Generated {report['generated']} by `scripts/qa_browser.py` against `site/` over file://.", "",
             f"- Engines: {', '.join(report['summary']['engines'])}", f"- Page loads: {len(runs)} (pages × RU/EN × phone 390×844 / desktop 1280×900 × 2 engines)",
             f"- Images checked for successful decode: {report['summary']['images_checked']}", f"- Loads with a failure (broken image, page-level horizontal overflow, console error, Cyrillic on EN page, missing controls): **{len(fails)}**",
             f"- No-JS interaction runs (phone): {len(report['nojs'])}, failing: **{len(nojs_fail)}**", "",
             "| Engine | View | Lang | Page | Images | Bad | H-overflow px | Tables (scrollable) | Cards | Figures | Console errors |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in runs:
        lines.append(f"| {r['engine'].split()[0]} | {r['view']} | {r['lang']} | {r['page']} | {r['imgs']} | {len(r['bad_imgs'])} | {r['h_overflow_px']} | {r['tables']} ({r['tables_scrollable']}) | {r['cards']} | {r['figures']} | {len(r['console_errors'])} |")
    lines += ["", "## No-JS interactions (JavaScript disabled, phone)", "", "| Engine | Lang | details open | theme toggle | lightbox | atlas: all → memory → memory+related | menu opens | menu navigates |", "|---|---|---|---|---|---|---|---|"]
    for r in report["nojs"]:
        lines.append(f"| {r['engine'].split()[0]} | {r['lang']} | {r.get('details_open')} | {r.get('theme_toggle')} | {r.get('lightbox_opens')} | {r.get('atlas_all')} → {r.get('atlas_memory')} → {r.get('atlas_memory_and_related')} | {r.get('mobile_menu_opens')} | {r.get('menu_navigates')} |" + (f" error: {r['error']}" if r.get("error") else ""))
    if fails:
        lines += ["", "## Failures", ""] + [f"- {r['engine']} {r['view']} {r['lang']}/{r['page']}: bad_imgs={r['bad_imgs'][:3]} overflow={r['h_overflow_px']} elems={r['overflowing_elems']} console={r['console_errors'][:2]} cyr={r['cyr_in_en']}" for r in fails]
    open(os.path.join(OUT, "REPORT.md"), "w").write("\n".join(lines) + "\n")
    print(json.dumps(report["summary"], indent=1))
    if fails: print("FAILS:", [(r["engine"][:6], r["view"], r["lang"], r["page"], r["h_overflow_px"], r["overflowing_elems"][:2], r["bad_imgs"][:2], r["console_errors"][:1], r["cyr_in_en"]) for r in fails[:20]])
    if nojs_fail: print("NOJS FAILS:", nojs_fail)
    sys.exit(1 if fails or nojs_fail else 0)

if __name__ == "__main__":
    main()
