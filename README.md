# Adaptive Intelligence: Self-Adapting Problem-Solving Strategies for AI Agents

This repository contains the implementation for **Project 2**. The goal is to investigate whether AI agents can learn from their own task history to improve their problem-solving procedures (planning, tool use, verification) on future tasks, without altering the underlying foundation model.

## Status

**Design review of 2026-10-20.** The plan was reviewed and its decisions frozen on 2026-10-20. Start with [`docs/OVERVIEW.md`](docs/OVERVIEW.md). The review is in [`docs/DESIGN_REVIEW_2026-10.md`](docs/DESIGN_REVIEW_2026-10.md), the decisions and open questions for Prof. Abdelrazek are in [`docs/DECISIONS.md`](docs/DECISIONS.md), and the risks are in [`docs/RISK_REGISTER.md`](docs/RISK_REGISTER.md). Where these files and the technical plan disagree, the 2026-10-20 files hold. No planned benchmark experiment or real-model episode has run. A one-task scripted Harbor smoke on Rohan passed using Apptainer 1.3.3; it validates the integration path only, not agent performance.

**Meeting of 2026-10-14.** Notes and follow-ups are in [`docs/MEETING_2026-10-14.md`](docs/MEETING_2026-10-14.md). The main change: the agent's model is a small open-weight model served locally. The primary is Qwen3.6-35B-A3B. Local fallbacks come before any API model, and GPT-5-mini is used only if Prof. Abdelrazek decides so. API spend for paper 1 is $0 ([`docs/DECISIONS.md`](docs/DECISIONS.md), Q6). Candidates are in [`docs/SMALL_MODELS.md`](docs/SMALL_MODELS.md).

**What exists.** The Phase 0 software, all of which runs offline:

- **Strategy object** (`strategy_schema/`). The typed, versioned strategy from the technical plan (section 3.2), with:
  - range validation;
  - JSON round-trip;
  - schema-checked edits of one or two operations, which create child versions;
  - a per-dimension `diff`;
  - `render()`, which produces the agent's instruction text.
- **Model interface** (`llm/`). A provider-agnostic chat interface, a scripted `MockModel`, and `OpenAICompatibleModel`, a standard-library client for any OpenAI-compatible chat-completions server: local servers for small open-weight models (Ollama, llama.cpp, vLLM, LM Studio) or hosted APIs. It returns the provider-reported token counts, refuses replies without them, and times each call. See [`docs/LOCAL_MODELS.md`](docs/LOCAL_MODELS.md).
- **Baselines** (`baselines/`). B0 (fixed strategy), B1 (reflection/retry) and B2 (best-of-N), run on a small custom agent loop. Each records:
  - model calls;
  - input and output tokens;
  - wall-clock time;
  - dollars, from a frozen price table: token prices, plus a compute rate per hour of model-call time for locally served models.

  B1 and B2 are driven by the agent's own checks only. B2 reports oracle pass@N separately, as an upper bound.
- **Environments** (`environments/`). A task/environment interface that keeps the agent's own checks apart from the hidden grade, and a **toy** text-manipulation environment used only to exercise the code.
- **Evaluation harness** (`evaluation/`):
  - seeded, stratified task splits (A/V/M/H) that are fixed once saved;
  - a runner that evaluates a strategy with a baseline on a split under a cost budget, writing one JSONL record per task;
  - a guard that refuses the held-out split outside the final evaluation.
- **Adaptation engine** (`adaptation_engine/`). The interface of one first-order round (run → diagnose → aggregate → propose → select → commit), with trivial rule-based components so it can be tested.

**What does not exist yet.**

- No run on any real benchmark. The TB-Pro route pilot and benchmark integration remain unfinished. Harbor 0.23.0 is installed on Rohan and passed one synthetic scripted Apptainer smoke; the planned five-task TB-Pro infrastructure smoke has not run.
- No run against a real model. The OpenAI-compatible client is tested only against a stub server, no model server or API has been called, and no result in this repository is about agent performance. The price entries for local models are placeholders without a compute rate.
- The agent loop reads only some strategy fields as behaviour; the others reach the agent only through the rendered instructions. The full `compile(strategy)`, with a unit test per compiled field, is gate G1, which must pass before Stage 1 of the experiments.
- No LLM diagnoser or proposer, and no B3/B4 baselines. The second-order loop has not been started.

Progress on Phase 0 is tracked in [`docs/PHASE0_CHECKLIST.md`](docs/PHASE0_CHECKLIST.md).

