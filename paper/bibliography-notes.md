# Bibliography construction and corpus coordination

`references.bib` is a paper-local bibliography built from the preserved October research, not a fresh literature search. The generator reads the archive without modifying it. Compilation needs only the checked-in bibliography and vendor files, not the archive.

## Canonical interface

The full `data/interface.md` and the 234 IDs in `data/canonical_ids.v0.json` supplied by the catalogue builder were read on 9 October 2026. Ordinary individual-work keys preserve the inherited source slug. Canonical metadata remains owned by the catalogue builder. The proposals below require parent integration into that registry; this worker did not modify `data/`.

Bundle identifiers and old aliases remain corpus identities. They are not silently reused as keys for different publications. A citation to one constituent uses a new explicit component key, with `part_of` recorded in `citation-key-map.json`. The paper bibliography omits a fabricated aggregate publication for case dossiers and the three `prev-*-cluster` table bundles.

## Proposed component IDs for parent integration

| Proposed BibTeX / work ID | `part_of` case or bundle | Publication title |
|---|---|---|
| `agentworm` | `prev-contagion-cluster` | AgentWorm: Self-Propagating Attacks Across LLM Agent Ecosystems |
| `ai-village-how-it-works` | `ai-village` | How the AI Village works |
| `ai-village-longitudinal` | `ai-village` | Norms, Tools, and the Say/Do Gap: Seventeen Months of Autonomous Frontier-Model Agents in the AI Village |
| `anthropic-multi-agent-research-system` | `anthropic-multi-agent-guidance` | How we built our multi-agent research system |
| `artificial-hivemind-reevaluation` | `artificial-hivemind` | How Strong Is the Evidence for the Artificial Hivemind? Reevaluating Evidence for the Open-Ended Homogeneity of Language Models |
| `attractor-states-anthropic-card` | `attractor-states` | System Card: Claude Opus 4 and Claude Sonnet 4 |
| `attractor-states-jakkli-post` | `attractor-states` | Models have some pretty funny attractor states |
| `attractor-states-ko-geiping-paper` | `attractor-states` | Attractor States Emerge in Multi-Turn LLM Conversations |
| `attributing-emergence` | `prev-population-dynamics-cluster` | Attributing Emergence in Million-Agent Systems |
| `cognition-dont-build-multi-agents` | `cognition-multi-agents` | Don't Build Multi-Agents |
| `cognition-multi-agents-working` | `cognition-multi-agents` | Multi-Agents: What's Actually Working |
| `conformity-no-speaker` | `prev-population-dynamics-cluster` | Most LLM Conformity Needs No Speaker |
| `cursor-scaling-long-running` | `cursor-scaling` | Scaling long-running autonomous coding |
| `cursor-self-driving` | `cursor-scaling` | Towards self-driving codebases |
| `emergent-languages` | `prev-moltbook-cluster` | Emergent Languages in Populations of Language Model Agents: From Token Efficiency to Oversight Evasion |
| `hf-huggingface-technical-timeline` | `hf-incident-case` | Agent Intrusion: Technical Timeline |
| `hf-metr-redwood-investigation` | `hf-incident-case` | OpenAI Hugging Face Incident Investigation |
| `hf-openai-technical-report` | `hf-incident-case` | OpenAI--Hugging Face Incident: Technical Report |
| `human-ai-consensus` | `prev-population-dynamics-cluster` | AI agents reshape consensus formation in human groups |
| `moltbook-form-without-function` | `prev-moltbook-cluster` | Form Without Function: Agent Social Behavior in the Moltbook Network |
| `moltbook-observatory` | `prev-moltbook-cluster` | The Moltbook Observatory Archive |
| `multi-agent-security-tax` | `prev-contagion-cluster` | Multi-Agent Security Tax |
| `naming-games` | `prev-population-dynamics-cluster` | Microscopic dynamics of consensus formation in multi-agent LLM Naming Games |
| `openclaw-norms` | `prev-moltbook-cluster` | OpenClaw Agents on Moltbook: Risky Instruction Sharing and Norm Enforcement in an Agent-Only Social Network |
| `opus46-launch-post` | `opus46-launch-cluster` | Claude Opus 4.6 |
| `piao-polarization` | `prev-population-dynamics-cluster` | Emergence of polarization in networks of large language model agents |
| `sakana-conductor` | `sakana-conductor-trinity-fugu` | Learning to Orchestrate Agents in Natural Language with the Conductor |
| `sakana-fugu-report` | `sakana-conductor-trinity-fugu` | Sakana Fugu Technical Report |
| `sakana-trinity` | `sakana-conductor-trinity-fugu` | Trinity: An Evolved LLM Coordinator |
| `structured-opinion-dynamics` | `prev-population-dynamics-cluster` | Collective Opinion Dynamics in Structured LLM Populations |
| `tanaka-memetic-drift` | `prev-population-dynamics-cluster` | When Is Collective Intelligence a Lottery? Multi-Agent Scaling Laws for Memetic Drift in LLMs |
| `topological-collapse` | `prev-moltbook-cluster` | Topological collapse of higher-order interactions bottlenecks collective intelligence in AI agent societies |
| `zombie-agents` | `prev-contagion-cluster` | Zombie Agents: Persistent Control of Self-Evolving LLM Agents via Self-Reinforcing Injections |

