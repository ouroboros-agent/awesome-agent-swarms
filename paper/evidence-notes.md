# Evidence appendix delivery notes

The appendix contains 57 selected evidence units: 55 coded from the current recovered October 4 manuscript, plus two parent-approved pre-cutoff recoveries qualified on October 9: the October 2 contagion preprint and the September 30 RHEON lead already present in the scout notes. This is a representative evidence map, not a publication census or an exhaustive systematic review. The inherited 153 metadata records and 147 manuscript cards are not treated as unique-publication totals.

Files owned by this work package:

- `paper/evidence-matrix.json`: manual English coding, explicit field-level missingness, separate concurrent/cumulative/capacity scale, citation keys, and source locators.
- `paper/appendix-evidence.tex`: generated comparative appendix, with provenance, eight contradiction analyses, 57 records, and discriminating future comparisons.
- `scripts/build_paper_evidence.py`: deterministic renderer, standard library only; regenerate with `python3 scripts/build_paper_evidence.py` from the repository root. The renderer requires no archive or network access.
- `paper/corpus-inventory.json`: byte-identical snapshot of all 153 inherited administrative records.
- `paper/evidence-notes.md`: this delivery record.

The coding uses the current `build/chapters/w1_t5_t1.md`, `w2_t3_wild.md`, `w3_t2_incident.md`, and `w4_t4_beliefs.md`. Detailed Agensh and Kim cards and inherited metadata resolve particular scale and resource fields. Per-record provenance retains these locators. The added `coherence-driven-contagion` and `rheon-consensus` records point to recovery notes and primary versions; their primary-source reading was done by the parent workflow, not repeated here. No experiments or new broad literature search were conducted for the appendix. The anti-slop writing skill was read and applied to preserve measurements, comparison conditions, uncertainty, and substantive distinctions.

A separate inventory appendix now displays all 153 administrative records. It uses full source titles (or explicit source-bundle labels), citations to actual component documents, inherited evidence classes, model-family fields, and scale-kind-aware numeric fields. It does not mechanically extend the eight-dimensional coding claim to those 153 records. Nine display rows are marked as source bundles. Component citations resolve available mapped documents; some subsidiary links within a grouped card do not have separate bibliography entries. The raw metadata snapshot SHA256 is `1fabffe8df6180a3082cb398ad101ba9eab4de563c8b84f85bc981f18fccfd01`; it matches the source byte-for-byte.

The eight domains contain 10 scaling records, 8 organization records, 8 memory records, 8 diversity records, 8 belief/population-model records, 8 safety records, 5 field records, and 2 methodological records. The contagion addition is a 30-state kernel/logit simulation using two small models. Its conditional topology result is not presented as a frontier-swarm result or as task-solving quality. RHEON adds an 8–1,000-state, sequential-update homogeneous Qwen3-14B population experiment; its call count, partial geometry/size confounding, five-question pooled factuality analysis, judge limitations, and hypothetical cost estimate remain explicit.

Implementation verification:

- Required fields and unique evidence IDs are checked by the renderer.
- A unit audit moved all evaluation counts (configurations, tasks, trials, seeds, calls, edits, and similar quantities) out of cumulative-agent scale into a separate `evaluation_extent` field. Participant/session totals and explicitly labeled identity proxies remain in cumulative scale. A renderer check rejects evaluation-unit words in that field.
- Generated record comments are checked to match every manual JSON record exactly once; all 153 inventory IDs are also rendered exactly once.
- After both bounded recoveries and inventory integration, all 165 cited keys resolve in the current bibliography. The generated LaTeX has no non-ASCII characters.
- The first integrated build exposed a grouping error that repeated rows across domains. It was fixed; no source data were affected. The renderer now checks the generated row set before writing.
- The generated source contains no non-ASCII characters and uses existing ACL manuscript packages (`longtable`, `array`, `booktabs`).
- Bundle record IDs remain available for corpus coordination, but citations use concrete canonical component keys. Bibliography resolution is checked against `paper/references.bib`; final integrated compilation and visual QA are performed by the main author workflow.
- The appendix changes to one-column layout and uses ragged-right columns at the normal small table font; no text is scaled down to fit a width.

