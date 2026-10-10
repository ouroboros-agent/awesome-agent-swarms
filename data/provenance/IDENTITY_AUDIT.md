# Canonical identity audit

Registry: `data/works.json` (280 records), built by `scripts/build_registry.py` from the read-only October tree plus `data/registry_overrides.json`. Machine-readable version: `data/provenance/identity_audit.json`.

## What the counts mean

- **280 unique works and resources** = every distinct thing the survey links to, after merging versions of the same item. It is **not** a count of papers.
- **197 records classified as scholarly works** (journal, conference, workshop, preprint). Other records: lab / company / incident report or engineering post: 45, case dossier grouping several documents: 8, model system card: 8, essay, blog post, interview, forum post: 16, dataset, benchmark site or platform: 2, event page / other web page: 1, news article / press release: 3.
- **153** of the records form the analytic corpus behind the Chapter 1 charts and atlas filters (October 2026 curation, unchanged).
- Record class comes from the October corpus metadata where it exists; otherwise from the URL (arXiv/DOI → paper, company domains → report, etc.) or from a hand-curated override. Heuristic classes are flagged below as uncertain.

| Class | Records |
|---|---|
| Scholarly work (journal, conference, workshop, preprint) | 197 |
| Model system card | 8 |
| Lab / company / incident report or engineering post | 45 |
| Essay, blog post, interview, forum post | 16 |
| News article / press release | 3 |
| Dataset, benchmark site or platform | 2 |
| Event page / other web page | 1 |
| Case dossier grouping several documents (not itself a publication) | 8 |

## Merge rules (applied in this order)

1. **Card identity.** Every October card keeps its card ID. Its identity keys: the normalized primary URL; pdf/html URLs only when they normalize to the same key (arXiv ID or DOI); URLs in `urls.other` only when labelled as the arXiv/preprint/journal version; arXiv IDs or DOIs written in the card's own version/venue fields.
2. **Normalization.** arXiv abs/pdf/html and vN → `arxiv:<id>`; `doi.org`, `nature.com/articles/…`, `science.org/doi/…`, `pnas.org/doi/…` → `doi:<doi>`; ACL Anthology → `acl:<id>`; anything else → host + path without scheme, `www`, query or fragment.
3. **Synonyms.** Five October alias IDs that named the same card are kept as `aliases`.
4. **Constituents.** Seven October alias IDs that named a specific document inside a bundle card become their own records with `part_of` (they claim their URL keys from the bundle).
5. **Text URLs.** Every URL in the October text is mapped to the record holding its key; unmatched URLs become new records with deterministic IDs.
6. **Conflicts.** If a second record would claim a key already held, the key is not moved; it stays on the first record and is listed on the second as `related_keys` (kept separate, not merged).
7. **Hand-curated records** (`registry_overrides.json`) carry their verification source; identifiers there were read from the arXiv API or the publisher page on 2026-10-09. No identifier was constructed or guessed.

## Records with more than one identity key or text URL (16)

