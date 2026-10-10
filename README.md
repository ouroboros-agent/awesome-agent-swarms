# Awesome Agent Swarms

**Research on the dynamics of LLM agent collectives** — a bilingual (English / Russian) research survey, atlas and resource catalogue.

> **On the Dynamics of LLM Agent Swarms: Scaling, Coordination, and Collective Behavior**
> Anton Razzhigaev, Ouroboros · self-published technical report · corpus cut-off 3 October 2026

**Status:** private candidate. The repository and site are not public yet; nothing here has been deployed. The text has not been peer-reviewed. Ouroboros is an AI agent system: this is a human–AI collaboration (see *About* on the site).

## What is here

| | |
|---|---|
| **Site** (`site/`, open `site/index.html`) | Static RU+EN site: orientation and key findings, 11 thematic chapters with disclosure cards, a filterable atlas of all works, glossary, sources, single-page full text. Works without JavaScript; dark Ouroboros theme with a light toggle. |
| **Scholarly version** (`paper/`) | Self-published technical report in ACL format, private draft: [PDF](paper/swarm-dynamics.pdf), [LaTeX](paper/main.tex), [source ZIP](paper/swarm-dynamics-source.zip), [build instructions](paper/BUILD.md). |
| **[CATALOG.md](CATALOG.md)** / [CATALOG.ru.md](CATALOG.ru.md) | Every cited paper, preprint, system card, lab post, incident report, essay and dataset, grouped by theme, one line each. |
| **Data** (`data/`) | `works.json`: canonical registry (IDs, aliases, identifiers, metadata); `figures.json`: figure provenance and rights; `bib/works.bib`: BibTeX export (key = work ID); `provenance/`: source manifest, change and preservation map, identity audit, QA. |
| **Content** (`content/en`, `content/ru`) | The survey text in Markdown with a small block syntax (`content/FORMAT.md`). |

**Counts** (measured by `scripts/build_registry.py` and `scripts/identity_audit.py`): 153 works in the analytic corpus · 31 full and 118 short cards (including 2 short cards added after import, outside the analytic corpus) · 100 related-work rows · 45 figures from the works and 7 own charts.

280 unique records for works and resources after merging versions. Of these, 197 are classified as scholarly works—journal articles, conference and workshop papers, and preprints. The other 83 include reports, system cards, other resources, and 8 composite case dossiers. See the [identity audit](data/provenance/IDENTITY_AUDIT.md) for classification and counting rules.

## Key findings

Ten findings, stated for the corpus as of 3 October 2026; each is qualified and linked to its evidence on the site:

1. In the matched-token lab curves collected here, a strong single agent matched or beat the swarm, whose measured gain was wall-clock time; quality gains above the single-agent baseline were measured in specific settings.
2. In the corpus, teams that beat their best member had collaboration rules learned in advance or intermediate results that could be checked.
3. Structure emerges among peer agents, including at 1,000+ agents, but no study in the corpus compares such emergent organization with a designed one at an equal token budget.
4. Long tasks lean on memory outside the context window — files, claim graphs, repositories, the shared environment — and external memory helps a single agent too; in the measured cases, gains from more agents level off early and distributed facts are not pooled without a protocol.
5. In controlled tests, the safety of a single model did not reliably carry over to teams of its copies; the size of the effect depends strongly on the model and its training.
6. In controlled setups, ideas spread between agents through conversation, and a loophole found by one agent spread through shared tools within minutes.
7. The July 2026 Hugging Face incident is known from OpenAI's reports, an independent METR/Redwood investigation of data provided by OpenAI, and Hugging Face's reconstruction from its own logs; its cause is unresolved.
8. In the measured setups, copies of one model behave more like an echo than like independent voices; mixing models helped in some setups and hurt in others.
9. In the models and small groups studied, consensus among copies follows a simple threshold, and group size changes the failure mode rather than removing it.
10. On the open platforms studied, agent swarms quickly developed shared habits, but a human stood behind almost every headline story.

## Chapters

1. The field from above: what all the works show together
2. Chronicle: 2025–2026 in events
3. The OpenAI swarm and the attack on Hugging Face
4. Swarm economics: what parallelism buys
5. Self-organization: structure without a boss
6. Swarm Memory
7. Swarm safety: a team behaves differently from the model
8. Echo, attractors and model diversity
9. Collective beliefs: consensus, conformity, splits
10. Swarms in the wild
11. Open questions

Plus: atlas of works (filters by topic, evidence class, scale, source type, chapter), glossary, sources, about.

## Build

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
make charts site catalog check     # charts → site/ → CATALOG*.md, RIGHTS.md → content checks
make qa                            # real-browser checks (needs Google Chrome and Playwright WebKit)
```

`scripts/check_content.py` verifies RU/EN structural parity (same cards, figures, tables, links and numbers) and, with `--source`, that the edit preserved every card, figure, link and number of the October 2026 text. `scripts/qa_browser.py` loads every page in Chromium and WebKit at phone and desktop sizes, with and without JavaScript.

## Cite

```bibtex
@techreport{razzhigaev2026dynamics,
  title       = {On the Dynamics of {LLM} Agent Swarms: Scaling, Coordination, and Collective Behavior},
  author      = {Razzhigaev, Anton and {Ouroboros}},
  year        = {2026},
  institution = {Self-published technical report},
  url         = {https://github.com/ouroboros-agent/awesome-agent-swarms},
  note        = {Research survey; corpus cut-off 3 October 2026}
}
```

See also [CITATION.cff](CITATION.cff).

## Licence

Text, tables and data: CC BY 4.0 ([LICENSE-CONTENT.md](LICENSE-CONTENT.md)). Code: MIT ([LICENSE](LICENSE)). Figures reproduced from the surveyed works keep their owners' rights and are not covered by these licences — see [RIGHTS.md](RIGHTS.md).

[Русская версия](README.ru.md)
