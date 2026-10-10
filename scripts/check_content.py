#!/usr/bin/env python3
"""Content checks for content/{ru,en}/*.md.

  python scripts/check_content.py                    # syntax + RU/EN parity for all pages
  python scripts/check_content.py --page ch04        # one page
  python scripts/check_content.py --source <S>       # also check RU preservation against the October source
  python scripts/check_content.py --json out.json    # machine-readable report

Exit code 1 if any ERROR. Checks:
  syntax       front matter, balanced blocks, known block kinds, card IDs known to data/works.json (if present)
  preservation (RU vs October import) cards, figures, URLs, table rows and numbers; a number missing from
               its page but present elsewhere on the RU site is reported as moved (info), missing everywhere = ERROR
  parity       (EN vs RU) same block sequence and card IDs, same figures in the same order, same URLs,
               same tables and row counts, same numbers (format-normalized), no Cyrillic in EN
"""
import argparse, json, os, re, sys
from collections import Counter, OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
KINDS = {"card", "short", "callout", "timeline", "takeaways", "findings", "related", "cover", "corpus", "sources", "chart"}
CYR = re.compile(r"[А-Яа-яЁё]")

def read_page(path):
    text = open(path, encoding="utf-8").read()
    fm = OrderedDict()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).split("\n"):
            k, _, v = line.partition(":")
            if k.strip(): fm[k.strip()] = v.strip()
        body = text[m.end():]
    else:
        body = text
    return fm, body

def parse(body):
    """Return list of items: ('block', kind, arg, text, lineno) / ('md', text, lineno) and errors."""
    items, errs, buf = [], [], []
    lines = body.split("\n"); i = 0; start = 1
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"^:::(\w+)\s*(.*)$", ln)
        if m:
            if buf: items.append(("md", "\n".join(buf), start)); buf = []
            kind, arg = m.group(1), m.group(2).strip()
            if kind not in KINDS: errs.append(f"line {i+1}: unknown block kind ':::{kind}'")
            j = i + 1; inner = []
            while j < len(lines) and lines[j].strip() != ":::":
                if re.match(r"^:::\w+", lines[j]): errs.append(f"line {j+1}: block opened inside ':::{kind}' (line {i+1}) — missing ':::'?"); break
                inner.append(lines[j]); j += 1
            if j >= len(lines): errs.append(f"line {i+1}: ':::{kind}' never closed")
            items.append(("block", kind, arg, "\n".join(inner), i + 1)); i = j + 1; start = i + 1; continue
        buf.append(ln); i += 1
    if buf: items.append(("md", "\n".join(buf), start))
    return items, errs

LINK = re.compile(r"\]\((https?://[^)\s]+)\)")
BARE = re.compile(r"(?<![(\[])https?://[^\s)\]|>]+")
FIG = re.compile(r"(?m)^\s*!fig\s+([^\s|]+)")

def urls(text):
    out = LINK.findall(text) + [u for u in BARE.findall(text)]
    return [u.rstrip(".,;") for u in out]

def strip_for_numbers(text):
    t = re.sub(r"\]\([^)]*\)", "]", text)              # link targets
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"(?m)^\s*!fig\s+\S+", " ", t)          # figure file names
    t = re.sub(r"#w-[\w-]+", " ", t)
    t = re.sub(r"(?m)^:::\w+.*$", " ", t)
    t = re.sub(r"(?m)^(page|num|nav):.*$", " ", t)
    t = re.sub(r"(?i)arxiv[:\s]*\d{4}\.\d{4,5}(v\d+)?", " ", t)   # arXiv identifiers
    t = re.sub(r"\b\d{4}\.\d{4,5}(v\d+)?\b", " ", t)
    t = re.sub(r"10\.\d{4,9}/\S+", " ", t)              # DOIs
    return t