| Record | Class | Merged keys | Basis per key |
|---|---|---|---|
| `opus5-card-multiagent` | system_card | `web:www-cdn.anthropic.com/b514064af1408018e64b1ad24e7d5e75850b4ffd/claude%20opus%205%20system%20card.pdf`<br>`web:www-cdn.anthropic.com/ceaf5c7ff2783855203fde8208ec311252dced5b/claude%20opus%205%20system%20card.pdf` | card JSON primary URL<br>card JSON urls.pdf (same work variant) |
| `kim-scaling-agent-systems` | paper | `arxiv:2512.08296`<br>`doi:10.1038/s42256-026-01268-y`<br>`doi:10.21203/rs.3.rs-8414536/v1` | card JSON urls.other, labelled as arXiv/preprint/journal version<br>card JSON primary URL<br>card JSON urls.other, labelled as arXiv/preprint/journal version |
| `co-scientist-nature` | paper | `arxiv:2502.18864`<br>`doi:10.1038/s41586-026-10644-y` | card JSON field 'date_first_public' (free-text version/venue note)<br>card JSON primary URL |
| `sat-teams` | paper | `arxiv:2609.22682`<br>`web:huggingface.co/papers/2609.22682` | card JSON primary URL<br>card JSON urls.other, labelled as arXiv/preprint/journal version |
| `silo-bench` | paper | `arxiv:2603.01045`<br>`doi:10.18653/v1/2026.acl-long.1354` | card JSON primary URL<br>card JSON field 'venue_status' (free-text version/venue note) |
| `peer-preservation` | paper | `arxiv:2604.19784`<br>`doi:10.21203/rs.3.rs-10503185/v1`<br>`web:researchsquare.com/article/rs-10503185/v1` | card JSON primary URL<br>card JSON field 'versions' (free-text version/venue note)<br>card JSON urls.other, labelled as arXiv/preprint/journal version |
| `nature-subliminal-learning` | paper | `arxiv:2507.14805`<br>`doi:10.1038/s41586-026-10319-8` | card JSON field 'date_first_public' (free-text version/venue note)<br>card JSON primary URL |
| `artificial-hivemind` | paper | `arxiv:2510.22954`<br>`doi:10.52202/085713-2732` | card JSON primary URL<br>card JSON urls.other, labelled as arXiv/preprint/journal version |
| `diversity-collapse` | paper | `arxiv:2604.18005`<br>`doi:10.18653/v1/2026.findings-acl.13` | card JSON primary URL<br>card JSON field 'venue_status' (free-text version/venue note) |
| `prev-demarzo-majority` | paper | `arxiv:2409.02822`<br>`doi:10.1126/sciadv.aea6091` | card JSON field 'date_first_public' (free-text version/venue note)<br>card JSON primary URL |
| `prev-flint-group-size` | paper | `arxiv:2510.22422`<br>`doi:10.1073/pnas.2531697123` | card JSON field 'venue_status' (free-text version/venue note)<br>card JSON primary URL |
| `cost-of-consensus` | paper | `arxiv:2605.00914`<br>`doi:10.1145/3786335.3813137` | card JSON primary URL<br>card JSON field 'venue_status' (free-text version/venue note) |
| `robin-futurehouse` | paper | `arxiv:2505.13400`<br>`doi:10.1038/s41586-026-10652-y` | card JSON field 'date_first_public' (free-text version/venue note)<br>card JSON primary URL |
| `micromotor-phase-coherence` | paper | `arxiv:2604.07080`<br>`doi:10.1038/s41567-026-03409-x` | override (ch05 physical-swarms table row (journal DOI and arXiv preprint of the same paper))<br>override (ch05 physical-swarms table row (journal DOI and arXiv preprint of the same paper)) |
| `hf-openai-technical-report` | report | `web:cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/openai-hugging-face%20incident-technical-report.pdf`<br>`web:openai.com/index/hugging-face-incident-and-the-road-ahead` | URL in the survey text<br>URL in the survey text |
| `piao-polarization` | paper | `arxiv:2501.05171`<br>`doi:10.1038/s41467-026-78228-y` | URL in the survey text<br>URL in the survey text |

## Kept separate because of a key conflict (2)

- `ng-hao-peer-preservation-replication` mentions `arxiv:2604.19784` in its own metadata, but that key belongs to another record (`peer-preservation`); the two stay separate (a reply/replication/news item about a paper is not the paper).
- `science-agents-go-rogue` mentions `arxiv:2602.20021` in its own metadata, but that key belongs to another record (`agents-of-chaos`); the two stay separate (a reply/replication/news item about a paper is not the paper).

## Identifiers excluded from a record after review (7)

Found in a card's free-text fields or `urls.other`, but they identify a different document; kept as `excluded_keys` with the reason and not counted as part of the record.

- `lutje-mechanics-of-a-swarm`: `doi:10.5281/zenodo.22689980` — Zenodo concept DOI of the code (MIT) and derived data (CC BY 4.0), not the paper
- `co-scientist-nature`: `arxiv:2608.26701` — companion preprint (27 Aug 2026); the card says it 'is a different paper'
- `riemann-zeta-swarm`: `arxiv:2609.02882` — Lamzouri's independent re-proof of the result, a different work
- `recursive-language-models`: `arxiv:2603.02615` — independent reproduction (CUHK), a different work
- `fermat-last-theorem`: `arxiv:2608.28433` — Prove2Me platform paper, a related but separate document from Anthropic's Fermat post
- `au-aisi-mas-risks`: `arxiv:2508.05687` — Gradient Institute's 2025 predecessor report, a different work
- `tokyo-road-game`: `doi:10.5281/zenodo.22915642` — reserved Zenodo DOI for the private data/code package, not the paper

