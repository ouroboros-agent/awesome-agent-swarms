#!/usr/bin/env python3
"""Build the Field edition: one scrolling page per language, a shared canvas renderer and the map of the catalogue.

  python scripts/build_field.py            # site/{ru,en}/index.html and delivery/Swarm-Field-{RU,EN}.html
  python scripts/build_field.py --site     # only site/{ru,en}/index.html (scripts/build_site.py calls this)

Sources:
  field/field.css, field/field.js   the shared page style and canvas renderer (no language text in them)
  field/{ru,en}.json                every visible word of one language: page text, sources, canvas labels
  updates/2026-10-19/catalogue.json the catalogue of 19 October 2026 (288 records), unchanged
  updates/2026-11-12/map-catalogue.json  the 26 records added for this edition and the map rules
                                    (one point per primary source, theme overrides, English display fields)
  data/works.json                   the registry of 3 October 2026: the 99 works of the 153-work analytic corpus
                                    that state how many agents run at once (the scale scene)

Two outputs per language from the same sources. delivery/Swarm-Field-*.html is one self-contained file that works
alone in an empty folder (file://, no server, no network): no link to any other local file. site/<lang>/index.html is
the same page inside the repository layout: it adds a language link that keeps the reader's place and a link to the
dated detailed survey (site/<lang>/survey-2026-10-19.html). Output is deterministic: the same sources give the same bytes.
"""
import html
import json
import os
import re
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELD = os.path.join(ROOT, "field")
LANGS = ("ru", "en")
SURVEY_PAGE = "survey-2026-10-19.html"       # where scripts/build_site.py writes the detailed survey of 19 October
DELIVERY = {"ru": "Swarm-Field-RU.html", "en": "Swarm-Field-EN.html"}
NB = " "

ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' "
        "fill='%23090b0c'/%3E%3Cg fill='%235fe3b3'%3E%3Ccircle cx='9' cy='9' r='2.6'/%3E%3Ccircle cx='16' cy='9' r='2.6' opacity='.45'/%3E"
        "%3Ccircle cx='23' cy='9' r='2.6' opacity='.45'/%3E%3Ccircle cx='9' cy='16' r='2.6' opacity='.45'/%3E%3Ccircle cx='16' cy='16' r='2.6'/%3E"
        "%3Ccircle cx='23' cy='16' r='2.6' opacity='.45'/%3E%3Ccircle cx='9' cy='23' r='2.6' opacity='.45'/%3E%3Ccircle cx='16' cy='23' r='2.6' "
        "opacity='.45'/%3E%3Ccircle cx='23' cy='23' r='2.6'/%3E%3C/g%3E%3C/svg%3E")
BRAND_SVG = ('<svg viewBox="0 0 18 18" aria-hidden="true"><g fill="#5fe3b3"><circle cx="3" cy="3" r="1.7"/><circle cx="9" cy="3" r="1.7" opacity=".4"/>'
             '<circle cx="15" cy="3" r="1.7" opacity=".4"/><circle cx="3" cy="9" r="1.7" opacity=".4"/><circle cx="9" cy="9" r="1.7"/>'
             '<circle cx="15" cy="9" r="1.7" opacity=".4"/><circle cx="3" cy="15" r="1.7" opacity=".4"/><circle cx="9" cy="15" r="1.7" opacity=".4"/>'
             '<circle cx="15" cy="15" r="1.7"/></g></svg>')
HEAD_JS = ("<script>(function(d){d.classList.add('js');try{if(matchMedia('(prefers-reduced-motion: reduce)').matches)d.classList.add('rm')}"
           "catch(e){}})(document.documentElement);</script>")

