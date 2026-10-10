# Content format

Every page of the site is one Markdown file in `content/ru/` and the same file name in `content/en/`.
The two languages are parallel: the same blocks, cards, figures, tables and links in the same order.
`scripts/build_site.py` renders them; `scripts/check_content.py` checks syntax, RU/EN parity and preservation.

## Files

| File | Page |
|---|---|
| `index.md` | Orientation: cover, key findings, how to read |
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
| `:::card <work-id>` | Full card of a key work. Optional first line `lead: …` (one-sentence takeaway). Body uses run-in labels: RU **Что сделали.** **Что получилось.** **Почему это важно.** **Оговорки.**; EN **What they did.** **Results.** **Why it matters.** **Caveats.** Figures inside with `!fig`. |
| `:::short <work-id>` | Short card: optional `lead: …` line, then one paragraph (or a short list). |
| `:::callout <Title>` | Boxed explanation (how to read numbers, definitions). |
| `:::timeline` | One event per line: `DD.MM.YYYY | text`. The date field is kept byte-identical in RU and EN; the builder formats it per language. |
| `:::takeaways` | Chapter summary (≤ 5 bullets). Replaces the old «Главное в главе» heading. |
| `:::findings` | Key findings on the index page. |
| `:::related` | Wraps one Markdown table «Ещё по теме» / "Related work" (columns: work, who/when, one line). Rendered as a list on phones. |
| `:::cover` | Index page only: `kicker:`, `title:`, `subtitle:`, `lede:`, `meta:` lines. |
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