| `agentsociety` | `prev-moltbook-cluster` | A Parallelized Framework for Simulating Large-Scale LLM Agents with Realistic Environments and Interactions |
| `ashery-conventions` | `prev-population-dynamics-cluster` | Emergent social conventions and collective bias in LLM populations |
| `gasim` | `prev-moltbook-cluster` | GASim: A Graph-Accelerated Hybrid Framework for Social Simulation |

## Draft citation replacements

These replace earlier provisional paper keys. They are local editorial mappings, not a change to the corpus aliases. Claims covering several documents should cite the relevant several component keys.

| Provisional citation | Concrete constituent citation |
|---|---|
| `hf-incident-case` | `hf-openai-technical-report` |
| `hf-metr-investigation` | `hf-metr-redwood-investigation` |
| `hf-technical-timeline` | `hf-huggingface-technical-timeline` |
| `attractor-states` | `attractor-states-jakkli-post` |
| `ko-geiping-attractors` | `attractor-states-ko-geiping-paper` |
| `opus4-bliss-attractor` | `attractor-states-anthropic-card` |
| `cursor-scaling` | `cursor-scaling-long-running` |
| `ai-village` | `ai-village-how-it-works` |
| `cognition-multi-agents` | `cognition-dont-build-multi-agents` |
| `anthropic-multi-agent-guidance` | `anthropic-multi-agent-research-system` |
| `sakana-conductor-trinity-fugu` | `sakana-fugu-report` |
| `opus46-launch-cluster` | `opus46-launch-post` |

`hivemind-reevaluation` remains an inherited corpus alias. The separate Schaeffer et al. paper is `artificial-hivemind-reevaluation`, arXiv:2609.33936, with all five names taken from the full card's `paired_work` block.

## Piao publication update

`piao-polarization` represents the same work as arXiv:2501.05171. The Nature Communications primary page was checked on 9 October 2026: title *Emergence of polarization in networks of large language model agents*; Jinghua Piao, Zhihong Lu, Chen Gao, Fengli Xu, Qinghua Hu, Fernando P. Santos, Yong Li, and James Evans; DOI `10.1038/s41467-026-78228-y`; publication date 8 October 2026. The publisher marks this as an early, citable article in press, subject to further edits. No unreported volume or article number was invented. The publisher page states CC BY 4.0, subject to its third-party credit-line exceptions. This is a metadata/version update, not an added unique research work.

Primary source: https://www.nature.com/articles/s41467-026-78228-y

## Metadata treatment and remaining gaps

The file currently has 261 citable entries after splitting inherited bundles. This is neither a deduplicated corpus size nor a coverage claim. Published versions with an explicit journal record in the October cards use their journal year and identifiers. arXiv-first dates are not substituted for known journal publication dates. For items cited via arXiv whose later venue is not fully specified, the record remains a preprint citation; no proceedings metadata is guessed.

