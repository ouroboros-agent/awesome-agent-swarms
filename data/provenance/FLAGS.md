# Factual flags and source-qualified adjudications (2026-10-09)

Raised by the page editors while editing against the card JSON. The 13 groups below now have source-qualified dispositions; **source conflict retained** means the uncertainty remains visible to readers, not that a source disagreement was resolved. Private historical editing notes are retained separately. This is a candidate change log, not publication approval.

## Fixed during this pass
- **ch07, Mind Viruses** — Russian «освобождения ИИ» corrected to «благополучия ИИ»: the card JSON names the virus "AI welfare".
- **ch04, Park et al.** — the comparison was called "comparable output tokens", but the card data shows the team of 5 spent about 24M vs about 8M output tokens for best@5 ("nearly twice"). Table and card now say "same number of agents and per-agent action budget; the team spends more output tokens".
- **ch03 intro** — the claim that METR and OpenAI judged the collective did what a single agent likely could not was presented as a main finding. It now sits in the hf-incident-case caveats with METR's own footnote (no measured comparison); Cotra's statement stays in her card as her judgment.

## Fixed after the meaning-level RU/EN review (2026-10-09)
Five reviewers compared RU and EN sentence by sentence (68 English fixes, logged per page). Russian-side issues they found were fixed against the card JSON:
- ch03: Cotra's clarification restored with her hedge ("more propensities than capabilities, though fuzzy"); «не сделал бы» → «не смог бы» (source: "could not"); Brown's paraphrase no longer in quotation marks.
- ch04: Cursor's hypothesis worded as in the source ("context efficiency, more than parallelism").
- ch05: «Маринки Житник» (Marinka Zitnik); «конструктивный конфликт» (constructive conflict); fourth Worse Together environment named «персональный ассистент (совместный заказ)»; «контролируемый бенчмарк».
- ch06: HiddenBench gains now say they are gains from discussion.
- ch09: «Рикко» (Ricco); the 98% / 92% sentence states what is explained; logit-kernel caveat separated from the authors' own caveats; section intros mention the two added cards; "model coupling" kept as the authors' term.
- ch10: «Гарсия» spelling unified; "to their knowledge" restored; the OpenClaw schedule is a fixed 4-hour heartbeat.
- ch02: the ≈$6.5M Navier–Stokes cost is attributed to a dev.to post.
- index: finding 8's effective team size 1.12 now names its setting (Qwen2.5-7B, MMLU-Hard).

## Metadata corrections integrated (2026-10-09, task 4aab7b90)
18 existing records received complete ordered bylines, three restored full titles (conformity-no-speaker, moltbook-observatory, multi-agent-security-tax; also zombie-agents, emergent-languages, openclaw-norms now carry their full titles) and journal fields for the two Nature papers and the Science Policy Forum. Conflicts preserved as notes: Moltbook dates year-only; Security Tax byline 'Peigné' vs abstract 'Peigne-Lefebvre'; Robin/Co-Scientist published titles vs preprint titles; AgentWorm NDSS placeholder DOI not used; Zombie Agents is a workshop paper. The ch04 related row for Robin now shows the published title. Details: `data/provenance/IDENTITY_AUDIT.md`.

## Final narrow webtext pass: dispositions of all 13 groups

This pass used source adjudication and Grok editorial review; their private working records are retained separately. `A` below is the read-only `research-archive` archive. No new research sweep or paper edits were made.

| Group | Disposition | Reader-facing result and retained uncertainty |
|---|---|---|
| 1. Navier–Stokes training | **resolved: qualified** | ch02 attributes the denial to OpenAI’s 10 September update and restricts it to Buckmaster’s Codex prompts in the two months before 8 September, including training. The earlier archived uncertainty is superseded, not restored. |
| 2. ≈$6.5M | **resolved: already fixed** | ch02 already calls this an estimate from a dev.to post, not an OpenAI bill. Preserved. |
| 3. Peer-Preservation dates | **resolved: qualified; exact announcement date unknown** | ch02 distinguishes arXiv v1 submission on 30 March from the Berkeley RDI page being public by 1 April. No exact arXiv public-announcement date is claimed. |
| 4. Anthropic Risk Report | **resolved: confirmed** | very low → low is supported by the report. ch03 now specifies high-stakes settings. |
| 5. Kim figures | **resolved: confirmed, unchanged** | ch04 captions correctly identify arXiv v2, not the later journal figures. |
| 6. DeLM | **resolved: clarified** | ch04 and ch06 now name Terminal-Bench 4.0. Results and small-sample caveats retained. |
| 7. Agensh / Cursor / OrgAgent | **resolved** | ≈800× remains a valid rounded upper bound. Both attributed Cursor ranges remain. The table explicitly selects two posts from the three-post series. OrgAgent now uses governance–execution–compliance. Agensh’s summary says messages, matching Mattermost. |
| 8. Opus / byline / CLM | **resolved: qualified** | ch06 distinguishes maximum/adaptive thinking from Sonnet’s 64-thousand-token budget. CLM’s four days is tied to its 29 September 2026 preprint and the corpus cut-off. Both verified harness authors remain. |
| 9. Sabotage / Security Tax | **resolved: qualified** | ch07 names the two-agent setting for 14%/26% and the three-agent coordinator prohibition for 0–6%. Security Tax has its own link in the combined related-work row; its pre-existing atlas/bibliography entry was not missing. |
| 10. Mythos / Hivemind / Kim / Mo’ Models | **resolved: qualified; incompatible units retained explicitly** | ch08 attributes Andon results through Anthropic’s system card. The unsupported 1.9–3.1× comparison is removed; its incompatible denominators are explained in the reader sentence. Threshold distance is 0.08–0.10 above the median; the recheck is dated September 2026. Kim uses configurations (also ch01), since centralization adds an orchestrator. Approximate Mo’ Models plot readings remain labelled and were not re-digitized. |
| 11. Social Circuits / Göttingen / generations / probes | **resolved: qualified** | ch09 says the single-agent baseline gets only its assigned passages; inputs are not matched. Standalone explanatory power is separated from effect strength; GPT-4o-mini and Grok interaction effects tend to exceed topic bias. The uncounted 2023–2025 majority is removed; transfer between model generations remains unestablished. Behavioural-probe wording was already correct. |
| 12. Field observations | **resolved: qualified; source conflicts retained** | ch10 attributes the disputed 44-hour shutdown to its author; the earlier date conflict remains. Chaos retains ≥9 days vs about an hour and distinguishes deletion in the text, modification in Fig. 13, overwriting on the site. The general “swarm does not win” is replaced with the actual AI Village / Superminds comparison limits. Historical 11 EinsteinArena records remain, with the later SimpleTES result added. Wiki gives the two-hour median first-to-last edit span per handle and the abstract’s roughly one-hour lifetime, without claiming a two-hour runtime for every run. |
| 13. Median 7 | **resolved: corrected denominator** | ch01 states that the median is over all 99 works with known simultaneous counts, separately from the observation that controlled experiments are mostly small. |