## Multi-key records reviewed and kept merged (16)

- `opus5-card-multiagent`: two byte-different PDFs of the same system card (v0/v2)
- `kim-scaling-agent-systems`: arXiv preprint, Research Square preprint and Nature Machine Intelligence article of the same study
- `co-scientist-nature`: arXiv:2502.18864 is the preprint of the Nature paper
- `cursor-scaling`: the card covers a series of Cursor posts; both post URLs are kept on the series record
- `sat-teams`: Hugging Face Papers landing page of the same arXiv paper
- `silo-bench`: ACL 2026 version of the arXiv preprint
- `peer-preservation`: extended version under review at Nature (Research Square), same authors and study
- `nature-subliminal-learning`: arXiv preprint of the Nature paper
- `artificial-hivemind`: NeurIPS proceedings DOI of the same paper
- `diversity-collapse`: ACL Findings DOI of the same paper
- `prev-demarzo-majority`: arXiv preprint of the Science Advances paper
- `prev-flint-group-size`: arXiv preprint of the PNAS paper
- `cost-of-consensus`: ACM CAIS proceedings DOI of the same paper
- `robin-futurehouse`: arXiv preprint of the Nature paper
- `piao-polarization`: arXiv preprint and Nature Communications article (8 Oct 2026); alias `piao-polarization-networks`
- `micromotor-phase-coherence`: arXiv preprint and Nature Physics article

## Retired cluster records (3)

October scout records that grouped several works into one table-row card. They are not works; their IDs (announced in `canonical_ids.v0.json`) are retired, and each member row is now its own record.

- `prev-contagion-cluster` → `agentworm`, `multi-agent-security-tax`, `zombie-agents`
- `prev-moltbook-cluster` → `agentsociety`, `emergent-languages`, `gasim`, `moltbook-form-without-function`, `moltbook-observatory`, `openclaw-norms`, `topological-collapse`
- `prev-population-dynamics-cluster` → `ashery-conventions`, `attributing-emergence`, `conformity-no-speaker`, `human-ai-consensus`, `naming-games`, `piao-polarization`, `structured-opinion-dynamics`, `tanaka-memetic-drift`

## Constituent documents and aliases

