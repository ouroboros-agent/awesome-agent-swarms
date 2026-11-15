# Evidence appendix notes

## Current edition (November 2026)

Appendix A of the report contains 82 selected evidence units. Fifty-seven come from the October 2026 research collection: 55 coded from its manuscript chapters and source cards, and two pre-cutoff works qualified on 9 October. 25 were coded for this edition directly from primary sources added after the 3 October cohort (21 from methods and results sections or tables, 4 at abstract level, marked in the table). By domain: 15 scaling and resource tradeoffs, 14 organization and task allocation, 12 memory and information integration, 8 diversity and correlated behavior, 12 collective beliefs and population models, 12 collective safety and control, 7 field observations and identity, 2 methodological controls. Appendix C lists all 153 records of the frozen 3 October inventory; `corpus-inventory.json` is byte-identical to the October snapshot, and the renderer adds its affiliation field and bracketed qualifiers without changing any value.

Regenerate the appendix with `python3 scripts/build_paper_evidence.py` (standard library only; no archive or network access). `scripts/build_paper_qa.py` checks that every unit and inventory record is rendered exactly once and recomputes the dated cohort statistics quoted in Section 3. Per-unit provenance in `evidence-matrix.json` records the source locator, version, retrieval date, reading depth, and, for primary sources read in November, the SHA-256 of the retrieved file.

## Coding rules and limits

- Composition, graph, medium, organization, memory, three scale meanings, control, resources, evaluation extent, outcome, and limit are coded separately. Evaluation counts (tasks, trials, seeds, calls) are kept out of the cumulative-agent field; identity totals such as accounts are marked as proxies.
- NR means not reported in the extracted evidence, not necessarily absent from the complete primary source.
- Logical populations, sequential roles, cumulative sessions, registrations, and configured capacity are kept apart where the evidence permits. Model mixtures, memory, topology, and organization often change together; their effects are not separated by inference when a source lacks a control.
- Outcomes with different metrics are not pooled. There is no independent dual coding.

## Primary-source pass

For the November edition, every number quoted from a post-cohort addition was re-read at its primary source on 14 November 2026 (UTC) and checked again against the methods, tables, and appendices named in an independent review on 15 November. `source-provenance.json` lists each URL with the SHA-256 of the retrieved bytes. The Agensh replay counts are reproducible with the script in `reproducibility/agensh-replay/`.

