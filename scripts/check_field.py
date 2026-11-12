#!/usr/bin/env python3
"""Static checks of the Field edition (no browser): the two languages, the map against the catalogue, the outputs.

  python scripts/check_field.py              # exits 1 on any failure
  python scripts/check_field.py --out DIR    # also writes DIR/check_field.json

Languages (field/ru.json, field/en.json): the same scenes, steps, paragraphs and sources; every source URL and linked
title the same; the same numbers in every step, source line and canvas label (thousands and decimal separators
normalised); no Cyrillic anywhere in English except the Russian name of the link back to Russian.
Map and scale: one point per primary URL, every point a catalogue record (19 October catalogue + the 12 November
additions, minus the constituents merged into their bundle card), the same points in both languages, English map text
free of Cyrillic; the scale scene's 99 works of the 3 October analytic corpus (median 7; 42 / 15 / 7 / 4); the BibTeX
of the additions equal to what the builder writes. Outputs: delivery/ and site/<lang>/index.html equal a fresh build
(twice the same bytes); the delivery files load nothing and link to no other local file; the page states the
3 October date at the 99-of-153 statistic.
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_field as F

RESULTS = []
CYR = re.compile(r"[А-Яа-яЁё]")


def ok(cond, name, detail=None):
    RESULTS.append({"check": name, "ok": bool(cond), "detail": detail})
    print(("PASS " if cond else "FAIL ") + name + ("" if cond or detail is None else "  " + json.dumps(detail, ensure_ascii=False)[:700]))


def plain(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or ""))


def numbers(s, lang):
    """Every number in a text, as strings with '.' decimals and no thousands separators."""
    t = plain(s).replace("−", "-")
    t = re.sub(r"(?<=\d)[    ](?=\d{3}(?!\d))", "", t)          # 36 612, 1 024
    if lang == "en":
        t = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", t)                          # 36,612
    else:
        t = re.sub(r"(?<=\d),(?=\d{3}(?!\d)\s*[A-Za-z])", "", t)                # an English title quoted in Russian: «… to 1,024 Agents»
        t = re.sub(r"(?<=\d),(?=\d)", ".", t)                                  # 0,769
    return sorted(re.findall(r"\d+(?:\.\d+)?", t))


def walk(x, path=""):
    """(path, string) for every string in a nested structure."""
    if isinstance(x, dict):
        for k, v in x.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(x, str):
        yield path, x


def shape(x):
    if isinstance(x, dict):
        return {k: shape(v) for k, v in x.items()}
    if isinstance(x, list):
        return [shape(v) for v in x]
    return type(x).__name__


def texts_of_step(s):
    return [s.get("kick", ""), s.get("h2", ""), s.get("sign", "")] + s.get("p", []) + s.get("qs", []) + [plain(x.get("text", "")) + plain(x.get("rest", "")) for x in s.get("src", [])]


def check_languages():
    RU, EN = F.read_json("field", "ru.json"), F.read_json("field", "en.json")
    ok(shape(RU) == shape(EN), "ru/en content: identical structure (scenes, steps, paragraphs, sources, labels)")
    srcs = lambda C: [(x.get("url"), x.get("title")) for _, x in sources(C)]
    a, b = srcs(RU), srcs(EN)
    ok(a == b, f"ru/en: the same {sum(1 for u, _ in a if u)} source links and linked titles in the same places", [x for x in zip(a, b) if x[0] != x[1]][:5])
    bad = []
    pairs = [("hero.mode%d" % k, [m["mech"], m["meas"]] + [plain(x.get("rest", "")) for x in m["src"]], [n["mech"], n["meas"]] + [plain(x.get("rest", "")) for x in n["src"]])
             for k, (m, n) in enumerate(zip(RU["hero"]["modes"], EN["hero"]["modes"]))]
    A, B = RU["hero"]["aside"], EN["hero"]["aside"]
    pairs.append(("hero.aside", A["p"] + [A["h2"]] + [plain(x.get("rest", "")) for x in A["src"]], B["p"] + [B["h2"]] + [plain(x.get("rest", "")) for x in B["src"]]))
    pairs.append(("hero.copy", [RU["hero"]["eyebrow"], RU["hero"]["h1"], RU["hero"]["lead"]], [EN["hero"]["eyebrow"], EN["hero"]["h1"], EN["hero"]["lead"]]))
    for sr, se in zip(RU["scenes"], EN["scenes"]):
        for st, (x, y) in enumerate(zip(sr["steps"], se["steps"])):
            pairs.append((f"scene{sr['id']}.step{st}", texts_of_step(x), texts_of_step(y)))
    for k in RU["labels"]:
        if k == "num":
            continue
        pairs.append((f"labels.{k}", [s for _, s in walk(RU["labels"][k])], [s for _, s in walk(EN["labels"][k])]))
    for name, x, y in pairs:
        nx = sorted(sum((numbers(t, "ru") for t in x), []))
        ny = sorted(sum((numbers(t, "en") for t in y), []))
        if nx != ny:
            bad.append({"where": name, "ru": nx, "en": ny})
    ok(not bad, f"ru/en: the same numbers in all {len(pairs)} steps, source lines and canvas label groups", bad[:6])
    cyr = [(p, s[:80]) for p, s in walk(EN) if CYR.search(s) and p != ".site.lang_title"]
    ok(not cyr, "en content: no Cyrillic except the Russian name of the link to the Russian page", cyr[:8])
    lat = [p for p, s in walk(RU["labels"]) if not CYR.search(s) and re.search(r"[a-z]{3}", s) and not re.search(r"(ScaleMAS|COLLABMEM|Moltbook|Agensh|Anthropic|OpenAI|Avalon|ParallACT|Mind Viruses|Music Lab|Minecraft|Swarm Scaling|Claude|GPT|Gemini|NARCBench|pull request|sharing|access|routing|provenance|conflict|retention|Sonnet|DeepMind|Y Combinator|YC|Microsoft|s³|Debate or Vote|Navier|J-Space|online SFT|Wiz|Wisconsin)", s)]
    ok(not lat, "ru labels: no untranslated English interface words", lat[:8])
    st1 = RU["scenes"][0]["steps"][1]["p"][0], EN["scenes"][0]["steps"][1]["p"][0]
    ok("3&nbsp;октября" in st1[0] and "3&nbsp;October" in st1[1] and "99" in st1[0] and "153" in st1[0],
       "scale statistic: 99 of 153 is dated 3 October at the statistic itself, in both languages")


def sources(C):
    for k, m in enumerate(C["hero"]["modes"]):
        for x in m["src"]:
            yield f"hero.mode{k}", x
    for x in C["hero"]["aside"]["src"]:
        yield "hero.aside", x
    for sc in C["scenes"]:
        for st, s in enumerate(sc["steps"]):
            for x in s.get("src", []):
                yield f"scene{sc['id']}.step{st}", x


def check_map():
    recs, rules = F.catalogue_records()
    ru, en = F.map_rows("ru"), F.map_rows("en")
    base = F.read_json("updates", "2026-10-19", "catalogue.json")["works"]
    add = F.additions()
    n_expected = len(base) - len(rules["merged"]) + len(add)
    ok(len(ru) == len(en) == n_expected == 306, f"map: {len(ru)} points = {len(base)} catalogue records − {len(rules['merged'])} merged constituents + {len(add)} additions")
    ok([r[3:] for r in ru] == [r[3:] for r in en], "map: the same points, months, themes, links and fresh marks in both languages")
    urls = [r[5] for r in ru]
    prim = {r["urls"]["primary"] for r in recs}
    ok(len(set(urls)) == len(urls) and set(urls) <= prim, "map: one point per primary URL, every point a catalogue record")
    by = {r["id"]: r for r in recs}
    merged_ok = all(by[m["record"]].get("part_of") == m["into"] and by[m["record"]]["urls"]["primary"] == by[m["into"]]["urls"]["primary"] for m in rules["merged"])
    ok(merged_ok and len(rules["merged"]) == 8, "map: each merged record is a constituent with its bundle card's exact URL (8)")
    cyr = [(r[0][:50], r[1][:50], r[2]) for r in en if CYR.search(" ".join(map(str, r[:3])))]
    ok(not cyr, "map (en): titles, organisations and dates without Cyrillic", cyr[:6])
    fr = sum(r[6] for r in ru)
    ok(all((r[6] == 1) == F.is_fresh(F.effective_date(next(x for x in recs if x["urls"]["primary"] == r[5]), rules)) for r in ru),
       f"map: {fr} fresh points, each first public on or after 15 October 2026 by its catalogue date (or its checked display date)")
    sc = F.scale_rows("ru")
    ok(len(sc) == 99, "scale: 99 works of the 3 October analytic corpus with a simultaneous agent count (median 7; 42/15/7/4 asserted in the builder)")
    bib = open(os.path.join(ROOT, "updates", "2026-11-12", "references.bib"), encoding="utf-8").read()
    keys = re.findall(r"^@misc\{([^,]+),", bib, re.M)
    ok(bib == F.bib_additions() and keys == [r["id"] for r in add], f"bibtex: updates/2026-11-12/references.bib has the {len(keys)} additions, as the builder writes them")


# Notes of the cataloguing work that must never reach a reader (map and scale tooltips), and a bare address as a title.
SERVICE = re.compile(r"[Nn]ot stated|[Nn]one stated|no affiliation|metadata|метадан|combined card|HTML title|multi-agent sections|LessWrong user|"
                     r"§|новостная статья|news article|not an institutional|\(blog\)|preprint title|also on |\(\d+ (?:автор|author)|организация\)|"
                     r"ведущий автор|lead author|\(Leibo\)|personal site|Independent author")
BARE = re.compile(r"^(?:https?://)?[a-z0-9-]+(?:\.[a-z0-9-]+)+/\S*$")


def check_display():
    """What a reader sees on hovering a dot (map, scale, labelled scale points): a title, a byline and (map) a date,
    with no cataloguing notes; FACT-CORRECTIONS.md held in the data and in the text."""
    recs, rules = F.catalogue_records()
    by_url = {r["urls"]["primary"]: r for r in recs if r["id"] not in {m["record"] for m in rules["merged"]}}
    for lang in F.LANGS:
        rows, sc, lm = F.map_rows(lang), F.scale_rows(lang), F.scale_landmarks(lang)
        items = [("map", r[0], r[1]) for r in rows] + [("scale", r[1], r[2]) for r in sc + lm]
        bad = [(k, t[:60], w[:60]) for k, t, w in items if not t.strip() or not w.strip() or SERVICE.search(t) or SERVICE.search(w) or BARE.match(t)]
        ok(not bad, f"{lang} tooltips: {len(items)} titles and bylines, none empty, a bare address or a cataloguing note", bad[:8])
        nod = [r[0][:60] for r in rows if r[2] == F.NO_DATE[lang] and not (rules["display"].get(by_url[r[5]]["id"]) or {}).get("no_date")]
        ok(not nod, f"{lang} map: 'no date' only where the source gives none ({sum(r[2] == F.NO_DATE[lang] for r in rows)} points, each with its reason)", nod[:6])
    # FACT-CORRECTIONS.md, as data
    RU, EN = F.read_json("field", "ru.json"), F.read_json("field", "en.json")
    fc = []
    for lang, C in (("ru", RU), ("en", EN)):
        rows, sc = F.map_rows(lang), F.scale_rows(lang)
        ordw = [r[1] for r in rows if "6cb7qd3RSkgnviCpf" in r[5]] + [plain(x.get("rest", "")) for _, x in sources(C) if "6cb7qd3RSkgnviCpf" in x.get("url", "")]
        fc.append((f"{lang} 3: Swarm Scaling without the uncertain Oxford attribution", ordw and not any("Oxford" in w or "Оксфорд" in w for w in ordw)))
        wt = [r[1] for r in rows if r[5].endswith("2610.00583")] + [r[2] for r in sc if r[4] == "worse-together"]
        fc.append((f"{lang} 9: Worse Together credited to the Anthropic Fellows, not the catalogue's bare 'Stanford University, Anthropic'", wt and all("Anthropic Fellows" in w for w in wt)))
        ag = [r for r in sc if r[4] == "agensh-1024"]
        fc.append((f"{lang} 1: Agensh on the scale at 1,024 agents, as in its label and text", ag and ag[0][0] == 1024))
        s2 = " ".join(plain(t) for st in C["scenes"][1]["steps"] for t in texts_of_step(st)).replace("\xa0", " ")
        fc.append((f"{lang} 1: scene 2 says Agensh did not measure token use", ("не считали" in s2 or "не сравнивали" in s2) if lang == "ru" else "not measured" in s2 or "does not compare" in s2))
        s5 = C["scenes"][4]["steps"]
        jt = " ".join(plain(t) for st in s5 for t in texts_of_step(st) if "J-Space" in t or "NARCBench" in t)
        fc.append((f"{lang} 8: J-Space reported as 86% against 33% of honest counterfactuals", "86" in jt and "33" in jt))
        inf = " ".join(plain(t) for st in s5 for t in st.get("p", []) if "надзир" in t or "oversee" in t)
        fc.append((f"{lang} 7: three oversight environments", ("трёх" in inf) if lang == "ru" else "three" in inf))
    bad = [n for n, c in fc if not c]
    ok(not bad, f"FACT-CORRECTIONS.md held in data and text ({len(fc)} assertions)", bad)


LOADERS = re.compile(r"""<link\b[^>]*\brel=["']?stylesheet|<script\b[^>]*\bsrc=|<img\b|<iframe\b|<video\b|<audio\b|<source\b|@import|\bfetch\s*\(|XMLHttpRequest|\bimport\s*\(|WebSocket|sendBeacon|EventSource""", re.I)