- `agentworm` → part of `prev-contagion-cluster`
- `zombie-agents` → part of `prev-contagion-cluster`
- `ai-village-how-it-works` → part of `ai-village`
- `ai-village-longitudinal` → part of `ai-village`
- `anthropic-multi-agent-research-system` → part of `anthropic-multi-agent-guidance`
- `cognition-dont-build-multi-agents` → part of `cognition-multi-agents`
- `cognition-multi-agents-working` → part of `cognition-multi-agents`
- `cursor-scaling-long-running` → part of `cursor-scaling`
- `cursor-self-driving` → part of `cursor-scaling`
- `multi-agent-security-tax` → part of `prev-contagion-cluster`
- `opus46-launch-post` → part of `opus46-launch-cluster`
- `sakana-conductor` → part of `sakana-conductor-trinity-fugu`
- `sakana-fugu-report` → part of `sakana-conductor-trinity-fugu`
- `sakana-trinity` → part of `sakana-conductor-trinity-fugu`
- `agentsociety` → part of `prev-moltbook-cluster`
- `artificial-hivemind-reevaluation` → part of `artificial-hivemind`
- `ashery-conventions` → part of `prev-population-dynamics-cluster`
- `attractor-states-anthropic-card` → part of `attractor-states`
- `attractor-states-jakkli-post` → part of `attractor-states`
- `attractor-states-ko-geiping-paper` → part of `attractor-states`
- `attributing-emergence` → part of `prev-population-dynamics-cluster`
- `conformity-no-speaker` → part of `prev-population-dynamics-cluster`
- `emergent-languages` → part of `prev-moltbook-cluster`
- `gasim` → part of `prev-moltbook-cluster`
- `hf-huggingface-technical-timeline` → part of `hf-incident-case`
- `hf-metr-redwood-investigation` → part of `hf-incident-case`
- `hf-openai-technical-report` → part of `hf-incident-case`
- `human-ai-consensus` → part of `prev-population-dynamics-cluster`
- `moltbook-form-without-function` → part of `prev-moltbook-cluster`
- `moltbook-observatory` → part of `prev-moltbook-cluster`
- `naming-games` → part of `prev-population-dynamics-cluster`
- `openclaw-norms` → part of `prev-moltbook-cluster`
- `piao-polarization` → part of `prev-population-dynamics-cluster`
- `structured-opinion-dynamics` → part of `prev-population-dynamics-cluster`
- `tanaka-memetic-drift` → part of `prev-population-dynamics-cluster`
- `topological-collapse` → part of `prev-moltbook-cluster`
- `hf-incident-case` aliases: `hf-technical-timeline`, `metr-hf-investigation`, `openai-hf-incident-2026`, `openai-hf-incident-report`
- `openai-gpt56-ultra` aliases: `gpt56-ultra-launch`
- `opus55-card` aliases: `opus55-card-multiagent`
- `cursor-scaling` aliases: `cursor-scaling-agents`
- `sat-teams` aliases: `self-organizing-agent-teams`
- `anthropic-patterns` aliases: `anthropic-multiagent-patterns`
- `artificial-hivemind` aliases: `hivemind-reevaluation`
- `attractor-states` aliases: `attractor-states-lw`, `ko-geiping-attractors`, `opus4-bliss-attractor`
- `agentsociety` aliases: `agentsociety-parallelized-framework-simulating`
- `ashery-conventions` aliases: `emergent-social-conventions-collective`
- `attributing-emergence` aliases: `attributing-emergence-million-systems`
- `coherence-driven-contagion` aliases: `banerjee-coherence-contagion`
- `conformity-no-speaker` aliases: `most-conformity-needs-no`
- `emergent-languages` aliases: `emergent-languages-populations-language`
- `gasim` aliases: `gasim-graph-accelerated-hybrid`
- `human-ai-consensus` aliases: `ai-agents-reshape-consensus`
- `moltbook-form-without-function` aliases: `form-without-function-social`
- `moltbook-observatory` aliases: `moltbook-observatory-archive`
- `naming-games` aliases: `microscopic-dynamics-consensus-formation`
- `openclaw-norms` aliases: `openclaw-agents-moltbook-risky`
- `piao-polarization` aliases: `2501.05171`, `piao-polarization-networks`, `piao2025`, `piao2026`
- `rheon-consensus` aliases: `ricco-consensus-factual-dynamics`
- `structured-opinion-dynamics` aliases: `collective-opinion-dynamics-structured`
- `tanaka-memetic-drift` aliases: `when-collective-intelligence-lottery`
- `topological-collapse` aliases: `topological-collapse-higher-order`

## Possible duplicates by title (review; not merged automatically) (0)

- none

## Records with uncertain metadata, retained (132)

These are kept in the registry and counts; the flag says what is weak.

