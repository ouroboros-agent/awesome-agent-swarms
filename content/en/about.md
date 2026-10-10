---
page: about
title: About: authors, method, rights, citation
nav: About
lead: Who assembled the survey, how the corpus was chosen, what the marks on the numbers mean, and how to cite the work.
---

## Authors

**Anton Razzhigaev and Ouroboros.** Ouroboros is an AI agent system. It collected and read the sources, wrote the cards, checked the numbers and prepared the text. Anton Razzhigaev set the scope, made the editorial decisions and is responsible for publication. This is a collaboration between a person and an agent system, and the authorship says so directly.

## How the corpus was assembled

- **Cut-off:** 3 October 2026. Later preprint versions, reviews and prize decisions are not in the text; known changes after the cut-off are listed below.
- **Analytic corpus:** {{stat:corpus}} works with metadata (date, organizations, models, scale, evidence class, topics). The Chapter 1 charts and the atlas filters are built from it.
- **Cards:** {{stat:cards_full}} full and {{stat:cards_short}} short; plus {{stat:related_rows}} rows in the related-work tables and the comparison with physical swarms. In total, {{stat:unique_works}} unique works and resources are linked, after merging versions of the same work (arXiv, journal, publisher page).
- **Selection:** targeted, not a systematic review under a pre-specified protocol. The corpus deliberately favours 2026; works from 2025 are included where recent work builds on them.
- **Sources:** peer-reviewed papers, preprints, model system cards, lab engineering blogs, incident investigations, essays and interviews. Every card carries its evidence class (table in Chapter 1).
- **Numbers:** every number is tied to a source. "Our estimate" marks a calculation from published charts or data, not a number reported by the authors of the work. The cards were checked against the primary sources in October 2026.

## Changes after the cut-off

- 8 October 2026: Piao et al., "Emergence of polarization in networks of large language model agents" (preprint [arXiv:2501.05171](https://arxiv.org/abs/2501.05171)), was published in [Nature Communications](https://www.nature.com/articles/s41467-026-78228-y) (received 14 April 2025, accepted 21 September 2026; CC BY 4.0). It is the same work and is counted once among the unique works.

## Rights

- **Survey text and tables:** CC BY 4.0. **Build code:** MIT.
- **The survey's own charts** (Chapter 1 and the C-compiler repository history): CC BY 4.0.
- **Figures from the works** remain under their owners' rights; the licence or the note "quoted for review" is given under each figure and in RIGHTS.md. The survey's licence does not cover them.

## How to cite

The article-format version and the citation files: [paper page](../paper/index.html), [PDF](../paper/swarm-dynamics.pdf), [LaTeX sources and figures (ZIP)](../paper/swarm-dynamics-source.zip).

Anton Razzhigaev, Ouroboros. *On the Dynamics of LLM Agent Swarms: Scaling, Coordination, and Collective Behavior.* Technical report, cut-off 3 October 2026.

```
@techreport{razzhigaev2026dynamics,
  title       = {On the Dynamics of {LLM} Agent Swarms: Scaling, Coordination, and Collective Behavior},
  author      = {Razzhigaev, Anton and {Ouroboros}},
  year        = {2026},
  institution = {Self-published technical report},
  url         = {https://github.com/ouroboros-agent/awesome-agent-swarms},
  note        = {Research survey; corpus cut-off 3 October 2026}
}
```

The repository [github.com/ouroboros-agent/awesome-agent-swarms](https://github.com/ouroboros-agent/awesome-agent-swarms) is private for now.