L = r"A-Za-zА-Яа-яЁё_"
def numbers(text, lang):
    """Normalized number strings. Thousands separators removed, decimal comma -> point, sign dropped.
    Dates DD.MM.YYYY / DD.MM keep day and year only (month names differ by language)."""
    t = strip_for_numbers(text)
    out = []
    def date_sub(m):
        out.append(str(int(m.group(1))))
        if m.group(3): out.append(m.group(3))
        return " "
    if lang == "ru":
        t = re.sub(r"(?<![\d.§])(\d{2})\.(0[1-9]|1[0-2])\.(\d{4})(?![\d.])", date_sub, t)
        t = re.sub(r"(?<![\d.§])([0-3]\d)\.(0[1-9]|1[0-2])(?![\d.])", lambda m: date_sub(re.match(r"(\d+)\.(\d+)()", m.group(0))) if 1 <= int(m.group(1)) <= 31 else m.group(0), t)
        for m in re.finditer(r"(\d+(?:,\d+)?)\s?(?:тыс\.|тысяч[аи]?)", t): out.append(norm(str(round(float(m.group(1).replace(",", ".")) * 1000))))
    else:  # EN keeps timeline date fields byte-identical (DD.MM.YYYY); only full dates are unambiguous in English text
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s?thousand", t): out.append(norm(str(round(float(m.group(1)) * 1000))))
        t = re.sub(r"(?<![\d.])(\d{1,2})\.(\d{2})[–-](\d{1,2})\.(\d{2})\.(\d{4})(?![\d.])", lambda m: (out.extend([str(int(m.group(1))), str(int(m.group(3))), m.group(5)]), " ")[1], t)
        t = re.sub(r"(?<![\d.])(\d{1,2})\.(\d{2})\.(\d{4})(?![\d.])", date_sub, t)
        t = re.sub(r"(?<![\d.])(\d{1,2})[–-](\d{1,2})\.(\d{2})\.(\d{4})(?![\d.])", lambda m: (out.extend([str(int(m.group(1)))]), date_sub(re.match(r"(\d+)\.(\d+)\.(\d+)", f"{m.group(2)}.{m.group(3)}.{m.group(4)}")))[1], t)
    t = re.sub(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)", lambda m: (out.extend([str(int(m.group(3))), m.group(1)]), " ")[1], t)
    # magnitude suffixes next to a number (272K, 1.5M, 70B) after a space, bracket or sign count as that number
    def suf(m):
        v = m.group(2).replace(",", ".") if lang == "ru" else m.group(2).replace(",", "")
        out.append(norm(v)); return m.group(1)
    t = re.sub(r"(^|[\s(≈~$×])(\d+(?:[.,]\d+)?)\s?[KMB](?![A-Za-zА-Яа-я])", suf, t)
    if lang == "ru":
        pat = re.compile(rf"(?<![{L}\d.,])(\d{{1,3}}(?:[   ]\d{{3}})+|\d+)((?:,\d+)|(?:\.\d+)+)?(?![{L}\d])")
        for m in pat.finditer(t):
            ip = re.sub(r"[   ]", "", m.group(1)); fr = m.group(2) or ""
            fr = "." + fr[1:] if fr.startswith(",") else fr
            out.append(norm(ip + fr))
    else:
        pat = re.compile(rf"(?<![{L}\d.,])(\d{{1,3}}(?:,\d{{3}})+|\d+)((?:\.\d+)+)?(?![{L}\d])")
        for m in pat.finditer(t):
            out.append(norm(m.group(1).replace(",", "") + (m.group(2) or "")))
    return out

def norm(s):
    if s.count(".") == 1:
        a, b = s.split(".")
        return str(int(a)) + "." + b
    if "." in s: return s
    return str(int(s))

def soft(n):
    try: return float(n) <= 12 and float(n) == int(float(n))
    except ValueError: return False

def tables(text):
    """List of row counts per markdown table (header + separator excluded)."""
    res, cur = [], None
    for ln in text.split("\n"):
        if ln.lstrip().startswith("|"):
            if cur is None: cur = 0
            if re.match(r"^\s*\|[\s:|-]+\|\s*$", ln): continue
            cur += 1
        else:
            if cur is not None: res.append(cur - 1); cur = None
    if cur is not None: res.append(cur - 1)
    return res