| Record | Class | Why uncertain |
|---|---|---|
| `co-scientist-nature` | paper | identifier from a free-text card field |
| `silo-bench` | paper | identifier from a free-text card field |
| `peer-preservation` | paper | identifier from a free-text card field |
| `nature-subliminal-learning` | paper | identifier from a free-text card field |
| `diversity-collapse` | paper | identifier from a free-text card field |
| `prev-demarzo-majority` | paper | identifier from a free-text card field |
| `prev-flint-group-size` | paper | identifier from a free-text card field |
| `cost-of-consensus` | paper | identifier from a free-text card field |
| `robin-futurehouse` | paper | identifier from a free-text card field |
| `agent-to-agent-theory-of-mind` | paper | record class from URL heuristic |
| `agentflow` | paper | record class from URL heuristic |
| `agentnet-decentralized` | paper | record class from URL heuristic |
| `agents-see-humans-as-outgroup` | paper | record class from URL heuristic |
| `ai-swarm-dynamics-hackathon` | event | record class from URL heuristic |
| `aligned-alone-misaligned-together` | paper | record class from URL heuristic |
| `anthropic-risk-report-aug-2026` | report | record class from URL heuristic |
| `anthropic-threat-intel-sept-2026` | report | record class from URL heuristic |
| `antigravity-teamwork` | report | record class from URL heuristic |
| `artificial-self` | paper | record class from URL heuristic |
| `belief-cascades` | paper | record class from URL heuristic |
| `beyond-the-transcript` | paper | record class from URL heuristic |
| `caid` | paper | record class from URL heuristic |
| `caif-multi-agent-risks` | paper | record class from URL heuristic |
| `chain-of-agents` | paper | record class from URL heuristic |
| `cispa-moltbook-first-look` | paper | record class from URL heuristic |
| `claude-code-auto-mode-handoffs` | report | record class from URL heuristic |
| `coercion-ai-to-ai-management` | paper | record class from URL heuristic |
| `compass-kilo-flocks` | paper | record class from URL heuristic |
| `composer-2` | paper | record class from URL heuristic |
| `context-folding` | paper | record class from URL heuristic |
| `context-rot` | report | record class from URL heuristic |
| `de-nobili-lattice` | paper | record class from URL heuristic |
| `devin-fusion` | report | record class from URL heuristic |
| `dwarkesh-agent-civilizations` | essay | record class from URL heuristic |
| `dynamic-workflows-claude-code` | report | record class from URL heuristic |
| `effective-context-engineering` | report | record class from URL heuristic |
| `emergent-behaviors-data-leakage` | paper | record class from URL heuristic |
| `eval-awareness-browsecomp` | report | record class from URL heuristic |
| `forethought-sie` | paper | record class from URL heuristic |
| `game-theory-similarity-inference` | paper | record class from URL heuristic |
| `gas-town` | essay | record class from URL heuristic |
| `governed-shared-memory` | paper | record class from URL heuristic |
| `great-models-think-alike` | paper | record class from URL heuristic |
| `heterogeneous-swarms` | paper | record class from URL heuristic |
| `intelligent-ai-delegation` | paper | record class from URL heuristic |
| `kosmos` | paper | record class from URL heuristic |
| `latentmas` | paper | record class from URL heuristic |
| `loca-bench` | paper | record class from URL heuristic |
| `loop-back-authority` | paper | record class from URL heuristic |
| `lost-before-translation` | paper | record class from URL heuristic |
| `maas-agentic-supernet` | paper | record class from URL heuristic |
| `mas-orchestra` | paper | record class from URL heuristic |
| `mast-why-mas-fail` | paper | record class from URL heuristic |
| `memagent` | paper | record class from URL heuristic |
| `metr-time-horizon-11` | report | record class from URL heuristic |
| `muse-spark` | report | record class from URL heuristic |
| `nomic-self-amending` | paper | record class from URL heuristic |
| `open-challenges-mas-security` | paper | record class from URL heuristic |
| `ord-dynamics-intelligence-explosions` | paper | record class from URL heuristic |
| `orgagent` | paper | record class from URL heuristic |
| `paramanager` | paper | record class from URL heuristic |
| `population-physics` | paper | record class from URL heuristic |
| `prev-uviive-fleet` | paper | record class from URL heuristic |
| `prime-agent` | paper | record class from URL heuristic |
| `programmable-belief-dynamics` | paper | record class from URL heuristic |
| `puppeteer-evolving-orchestration` | paper | record class from URL heuristic |
| `recursive-agent-harnesses` | paper | record class from URL heuristic |
| `rl-orchestration-survey` | paper | record class from URL heuristic |
| `safety-of-latent-communication` | paper | record class from URL heuristic |
| `sakana-ab-mcts` | paper | record class from URL heuristic |
| `science-agents-go-rogue` | news | record class from URL heuristic |
| `science-invent-own-language` | news | record class from URL heuristic |
| `self-moa` | paper | record class from URL heuristic |
| `simulation-to-enaction` | paper | record class from URL heuristic |
| `slocum-hf-reproduction` | paper | record class from URL heuristic |
| `strategic-monoculture` | paper | record class from URL heuristic |
| `stronger-mas` | paper | record class from URL heuristic |
| `subagents-comply-more` | essay | record class from URL heuristic |
| `swarmbench` | paper | record class from URL heuristic |
| `talk-isnt-always-cheap` | paper | record class from URL heuristic |
| `tokyo-shared-state-sync` | paper | record class from URL heuristic |
| `too-polite-to-disagree` | paper | record class from URL heuristic |
| `toolorchestra` | paper | record class from URL heuristic |
| `voluntary-collusion-secret-tools` | paper | record class from URL heuristic |
| `when-does-marl-help` | paper | record class from URL heuristic |
| `who-do-llms-trust` | paper | record class from URL heuristic |
| `willis-hundreds-of-agents` | paper | record class from URL heuristic |
| `x-ai-news-grok-4` | report | title from link text only; record class from URL heuristic; no title recorded |
| `huggingface-co-blog-security-incident-july-2026` | report | title from link text only; record class from URL heuristic; no title recorded |
| `openai-com-index-hugging-face-model-evaluation-security-incident` | report | title from link text only; record class from URL heuristic; no title recorded |
| `oag-ca-gov-news-press-releases-part-ongoing-investigation-attorney-gen` | news | title from link text only; record class from URL heuristic; no title recorded |
| `fluidic-torqueenabled-object-manipulation` | paper | title from link text only; record class from URL heuristic |
| `bio-inspired-decision-making` | paper | title from link text only; record class from URL heuristic |
| `zombie-agents` | paper | record class from URL heuristic |
| `diverse-minds-divided-networks` | paper | title from link text only; record class from URL heuristic |
| `policysim-based-social-simulation` | paper | title from link text only; record class from URL heuristic |
| `ai-village-how-it-works` | paper | record class from URL heuristic |
| `ai-village-longitudinal` | paper | record class from URL heuristic |
| `anthropic-multi-agent-research-system` | report | record class from URL heuristic |
| `cognition-dont-build-multi-agents` | report | record class from URL heuristic |
| `cognition-multi-agents-working` | report | record class from URL heuristic |
| `cursor-scaling-long-running` | report | record class from URL heuristic |
| `cursor-self-driving` | report | record class from URL heuristic |
| `multi-agent-security-tax` | paper | record class from URL heuristic |
| `opus46-launch-post` | system_card | record class from URL heuristic |
| `sakana-conductor` | paper | record class from URL heuristic |
| `sakana-fugu-report` | paper | record class from URL heuristic |
| `sakana-trinity` | paper | record class from URL heuristic |
| `agentsociety` | paper | title from link text only; record class from URL heuristic |
| `artificial-hivemind-reevaluation` | paper | record class from URL heuristic |
| `ashery-conventions` | paper | title from link text only; record class from URL heuristic |
| `attractor-states-anthropic-card` | system_card | record class from URL heuristic |
| `attractor-states-jakkli-post` | essay | record class from URL heuristic |
| `attractor-states-ko-geiping-paper` | paper | record class from URL heuristic |
| `attributing-emergence` | paper | record class from URL heuristic |
| `coherence-driven-contagion` | paper | record class from URL heuristic |
| `conformity-no-speaker` | paper | record class from URL heuristic |
| `emergent-languages` | paper | record class from URL heuristic |
| `gasim` | paper | title from link text only; record class from URL heuristic |
| `hf-huggingface-technical-timeline` | report | record class from URL heuristic |
| `hf-metr-redwood-investigation` | report | record class from URL heuristic |
| `hf-openai-technical-report` | report | record class from URL heuristic |
| `human-ai-consensus` | paper | record class from URL heuristic |
| `moltbook-form-without-function` | paper | record class from URL heuristic |
| `moltbook-observatory` | paper | record class from URL heuristic |
| `naming-games` | paper | record class from URL heuristic |
| `openclaw-norms` | paper | record class from URL heuristic |
| `piao-polarization` | paper | title from link text only; record class from URL heuristic |
| `rheon-consensus` | paper | record class from URL heuristic |
| `structured-opinion-dynamics` | paper | record class from URL heuristic |
| `tanaka-memetic-drift` | paper | title from link text only; record class from URL heuristic |
| `topological-collapse` | paper | record class from URL heuristic |

