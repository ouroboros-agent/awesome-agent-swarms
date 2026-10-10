#!/usr/bin/env python3
"""Write data/provenance/preservation_map.json and PRESERVATION.md: per page, what the October text had
and what the edited RU and the EN translation have (words, cards, figures, table rows, URLs, distinct numbers).
  python scripts/preservation_map.py <S>"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import check_content as C
S = sys.argv[1] if len(sys.argv) > 1 else "research-archive"
src = C.import_source(S); ru = C.load_lang("ru"); en = C.load_lang("en")
def words(t): return len(re.findall(r"[\wА-Яа-яЁё][\w\-’'А-Яа-яЁё]*", re.sub(r"\]\([^)]*\)|https?://\S+|!fig\s+\S+|^:::.*$", " ", t, flags=re.M)))
def lead_words(t): return sum(len(l.split()) - 1 for l in re.findall(r"(?m)^lead:.*$", t))
rows = []; site_nums = set(); [site_nums.update(C.numbers(s["text"], "ru")) for s in ru.values()]
for p in list(ru.keys()):
    s0 = src.get(p); r = ru[p]; e = en.get(p)
    n0 = set(C.numbers(s0["text"], "ru")) if s0 else set(); nr = set(C.numbers(r["text"], "ru")); ne = set(C.numbers(e["text"], "en")) if e else set()
    rows.append(dict(page=p, title=r["fm"].get("title"),
        src_words=words(s0["text"]) if s0 else 0, ru_words=words(r["text"]), ru_lead_words=lead_words(r["text"]), en_words=words(e["text"]) if e else 0,
        cards=[len(s0["cards"]) if s0 else 0, len(r["cards"]), len(e["cards"]) if e else 0],
        figures=[len(s0["figs"]) if s0 else 0, len(r["figs"]), len(e["figs"]) if e else 0],
        table_rows=[sum(s0["tables"]) if s0 else 0, sum(r["tables"]), sum(e["tables"]) if e else 0],
        urls=[len(set(s0["urls"])) if s0 else 0, len(set(r["urls"])), len(set(e["urls"])) if e else 0],
        numbers_src=len(n0), numbers_kept_on_page=len(n0 & nr), numbers_moved_elsewhere=len((n0 - nr) & site_nums), numbers_lost=sorted(n0 - nr - site_nums),
        numbers_ru_missing_in_en=sorted(x for x in nr - ne if not C.soft(x)),
        cards_added=sorted(set(r["cards"]) - set(s0["cards"] if s0 else [])), changelog=f"data/provenance/editorial/{p}.md" if os.path.exists(os.path.join(ROOT, "data/provenance/editorial", p + ".md")) else None))
json.dump(rows, open(os.path.join(ROOT, "data/provenance/preservation_map.json"), "w"), ensure_ascii=False, indent=1)
T = lambda a: " / ".join(str(x) for x in a)
md = ["# Change and preservation map", "",
      "October 2026 Russian text (imported verbatim by `scripts/import_source.py` from the read-only source tree, SHA-256 in `data/provenance/source_manifest.json`) → edited Russian (`content/ru/`) → English (`content/en/`).",
      "Counts are measured by `scripts/preservation_map.py`; triples are *source / RU / EN*. “Numbers” are distinct numeric values after format normalization (`scripts/check_content.py`). Lead words are the one-line card summaries added by the edit.", "",
      "| Page | Words src → RU (of which leads) · EN | Cards | Figures | Table rows | URLs | Numbers: src · kept on page · moved · lost | RU numbers missing in EN | Added cards |", "|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    md.append(f"| {r['page']} | {r['src_words']} → {r['ru_words']} ({r['ru_lead_words']}) · {r['en_words']} | {T(r['cards'])} | {T(r['figures'])} | {T(r['table_rows'])} | {T(r['urls'])} | {r['numbers_src']} · {r['numbers_kept_on_page']} · {r['numbers_moved_elsewhere']} · {len(r['numbers_lost'])} {' '.join(r['numbers_lost'])} | {len(r['numbers_ru_missing_in_en'])} | {', '.join(r['cards_added']) or '—'} |")
tot = lambda k, i: sum(r[k][i] for r in rows)
md += ["", f"**Totals:** cards {tot('cards',0)} / {tot('cards',1)} / {tot('cards',2)} · figures {tot('figures',0)} / {tot('figures',1)} / {tot('figures',2)} · table rows {tot('table_rows',0)} / {tot('table_rows',1)} / {tot('table_rows',2)} · words {sum(r['src_words'] for r in rows)} → {sum(r['ru_words'] for r in rows)} RU ({sum(r['ru_lead_words'] for r in rows)} in new leads) · {sum(r['en_words'] for r in rows)} EN.", "",
       "Lost numbers are allowed only when listed with a reason in `data/provenance/intentional_removals.json` (currently: the October cover count “247 работ”, which was a sum of cards and table rows, not unique works).",
       "Per-page editorial change logs (what was cut, where each fact now lives, flagged concerns): `data/provenance/editorial/<page>.md`.", ""]
open(os.path.join(ROOT, "data/provenance/PRESERVATION.md"), "w").write("\n".join(md))
print("\n".join(md[6:]))