### Further Grok corrections and primary-card adjudications

- All eight accepted priority groups applied: qualified README classification (197 classified scholarly works / 280 records / 153 analytic works); ch02 counterfactual removed; Cotra’s **could not** restored in RU ch03/ch04 without dropping attribution; model and instruction diversity separated; CLM date anchored; ch05/ch11 comparisons bounded with positive DeLM/Opus cases retained; HiddenBench and Silo-Bench separated; ch10 viral-story claim bounded to six examined Moltbook narratives.
- **Artificial Self: resolved by correcting RU, not EN.** The verified deep card quotes the primary abstract as “can sometimes change its behaviour as much as changing its goals”; RU now says «столь же сильно», EN remains “as much”. `A/cards_b/vidal-models-identify-as-swarm.json:30,87`; no standalone primary paper was retained locally. The light card’s stronger «не меньше» is not followed.
- **Voluntary Collusion: qualified; aggregate unknown.** Both reader rows now give verified V0 examples: Claude Sonnet 4.5 0%, GPT-4.1 / Gemini-2.5-Flash 100%, within a 12-model study. They explicitly do not claim a pooled trial frequency or a precise accepting-model numerator. `A/cards_c/voluntary-collusion-secret-tools.json:9,11` (including its `problems` verification); no standalone primary table was retained locally. The previous editorial-log inference from three examples to “most of 12” is marked superseded.
- **Opus sub-lead: confirmed.** EN’s “main sender” matches the recipient-specific primary criterion; RU now makes that criterion explicit. `A/inputs/opus55_system_card.txt:6527–6532` (Fig. 8.12.3.E).
- **Cursor subset: clarified.** Three posts remain in the card; the table explicitly includes two of that series and keeps both URLs. `A/cards/cursor-scaling.json:3,10,12,15–21` and `A/lanes/v2_00/scratch/src/cursor{1,2,3}.txt`.
- EN “128 agents exceeded 30%” and RU Grok 4.20’s token-use and latency tradeoff corrected. No changes to “98 tasks found by agents”: the supervisor is itself an agent.
- `piao-polarization` remains the canonical ID; `piao-polarization-networks` is labelled as its alias in identity-audit prose. No canonical renaming or bibliography work.

### Preservation and check interpretation

No card ID, figure reference, external URL or table row is removed. The intentionally invalid Hivemind ratio is the sole removed numerical claim; this is a source-qualified correction, not evidence loss. The existing checker reports `0.1` and `1.9` as still present elsewhere and therefore does not detect this semantic change. Its output is retained verbatim; no check logic, allowance or numeric expectation was weakened. The replacement sentence explains why a new ratio is not calculated. All 52 figure references and all original assets remain; generated web PNG encoding may differ with the project virtualenv, checked separately for equal pixels.

## Small additions made by editors from the card JSON (not new research)
- ch03: dates "21 June" (timeline) and "from 24 May" (Lütje card); ch06: "(11 дней)" in the Fermat card; ch09: which single-model teams scored ≈0.55 / ≈0.64 (Flag Game), temperature labels for Okawa's ≈0.855 / ≈0.89, the Riedl main-experiment scope; ch02: Kim et al.'s 95% interval next to 0.0% and "cumulative" next to the incident counts.

## Added after the cut-off (dated, kept out of the 153-work analytic corpus and its charts)
- **piao-polarization-networks**: published in Nature Communications on 8 Oct 2026 (publisher page read 2026-10-09; same work as arXiv:2501.05171). Status note added to the ch09 related row, the passport and the About page.
- **banerjee-coherence-contagion** (arXiv:2610.02654, 2 Oct 2026, NeurIPS 2026 FAST workshop) and **ricco-consensus-factual-dynamics** (arXiv:2609.39211, 30 Sep 2026): pre-cut-off works missed by the October corpus, added as ch09 short cards from the parent's primary-source reading notes; metadata confirmed via the arXiv API. Their texts should get one primary-source read before public release.
