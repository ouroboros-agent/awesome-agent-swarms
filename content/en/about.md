---
page: about
title: About: authors, method, rights, citation
nav: About
lead: Who made the survey, how the corpus was assembled, what the labels mean and how to cite it.
---

## Authors

**Anton Razzhigaev and Ouroboros.** Ouroboros is an AI agent system. It collected and read the sources, wrote the cards, ran the checks and prepared the text; Anton Razzhigaev set the scope of the survey, made the editorial decisions and is responsible for the publication. This is a human–AI collaboration, and we say so plainly.

Status: a private draft technical report and research survey prepared for self-publication. It is not yet public, has not been peer-reviewed, is not an ACL publication and has not been submitted to arXiv.

## How the corpus was assembled

- **Cut-off:** 3 October 2026. Later preprint versions, reviews and prize decisions are not reflected in the text; known changes after the cut-off are listed below.
- **Analytic corpus:** {{stat:corpus}} works with metadata (date, organizations, models, scale, evidence class, topics); the Chapter 1 charts and the atlas filters are built from it.
- **Cards:** {{stat:cards_full}} full and {{stat:cards_short}} short; plus {{stat:related_rows}} rows in the related-work tables and the comparison with physical swarms. In total, {{stat:unique_works}} unique works and resources are linked, after merging versions of the same work (arXiv, journal, publisher page).
- **Selection:** targeted, not a systematic review following a pre-specified protocol. The corpus deliberately favours 2026; works from 2025 are included where recent work builds on them.
- **Sources:** peer-reviewed papers, preprints, model system cards, lab engineering blogs, incident investigations, essays and interviews. Every card carries its evidence class (table in Chapter 1).
- **Numbers:** every number is tied to a source. "Our estimate" marks the review's own calculation from published charts or data, not a number reported by the authors. The cards were checked against the primary sources in several review rounds in October 2026.

## Changes after the cut-off

- 8 October 2026: Piao et al., "Emergence of polarization in networks of large language model agents" (preprint [arXiv:2501.05171](https://arxiv.org/abs/2501.05171)), was published in [Nature Communications](https://www.nature.com/articles/s41467-026-78228-y) (received 14 April 2025, accepted 21 September 2026; CC BY 4.0). It is the same work and is counted once among the unique works.

## Rights

- **Survey text and tables:** CC BY 4.0. **Build code:** MIT.
- **The survey's own charts** (Chapter 1 and the C-compiler repository history): CC BY 4.0.
- **Figures from the works** remain under their owners' rights; the licence or the note "quoted for review" is given under each figure and in RIGHTS.md. The survey's licence does not cover them.

## How to cite

[Paper and citation page](../paper/index.html). Scholarly version in ACL format: [download PDF](../paper/swarm-dynamics.pdf) · [LaTeX sources and figures (ZIP)](../paper/swarm-dynamics-source.zip). This is a private draft prepared for self-publication.

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
