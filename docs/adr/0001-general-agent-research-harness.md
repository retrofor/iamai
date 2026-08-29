---
status: accepted
---

# Make the general-agent research harness the product north star

iamai 1.0 is a stable messaging Runtime, while its model and tool helpers are provisional. We will add a headless, record-first `iamai.harness` whose core flow is `Task → Agent → Environment → Trajectory → Evaluation`; its execution model does not construct or use Runtime, Adapter, Plugin, Event, SessionManager, or any LLM provider, and the stable 1.x types retain their existing meanings and integrate only through a later messaging bridge. AGI is the research north star, not a release claim: every claim about progress or generality must identify the Task and Environment distribution, seeds, budgets, Agent and Evaluator versions, and baseline.