def check_outputs():
    for lang in F.LANGS:
        d1, d2 = F.page(lang, site=False), F.page(lang, site=False)
        s1 = F.page(lang, site=True)
        ok(d1 == d2, f"{lang}: two renders give the same bytes")
        p = os.path.join(ROOT, "delivery", F.DELIVERY[lang])
        cur = open(p, encoding="utf-8").read() if os.path.exists(p) else None
        ok(cur == d1, f"{lang}: delivery/{F.DELIVERY[lang]} is up to date with field/ and the catalogue")
        sp = os.path.join(ROOT, "site", lang, "index.html")
        ok(os.path.exists(sp) and open(sp, encoding="utf-8").read() == s1, f"{lang}: site/{lang}/index.html is up to date (the Field page, not the survey)")
        refs = re.findall(r"""\b(?:href|src)\s*=\s*["']([^"']*)["']""", d1)
        local = [r for r in refs if not r.startswith(("https://", "http://", "data:", "#"))]
        ok(not local, f"{lang} delivery: no link to another local file ({len(refs)} links, all https, data: or in-page)", local[:5])
        ok(not LOADERS.search(d1), f"{lang} delivery: loads nothing (no external script, style, image, frame, fetch or socket)", (LOADERS.search(d1) or [None])[0])
        ok(len(d1.encode()) < 1_500_000, f"{lang} delivery: {len(d1.encode())} bytes")
        site_refs = [r for r in re.findall(r"""\b(?:href|src)\s*=\s*["']([^"']*)["']""", s1) if not r.startswith(("https://", "http://", "data:", "#"))]
        miss = [r for r in site_refs if not os.path.exists(os.path.normpath(os.path.join(ROOT, "site", lang, r.split("#")[0])))]
        ok(site_refs and not miss, f"{lang} site page: its repository links exist ({', '.join(sorted(set(r.split('#')[0] for r in site_refs)))})", miss)
        if lang == "en":
            vis = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", "", d1, flags=re.S)
            ok(not CYR.search(vis) and not CYR.search(d1), "en delivery: no Cyrillic in the file (markup, data, labels, script)")


if __name__ == "__main__":
    check_languages()
    check_map()
    check_display()
    check_outputs()
    fails = [r for r in RESULTS if not r["ok"]]
    print(f"\n{len(RESULTS) - len(fails)} passed, {len(fails)} failed")
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "check_field.json"), "w", encoding="utf-8") as f:
            json.dump(RESULTS, f, ensure_ascii=False, indent=1)
    sys.exit(1 if fails else 0)
