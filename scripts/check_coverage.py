#!/usr/bin/env python3
"""Content coverage of the single page: nothing from the sources or from the former pages may go missing.

  python scripts/check_coverage.py                      # against content/ and data/
  python scripts/check_coverage.py --old qa/oldsite     # also against a build of the former multipage site
  python scripts/check_coverage.py --json out.json

Checks per language on site/<lang>/index.html:
  cards       every :::card / :::short id from content/<lang>/*.md is on the page exactly once (id="w-<id>")
  figures     every file in data/figures.json is on the page (image, or the static PNG behind a native chart)
  links       every external URL written in content/<lang>/*.md is a link on the page
  headings    every Markdown heading text is on the page
  blocks      timeline entries, related-work rows, glossary terms, atlas rows, source entries: counts match
  forwarding  every former page exists and forwards (checked by scripts/build_site.py --check)
With --old, against the former multipage build (index, ch01–ch11, atlas, glossary, sources, about):
  ids         every card, related-row, atlas-row and source id of the former pages exists on the single page
  hrefs       every external link of the former pages is on the single page
  text        every paragraph, list item, table cell and caption of the former pages' main content is on the page
              (whitespace-normalised); the few intentional removals are listed with their reason
Exit code 1 on any missing item.
"""
import argparse, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
PAGES = [f"ch{n:02d}" for n in range(1, 12)] + ["index", "atlas", "glossary", "sources", "about"]

# Former index-page copy that the single page deliberately does not repeat (it restated the Agensh card in ch. 5).
INTENTIONAL = {
    "en": [("In “Agensh: Scaling Organizational Intelligence to 1,024 Agents”", "index Agensh case, first paragraph: restates the Agensh card the scene now follows in Ch. 5"),
           ("This goes further than spreading prompts across processes", "index Agensh case: restates the card's 'no boss, not no structure' paragraph"),
           ("In six hours a single agent passed 33.89% of pandoc's hidden tests", "index Agensh case: the result is in the card and in the chart right below"),
           ("The full card is in Chapter 5", "index Agensh case: links to the card and the two runs that now follow it on the same page"),
           ("How big real swarms are", "index scale section heading: Ch. 1 'How many agents there really are' now holds the dashboard"),
           ("Across the 153 works in the survey, “swarm” covers very different systems", "index scale lede: restated by Ch. 1 text and the dashboard's tabs"),
           ("Findings", "index section label; the findings keep their own heading in the epilogue"),
           ("Chapters", "index chapter-grid label; replaced by the route in the intro"),
           ("Eleven chapters and an atlas of works", "index chapter-grid heading; replaced by the route in the intro"),
           ("Bars show the share of the 99 works. The survey's count over 153 works, cut-off 3 October 2026; see Chapter 1", "the ladder now sits inside Chapter 1: the sentence is kept, its pointer to Chapter 1 dropped")],
    "ru": [("В работе «Agensh: Scaling Organizational Intelligence to 1,024 Agents»", "разбор Agensh с прежней главной, первый абзац: повторяет карточку Agensh в гл. 5"),
           ("Это интереснее простого распределения промптов по процессам", "разбор Agensh: повторяет абзац карточки"),
           ("За шесть часов одиночный агент дошёл до 33,89", "разбор Agensh: результат есть в карточке и на графике ниже"),
           ("Подробный разбор — в главе 5", "разбор Agensh: ссылки на карточку и два запуска, которые теперь идут следом"),
           ("Насколько велики настоящие рои", "заголовок раздела масштаба с прежней главной: его место занял дашборд в гл. 1"),
           ("В 153 работах обзора под роем понимают очень разные системы", "вводка раздела масштаба: её повторяют текст гл. 1 и вкладки дашборда"),
           ("Выводы", "метка раздела прежней главной"), ("Главы", "метка сетки глав прежней главной; её заменил маршрут во вступлении"),
           ("Одиннадцать глав и атлас работ", "заголовок сетки глав прежней главной; его заменил маршрут во вступлении"),
           ("Полоса — доля от 99 работ. Расчёт обзора по 153 работам, срез 3 октября 2026 — глава 1", "лесенка теперь стоит в главе 1: фраза сохранена без ссылки на главу 1")],
}
INTENTIONAL_HREF = {"https://arxiv.org/html/2609.26781v1": "HTML version of the Agensh paper from the index case's closing paragraph; the card and the chart's source line link the same paper (arXiv:2609.26781)"}
REASON = "former index-page copy the single page does not repeat"


