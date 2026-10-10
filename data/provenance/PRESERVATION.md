# Change and preservation map

October 2026 Russian text (imported verbatim by `scripts/import_source.py` from the read-only source tree, SHA-256 in `data/provenance/source_manifest.json`) → edited Russian (`content/ru/`) → English (`content/en/`).
Counts are measured by `scripts/preservation_map.py`; triples are *source / RU / EN*. “Numbers” are distinct numeric values after format normalization (`scripts/check_content.py`). Lead words are the one-line card summaries added by the edit.

| Page | Words src → RU (of which leads) · EN | Cards | Figures | Table rows | URLs | Numbers: src · kept on page · moved · lost | RU numbers missing in EN | Added cards |
|---|---|---|---|---|---|---|---|---|
| about | 0 → 410 (0) · 456 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 4 / 4 | 0 · 0 · 0 · 0  | 0 | — |
| atlas | 77 → 67 (0) · 82 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 2 · 1 · 1 · 0  | 0 | — |
| ch01 | 2091 → 2042 (0) · 2440 | 0 / 0 / 0 | 6 / 6 / 6 | 11 / 23 / 23 | 0 / 0 / 0 | 80 · 80 · 0 · 0  | 0 | — |
| ch02 | 2529 → 2495 (30) · 2975 | 1 / 1 / 1 | 1 / 1 / 1 | 0 / 0 / 0 | 66 / 67 / 67 | 91 · 91 · 0 · 0  | 0 | — |
| ch03 | 3305 → 3580 (443) · 4382 | 15 / 15 / 15 | 3 / 3 / 3 | 3 / 3 / 3 | 4 / 4 / 4 | 79 · 79 · 0 · 0  | 0 | — |
| ch04 | 7536 → 7824 (634) · 9141 | 24 / 24 / 24 | 9 / 9 / 9 | 14 / 24 / 24 | 21 / 21 / 21 | 287 · 287 · 0 · 0  | 0 | — |
| ch05 | 6328 → 6248 (358) · 7439 | 16 / 16 / 16 | 10 / 10 / 10 | 27 / 27 / 27 | 30 / 30 / 30 | 234 · 233 · 1 · 0  | 0 | — |
| ch06 | 4470 → 4554 (439) · 5370 | 15 / 15 / 15 | 3 / 3 / 3 | 13 / 13 / 13 | 13 / 13 / 13 | 224 · 221 · 3 · 0  | 0 | — |
| ch07 | 5835 → 6631 (867) · 8048 | 30 / 30 / 30 | 6 / 6 / 6 | 15 / 15 / 15 | 17 / 17 / 17 | 172 · 171 · 1 · 0  | 0 | — |
| ch08 | 5840 → 6007 (558) · 7117 | 20 / 20 / 20 | 9 / 9 / 9 | 10 / 10 / 10 | 12 / 12 / 12 | 222 · 222 · 0 · 0  | 0 | — |
| ch09 | 4286 → 4973 (444) · 5910 | 14 / 16 / 16 | 3 / 3 / 3 | 19 / 19 / 19 | 19 / 20 / 20 | 154 · 154 · 0 · 0  | 0 | coherence-driven-contagion, rheon-consensus |
| ch10 | 3981 → 3973 (300) · 4717 | 12 / 12 / 12 | 2 / 2 / 2 | 17 / 17 / 17 | 19 / 19 / 19 | 181 · 181 · 0 · 0  | 0 | — |
| ch11 | 799 → 846 (0) · 1034 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 46 · 46 · 0 · 0  | 0 | — |
| glossary | 422 → 470 (0) · 578 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 6 · 6 · 0 · 0  | 0 | — |
| index | 1361 → 1037 (0) · 1151 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 101 · 60 · 40 · 1 247 | 0 | — |
| sources | 0 → 0 (0) · 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 · 0 · 0 · 0  | 0 | — |

**Totals:** cards 147 / 149 / 149 · figures 52 / 52 / 52 · table rows 129 / 151 / 151 · words 48860 → 51157 RU (4073 in new leads) · 60840 EN.

Lost numbers are allowed only when listed with a reason in `data/provenance/intentional_removals.json` (currently: the October cover count “247 работ”, which was a sum of cards and table rows, not unique works).
Per-page editorial change logs (what was cut, where each fact now lives, flagged concerns): `data/provenance/editorial/<page>.md`.
