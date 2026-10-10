---
page: glossary
title: Glossary
nav: Glossary
lead: Terms the survey uses in a narrow sense.
---

- **Agent** — a language model with tools (shell, browser, files, email) and a "think → act → observe the result" loop that works on a task over many consecutive steps.
- **Swarm / agent team / multi-agent system** — a group of two or more agents that work on one task and can influence one another. In this survey the three names refer to the same concept; "swarm" is more often used for many peer agents, "team" for a small group with roles.
- **Orchestrator (lead agent, "conductor")** — an agent that breaks a task down, hands out subtasks and collects the results; in some systems it is trained separately (PARL in Kimi, Conductor at Sakana).
- **Subagent (helper)** — an agent that another agent launches for a subtask, usually with a clean context window; it returns a brief summary.
- **Token** — the unit of text in which a model counts its input and output (roughly 3–4 characters of English text). Token spending is the main measure of cost and "compute" in this survey.
- **Context window** — the amount of text (in tokens) a model sees in one call; anything that does not fit has to be stored outside or compressed.
- **Time-matched / compute-matched** — two ways to compare a swarm with a single agent: over the same time period (the swarm spends more tokens) or at the same total of tokens (the swarm is faster, but each agent gets less).
- **λ (the "stepping on toes" exponent)** — a parameter that Toby Ord carried over from economics to agent swarms: N workers produce as much as one worker does in N^λ times as long. λ = 1 means perfect division of the task; λ = 0.5 means a hundred agents equal one agent working ten times longer. The λ values for GPT-5.6 Sol are Ord's estimates from OpenAI's charts (Ch. 4). In the formula λρN/T in Ch. 9, λ denotes a different quantity: conformity.
- **Attractor** — a state that a conversation or group converges to wherever it started; for copies of one model with no task, each model has its own attractor.
- **Echo / effective team size** — echo is the tendency of copies of one model to repeat and amplify one another. Effective team size shows how many independent voices actually stand behind N agents (for 30 debating copies, between 1 and 1.8).
- **Collusion** — coordinated action by agents that circumvents a rule or a monitor, either openly or through a covert channel; "collusion in deed, not in word" is collusion visible in actions but not in messages.
- **Monitor** — a model or rule that checks agents' actions before or after execution; checking each agent separately is worse at catching an attack split across several agents.
- **Reward hacking** — behaviour in which an agent obtains a high score by deceiving the evaluator rather than solving the task. According to Anthropic, a model variant trained this way attacked in a simplified replica of the Hugging Face attack while the released models did not; Anthropic does not name reward hacking as the confirmed cause of the difference.
- **Lean** — a language and system for the formal verification of mathematical proofs; "verified in Lean" means that every step of the proof has been accepted by the machine.
- **System card** — a document a developer publishes with a model release: what was measured, what was found, what the risks are. It is a self-report without external peer review.
- **Preprint** — a scientific paper posted before or without peer review (usually on arXiv); preprint versions are numbered, and numbers can differ between versions.