| Key | Version read | Quoted facts checked | Result |
|---|---|---|---|
| `anthropic-fable-team-scaling` | Blog post, 9 Nov 2026 | 1,000 agents (one lead, 999 helpers); 28.7 h; one-third of the output tokens and one-seventh the proof length of the September formalization, which also supplied 47 lemmas; coordination only through Postgres and Git; 36,612 writes and 311,734 reads by hour 30; about 750 helpers on Langlands–Tunnell; 2,418-task tree; restart near hour 18 | Read in full. |
| `openai-peers-unauthorized-access` | Report; incident 19 Jul, updated 10 Nov 2026 | 17,960 agents in two ExploitGym runs; 285 attempted posts (1,361 calls); 79 agents read 35 messages from other runs; five root executions in CI workloads; no coordinating agent | Read in full. |
| `avalon-m1` | Technical report (81 pp.), "model still training" | Equal-output-token control B8/S8: FrontierScience 63.5/55.5 (160 tasks x 1); SWE-Bench Pro V2 (Hard) 23.5/37.3 (51 x 1); IMO-ProofBench-Advanced 37.5/37.7 (30 x 4, 0-7 proof grade as percent); plans 71->31% and 16->54%; reporting 77->20->0-3% | Confirmed. No printed date; IMO values are close means, not established equivalence. |
| `parallel-agent-teams` | arXiv v1, 6 Nov 2026 | 10 of 12 tasks; all four tasks with a 100-agent team; equal dollar cost: 4 of 8 tasks versus GPT-5.6 Sol; teams of 64 and 100 saw only the newest 100 forum titles and unread posts | Confirmed; best-of results under a verifier. |
| `coding-team-compute-allocation` | arXiv v1, 12 Oct 2026 | 3-7x cost; planning-only delegation at about half the cost; 47.5% of the gain for 13.9% of the extra cost; 1.4 points at 70% lower cost | Confirmed. |
| `scalemas-substrate` | arXiv v1, 12 Oct 2026 | 55.1/46.8/38.0 (Table 2); 60.0 vs 26.0 at about 20M tokens; up to 128 agents | Confirmed. Not the first shared-versus-private comparison (LLMA-Mem has one). |
| `mpt-self-orchestration` | arXiv v2, 19 Oct 2026 | 21.0+-4.1% vs 9.0+-2.1% on 50 held-out questions, three runs each; 41.5 vs 25.4 on 32 seeds | Confirmed. |
| `s3-swarm-scaling` | arXiv v1, 5 Nov 2026 | More than 20x online SFT at eight agents (trained with four); advantage persists through twelve; all methods struggle at sixteen; repeated work nearly halved | Confirmed; the paper quotes the localized result. |
| `waggle-2026` | arXiv v1, 28 Sep 2026 | Over 96% of substrate-specific oracle quality; transfer as populations and budgets change | Abstract-level. |
| `persistent-memory-controlled-ablation` | arXiv v1, 6 Oct 2026 | +0.015 [-0.011, +0.046]; 14.3 vs 35.5 / 35.3 MiB | Confirmed. |
| `multi-agent-transactive-memory` | arXiv v2, 15 Oct 2026 | 77.82% index share and 25.6% of best-ranker retrievals; 31 producers with 1.4% of the index supply 40.7% (31.8% pooled) | Confirmed (Appendix H). |
| `collabmem-2026` | EMNLP 2026, pp. 27343-27356 | TMS-GRAPH++ averages 69.6% over five evaluation splits; 85.7% on the 1,118 core probes under loose scoring; 58 core scenarios | Confirmed; DOI from the Anthology record. |
| `gemini4-argon-minecraft` | arXiv v1, 15 Oct 2026 | Four agents; 27 h 14 min; 2,783 programs; 605 deaths; chat and shared memory, no assigned roles | Abstract-level; one run. |
| `parallact-shared-codebases` | arXiv v1, 30 Oct 2026 | 62% vs 16%; awareness 26%, not significant | Confirmed. |
| `inbox-coordination-primitive` | arXiv v1, 26 Oct 2026 | Up to 16,000 simulated agents; agents shown the same information share one model answer, so a 16,000-agent run makes 6-23 model calls; 97% already-rejected proposals in a separate 20-negotiation experiment | Confirmed; simulated society with reused answers. |
| `network-topology-consensus` | arXiv v1, 22 Oct 2026 | 10^3-10^5 agents running policies extracted from four LLMs; median critical mass 3% / 16% / 35% | Confirmed; surrogate population. |
| `believed-but-not-said` | arXiv v1, 15 Oct 2026 | Final private infection: share of benign agents whose private probe answer at the last step is false, averaged over 18 model-dataset cells: 44.8% (one adversary), 60.5% (three); 51.6% held vs 19.7% endorsed in exposed turns | Confirmed; a probe, not a hidden-state reading. |
| `herding-runaway-cascades` | arXiv v1, 22 Oct 2026 | 48 Suno songs as titles and lyrics; runaway cascades with rare self-correction; human Music Lab as a qualitative benchmark only | Confirmed; no controlled human-LLM estimate. |
| `cooperation-without-adaptation` | arXiv v1, 16 Oct 2026 | Six players, ten rounds; 20.0 vs 5.0 payoff per seat; different sets of four models contribute at positive and at zero risk; an own-payoff instruction reduces zero-risk contributions for most models | Confirmed. |
| `collaboration-serving-users` | arXiv v1, 20 Oct 2026 | Worse in 12 of 13 mechanically valid cells; thirteenth +2.7 [-6.7, +12.7]; no cell met the fidelity bar (680 of 2,744 write orders, 25%) | Confirmed; limited to this division of labor. |
| `multi-agent-loss-of-control` | arXiv v1, 16 Oct 2026 | 7% vs 87% of successful attacks flagged by a GPT-5.6 Sol monitor | Abstract-level. |
| `inter-agent-influence` | arXiv v1, 3 Nov 2026 (NeurIPS 2026) | Five environments; in the three oversight environments all tested models moved overseers from rejection to approval | Confirmed. |
| `collusion-j-space` | arXiv v1, 1 Nov 2026 | 86% vs 33% on NARCBench with DeepSeek-V4-Flash | Confirmed; representation analysis. |
| `voluntary-collusion-secret-tools` | arXiv v2, 5 Oct 2026 | Unfair framing (V0): Sonnet 4.5 0% for both tools, Gemini 2.5 Flash 100% (channel) and 98+-2.7% (hint); neutral framing (V1): Sonnet 4.5 100% and 49+-8.2% | Confirmed (Tables 2-3). |
| `swarmevolve` | arXiv v1, 5 Nov 2026 | Median 4-8 minutes with Qwen3-8B, 3-6 with larger models, to reach the 60-minute scores of text frameworks; 21 problems | Confirmed; CC BY-NC-ND, no figure reproduced. |
| `moltbook-collective-behavior` | arXiv v2, 7 Oct 2026 | 4,189,979 posts; 19,617,496 comments; 184,909 active agents; exponent about 0.79; about 85% coverage after June; 0.49% of posts with about 62% of comments excluded from tree analyses | Confirmed. |
| `worse-together` | arXiv v1 (30 Sep) and blog (11 Nov 2026) | API key 30/12% vs 64/32% of optimum; personal assistant 94-99 / 47-67 / 56-68 vs 19-36% | Confirmed; the two versions list different affiliations. |
| `google-science-of-scaling-agents` | Blog, 28 Jan 2026 | 180 configurations; Finance-Agent +80.9%; PlanCraft -39 to -70% | Confirmed; the journal version (Kim et al.) reports 260 configurations. |
| `ord-swarm-scaling` | LessWrong post | lambda 0.68 / 0.57 / 0.48 from regressions on OpenAI charts | Confirmed; estimates from curves, not a matched-budget run. |
| `yc-agents-in-games` | Project page, Oct 2026 | Civ50: 50 GPT-6.1 Sol agents, 3 h, about 5,900 messages | Confirmed. |
| `agensh-1024` | arXiv v1 and the authors' published replay | Paper: pandoc 33.89->55.06%, five-task mean 19.31->28.78%. Replay (45,518,428 bytes, SHA-256 4543d032...): 11,111 PR creations, 2,800 merges, 148,079 board writes with 56,472 labelled FAIL, peak 1,020 non-idle identities per displayed 37.5-s bin | Recounted; see reproducibility/agensh-replay/. Non-idle is not simultaneous model inference. |
| `steering-information-networks` | arXiv v1 9 Nov; v2 10 Nov 2026 | Withdrawn by its authors | Not used. |

