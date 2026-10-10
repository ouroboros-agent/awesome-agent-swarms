---
page: glossary
title: Glossary
nav: Glossary
lead: Terms the survey uses in a narrow sense.
---

- **Agent** — a model that takes successive actions, using tools or exchanging messages, and incorporates the responses. A single chat call without that loop is not an agent in this survey.
- **Swarm / agent team / multi-agent system** — two or more agents on one task who can influence one another. The three names cover that class here; "swarm" is the usual word for many peers, "team" for a small group with roles.
- **Orchestrator (lead agent, "conductor")** — an agent that splits a task, hands out subtasks and collects the results. Some systems train it separately: PARL in Kimi, Conductor at Sakana.
- **Subagent (helper)** — an agent that another agent launches on a subtask, usually with a clean context. What comes back is a short summary, not the whole transcript.
- **Time-matched / compute-matched** — two different comparisons of a swarm with a single agent, distinguished by which quantity is held fixed. Time-matched holds wall-clock time fixed, and token spend may differ. Compute-matched holds the total token budget fixed, and elapsed time and each agent's share may differ. An earlier finish, or a higher token spend, is the outcome of a particular comparison, not a consequence that follows from the match itself. A result in this survey is not readable until the text says which quantity was held fixed.
- **λ (the "stepping on toes" exponent)** — a parameter Toby Ord carried from labour economics to agent swarms: N workers produce as much as one worker does in N^λ times as long. λ = 1 is a lossless split of the task; λ = 0.5 means a hundred agents equal one agent working ten times longer. The λ values for GPT-5.6 Sol are Ord's estimates from OpenAI's charts (Ch. 4). In the formula λρN/T in Ch. 9, λ means something else: conformity, not the return to parallel labour.
- **Attractor** — a state a conversation or a group converges to wherever it started. Copies of one model with no assigned task have an attractor of their own, different for each model.
- **Echo / effective team size** — echo is the tendency of copies of one model to repeat and amplify one another. Effective team size is how many independent voices actually stand behind N agents. In the measured case of 30 debating copies, it lay between 1 and 1.8.
- **Collusion** — coordinated action by agents that gets around a rule or a monitor, in the open or through a covert channel. "Collusion in deed, not in word" shows up in actions and not in the messages.
- **Monitor** — a model or a rule that inspects agents' actions before or after they run. Checking each agent alone is worse at catching an attack split across several of them.
- **Reward hacking** — an agent gets a high score by deceiving the evaluator rather than by solving the task. According to Anthropic, a variant trained this way attacked in a simplified replica of the Hugging Face attack, and the released models did not. Anthropic does not name reward hacking as the confirmed cause of that difference.
- **Lean** — a language and system for formally checking mathematical proofs. "Verified in Lean" means the machine accepted every step, not that a person read the proof and agreed.
- **System card** — a developer's document shipped with a model: what was measured, what was found, which risks were named. It is the authors' self-report, and the document itself is not a peer-reviewed paper.
- **Preprint** — a scientific paper posted before peer review or without it, usually on arXiv. Versions are numbered, and the numbers in them may differ.