def summarize(fm, body):
    items, errs = parse(body)
    seq, cards, figs, leads = [], [], [], {}
    for it in items:
        if it[0] == "block":
            _, kind, arg, txt, ln = it
            if kind in ("card", "short"):
                cid = arg.split()[0] if arg else ""
                cards.append(cid); seq.append(f"{kind}:{cid}")
                leads[cid] = bool(re.match(r"\s*lead:\s*\S", txt))
            elif kind in ("callout", "timeline", "takeaways", "findings", "related", "cover", "corpus", "sources", "chart"):
                seq.append(kind)
            figs += FIG.findall(txt)
        else:
            figs += FIG.findall(it[1])
    heads = re.findall(r"(?m)^(#{2,4})\s", body)
    return {"items": items, "errors": errs, "seq": seq, "cards": cards, "figs": figs, "leads": leads,
            "urls": urls(body), "tables": tables(body), "heads": len(heads), "text": body, "fm": fm}

def load_lang(lang, page=None):
    d = os.path.join(CONTENT, lang); out = OrderedDict()
    if not os.path.isdir(d): return out
    for f in sorted(os.listdir(d)):
        if not f.endswith(".md"): continue
        p = f[:-3]
        if page and p != page: continue
        fm, body = read_page(os.path.join(d, f)); out[p] = summarize(fm, body)
    return out

_rp = os.path.join(ROOT, "data", "provenance", "intentional_removals.json")
REMOVALS = json.load(open(_rp, encoding="utf-8")).get("numbers", {}) if os.path.exists(_rp) else {}

def import_source(S):
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import tempfile, subprocess
    tmp = tempfile.mkdtemp(prefix="aas-import-")
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "import_source.py"), S, "--out", tmp], check=True, capture_output=True)
    out = OrderedDict()
    for f in sorted(os.listdir(tmp)):
        fm, body = read_page(os.path.join(tmp, f)); out[f[:-3]] = summarize(fm, body)
    return out