## Running the tests

The tests run in Docker, offline, as the calling user, limited to 1 CPU and 1 GB by default:

```
make test                   # builds the image, then runs pytest
make test CPUS=0.5 MEMORY=512m
```

## Directory Structure
* `/strategy_schema` - The versioned strategy object: fields, edits, diff, rendering, and the starting strategy S0.
* `/llm` - Chat-model interface, the mock model, and the client for OpenAI-compatible model servers.
* `/baselines` - The agent loop, baselines B0–B2, and cost accounting.
* `/environments` - Task/environment interface and the toy environment.
* `/evaluation` - Task splits, the evaluation runner, result records and the price table.
* `/adaptation_engine` - The first-order adaptation round. The second-order loop is not implemented.
* `/tests` - Offline pytest suite.

## Tech Stack
* **Agent Orchestration:** a minimal custom loop for now. Decided on 2026-10-20: a custom agent loaded into the Harbor harness process, with per-step JSONL logs. LangGraph is not used (DECISIONS.md, section 1.3, item 8).
* **Tracking & Logging:** JSONL result records. MLflow and LangSmith are planned but not set up.
* **Evaluation Benchmarks:** Terminal-Bench 2.0 held out, terminal-bench-pro for adaptation (see below).

## Documents
* [`docs/OVERVIEW.md`](docs/OVERVIEW.md) - Start here. A short overview of paper 1: the problem, the research questions, the current state, the next gates, the decisions needed and the compute request.
* [`docs/DESIGN_REVIEW_2026-10.md`](docs/DESIGN_REVIEW_2026-10.md) - Record of the 2026-10-20 design review of the technical plan, with each motion, its verdict and the evidence.
* [`docs/DECISIONS.md`](docs/DECISIONS.md) - Decision record: open questions for Prof. Abdelrazek, the decisions of 2026-10-20, and a log of deviations and defaults.
* [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md) - Each planned paper-1 experiment as a card, with its design, cost and decision rules.
* [`docs/EXECUTION_PLAN.md`](docs/EXECUTION_PLAN.md) - The experiments as a dated plan: order of work, effort estimates and dates.
* [`docs/PAPER_PLAN.md`](docs/PAPER_PLAN.md) - Plan of paper 1: contributions, section plan, figures and tables, pre-registration and candidate venues, with placeholders for results.
* [`docs/RISK_REGISTER.md`](docs/RISK_REGISTER.md) - Risks to paper 1, with likelihood, impact and mitigations.
* [`docs/GLOSSARY.md`](docs/GLOSSARY.md) - Research-methodology, statistics, cost and systems terms used in these documents, with examples.
* [`docs/LITERATURE_MAP.md`](docs/LITERATURE_MAP.md) - Map of the literature closest to paper 1, checked at the source.
* [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - Initial architecture and tooling plan.
* [`docs/TECHNICAL_PLAN.md`](docs/TECHNICAL_PLAN.md) - Detailed technical plan: strategy object, baselines, first- and second-order adaptation, evaluation design, budget, timeline and open decisions.
* [`docs/PRIOR_WORK.md`](docs/PRIOR_WORK.md) - Closest prior work and a comparison of candidate benchmarks.
* [`docs/PHASE0_CHECKLIST.md`](docs/PHASE0_CHECKLIST.md) - Status of each Phase 0 item, the snapshot-support check, and proposed benchmark pins.
* [`docs/LOCAL_MODELS.md`](docs/LOCAL_MODELS.md) - Pointing the agent loop at a locally served model, and how its cost is counted.
* [`docs/SMALL_MODELS.md`](docs/SMALL_MODELS.md) - Small open-weight model candidates, their published Terminal-Bench 2.0 scores, and what it takes to run them locally.
* [`docs/MEETING_2026-10-14.md`](docs/MEETING_2026-10-14.md) - Record of the 2026-10-14 meeting with Prof. Abdelrazek and the resulting follow-ups.

**Benchmark choice.** The architecture note names SWE-bench Lite and WebArena, and the technical plan proposed Terminal-Bench 2.0 with AppWorld for transfer. Both are superseded. The 2026-10-20 design holds out all 89 Terminal-Bench 2.0 tasks and adapts on deduplicated terminal-bench-pro, after a pilot. AppWorld moves to paper 2 by default. Prof. Abdelrazek still has to approve this (DECISIONS.md, Q3 and Q4).
