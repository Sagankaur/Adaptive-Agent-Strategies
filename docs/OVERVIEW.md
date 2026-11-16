# Overview for Prof. Abdelrazek

Sagandeep Kaur, 2026-10-20. Dates and GPU-days (24 hours of one graphics processing unit, GPU) are estimates.

**The one urgent ask.** Please tell us which GPU we can use by 2026-11-16, so that a run host is ready by 2026-11-30 (Q5 below). Everything else can wait until 2027-01-11 or 2027-03-01.

## The problem

A small open-weight model runs on one local GPU and solves terminal tasks, such as fixing a build or configuring a server. It follows a *strategy*: a typed set of fields for exploration, planning, tool policy, memory, verification, recovery and short free-text notes. Today that strategy is hand-written and never changes. We test whether editing it from the agent's own failed runs helps. For example, if the logs show commands that time out once and then succeed, an edit could raise `recovery.max_retries` from 1 to 2. The question that matters is cost: can a cheap local model improve itself more cheaply than just sampling more answers and picking one? The paper will report one line: the adapted strategy's gain over each baseline on unseen tasks, with a confidence interval, at the same compute per task, and its cost in dollars per task.

## Closest work and what is new

Close work exists. A frozen Qwen3.5-35B-A3B already improves its own harness on Terminal-Bench ([Self-Harness, arXiv 2606.09498](https://arxiv.org/abs/2606.09498)). [MetaRSI (arXiv 2609.06396)](https://arxiv.org/abs/2609.06396) applies typed operators to a self-hosted Qwen3.5-35B-A3B on Terminal-Bench 2.1, with frozen weights only in its harness-only condition. Among the harness-evolution methods we checked, none compares itself with best-of-N at matched compute. One evaluation study does: with frontier API models, harness evolution did not beat best-of-N sampling or sequential refinement at a matched budget on Terminal-Bench 2.1 ([Wang et al., arXiv 2607.12227](https://arxiv.org/abs/2607.12227)). Paper 1 asks that matched-compute question for a small, locally served model with a typed, compiled strategy, on held-out tasks, and makes no "first" claim.

What is new: best-of-N and reflection-retry baselines matched per task on held-out tasks; a random-edit control in the same edit space; a unit test for every field that is enforced in code; an enforced-versus-advised contrast; cost per task for every arm; and a pre-registered analysis. Novelty risk: the contribution is the test, not a new method. If the adapted strategy does not beat best-of-N, that is a valid, reported result. Details: [PRIOR_WORK.md](PRIOR_WORK.md) and [LITERATURE_MAP.md](LITERATURE_MAP.md). The risks to the project, with triggers and fallbacks, are in [RISK_REGISTER.md](RISK_REGISTER.md).

## Terms

| Term | Meaning |
|---|---|
| Episode | One agent attempt at one task, with one pass or fail |
| Arm | One condition in the comparison, for example the fixed strategy or best-of-N |
| Best-of-N | Run the fixed strategy N times and let a judge pick one answer |
| Reflection-retry | The agent checks its own work and retries inside the same attempt |
| Matched compute | Each arm gets the same model compute per task, so no arm wins by spending more |
| Held-out | Tasks never used while adapting; used once, in the final run |
| Seeded split | A random division of tasks into pools, fixed by a seed |
| Compiled field | A strategy field that changes the controller code, with a unit test. Other fields are only advice in the prompt |
| Pre-registration | Hypotheses and analysis frozen in a signed git tag before the data that tests them exist. Stage 1 is the first tag |
| Gate (G-INFRA, G0) | A checkpoint that must pass before the next phase starts |
| Floor | The smallest GPU budget that still answers the main question |
| Portability check | The fixed strategy run on a consumer-class machine. "Emulated" means the main GPU limited to 8 GB of memory |
| Contested task | A task solved in some runs but not all |

More terms: [GLOSSARY.md](GLOSSARY.md).

## Paper-1 research questions

| RQ (research question) | Question | Status |
|---|---|---|
| RQ1 | Does the adapted strategy beat a fixed strategy, random edits, reflection-retry and best-of-N at matched compute per task? | Paper 1, confirmatory |
| RQ2 | Do gains hold on tasks from another source? Adapt on terminal-bench-pro (TB-Pro), test on all 89 Terminal-Bench 2.0 (TB2) tasks (Q3) | Paper 1, same test as RQ1 |
| RQ3 | Does a second-order loop, which changes how the strategy is edited, add to the gain? | Paper 2 by default (Q4) |
| RQ4 | Which strategy dimensions account for the gains? | Paper 1, exploratory |

RQ1 and RQ2 share one test: the final run on all 89 TB2 tasks. RQ2 is the cross-source reading of the same estimate. It cannot separate transfer from the effect itself, and the paper says so.

## Your six meeting points

| Point | How it is handled | Where |
|---|---|---|
| 1. "baseline cost : task" | Cost per task for every arm (Table 4), never cut | [EXPERIMENTS: E3, cost table E3-COST](EXPERIMENTS.md#e3-confirmatory-run-on-tb2-89); [PAPER_PLAN 6.1, Table 4](PAPER_PLAN.md#61-main-text-tables) |
| 2. "benchmark : task" | 89-row per-task table; all TB2 tasks held out (Q3) | [EXPERIMENTS: E3](EXPERIMENTS.md#e3-confirmatory-run-on-tb2-89); [PAPER_PLAN 7](PAPER_PLAN.md#7-appendices) |
| 3. "strategy adapt" | The core: adaptation with two seeds, compared with four baselines in a pre-registered sequence; the code-edit baseline is optional | [EXPERIMENTS: E2](EXPERIMENTS.md#e2-adaptation-loops) |
| 4. "intelligence index" | Your reading needed (Q1); every variant is computed from existing logs, with no extra episodes | [EXPERIMENTS: E11](EXPERIMENTS.md#e11-adaptation-efficiency-index) |
| 5. "strategy switching" | Your reading needed (Q2); per-task choice is computed from existing logs, with no extra episodes | [EXPERIMENTS: E4-SW](EXPERIMENTS.md#e4-sw-offline-strategy-switching) |
| 6. "small models on terminal bench" | Local open-weight model first; portability check, never cut (Q5, Q6) | [EXPERIMENTS: E-PORT](EXPERIMENTS.md#e-port-portability-check) |

Full mapping: [PAPER_PLAN section 11](PAPER_PLAN.md#11-where-the-six-meeting-points-are-answered).

## Current state

| Exists | Has not run |
|---|---|
| Strategy schema, adaptation-round interface, local-model client, offline tests on a toy environment | No model has been called |
| Three baselines as drafts; a repair is planned ([DESIGN_REVIEW M8](DESIGN_REVIEW_2026-10.md#m8-baseline-repair)) | No agent has run on any benchmark |
| 89 TB2 task ids and a seeded split (commit `92c1621`); Q3 proposes to replace this split | TB-Pro tasks not examined; no GPU granted |
| Design review of 2026-10-20 ([DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md)) | |

**Main uncertainties.**

- TB-Pro: whether its tasks build and run here, and whether its licence allows our use. The plan depends on it most.
- GPU: whether one is granted, and when.
- Throughput: the real episodes per GPU-day, measured only at G0.
- Model fitness: whether the local model solves enough TB-Pro tasks to adapt on.
- Power: the comparisons with reflection-retry and best-of-N (H3, H4) may be too small to detect.

Each of these is a rated risk with a trigger and a fallback in [RISK_REGISTER.md](RISK_REGISTER.md).

## Next three gates

| Gate | Week of | Condition |
|---|---|---|
| G-INFRA | 2026-12-28 | Harness and baselines pass tests; a 5-task TB-Pro smoke run has no harness errors |
| G0 | 2027-01-11 | TB-Pro calibration sets model fitness, measured throughput and what fits the GPU-days |
| Stage-1 tag | 2027-03-01 | Unit tests for compiled fields pass; pre-registration signed; unanswered questions take defaults |

Dates assume 20 hours per week and a run host from 2026-11-30 ([EXECUTION_PLAN.md](EXECUTION_PLAN.md#4-gates)).

At 20 hours per week the plan needs about 31 weeks (draft paper 2027-05-23, estimate) against the 24-week default. Finishing in 24 weeks needs about 28 hours per week, a later end date, or cuts ([DECISIONS plan item 1](DECISIONS.md#plan-item-1-duration-start-date-hours-per-week-and-supervision-rhythm)).

## Decisions needed from you

This is the same list as [DECISIONS.md, section 1](DECISIONS.md#1-open-decisions), ordered by date. The options, costs and full defaults are there.

| Q | Question | Default | Answer by |
|---|---|---|---|
| Q5 | Which GPU | Plan the full core | **2026-11-16** |
| Q5 | GPU-days | Halt at G0 if below the floor | 2027-01-11 (G0) |
| Q5 | A consumer machine | Portability check emulated on the main GPU | 2027-03-01 (Stage 1) |
| Plan item 1 | Internship length, hours per week, meeting rhythm | 24 weeks part-time stays the target; schedule assumes 20 hours per week | 2027-01-11 (G0) |
| Q3 | Replace the committed split with all 89 TB2 tasks held out | Approve | 2027-03-01 (Stage 1) |
| Q4 | Second-order loop, AppWorld transfer and rollback to paper 2 | Paper 2 | 2027-03-01 (Stage 1) |
| Q2 | Meaning of "strategy switching" | Per-task choice only | 2027-03-01 (Stage 1) |
| Q1 | Meaning of "intelligence index" | Adaptation efficiency (best-of-N samples the adapted strategy is worth), plus payback in tasks | 2027-03-01 (Stage 1) |
| Q8 | A free-form code-edit baseline (B5) | Stays optional; runs only if budget and safety checks allow | 2026-12-28 preferred; 2027-03-01 at the latest |
| Plan item 6 | Same or stronger model for the diagnoser and proposer | Same model | 2027-03-01 (Stage 1) |
| Q6 | Fallback models | Stated order; keep the best local model if none passes | Only if the primary model fails at G0 (2027-01-11); then within one week |
| Plan item 11 | Venue and authorship | None | 2027-04-26; earlier if NeurIPS 2027 is wanted |

Options: [DECISIONS.md](DECISIONS.md#1-open-decisions).

## Compute request

| Item | Request |
|---|---|
| Research machine | 1 NVIDIA GPU with at least 24 GB (32 GB or more recommended for 2 or more parallel slots), 16 cores, 64 GB RAM, 500 GB NVMe disk (1 TB recommended), nftables available, dedicated during budgeted runs |
| GPU-days | About 45 dedicated (35 to 65 across the throughput uncertainty); floor about 29 |
| Portability machine | A consumer-class x86-64 machine with at least 8 GB of GPU memory (VRAM), 32 GB RAM and Docker |
| API (paid model service) budget | None for paper-1 arms |

GPU-days use a planning rate from a public laptop run, with a ±30% band. "Dedicated" matters: the rate assumes no other jobs share the GPU. Exact figures: [EXPERIMENTS.md](EXPERIMENTS.md#throughput-used-for-every-gpu-day-figure).