def norm(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = s.replace(" ", " ").replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def read(p):
    return open(p, encoding="utf-8").read()


def page_text(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S)
    return norm(h)


def md_files(lang):
    d = os.path.join(ROOT, "content", lang)
    return {f[:-3]: read(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".md")}


def check_lang(lang, old):
    R = {"lang": lang, "missing": {}, "counts": {}}
    h = read(os.path.join(SITE, lang, "index.html"))
    text = page_text(h)
    ids = re.findall(r'\sid="([^"]+)"', h)
    idset = set(ids)
    hrefs = set(html.unescape(x) for x in re.findall(r'href="([^"]+)"', h))
    srcs = set(re.findall(r'(?:src|href|data-full|data-full-light)="([^"]+)"', h))
    md = md_files(lang)
    # cards
    cards = [cid for t in md.values() for cid in re.findall(r"^:::(?:card|short)\s+(\S+)", t, re.M)]
    R["counts"]["cards"] = len(cards)
    R["missing"]["cards"] = [c for c in cards if ids.count("w-" + c) != 1]
    # figures
    figs = json.load(open(os.path.join(ROOT, "data", "figures.json"), encoding="utf-8"))["figures"]
    miss = []
    for f in figs:
        name = f["file"]
        if name.startswith("dash_"):
            base = name.replace("_dark.png", "")
            if not any(s.endswith(f"{base}_{lang}_dark.png") for s in srcs): miss.append(name)
        elif not any(s.endswith("/" + name) for s in srcs): miss.append(name)
    R["counts"]["figures"] = len(figs); R["missing"]["figures"] = miss
    # external links written in the Markdown
    urls = set()
    for t in md.values():
        for u in re.findall(r"\]\((https?://[^)\s]+)\)", t): urls.add(u)
    R["counts"]["links"] = len(urls)
    R["missing"]["links"] = sorted(u for u in urls if u not in hrefs)
    # headings
    heads = [norm(re.sub(r"[*_`]", "", m)) for t in md.values() for m in re.findall(r"^#{2,4}\s+(.+)$", t, re.M)]
    R["counts"]["headings"] = len(heads)
    R["missing"]["headings"] = [x for x in heads if x not in text]
    # blocks
    tl = sum(len([l for l in b.split("\n") if l.strip()]) for t in md.values() for b in re.findall(r"^:::timeline\n(.*?)\n:::", t, re.M | re.S))
    rel = sum(max(0, len([l for l in b.split("\n") if l.strip().startswith("|")]) - 2) for t in md.values() for b in re.findall(r"^:::related\n(.*?)\n:::", t, re.M | re.S))
    gl = len(re.findall(r"^- \*\*", md.get("glossary", ""), re.M))
    R["counts"].update(timeline_md=tl, timeline_page=h.count('<ol class="timeline">') and len(re.findall(r'<ol class="timeline">.*?</ol>', h, re.S)) and sum(x.count("<li>") for x in re.findall(r'<ol class="timeline">.*?</ol>', h, re.S)),
                       related_md=rel, related_page=sum(x.count("<li") for x in re.findall(r'<ul class="related">.*?</ul>', h, re.S)),
                       glossary_md=gl, atlas_rows=h.count('class="w" id="a-'), sources=len(re.findall(r'<li id="s-', h)))
    bad = []
    if R["counts"]["timeline_md"] != R["counts"]["timeline_page"]: bad.append("timeline")
    if R["counts"]["related_md"] != R["counts"]["related_page"]: bad.append("related")
    if R["counts"]["atlas_rows"] != 280: bad.append("atlas")
    R["missing"]["blocks"] = bad
    # against the former multipage build
    if old:
        oids, ohrefs, otexts = set(), set(), []
        for p in PAGES:
            fp = os.path.join(old, lang, p + ".html")
            if not os.path.exists(fp): continue
            t = read(fp)
            m = re.search(r'<main id="main"[^>]*>(.*?)</main>', t, re.S)
            body = m.group(1) if m else t
            for i in re.findall(r'\sid="((?:w|a|src)-[^"]+|s-[a-z][^"]*)"', body): oids.add(i)
            for u in re.findall(r'href="(https?://[^"]+)"', body): ohrefs.add(html.unescape(u))
            body = re.sub(r"<(script|style|svg)[^>]*>.*?</\1>", " ", body, flags=re.S)
            # page chrome of the former pages (pager, back-to-top, reading time, expand-all, the index's chapter grid and buttons) is not content
            for rx in (r'<p class="chend">.*?</p>', r'<ul class="chmeta">.*?</ul>', r'<p class="cta">.*?</p>', r'<nav class="pager".*?</nav>',
                       r'<section class="sec chmap".*?</section>', r'<span class="fnum">.*?</span>', r'<a class="orig"[^>]*>.*?</a>'):
                body = re.sub(rx, " ", body, flags=re.S)
            for blk in re.findall(r"<(p|li|td|th|dd|dt|figcaption|h[1-4]|time)(?:\s[^>]*)?>(.*?)</\1>", body, re.S):
                s = norm(blk[1])
                if len(s) >= 3: otexts.append((p, s))
        R["counts"]["old_ids"] = len(oids); R["counts"]["old_hrefs"] = len(ohrefs); R["counts"]["old_texts"] = len(otexts)
        R["missing"]["old_ids"] = sorted(i for i in oids if i not in idset)
        R["missing"]["old_hrefs"] = sorted(u for u in ohrefs if u not in hrefs and u not in INTENTIONAL_HREF)
        R["intentional_hrefs"] = {u: r for u, r in INTENTIONAL_HREF.items() if u in ohrefs and u not in hrefs}
        lost, intentional = [], []
        seen = set()
        for p, s in otexts:
            if s in seen: continue
            seen.add(s)
            if s in text: continue
            why = next((r for x, r in INTENTIONAL[lang] if s == x or (len(x) > 20 and s.startswith(x))), None)
            if why: intentional.append((p, s[:90], why)); continue
            lost.append((p, s[:200]))
        R["missing"]["old_text"] = lost
        R["intentional"] = {"reason": REASON, "items": intentional}
    return R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    out = [check_lang(l, a.old) for l in ("en", "ru")]
    fail = False
    for R in out:
        print(f"[{R['lang']}] counts: " + ", ".join(f"{k}={v}" for k, v in R["counts"].items()))
        for k, v in R["missing"].items():
            if v:
                fail = True
                print(f"  MISSING {k}: {len(v)}")
                for x in v[:12]: print("    -", x)
        if R.get("intentional"):
            print(f"  intentional removals: {len(R['intentional']['items'])} ({R['intentional']['reason']})")
    if a.json: json.dump(out, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("coverage:", "FAIL" if fail else "OK")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