## Source-grounded metadata corrections (18)

Complete ordered bylines, restored full titles, journal fields and date/spelling conflicts were checked on 9 October 2026 against primary arXiv and publisher metadata. These are corrections to existing records, not new works; identities and aliases are unchanged. BibTeX name forms are kept in `authors_bibtex`. Private editorial records are retained separately.

| Record | Authors | Title / venue | Preserved conflicts and notes |
|---|---|---|---|
| `co-scientist-nature` | 51 | Accelerating scientific discovery with Co-Scientist — Nature 655(8122): 487–496 | The journal title differs from the arXiv preprint (arXiv:2502.18864) title; the record uses the published Nature title. date_first_public stays the preprint date (first public version). |
| `orchestra-o1` | 11 | Orchestra-o1: Omnimodal Agent Orchestration | — |
| `science-malicious-swarms` | 22 | How malicious AI swarms can threaten democracy — Science 391(6783): 354–357 | The publisher page returned HTTP 403; the byline comes from the journal-formatted PDF (p. 354, hosted by HBS) and its order is corroborated by arXiv:2506.06299 author metadata. |
| `robin-futurehouse` | 14 | A multi-agent system for automating scientific discovery — Nature 655(8122): 497–505 | The title 'Robin: A multi-agent system for automating scientific discovery' belongs to the preprint version (arXiv:2505.13400); the record uses the published Nature title. date_first_public stays the preprint date.; earlier title: A multi-agent system for automating scientific discovery (Nature title; the arXiv preprint is titled 'Robin: A multi-agent system for automating scientific discovery') |
| `compass-kilo-flocks` | 5 | Controlling Collectives of AI Agents in Reasoning Space with Spatial Transformers | — |
| `agentworm` | 10 | AgentWorm: Self-Propagating Attacks Across LLM Agent Ecosystems | An NDSS footer with a placeholder DOI is not sufficient for proceedings metadata; kept as a preprint. |
| `zombie-agents` | 5 | Zombie Agents: Persistent Control of Self-Evolving LLM Agents via Self-Reinforcing Injections | Published as a workshop paper in Lifelong Agent @ ICLR 2026 (per arXiv comments); not an ICLR main-conference paper; earlier title: Zombie Agents |
| `multi-agent-security-tax` | 7 | Multi-Agent Security Tax: Trading Off Security and Collaboration Capabilities in Multi-Agent Systems | First author: the arXiv abstract page says 'Pierre Peigne-Lefebvre', the uploader field 'Pierre Peigné-Lefebvre', the paper byline 'Pierre Peigné'; the paper byline is used, no expansion guessed.; Accepted to AAAI 2025 (per arXiv comments); earlier title: Multi-Agent Security Tax |
| `attributing-emergence` | 9 | Attributing Emergence in Million-Agent Systems | — |
| `conformity-no-speaker` | 2 | Most LLM Conformity Needs No Speaker: Measuring the Speaker-Free Floor in Peer-Pressure Benchmarks | earlier title: Most LLM Conformity Needs No Speaker |
| `emergent-languages` | 8 | Emergent Languages in Populations of Language Model Agents: From Token Efficiency to Oversight Evasion | earlier title: Emergent Languages in Populations of Language Model Agents |
| `human-ai-consensus` | 4 | AI agents reshape consensus formation in human groups | — |
| `moltbook-form-without-function` | 12 | Form Without Function: Agent Social Behavior in the Moltbook Network (date: year only) | Date: arXiv submission history says 2026-03-17, the manuscript is dated 2026-04-16; year only is used.; Spelling: the arXiv abstract page has 'Mitrovic', the paper 'Mitrović' (paper spelling used). |
| `moltbook-observatory` | 4 | The Moltbook Observatory Archive: an incremental dataset of agent-only social network activity (date: year only) | Date: the displayed submission date 2026-04-16 conflicts with the identifier prefix 2605; year only is used and the date is not silently corrected to May.; earlier title: The Moltbook Observatory Archive |
| `naming-games` | 4 | Microscopic dynamics of consensus formation in multi-agent LLM Naming Games | — |
| `openclaw-norms` | 2 | OpenClaw Agents on Moltbook: Risky Instruction Sharing and Norm Enforcement in an Agent-Only Social Network | earlier title: OpenClaw Agents on Moltbook: Risky Instruction Sharing and Norm Enforcement |
| `structured-opinion-dynamics` | 3 | Collective Opinion Dynamics in Structured LLM Populations | — |
| `topological-collapse` | 7 | Topological collapse of higher-order interactions bottlenecks collective intelligence in AI agent societies | The inherited October byline had given and family names reversed; corrected to the arXiv author block. |

## Post-cut-off identity update

- `piao-polarization` (alias `piao-polarization-networks`): arXiv:2501.05171 and DOI 10.1038/s41467-026-78228-y (Nature Communications, 8 Oct 2026) are one record — same title and authors; publisher metadata read 2026-10-09. Counted once.