Incomplete author lists in the short cards were first supplemented from the already preserved `lanes/t_fable_triage/scratch/arxiv_meta.json` when available. Eighteen entries still lacked complete bylines after that step. On 9 October 2026 their complete ordered bylines, exact titles and publication dates were read from primary arXiv, publisher and journal pages; the research handoff is `swarm-recovery-20261009/metadata-18-bylines.md` (SHA-256 recorded in `source-provenance.json`). The generator applies them in one block, records `author_metadata_source`, `primary_dates` and any `metadata_conflicts` per key in `citation-key-map.json`, and clears `partial_author_list` for these keys only. No `partial_author_list` flag remains. Two short-card entries (`claude-code-auto-mode-handoffs`, `eval-awareness-browsecomp`) still end in `and others` because only their first author is recorded; they were not part of this metadata task and are not flagged.

Entries completed: `agentworm`, `attributing-emergence`, `co-scientist-nature`, `compass-kilo-flocks`, `conformity-no-speaker`, `emergent-languages`, `human-ai-consensus`, `moltbook-form-without-function`, `moltbook-observatory`, `multi-agent-security-tax`, `naming-games`, `openclaw-norms`, `orchestra-o1`, `robin-futurehouse`, `science-malicious-swarms`, `structured-opinion-dynamics`, `topological-collapse`, `zombie-agents`.

Titles restored to their full primary form: `conformity-no-speaker` (subtitle *Measuring the Speaker-Free Floor in Peer-Pressure Benchmarks*), `moltbook-observatory` (subtitle *an incremental dataset of agent-only social network activity*), `multi-agent-security-tax` (*Trading Off Security and Collaboration Capabilities in Multi-Agent Systems*). Status notes added only where the arXiv comments state them: Security Tax, `Accepted to AAAI 2025 (per arXiv comments)`; Zombie Agents, `Published as a workshop paper in Lifelong Agent @ ICLR 2026 (per arXiv comments)` — a workshop, not the ICLR main conference. Orchestra-o1 gains the DOI shown in its primary metadata, `10.48550/arXiv.2606.13707`. No proceedings or journal fields were invented.

Conflicts kept as recorded, not resolved by guesswork:

- `multi-agent-security-tax`: the paper byline reads *Pierre Peigné*; the abstract metadata reads *Pierre Peigne-Lefebvre* and the uploader field *Pierre Peigné-Lefebvre*. The paper byline is used.
- `moltbook-form-without-function`: arXiv submission history 2026-03-17 versus manuscript date 2026-04-16; year only is cited. The abstract page spells *Mitrovic*, the paper *Mitrović*; the paper is followed.
- `moltbook-observatory`: displayed submission 2026-04-16 conflicts with the `2605` identifier prefix; year only is cited.
- `agentworm`: an NDSS footer with a placeholder DOI is not sufficient for proceedings metadata; the entry stays a preprint.
- `science-malicious-swarms`: the publisher page returned HTTP 403; the byline was read from the journal-formatted PDF and corroborated by arXiv:2506.06299 author metadata.
- `robin-futurehouse`: the journal title is used; the earlier "Robin:" preprint title belongs to another version.
- `topological-collapse`: the inherited card had reversed given and family names; the arXiv order is used.

Exact spellings and initials are kept (`Dang H. Dang`, `Md Motaleb Hossen Manik`, `Lyngsø`, `Lukas Galke Poech`); compound family names are braced or given in `Last, First` form (`{Ghosh Dastidar}`, `{Schroeder de Witt}, Christian`, `{Van Bavel}, Jay J.`, `van der Linden, Sander`, `Garcia Camargo, Romina`, `De Nobili, Cristiano`).

The ACL style prints at most its own limit of names in the reference list and then "and N others" (Co-Scientist, Kimi K2.5, Agents of Chaos). That is a display rule; the `.bib` holds the complete bylines.

Surname particles: four recorded names with a capitalized particle (`Giordano De Marzo`, `Sydney Von Arx`, `Cristiano De Nobili`, `Manlio De Domenico`) were parsed by BibTeX as given name + bare surname, producing labels such as "Marzo et al.". The generator now emits them in `Last, First` form; the rendered labels are "De Marzo et al.", "Von Arx et al." and "Zomer and De Domenico".