Scientific limits retained in the artifact:

- NR means not reported in the extracted evidence, not necessarily absent from the complete primary source.
- Logical agent populations, sequential roles, active inference, cumulative sessions, registrations, and configured capacity are identified separately where the inherited evidence permits.
- No independent dual-coder agreement or fresh primary-paper extraction was performed for every field.
- Model mixtures, external memory, topology, and organization often change together. Their effects are not separated by inference when the source lacks a control.
- Outputs with different metrics are not pooled; there is no effect-size forest plot or universal scaling exponent.
- Counts, figures, and method details inherited from vendor reports retain their source-class limitations. Selected qualitative mechanisms are not population prevalence estimates.

Editorial/metadata correction pass (9 October 2026):

- `coherence-driven-contagion`: the matching field read "temperature claim 36 C". The primary paper (arXiv:2610.02654v1, §3.2 and Table 4, clustering column) shows that 36°C is the value in the belief statement "Tomorrow it will be T°C in Boston" used for the clustered-versus-random comparison, not a sampling temperature or a health measurement. The field now quotes that claim. The paper does not say in prose why 36°C counts as marginal (its Table 3 labels 35°C borderline), so no further interpretation was added. The two domains (next-day temperature, commute time) are named in the limit field.
- `hf-incident-case`: the headline "more than 70,000 messages and files" is attributed to METR, and the 8–13 July window is tied to the board's active period with about 1,200 cumulative participants, about 700 of whom joined the attack. The figure caption separately reports the source figure's own category tallies for its plotted 9–13 July span. The two are not presented as contradictory: the source figure's header describes its counting rule (files counted once; many uncategorized entries expected to be file-encoding fragments).
- `opus55-card`: the ProgramBench comparator is now explicit (five peers versus one agent); the token ratio is labeled as a plot reading. The organization section keeps its separate comparison with the asynchronous hierarchy.
- `deepmind-cheating-whistleblowing`: the 100-agent denominator is stated next to the 14 cheaters and 24 whistleblowers.
- Recovery-history phrases were removed from reader-facing limit fields (`rheon-consensus`, `coherence-driven-contagion`, `teams-hold-experts-back`). The provenance blocks still record how the two additions entered.
- Appendix C keeps every raw inventory value unchanged. For eight rows whose bare number is not a within-run concurrent count, a bracketed qualifier rendered from the snapshot's own `scale_note_ru` follows the value: Agensh, Cursor, Colosseum, Physics of Agents, PIMMUR, the enzyme campaign, Anthropic's internal platform figure, and Navier–Stokes. The qualifiers live in `SCALE_QUALIFIERS` in the generator.
- The generator no longer adds a row spacer after a table's final row (it could leave a closing rule alone on a page) and escapes `°` and typographic quotes.

Reviewer corrections (parent source adjudication, checked against the retained cards before editing):

- `brockers-opinion-dynamics`: effect strength and explanatory power are now separated, keeping the primary text's "tends to surpass" hedge for GPT-4o-mini and Grok (card `cards_b/brockers-opinion-dynamics.json`, key result on the Bayesian decomposition).
- `wiki-copying`: the two hours are the median first-to-last edit span per handle in Results (card `cards/wiki-copying.json`; the card also records the abstract's "about an hour").
- `einsteinarena`: the 11 historical records stay; the limit adds the SimpleTES Erdős result from the authors' footnote 4 (card `cards_b/einsteinarena.json`).
- `delm-shared-context`: "Terminal-Bench 4.0" per the card.
- `sections/collective.tex`: the debate freeze is described as triggered by behavioral signals; the card records a probe-gated freeze and a Round-1 majority-change rule, with no activation access.

This note records implementation checks and remaining evidence limits. It is not independent review or acceptance of the manuscript.