def known_ids():
    p = os.path.join(ROOT, "data", "works.json")
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        ws = d["works"] if isinstance(d, dict) else d
        ids = set()
        for w in ws: ids.add(w["id"]); ids.update(w.get("aliases") or [])
        return ids
    p = os.path.join(ROOT, "data", "canonical_ids.v0.json")
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8")); ids = set()
        for w in d["ids"]: ids.add(w["id"]); ids.update(w.get("aliases") or [])
        return ids
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page"); ap.add_argument("--source"); ap.add_argument("--json")
    ap.add_argument("--no-parity", action="store_true")
    a = ap.parse_args()
    report = OrderedDict(); n_err = 0
    def add(page, level, msg):
        nonlocal n_err
        report.setdefault(page, []).append((level, msg))
        if level == "ERROR": n_err += 1
    ru, en = load_lang("ru", a.page), load_lang("en", a.page)
    ids = known_ids()
    for lang, pages in (("ru", ru), ("en", en)):
        for p, s in pages.items():
            for e in s["errors"]: add(p, "ERROR", f"[{lang}] syntax: {e}")
            if s["fm"].get("page") != p: add(p, "ERROR", f"[{lang}] front matter 'page' must be '{p}'")
            if ids is not None:
                for c in s["cards"]:
                    if c not in ids: add(p, "ERROR", f"[{lang}] unknown work id '{c}'")
            for c, has in s["leads"].items():
                if not has: add(p, "WARN", f"[{lang}] card '{c}' has no lead: line")
            for f in s["figs"]:
                if not (os.path.exists(os.path.join(ROOT, "assets", "figures", f)) or os.path.exists(os.path.join(ROOT, "assets", "charts", f))):
                    add(p, "WARN", f"[{lang}] figure file not in assets yet: {f}")
    if a.source:
        src = import_source(a.source)
        ru_all = load_lang("ru")
        site_nums = Counter(); site_urls = set(); site_figs = set(); site_cards = {}
        for p, s in ru_all.items():
            site_nums.update(numbers(s["text"], "ru")); site_urls.update(s["urls"]); site_figs.update(s["figs"])
            for c in s["cards"]: site_cards[c] = p
        for p, s in src.items():
            if a.page and p != a.page: continue
            new = ru_all.get(p)
            if new is None: add(p, "ERROR", "[ru] page missing"); continue
            for c in s["cards"]:
                if c not in new["cards"]:
                    if c in site_cards: add(p, "INFO", f"[ru] card {c} moved to {site_cards[c]}")
                    else: add(p, "ERROR", f"[ru] card {c} lost")
            for f in s["figs"]:
                if f not in new["figs"]:
                    add(p, "INFO" if f in site_figs else "ERROR", f"[ru] figure {f} " + ("moved" if f in site_figs else "lost"))
            for u in set(s["urls"]):
                if u not in new["urls"]:
                    add(p, "INFO" if u in site_urls else "ERROR", f"[ru] URL {'moved' if u in site_urls else 'lost'}: {u}")
            sn, nn = set(numbers(s["text"], "ru")), set(numbers(new["text"], "ru"))
            allowed = REMOVALS.get(p, {})
            for x in sorted(x for x in sn - nn if x not in site_nums and x in allowed):
                add(p, "INFO", f"[ru] number {x} intentionally removed: {allowed[x]}")
            lost = sorted(x for x in sn - nn if x not in site_nums and x not in allowed)
            moved = sorted(x for x in sn - nn if x in site_nums)
            if lost: add(p, "ERROR", f"[ru] numbers lost from the whole RU site ({len(lost)}): {' '.join(lost)}")
            if moved: add(p, "INFO", f"[ru] numbers no longer on this page but present elsewhere ({len(moved)}): {' '.join(moved[:60])}")
            if sum(s["tables"]) > sum(new["tables"]):
                add(p, "WARN", f"[ru] table rows {sum(s['tables'])} -> {sum(new['tables'])}")
    if not a.no_parity:
        for p, r in ru.items():
            e = en.get(p)
            if e is None: add(p, "ERROR", "[en] page missing"); continue
            if r["fm"].get("num") != e["fm"].get("num"): add(p, "ERROR", "[en] front matter num differs")
            if r["seq"] != e["seq"]:
                add(p, "ERROR", f"[en] block sequence differs: ru={len(r['seq'])} en={len(e['seq'])}; first diff at "
                    + str(next((i for i, (x, y) in enumerate(zip(r['seq'], e['seq'])) if x != y), min(len(r['seq']), len(e['seq'])))))
            if r["figs"] != e["figs"]: add(p, "ERROR", f"[en] figures differ: missing {sorted(set(r['figs'])-set(e['figs']))} extra {sorted(set(e['figs'])-set(r['figs']))} (or order)")
            mu, xu = set(r["urls"]) - set(e["urls"]), set(e["urls"]) - set(r["urls"])
            if mu: add(p, "ERROR", f"[en] URLs missing: {sorted(mu)}")
            if xu: add(p, "WARN", f"[en] URLs extra: {sorted(xu)}")
            if r["tables"] != e["tables"]: add(p, "ERROR", f"[en] tables/rows differ: ru={r['tables']} en={e['tables']}")
            if r["heads"] != e["heads"]: add(p, "WARN", f"[en] heading count ru={r['heads']} en={e['heads']}")
            rn, en_ = set(numbers(r["text"], "ru")), set(numbers(e["text"], "en"))
            miss = sorted(rn - en_, key=lambda x: float(x) if x.replace('.', '', 1).isdigit() else 0)
            hard = [x for x in miss if not soft(x)]; sft = [x for x in miss if soft(x)]
            if hard: add(p, "ERROR", f"[en] numbers in RU but not EN ({len(hard)}): {' '.join(hard)}")
            if sft: add(p, "WARN", f"[en] small integers in RU not written as digits in EN: {' '.join(sft)}")
            extra = sorted(x for x in en_ - rn if not soft(x))
            if extra: add(p, "WARN", f"[en] numbers in EN but not RU ({len(extra)}): {' '.join(extra[:40])}")
            cyr = CYR.findall(e["text"])
            if cyr:
                lines = [i + 1 for i, ln in enumerate(e["text"].split("\n")) if CYR.search(ln)]
                add(p, "ERROR", f"[en] Cyrillic characters: {len(cyr)} on body lines {lines[:15]}")
        for p in en:
            if p not in ru: add(p, "ERROR", "[en] page has no RU counterpart")
    for p, msgs in report.items():
        for lvl, m in msgs:
            print(f"{lvl:5} {p}: {m}")
    print(f"pages ru={len(ru)} en={len(en)}  errors={n_err}")
    if a.json:
        json.dump({p: [{"level": l, "msg": m} for l, m in v] for p, v in report.items()}, open(a.json, "w"), ensure_ascii=False, indent=1)
    sys.exit(1 if n_err else 0)

if __name__ == "__main__":
    main()
