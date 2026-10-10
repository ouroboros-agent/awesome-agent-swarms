#!/usr/bin/env python3
"""Build data/figures.json: one record per figure used in the text, with source work and rights.
Rights come from the October figure catalogue (<S>/figcat/group_*.json) and the credit line printed under
each figure; nothing is inferred beyond those. Usage: python scripts/build_figures_registry.py <S>"""
import json, os, re, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = sys.argv[1] if len(sys.argv) > 1 else "research-archive"
cat = {}
for p in sorted(glob.glob(os.path.join(S, "figcat", "group_*.json"))):
    for r in json.load(open(p, encoding="utf-8")): cat.setdefault(r["file"], r)
def rights(lic, credit):
    t = (lic or "") + " " + (credit or "")
    if re.search(r"CC BY-NC-ND", t): return "cc-by-nc-nd-4.0"
    if re.search(r"CC0", t) and "расчёт обзора" in (credit or ""): return "own-chart-cc0-data"
    if re.search(r"\bCC BY 4\.0\b|CC BY\b", t) and not re.search(r"not CC|не CC", t): return "cc-by-4.0"
    if re.search(r"non-?exclusive", t, re.I): return "arxiv-nonexclusive"
    if re.search(r"©|\(c\)|copyright", t, re.I): return "all-rights-reserved"
    return "unknown"
figs = []
src = os.path.join(ROOT, "content", "ru")
for f in sorted(os.listdir(src)):
    if not f.endswith(".md"): continue
    for ln in open(os.path.join(src, f), encoding="utf-8"):
        m = re.match(r"\s*!fig\s+(\S+)\s*\|(.*?)\|(.*)$", ln.rstrip("\n"))
        if not m: continue
        file, cap, credit = m.group(1), m.group(2).strip(), m.group(3).strip()
        base = file.replace("_hires", "")
        r = cat.get(file) or cat.get(base) or {}
        own = file.startswith("dash_") or file == "anthropic-c-compiler_fig2.png"
        figs.append({"file": file, "page": f[:-3], "kind": "own_chart" if own else "third_party",
                     "work_id": None if file.startswith("dash_") else (r.get("card_id") or re.sub(r"_fig\d+.*$", "", file)),
                     "source_label": r.get("label"),
                     "rights": "own-cc-by-4.0" if file.startswith("dash_") else ("own-chart-cc0-data" if own else rights(r.get("license"), credit)),
                     "license_note_october": r.get("license"), "credit_ru": credit,
                     "shows_en": r.get("shows")})
json.dump({"note": "Rights as recorded in the October figure catalogue and credit lines. Third-party figures are NOT covered by the survey's CC BY 4.0 licence; 'all-rights-reserved' and 'arxiv-nonexclusive' figures are reproduced as attributed quotations in this private candidate and need a rights decision before any public release.",
           "figures": figs}, open(os.path.join(ROOT, "data", "figures.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
print(len(figs), Counter(x["rights"] for x in figs))
