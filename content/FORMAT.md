# Content format

The site is one continuous page per language, `site/ru/index.html` and `site/en/index.html`. Its text comes from one
Markdown file per former page in `content/ru/` and the same file name in `content/en/`. The two languages are parallel:
the same blocks, cards, figures, tables and links in the same order. `scripts/build_site.py` renders them in the order set by
`scripts/longread.py`; `scripts/check_content.py` checks syntax, RU/EN parity and preservation; `scripts/check_coverage.py`
checks that every card, figure, link, heading and block of the sources (and of a former multipage build, with `--old`) is on the
single page. The prologue's topology scene and the Agensh scene come from `scripts/site_story.py`; the other native scenes from
`scripts/scenes.py` and `scripts/scenes_mech.py`, not from these files.

## Files

| File | Page |
|---|---|
| `index.md` | Cover (the intro under the prologue), the ten findings (set in the epilogue), the note on cards and labels (reference appendix) |
| `ch01.md` … `ch11.md` | Chapters 1–11 (1 field overview, 2 chronicle, 3–10 themes, 11 open questions) |
| `atlas.md` | Chapter 12: atlas of all works (table is generated) |
| `glossary.md` | Glossary |
| `sources.md` | Generated list of sources |
| `about.md` | Authorship, method, rights, how to cite |

## Front matter

```
---
page: ch04
num: 4
title: Экономика роя: что покупает параллельность
nav: Экономика роя
lead: Одна-две фразы о вопросе главы (для карты глав и шапки страницы).
---
```

`page` and `num` are identical in both languages. `nav` is a short title for menus (≤ 4 words).

## Blocks

A block opens with `:::kind args` on its own line and closes with `:::` on its own line. Blocks do not nest.

| Block | Meaning |
|---|---|
| `:::card <work-id>` | Full card of a key work. Optional first line `lead: …` (one-sentence takeaway). The body is ordinary Markdown: connected paragraphs, lists or a table, in whatever order the work needs; no fixed headings or labels are required. A paragraph may still open with a bold run-in label (`**Caveats.**`), which is set as a label. Figures inside with `!fig`. |
| `:::short <work-id>` | Short card: optional `lead: …` line, then one paragraph (or a short list). |
| `:::callout <Title>` | Boxed explanation (how to read numbers, definitions). |
| `:::timeline` | One event per line: `DD.MM.YYYY | text`. The date field is kept byte-identical in RU and EN; the builder formats it per language. |
| `:::takeaways` | Chapter summary (≤ 5 bullets). Replaces the old «Главное в главе» heading. |
| `:::findings` | The ten findings, set in the epilogue before Chapter 11: a numbered list. If an item opens with a bold sentence, the site sets it as the item's headline; items without one render as plain paragraphs. |
| `:::related` | Wraps one Markdown table «Ещё по теме» / "Related work" (columns: work, who/when, one line). Rendered as a list on all viewports. |
| `:::cover` | `index.md` only: `kicker:`, `title:`, `subtitle:`, `lede:`, `meta:` lines. On the site it becomes the intro under the topology scene, followed by the route through the parts; large counts are read from `data/stats.json`; parts of `meta` separated by ` · ` that contain `{{stat:…}}` are omitted to avoid repeating those counts. |
| `:::corpus`, `:::sources` | Placeholders filled by the builder. |

`<work-id>` is the canonical ID from `data/works.json` (see `data/interface.md`). Never invent or rename IDs.

## Figures

`!fig <file> | caption | credit` on its own line (inside or outside a card). `<file>` is a file name in `assets/figures/` (or `assets/charts/` for the review's own charts, names starting with `dash_`). Captions and credits are translated; file names are not.

## Links

- External links are ordinary Markdown links; URLs are byte-identical in RU and EN.
- Link to a card anywhere on the site: `[text](#w-<work-id>)`; the builder points it to the right page.
- Chapter references such as `гл. 4`, `глава 5` / `Ch. 4`, `Chapter 5` are linked automatically.

## Tables

Ordinary Markdown pipe tables. The builder wraps every table in a horizontally scrollable box with a scroll hint; keep the first column short.

## The single page

Order (scripts/longread.py): prologue (topology scene) → intro and route → Part I (chapters 1–3) → Part II (4–6) →
Part III (7–10) → epilogue (the ten findings, chapter 11, the atlas as chapter 12) → reference appendix (glossary, cards
and labels, sources, about). Each part opens with a short statement; each chapter opens with a plate (number, title, the
lead's question and answer, counts) that pins while the chapter's sheet slides over it. Chapter Markdown headings become
`h3`/`h4` under the chapter's `h2`. The section "How to read the cards" of `ch01.md` and the index's note on labels move to
the appendix ("Cards and labels") with their ids, so the reading flow carries no reading instructions.

Native scenes sit at hooks in `PLACE` (scripts/longread.py): `fig:<file>` replaces one of the survey's own charts and keeps its
number and caption (the static PNG stays linked under it); `after:<card>`, `before:<card>`, `callout:<k>`, `table:<k>` place a
scene by a card, a callout or a table. Every scene's markup is its end state, so the page reads the same without JavaScript or with
reduced motion. A scene marked *Survey data* computes its numbers from `data/works.json`; *Card data* and *Schematic* scenes
quote only numbers from the card next to them, and the motion between them is illustrative. Where a schematic computes numbers of
its own (the λ rule, the consensus toy model), the scene says it is a calculation or a toy, not a measurement.
`scripts/check_scenes.py` (part of `make check`) checks every quoted number against its card and recomputes the toy model.

## Addresses

Ids on the single page are unique and stable:

| Former address | On the single page |
|---|---|
| `chNN.html`, `glossary.html`, `about.html` | `index.html#chNN`, `#glossary`, `#about` |
| `atlas.html`, `sources.html` | `#atlas`, `#sources` |
| `chNN.html#s-K` (section headings, card titles) | `#chNN-s-K` (the same counter) |
| `chNN.html#fig-K`, `#zoom-K` | `#chNN-fig-K` |
| `#w-<work>`, `#a-<work>`, `#src-<page>`, `#s-<work>` | unchanged |
| `full.html#p-chNN`, `#chNN-s-K`, `#fig-N` | `#chNN`, unchanged, the figure's new id |
| `index.html#how`, `#survey`, `#scale`, `#findings`, `#agensh`, `#chapters`, `#howto`, `#s-1` | kept on the single page |

The former pages remain as small files: with JavaScript they forward the fragment to its new place at once; without it
they list their sections, cards and figures as links, and the addressed one is highlighted (`:target`).