# ---------------------------------------------------------------- catalogue -> map rows
MONTHS = {
    "ru": (["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"],
           ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]),
    "en": (["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],) * 2,
}
NO_DATE = {"ru": "дата не указана", "en": "date not given"}
ORGS_MORE = {"ru": " и др.", "en": " and others"}
AUTHORS_MORE = {"ru": " и соавторы", "en": " et al."}
AUTHORS_AND = {"ru": " и ", "en": " and "}
FRESH_FROM = "2026-10-15"
# Where a source was published, read from its address: shown with the authors when a record names no organisation.
PLATFORMS = ((r"lesswrong\.com", "LessWrong"), (r"alignmentforum\.org", "AI Alignment Forum"), (r"substack\.com", "Substack"),
             (r"arxiv\.org", "arXiv"), (r"openreview\.net", "OpenReview"), (r"aclanthology\.org|doi\.org/10\.18653/", "ACL Anthology"),
             (r"doi\.org/10\.1126/sciadv", "Science Advances"), (r"doi\.org/10\.1126/science|science\.org/", "Science"),
             (r"doi\.org/10\.1038/s41467", "Nature Communications"), (r"doi\.org/10\.1038/s42256", "Nature Machine Intelligence"),
             (r"doi\.org/10\.1073/pnas", "PNAS"), (r"doi\.org/10\.1145/", "ACM"), (r"zenodo\.org|doi\.org/10\.5281/", "Zenodo"),
             (r"huggingface\.co", "Hugging Face"))
PARTICLES = {"de", "De", "van", "Van", "von", "Von", "da", "Da", "di", "Di", "del", "Del", "der", "Der", "le", "Le", "la", "La"}
ARXIV_ID = re.compile(r"^(\d{2})(\d{2})\.\d{4,5}$")


def read_json(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return json.load(f)


def date_text(s, lang):
    if not s:
        return NO_DATE[lang]
    p = s.split("-")
    day_names, month_names = MONTHS[lang]
    if len(p) == 3:
        return f"{int(p[2])} {day_names[int(p[1]) - 1]} {p[0]}"
    if len(p) == 2:
        return f"{month_names[int(p[1]) - 1]} {p[0]}"
    return p[0]


def month_index(s):
    """Map column: 0 = January 2025 … 22 = November 2026; -1 = before 2025; -2 = no month known."""
    if not s or len(s) < 7:
        return -2
    y, m = int(s[:4]), int(s[5:7])
    return -1 if y < 2025 else (y - 2025) * 12 + m - 1


def is_fresh(s):
    """First public on or after 15 October 2026; a record known only to a month counts from November 2026."""
    if not s:
        return 0
    if len(s) >= 10:
        return int(s >= FRESH_FROM)
    return int(len(s) == 7 and s >= "2026-11")


def effective_date(rec, rules):
    """The date a map point is placed and labelled by: a checked date from the display rules, else the catalogue date,
    else (or when the catalogue knows only the year) the month of first submission that an arXiv identifier encodes."""
    fix = (rules.get("display") or {}).get(rec["id"], {})
    if fix.get("date_iso"):
        return fix["date_iso"]
    d = rec.get("date_first_public")
    if d and len(d) >= 7:
        return d
    m = ARXIV_ID.match((rec.get("identifiers") or {}).get("arxiv") or "")
    if m and (not d or d == "20" + m.group(1)):
        return f"20{m.group(1)}-{m.group(2)}"
    return d


def flat_orgs(orgs):
    return [x.strip() for e in (orgs or []) for x in e.split(";") if x.strip()]


def platform(url):
    return next((name for pat, name in PLATFORMS if re.search(pat, url or "")), "")


def surname(name):
    t = name.split()
    return " ".join(t[-2:]) if len(t) >= 3 and t[-2] in PARTICLES else (t[-1] if t else "")


def authors_text(rec, lang):
    """Authors as a short byline: one or two surnames, or the first surname and "et al."."""
    a = [x.strip() for x in (rec.get("authors") or []) if x and x.strip()]
    if not a:
        return ""
    more = bool(rec.get("et_al")) or (rec.get("n_authors") or 0) > len(a) or len(a) > 2
    s = [surname(x) for x in a]
    if more:
        return s[0] + AUTHORS_MORE[lang]
    return AUTHORS_AND[lang].join(s)


def who_text(rec, lang, display_en):
    """The tooltip's second line: organisations (first three), else authors with the platform, else the platform."""
    orgs = rec.get("orgs") or []
    if lang == "en" and rec["id"] in display_en.get("orgs", {}):
        orgs = display_en["orgs"][rec["id"]]
    o = flat_orgs(orgs)
    venue = rec.get("venue_note") if rec.get("added_record") else ""
    if o:
        s = ", ".join(o[:3]) + (ORGS_MORE[lang] if len(o) > 3 else "")
    else:
        s = " · ".join(x for x in (authors_text(rec, lang), "" if venue else platform(rec["urls"]["primary"])) if x)
    return " · ".join(x for x in (s, venue) if x)


def title_text(rec, lang, display_en):
    if lang == "en" and rec["id"] in display_en.get("titles", {}):
        return display_en["titles"][rec["id"]]
    return rec.get("title") or re.sub(r"^https?://", "", rec["urls"]["primary"]).rstrip("/")


def display(rec, lang, rules):
    """(title, who, date text, date) of one record as the reader sees it: the display rules of map-catalogue.json
    (language-neutral "title"/"who", per-language "ru"/"en", a checked "date_iso") over the catalogue fields."""
    ov = (rules.get("display") or {}).get(rec["id"], {})
    fix = {k: ov[k] for k in ("title", "who") if k in ov}
    fix.update(ov.get(lang, {}))
    d = effective_date(rec, rules)
    return (fix.get("title") or title_text(rec, lang, rules["display_en"]), fix.get("who") or who_text(rec, lang, rules["display_en"]),
            fix.get("date") or date_text(d, lang), d)


def catalogue_records():
    """The current catalogue: 288 records of 19 October, then the 26 records added for this edition."""
    base = read_json("updates", "2026-10-19", "catalogue.json")["works"]
    add = read_json("updates", "2026-11-12", "map-catalogue.json")
    added = [dict(r, added_record=True) for r in add["added"]]
    ids = [r["id"] for r in base] + [r["id"] for r in added]
    assert len(ids) == len(set(ids)), "duplicate record ids"
    return base + added, add["map"]


def map_rows(lang):
    """[title, who, date, month column, theme index, url, fresh] for every point of the map."""
    recs, rules = catalogue_records()
    by = {r["id"]: r for r in recs}
    merged = {m["record"] for m in rules["merged"]}
    for m in rules["merged"]:
        assert by[m["record"]]["urls"]["primary"] == by[m["into"]]["urls"]["primary"] == m["url"], m
    rows = []
    for r in recs:
        if r["id"] in merged:
            continue
        if r.get("added_record"):
            ch = r["theme"]
        elif r["id"] in rules["theme_overrides"]:
            ch = rules["theme_overrides"][r["id"]]
        else:
            pages = r.get("source_pages") or (by[r["part_of"]].get("source_pages") if r.get("part_of") else None) or []
            ch = pages[0]
        title, who, when, d = display(r, lang, rules)
        rows.append([title, who, when, month_index(d), int(ch[2:]) - 2, r["urls"]["primary"], is_fresh(d)])
    urls = [x[5] for x in rows]
    assert len(urls) == len(set(urls)), "two map points share a primary URL"
    return rows


def scale_rows(lang):
    """The 99 works of the analytic corpus (3 October 2026) that state how many agents run at once, shown with the same
    titles and bylines as their map points (the catalogue record with the same primary URL)."""
    works = read_json("data", "works.json")["works"]
    recs, rules = catalogue_records()
    merged = {m["record"] for m in rules["merged"]}
    by_url = {}
    for r in recs:
        if r["id"] not in merged:
            by_url.setdefault(r["urls"]["primary"], r)
    counts = rules.get("scale_counts") or {}
    out = []
    for w in works:
        c = w.get("corpus") or {}
        n = c.get("agents_max_simultaneous")
        if c.get("scale_kind") == "simultaneous" and isinstance(n, (int, float)):
            rec = by_url.get(w["urls"]["primary"], w)
            title, who, _, _ = display(rec, lang, rules)
            out.append([int(counts.get(w["id"], {}).get("n", n)), title, who, w["urls"]["primary"], w["id"]])
    out.sort(key=lambda x: (x[0], x[1]))
    known = [x[0] for x in out]
    assert len(known) == 99 and statistics.median(known) == 7, (len(known), statistics.median(known))
    assert [sum(1 for x in known if x >= t) for t in (10, 100, 1000, 10000)] == [42, 15, 7, 4]
    return out


def scale_landmarks(lang):
    """Labelled points of the scale scene that are not in the 3 October sample: [agents, title, who, url, id]."""
    recs, rules = catalogue_records()
    by = {r["id"]: r for r in recs}
    out = []
    for m in rules.get("scale_landmarks") or []:
        title, who, _, _ = display(by[m["record"]], lang, rules)
        out.append([m["n"], title, who, by[m["record"]]["urls"]["primary"], m["record"]])
    return out


def additions():
    """The 26 records added for this edition (updates/2026-11-12/map-catalogue.json), in file order."""
    return read_json("updates", "2026-11-12", "map-catalogue.json")["added"]


def addition_who(r, lang):
    return who_text(dict(r, added_record=True), lang, {})


def bib_additions():
    """BibTeX of the added records (updates/2026-11-12/references.bib). Key = record id. Authors as the sources were
    recorded: full names where the record has them, otherwise surnames and "others"; an organisation as corporate author."""
    out = ["% Swarm Dynamics: BibTeX of the 26 records added for the Field edition, 12 November 2026.",
           "% Generated by scripts/build_field.py from updates/2026-11-12/map-catalogue.json; key = record id.",
           "% Authors as recorded there: full names where known, otherwise surnames with \"others\"; an organisation as corporate author.", ""]
    for r in additions():
        names = list(r.get("authors") or []) + (["others"] if r.get("et_al") else [])
        if not names and r.get("orgs"):
            names = ["{" + o + "}" for o in r["orgs"]]
        d = r["date_first_public"]
        f = [f"  title = {{{r['title']}}}"]
        if names:
            f.append("  author = {" + " and ".join(names) + "}")
        f += [f"  year = {{{d[:4]}}}", f"  url = {{{r['urls']['primary']}}}"]
        note = "; ".join([f"Dated {d}"] + [r[k].rstrip(".") for k in ("venue_note", "date_note") if r.get(k)] + ["added to the map 12 November 2026"])
        f.append("  note = {" + note + "}")
        ids = r.get("identifiers") or {}
        if ids.get("doi"):
            f.append(f"  doi = {{{ids['doi']}}}")
        if ids.get("arxiv"):
            f += [f"  eprint = {{{ids['arxiv']}}}", "  archivePrefix = {arXiv}"]
        out.append(f"@misc{{{r['id']},\n" + ",\n".join(f) + "\n}\n")
    return "\n".join(out)


# ---------------------------------------------------------------- page
def src_html(s):
    if "url" in s:
        return f'<a href="{html.escape(s["url"])}" target="_blank" rel="noopener">{s["title"]}</a>{s["rest"]}'
    return s["text"]


def step_html(sc, st, s, site, extra):
    """One step of a scene. extra: lines added at the end of the card (the legend of the map, the survey link).
    The card's content sits in div.ci: when the text is taller than the space the card has, field.js keeps the box and moves .ci."""
    cls = " " + s["cls"] if s.get("cls") else ""
    sid = f' id="s{sc}-{st}"' if site else ""
    out = [f'  <div class="step{cls}"{sid} data-sc="{sc}" data-st="{st}"><div class="card"><div class="ci">']
    if "kick" in s:
        out.append(f'    <p class="kick"><i>{sc:02d}</i>{s["kick"]}</p>')
    if "h2" in s:
        out.append(f'    <h2>{s["h2"]}</h2>')
    for p in s.get("p", []):
        out.append(f'    <p style="margin-top:20px">{p}</p>' if s.get("cls") == "long" else f"    <p>{p}</p>")
    for x in s.get("src", []):
        out.append(f'    <p class="src">{src_html(x)}</p>')
    if "qs" in s:
        out.append('    <ol class="qs">')
        out += [f"      <li>{q}</li>" for q in s["qs"]]
        out.append("    </ol>")
    if "sign" in s:
        out.append(f'    <p class="sign">{s["sign"]}</p>')
    out += extra
    out.append("  </div></div></div>")
    return out


def legend_html(labels, rows):
    """The map legend as plain HTML, so the themes and their counts read without JavaScript; the script redraws it."""
    th = [0] * len(labels["themes"])
    for r in rows:
        th[r[4]] += 1
    items = [f"<li><i></i><span>{t}</span><em>{n}</em></li>" for t, n in zip(labels["themes"], th)]
    items.append(f'<li class="fresh"><i></i><span>{labels["freshLegend"]}</span><em>{sum(r[6] for r in rows)}</em></li>')
    return "".join(items)


def page(lang, site=False):
    C = read_json("field", f"{lang}.json")
    css = open(os.path.join(FIELD, "field.css"), encoding="utf-8").read()
    js = open(os.path.join(FIELD, "field.js"), encoding="utf-8").read()
    rows = map_rows(lang)
    H = C["hero"]
    other = "en" if lang == "ru" else "ru"
    lines = ["<!DOCTYPE html>", f'<html lang="{lang}">', "<head>", '<meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
             f"<title>{C['title']}</title>", f'<meta name="description" content="{C["description"]}">',
             '<meta name="theme-color" content="#090b0c">', '<meta name="color-scheme" content="dark">', f'<link rel="icon" href="{ICON}">']
    if site:
        lines.append(f'<link rel="alternate" hreflang="{other}" href="../{other}/index.html"><link rel="alternate" hreflang="{lang}" href="index.html">')
    if site:
        # an address of the single page of 19 October (index.html#ch04, #atlas, #w-…) still lands on that survey
        lines.append("<script>(function(h){if(h.length>1&&!/^#s[0-7](-[0-9]+)?$/.test(h))location.replace(" + json.dumps(SURVEY_PAGE) + "+h)})(location.hash);</script>")
    lines += [HEAD_JS, "<style>", css + "</style>", "</head>", "<body>",
              '<canvas id="field" aria-hidden="true"></canvas>', '<div class="prog" id="prog"></div>', '<header class="top">',
              f'  <div class="brand">{BRAND_SVG}{C["brand"]}</div>', '  <div class="where" id="where"></div>']
    if site:
        S = C["site"]
        lines.append(f'  <a class="lang" id="lang" href="../{other}/index.html" hreflang="{other}" lang="{other}" title="{S["lang_title"]}">{S["lang"]}</a>')
    lines += ["</header>", "", "<main>", '<section class="hero" id="s0">', '  <div class="pin" id="pin">', '    <div class="h-copy" id="hCopy">',
              f'      <p class="eyebrow">{H["eyebrow"]}</p>', f'      <h1>{H["h1"]}</h1>', f'      <p class="lead">{H["lead"]}</p>', "    </div>",
              '    <div class="cue" id="cue" aria-hidden="true"></div>', '    <div class="h-cap" id="hCap">',
              f'      <div class="tabs" role="tablist" aria-label="{H["tabs_label"]}">']
    for k, m in enumerate(H["modes"]):
        on, sel = (" on", "true") if k == 0 else ("", "false")
        lines.append(f'        <button class="tab{on}" role="tab" aria-selected="{sel}" data-m="{k}"><i>{k + 1}</i><span class="nm">{m["name"]}</span><span class="pb"></span></button>')
    lines += ["      </div>", '      <div class="modes">']
    for k, m in enumerate(H["modes"]):
        lines += [f'        <div class="mode{" on" if k == 0 else ""}">', f'          <p class="mech">{m["mech"]}</p>',
                  f'          <div class="mr"><p class="meas">{m["meas"]}</p>']
        lines += [f'          <p class="src">{src_html(x)}</p></div>' if i == len(m["src"]) - 1 else f'          <p class="src">{src_html(x)}</p>'
                  for i, x in enumerate(m["src"])]
        lines.append("        </div>")
    A = H["aside"]
    lines += ["      </div>", "    </div>", '    <div class="h-a" id="hA"><div class="ci">', f'      <h2>{A["h2"]}</h2>']
    lines += [f"      <p>{p}</p>" if i == 0 else f'      <p style="margin-top:12px">{p}</p>' for i, p in enumerate(A["p"])]
    lines += [f'      <p class="src">{src_html(x)}</p>' for x in A["src"]]
    lines += ["    </div></div>", "  </div>"]
    if site:
        lines.append('  <div class="mark" id="s0-1" aria-hidden="true"></div>')
    lines.append("</section>")
    for scene in C["scenes"]:
        sc = scene["id"]
        lines += ["", f'<section class="scene" id="s{sc}">']
        for st, s in enumerate(scene["steps"]):
            extra = []
            if s.get("cls") == "long":
                extra.append(f'    <ul class="legend" id="legend">{legend_html(C["labels"], rows)}</ul>')
            if s.get("cls") == "fin" and site:
                extra.append(f'    <p class="more"><a href="{SURVEY_PAGE}">{C["site"]["survey"]}</a></p>')
            lines += step_html(sc, st, s, site, extra)
        if sc == 7:
            lines.append('  <div class="end"></div>')
        lines.append("</section>")
    data = {"L": C["labels"], "works": rows, "scale": scale_rows(lang), "scaleLm": scale_landmarks(lang)}
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    lines += ["</main>", "",
              f'<div class="tip" id="tip" role="status"><div class="t"></div><div class="m"></div><div class="th"><i></i><span></span></div><a target="_blank" rel="noopener">{C["tip_open"]}</a></div>',
              "", f'<script id="data" type="application/json">{blob}</script>', "<script>", js.rstrip("\n"), "</script>", "</body>", "</html>", ""]
    return "\n".join(lines)


def build(site_dir=None, delivery_dir=None):
    written = []
    if site_dir:
        os.makedirs(os.path.join(site_dir, "data"), exist_ok=True)
        for name, text in (("map-catalogue-2026-11-12.json", open(os.path.join(ROOT, "updates", "2026-11-12", "map-catalogue.json"), encoding="utf-8").read()),
                           ("references-2026-11-12.bib", bib_additions())):
            with open(os.path.join(site_dir, "data", name), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            written.append(os.path.relpath(os.path.join(site_dir, "data", name), ROOT))
    for lang in LANGS:
        if site_dir:
            os.makedirs(os.path.join(site_dir, lang), exist_ok=True)
            p = os.path.join(site_dir, lang, "index.html")
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(page(lang, site=True))
            written.append(os.path.relpath(p, ROOT))
        if delivery_dir:
            os.makedirs(delivery_dir, exist_ok=True)
            p = os.path.join(delivery_dir, DELIVERY[lang])
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(page(lang, site=False))
            written.append(os.path.relpath(p, ROOT))
    return written


if __name__ == "__main__":
    if "--bib" in sys.argv:          # refresh updates/2026-11-12/references.bib from map-catalogue.json
        with open(os.path.join(ROOT, "updates", "2026-11-12", "references.bib"), "w", encoding="utf-8", newline="\n") as f:
            f.write(bib_additions())
        print("wrote updates/2026-11-12/references.bib")
        sys.exit(0)
    site_only = "--site" in sys.argv
    out = build(os.path.join(ROOT, "site"), None if site_only else os.path.join(ROOT, "delivery"))
    for p in out:
        print("wrote", p, os.path.getsize(os.path.join(ROOT, p)), "bytes")
