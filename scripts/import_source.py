#!/usr/bin/env python3
"""One-time, reproducible import of the October 2026 Russian corpus text into content/ru/.

Reads (never writes) the sprint source tree:
  <S>/build/front.md, <S>/build/chapters/*.md, <S>/build/back.md
and splits it into one Markdown file per page with a small front-matter header.
Usage: python scripts/import_source.py /path/to/swarm-dynamics-20261003 [--out content/ru-import]
The edited text in content/ru/ started from this import (checkpoint 1); re-running the
import does not overwrite content/ru/ unless --out content/ru is given explicitly.
"""
import argparse, os, re, sys

ap = argparse.ArgumentParser()
ap.add_argument("source")
ap.add_argument("--out", default="content/ru-import")
a = ap.parse_args()
B = os.path.join(a.source, "build")
front = open(os.path.join(B, "front.md"), encoding="utf-8").read()
back = open(os.path.join(B, "back.md"), encoding="utf-8").read()
chap = {}
for f in ("w1_t5_t1", "w2_t3_wild", "w3_t2_incident", "w4_t4_beliefs"):
    t = open(os.path.join(B, "chapters", f + ".md"), encoding="utf-8").read()
    for p in re.split(r"(?m)^(?=# \d+ \|)", t):
        m = re.match(r"# (\d+) \|\s*(.+)", p)
        if m: chap[int(m.group(1))] = p
def parts(text):
    out = {}
    for p in re.split(r"(?m)^(?=# \d+ \|)", text):
        m = re.match(r"# (\d+) \|\s*(.+)", p)
        out[int(m.group(1)) if m else 0] = p
    return out
fp, bp = parts(front), parts(back)
chap.update({k: v for k, v in fp.items() if k}); chap.update({k: v for k, v in bp.items() if k})
os.makedirs(a.out, exist_ok=True)
def write(name, meta, body):
    hdr = "---\n" + "".join(f"{k}: {v}\n" for k, v in meta.items()) + "---\n\n"
    open(os.path.join(a.out, name), "w", encoding="utf-8").write(hdr + body.strip() + "\n")
# index: cover + key findings
idx = fp[0].replace(":::toc\n:::\n", "")
write("index.md", {"page": "index", "title": "Динамика роёв ИИ-агентов"}, idx)
for n in range(1, 12):
    p = chap[n]
    m = re.match(r"# (\d+) \|\s*(.+)\n", p)
    body = p[m.end():]
    write(f"ch{n:02d}.md", {"page": f"ch{n:02d}", "num": n, "title": m.group(2).strip()}, body)
# chapter 12: corpus table intro + glossary + sources
p12 = chap[12]; m = re.match(r"# 12 \|\s*(.+)\n", p12); body = p12[m.end():]
atlas, _, rest = body.partition("## Словарик")
gloss, _, src = rest.partition(":::sources")
write("atlas.md", {"page": "atlas", "num": 12, "title": m.group(1).strip()}, atlas)
write("glossary.md", {"page": "glossary", "title": "Словарик"}, gloss)
write("sources.md", {"page": "sources", "title": "Источники"}, ":::sources\n:::\n")
print("wrote", sorted(os.listdir(a.out)))