The full corpus deduplication and verification of every light-card byline remain outside this paper-local conversion. The map records each source card, source-file hash when applicable, supplemental metadata source, inherited venue note, and proposed component membership.

## Official ACL source and build verification

The official upstream files, pinned commit, hashes, and retained license notices are documented in `vendor/upstream.json` and `vendor/LICENSE-NOTES.md`. The style is unchanged. It selects the bibliography style itself, so the build should set `TEXINPUTS=vendor/:` and `BSTINPUTS=vendor/:` from `paper/` and use `\usepackage[preprint]{acl}` without a second bibliography-style command.

A standalone `\nocite{*}` compilation is kept under `vendor/.bibcheck/` to exercise every entry. This is a build check, not an independent scholarly review or acceptance. Final command results and warnings are recorded after the last regeneration.

Initial all-entry bibliography check (9 October 2026, before the bounded addition below): `latexmk -pdf -interaction=nonstopmode -halt-on-error bibcheck.tex` with `TEXINPUTS=../:` and `BSTINPUTS=../:` completed under TeX Live 2026 / pdfTeX 1.40.29, latexmk 4.87 and BibTeX 0.99e. All 259 entries were cited. The PDF has 10 pages, 119,079 bytes; SHA-256 `4a048e83fce8e9e67ef1f9763bd705780c91e6fb9f6101ff37cd34ab13934b99`. Final logs contain zero LaTeX warnings, zero BibTeX warnings, zero overfull boxes, and 127 underfull boxes in the two-column bibliography. These spacing diagnostics are retained in the log; this check does not claim visual inspection of the final report. `vendor/.bibcheck/verification.json` records the result. All vendored upstream file hashes still match.