## October 2026 coding (dated record)

The 57 inherited units were coded in October 2026 from the research collection's chapters and source cards; their locators remain in the per-unit provenance. Corrections made then, after checks against primary papers and the retained cards:

- `coherence-driven-contagion`: 36°C is the value in the belief statement "Tomorrow it will be T°C in Boston" (arXiv:2610.02654v1, §3.2 and Table 4), not a sampling temperature.
- `hf-incident-case`: the headline "more than 70,000 messages and files" is attributed to METR; about 1,200 cumulative participants used the board on 8–13 July, about 700 of whom joined the attack.
- `opus55-card`: the ProgramBench comparator is five peers versus one agent; the token ratio is a plot reading.
- `deepmind-cheating-whistleblowing`: the 100-agent denominator is stated next to the 14 cheaters and 24 whistleblowers.
- `brockers-opinion-dynamics`: effect strength and explanatory power are separated, keeping the primary text's "tends to surpass" hedge.
- `wiki-copying`: the two hours are the median first-to-last edit span per handle.
- `einsteinarena`: the limit adds the SimpleTES Erdős result from the authors' footnote 4.
- The debate freeze in the homogeneous-panel study is described as triggered by behavioral signals.
- Appendix C keeps raw inventory values; for eight rows whose number is not a count from one experiment, a bracketed qualifier from the snapshot's own scale note follows the value (Agensh, Cursor, Colosseum, Physics of Agents, PIMMUR, the enzyme campaign, Anthropic's internal platform, and Navier–Stokes).
