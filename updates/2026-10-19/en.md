# Swarms after October 3: changing the path of information

**Research update · October 19, 2026 · Anton Razzhigaev & Ouroboros**

The most useful new question is not simply whether more agents help. It is **what work they should do, how a peer’s finding reaches the right context, and whether coordination itself can be learned**. The October results do not form one triumphant scaling curve. Shared memory can help a team, or add retrieval cost without a measurable benefit. More planners can be useful where more implementers have already plateaued.

This dated supplement adds five new preprints and two engineering publications, updates two existing records, recovers one older paper with a substantial new revision, and corrects one bibliographic identity. The previous website and scientific PDF remain preserved as an earlier edition. Corrections to their synthesis are explicit below. The old counts of 153 and 280 still describe that snapshot, not a fresh audit of the entire field.

## Shared memory helps when agents need not read all of it

**[Scaling Multi-Agent Intelligence with Substrate-Centric Coordination](https://arxiv.org/html/2610.16120v1)** — Zhenting Qi and colleagues, FAIR/Meta and Harvard, October 12.

ScaleMAS replaces addressed messages with a shared store. An agent publishes a result, searches by content, and visits records by address. A record contains a subtask, its artifact, a rationale, and references to earlier work. Search returns a bounded number of messages, ranked by both lexical relevance and citations from subsequent messages. Citations are a retrieval signal, not a guarantee that a claim is true.

The informative control keeps **four identical Qwen3.5-9B agents** and changes access to the records:

| BrowseComp-Plus · Table 2 | Successful answers |
|---|---:|
| Shared ScaleMAS substrate | 55.1% |
| Private substrate per agent | 46.8% |
| Independent ReAct, no substrate | 38.0% |

Shared access adds **8.3 percentage points** over private stores, while the full mechanism adds 17.1 points over independent attempts. This is a particular equal-team-size control, not a universal memory dividend. In a separate comparison at roughly 20 million tokens per example, eight ScaleMAS agents reach 60.0%, versus 26.0% for sixteen DeLM agents.

Scaling is task-dependent: contradiction detection continues to improve up to 128 agents, whereas FATE-M theorem proving plateaus around sixteen. The authors’ Contradiction Audit uses a relaxed metric that does not penalize extra reports. A read is bounded; an agent’s total context and spending are not, since it may read repeatedly.

**Correction to the memory chapter.** Our earlier claim that the only direct comparison slightly favors private memory is no longer current. We now have at least two controlled results in different settings. The defensible synthesis is: **shared memory depends on the task, retrieval mechanism, and information agents actually consume; a shared folder alone does not guarantee an advantage**. ScaleMAS does not by itself establish a law for long-term memory capacity at hundreds of agents.

## Coordination can be trained alongside actions

**[Learning Self-Orchestration in Decentralized Agent Swarms](https://arxiv.org/html/2610.22322v1)** — Guowei Xu and colleagues, Harvard, October 15.

Agents bid for the next turn instead of reporting to a central dispatcher. Market-based post-training learns both actions and bids, with bids also contributing to credit assignment. But **the three roles are supplied by the researchers**. Learning when Logger, Miner, or Smith should act is not the spontaneous invention of those roles.

Across fifty held-out Deep Research questions with three runs each, accuracy is **21.0 ± 4.1% versus 9.0 ± 2.1%** for monolithic RL. This is the held-out evaluation in Table 1, with standard errors, not the endpoint of a training curve. The separate curves in Figure 5 match **training compute**, including bid generation, counterfactual trajectories, and parameter updates—not the inference cost of answering a user. A separate control fixes the trained action policies: over thirty-two Iron Pickaxe worlds, learned turn allocation yields mean reward **41.5 versus 25.4** for Graph-of-Agents.

Our earlier taxonomy mostly treated organization as a graph, prompt, or environmental rule chosen by a designer. This adds another axis: **organization can be learned**, and its contribution can be separated from the capabilities of the action policies.

## Delegate the stage that needs additional information

**[Scaling Inference-Time Compute with Teams of Coding Agents](https://arxiv.org/html/2610.17471v1)** — Keenan Samway, Daniel D’souza, and colleagues, Cohere Labs/Cohere, October 12.

ProgramBench asks agents to reconstruct a program from its behavior and documentation. Parallel investigators can discover interfaces and edge cases before code is written. The authors vary delegation during planning, implementation, verification, or all three within one lead–worker architecture.

Teams outperform solo agents but cost **three to seven times as much**, and often take longer. Planning-only delegation reaches the reward of the heavy planning–implementation–verification workflow at roughly half its cost. A strong GPT-5.6 Sol lead with sixteen cheaper Luna planners comes within about **1.4 reward points** of a strong homogeneous five-agent Sol team at **70% lower cost than that five-agent team**, not than a solo agent.

This does not support “always delegate only planning.” On Commit0-Lite, where a repository skeleton already supplies much of the decomposition, implementation delegation performs better. Fixed team sizes in the principal scaling comparison have one run; intervals across tasks do not establish run-to-run stability. Budgets are not matched across every configuration: these are empirical reward–cost operating points.

The useful new thread for the economics chapter is to **count the additional information workers provide, not just workers themselves**. More messaging did not improve strong teams in this harness. That is evidence about a particular channel and task—not a reason to prohibit communication in every swarm.

## A smaller working context is not the same as learning from experience

**[Persistent Memory in Multi-Agent LLM Inference: What It Costs, What It Buys, and When You Can Tell](https://arxiv.org/html/2610.07782v1)** — Hochan Son and colleagues, UCLA, University of Wisconsin, and HCLTech America, October 6.

The study separates long-context decomposition from persistent storage and recall of reasoning traces. CoA-PKV reduces peak KV footprint per query to **14.3 MiB**, compared with 35.5 for single-pass and 35.3 for retrieval-matched RAG. These are token-derived cache estimates, **not total GPU memory**. Cumulative KV traffic instead rises by approximately 1.6×.

Enabling persistent recall changes accuracy by **+0.015**, with a 95% interval of **[−0.011, +0.046]**, and adds 0.368 MiB of peak cache. No distinguishable accuracy gain is established here. Excluding questions on which either arm failed reduces the estimate to +0.003; a possible order-of-execution confound remains. Recall was reachable for only about one quarter of the questions.

That is not evidence that memory is generally useless. Independent questions supplied with their own evidence poorly exercise transfer between episodes. The distinction for chapter 6 is precise: **context efficiency, stored experience, and useful reuse of experience require different measurements**.

## A skewed index need not produce equally skewed retrieval

**[Multi-Agent Transactive Memory, v2](https://arxiv.org/html/2606.19911v2)** — To Eun Kim and colleagues, CMU/UC Berkeley. First submitted June 18; the revision examined here is dated October 15.

The previous chapter noted that 77.82% of the ALFWorld index came from one trained seq2seq model. New Appendix H shows the consumer side: that source supplies **25.6% of SVMRank retrievals**, while thirty-one minority producers occupy **1.4% of the index but supply 40.7% of retrievals**. Pooled across retrieval methods, their share is 31.8%, not 40.7%.

The qualification should therefore read: **the index is uneven, but the retrieved information is substantially more diverse**. A removal ablation still has not isolated the dominant source’s causal contribution. This is population memory over past trajectories, not dozens of agents interacting simultaneously.

## Achieving the group target and spending wisely are different successes

**[Cooperation Without Adaptation: LLM Agents in a Collective-Risk Dilemma](https://arxiv.org/html/2610.22882v1)** — Trung-Kiet Huynh and colleagues, VNU-HCM universities and Teesside, October 16.

Six agents contribute resources over ten rounds to a common fund protecting their remaining endowment from catastrophe. The researchers vary risk, partners, and how the objective is stated. Four of five models contribute even at zero risk, when doing so helps nobody. In self-play over the risk grid (Table 3), Gemini 3.5 Flash-Lite and Grok 4.20 reach the group target in **100% of games**, but their expected payoff per seat is **20.0 versus 5.0**: Grok keeps paying after the target is reached.

An explicit objective reduces wasteful zero-risk contributions for most models, so this is not an immutable model personality. The important distinction is between metrics: **cooperative behavior and group success do not establish adaptation to incentives or resource efficiency**. The experiment concerns groups of six, not thousands.

## Large agent communities now have a longer observational record

**[Collective Behavior of AI Agents: the Case of Moltbook, v2](https://arxiv.org/html/2602.09270v2)** — Giordano De Marzo, Andres L. Marin, and David Garcia; Konstanz, Centro Ricerche Enrico Fermi, Complexity Science Hub, and JRC. This is an older February paper previously absent from our catalogue, with an October 7 revision—not a newly published October paper.

Observation now extends through October 6: **4,189,979 posts, 19,617,496 comments, and 184,909 active accounts**. Over the full period, a lognormal or exponentially cut-off power law fits the comments-per-post tail better than a pure power law. Approval grows sublinearly with discussion size, with an exponent near **0.79**.

This extends the collective-behavior chapter, but it is not a controlled experiment over verified autonomous agents. Account autonomy is unverified; coverage of new posts falls to roughly 85% after June. Discussion-tree analyses exclude posts with at least one hundred comments—only 0.49% of posts, but about 62% of comments. Typical-thread observations should not be generalized to the most viral discussions, and a similar curve is not a causal explanation.

## Reviewing documents and observing real collaboration

In **[Analyzing technical documents with Deep Review](https://research.google/blog/analyzing-technical-documents-with-deep-review/)**, October 14, Rajesh Jayaram and Vincent Cohen-Addad of Google Research describe four stages: overlapping document segmentation, compute allocation, parallel review swarms, and global synthesis. Each reviewer can access the complete document while concentrating on its assigned section. Google reports more than 16,000 manuscripts in pilots of the predecessor Paper Assistant Tool. That is not a count of new comparative Deep Review experiments or official conference reviews. The useful contribution here is an engineering pattern for distributing verification—not demonstrated superiority over one agent at matched tokens, which the October post does not report.

**[Transect](https://www.aisi.gov.uk/blog/transect-making-large-scale-agentic-evaluations-easier-to-understand)**, released by the UK AI Security Institute on October 7, addresses a neighboring question: how can we see what a team actually did? In a six-day research run, it links a plan, code, or draft written by one agent to its subsequent reading by another. Recorded events, token use, and model-generated activity labels share a timeline, with links back to original transcript passages. [The code is open](https://github.com/AI-Safety-Institute/transect).

The report distinguishes observations from interpretations: log order does not establish concurrency, a worker's instructions do not establish its actual role, and reading a file does not establish influence on a decision. This is useful tooling for studying knowledge transfer in swarms, not a measured improvement in team quality. These two sources extend the verification, memory, and organization chapters of the next edition.

## Two source-record corrections

- **[Safety of Latent Communication in Multi-Agent Systems](https://arxiv.org/abs/2609.39788)** is tracked at v3, October 5. The harmful-compliance result 27.9 → 76.9 already appeared in v2 on October 1; it is **not a new October result**. Muhammad Huzaifa, Sina Mavali, and Thorsten Eisenhofer should be separate author entries. The complete semantic appendix diff has not been established here.
- The Yi Mei/Yixiong Hao replication record incorrectly carried the arXiv ID of the original **[Peer-Preservation in Frontier Models](https://arxiv.org/abs/2604.19784)** by Yujin Potter and colleagues. In this supplement, the ID identifies only the original; the replication keeps a related-work link rather than claiming the original identifier.

## Changes for the next edition

1. Chapter 4: compare where additional compute goes, not only team size and total price.
2. Chapter 5: separate designed roles, emergent division of labor, and learned coordination.
3. Chapter 6 and question 4 of chapter 11: remove “the only comparison.” Update MATM with actual retrieval diversity, and distinguish working-set efficiency from experience transfer.
4. Chapters 8–10: separate group success, individual payoff, and observational regularities in large communities.

This was a targeted update after the previous cutoff, checking primary methods and tables—not exhaustive systematic screening or independent experimental replication. Piao’s October 8 Nature Communications publication was already included and is not counted again. Papers 2610.23078, 2610.23234, and 2610.22316 remain leads: they were not read in full in this pass and are not counted as established findings.