The `agentsociety` URL/DOI gap is closed: the current author chapter provided [ACL Anthology 2025.acl-industry.94](https://aclanthology.org/2025.acl-industry.94/), checked directly on 9 October 2026. The title, seven authors, venue and pages match the inherited entry; its official DOI is `10.18653/v1/2025.acl-industry.94`. The archive also contains only a shortened TraitMix title, so a separate TraitMix bibliographic record was not fabricated; its evidence remains in the source population-dynamics bundle for the catalogue builder.

## Bounded missed-paper addition for parent integration

Proposed stable work/BibTeX key: `coherence-driven-contagion`; `part_of: null`. This is one missed pre-cutoff work, not a post-cutoff discovery and not a new literature search. Parent authorization and source reading are recorded in `swarm-recovery-20261009/freshness-notes.md`; this worker checked the [primary arXiv metadata](https://arxiv.org/abs/2610.02654) on 9 October 2026.

Exact title: *Coherence-Driven Belief Formation and Population Dynamics of Contagion in LLM Agents*. Authors, in order: Tathagata Banerjee and Nima Moghaddas. arXiv:2610.02654v1 was submitted on 2 October 2026 at 01:20:52 UTC. The arXiv comments report acceptance at the NeurIPS 2026 Workshop on Foundations of Agentic Systems Theory (FAST). The bibliography marks that status as **per authors**; it does not classify this as a NeurIPS main-conference publication. The arXiv DOI is shown as pending registration, so the entry uses the stable arXiv URL and identifier without relying on DOI resolution.

Primary abstract/metadata: https://arxiv.org/abs/2610.02654. Primary full text: https://arxiv.org/html/2610.02654v1. The parent’s full-text notes identify CC BY 4.0 and a 30-agent, two-model, kernel/logit-based simulation design; no additional empirical claims were added by this bibliography update.

At this stage the bibliography contained 260 entries. The earlier all-entry compile receipt covers the 259-entry version; the parent’s manuscript build must include this bounded addition. Generator execution and citation-key resolution were checked after the update. Canonical `data/` files and all manuscript/figure/vendor files remain unchanged by this delta.

## RHEON: recovery of an existing scout lead

Proposed stable work/BibTeX key: `rheon-consensus`; `part_of: null`. No RHEON/arXiv:2609.39211 key existed in the supplied canonical registry when checked. The lead is already present in the preserved `discovery/sonnet_A8.md`, lines 154–156 and 222; the citation map records that file's SHA-256. Parent authorization and further primary-source qualification are recorded in the RHEON section of `swarm-recovery-20261009/freshness-notes.md`. This is recovery of an omitted existing lead, not a new post-cutoff discovery or a new search campaign.

Exact title: *Consensus and Factual Dynamics in Large Populations of Interacting Language Models*. The four authors, in order, are Emanuele Ricco, Elia Onofri, Vincenzo Sammartino, and Roberto Di Pietro. arXiv:2609.39211v1 is a preprint dated 30 September 2026. The parent checked the [primary full text](https://arxiv.org/html/2609.39211v1) on 9 October and records its license as **CC BY-NC-SA 4.0**, not CC BY. The bibliography adds no claimed conference or journal acceptance.

Primary metadata: https://arxiv.org/abs/2609.39211. Qualified version: https://arxiv.org/html/2609.39211v1. The parent notes distinguish the tested populations (up to 1,000 agents) from the approximately 4.7 million generated responses and retain the factual-evaluation caveats; this bibliography change adds no new empirical interpretation.

The bibliography now contains 261 entries. The generator and current manuscript citation-key resolution were checked. The original standalone bibliography compile receipt remains explicitly scoped to the earlier 259-entry version; the parent will compile the final manuscript with both bounded additions. This delta changes only the bibliography, citation map, bibliography notes, and their generator.

## Corrections found in rendered bibliography QA

The initial 57-page PDF bibliography was visually inspected on pages 19–25. Three inherited conversion residues were corrected in both `references.bib` and its generator: Robin's journal title no longer contains a preprint-title editorial parenthetical; the Jakkli constituent is labeled `LessWrong post`; the Opus 4.6 news constituent is labeled `Anthropic launch post`. See `qa/pre-apply/visual-bibliography.md` for the initial PDF hash, exact image coverage and completed final reinspection against PDF SHA-256 `1d50eebe6471d322fa3b1af81b6640ca31b4fbb532eb15bb76cd9c3f507da32b`.

## All-entry compile after the byline corrections

The `vendor/.bibcheck/` all-entry compile was re-run on 9 October 2026 after the corrections above: 261 entries, 11 pages, PDF SHA-256 `9ac00d086f46b287b30f0f6e29da1faab3c7b1bc6811ba490c6545127f341ffe`, 0 LaTeX warnings, 0 BibTeX warnings, 0 overfull boxes, 133 underfull boxes. `vendor/.bibcheck/verification.json` now records this run; the earlier 259-entry receipt above is historical. The rendered references of the corrected manuscript (pages 19–25) were inspected; see `qa/visual-review.md`.

## Reconciliation with the integrated canonical registry (read-only)

On 9 October 2026 the paper bibliography was compared, without editing `data/`, against the integrated registry `data/works.json` (280 records; SHA-256 `cf491351f3683f72cb1bd79fdf2bcba3075fcadda00e173123fd88cdbc761c71`) and `data/provenance/IDENTITY_AUDIT.md` (SHA-256 `dceeb5cdda0c12216b47fbbf0c60d1eff7cebee94721bbb7a0d6ee76a7f7a889`).

- All **261** BibTeX keys exist as exact canonical record IDs; none needs an alias or identifier lookup.
- No arXiv identifier or DOI in `references.bib` disagrees with the registry's identifiers or identity keys (the arXiv-issued DOI `10.48550/arXiv.2606.13707` is treated as an arXiv identifier).
- Every `part_of` value in `citation-key-map.json` equals the registry's `part_of`. The registry has since retired the three `prev-*-cluster` bundles as works; the paper never cites them, and the map keeps them only as `part_of` provenance.
- The 18 entries completed above have the same author counts and exact titles in the registry.
- One note for the data owner: the "Multi-key records reviewed and kept merged" list in `IDENTITY_AUDIT.md` names `piao-polarization-networks`, which is not a record in `works.json`; the record is `piao-polarization`. The paper uses `piao-polarization`.

The "Proposed component IDs" table above is therefore historical: the proposals are now integrated.

