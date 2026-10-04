# Adaptive Intelligence: Self-Adapting Problem-Solving Strategies for AI Agents

This repository contains the implementation for **Project 2**. The goal is to investigate whether AI agents can learn from their own task history to improve their problem-solving procedures (planning, tool use, verification) on future tasks, without altering the underlying foundation model.

## Status

**What exists.** The Phase 0 software, all of which runs offline:

- **Strategy object** (`strategy_schema/`). The typed, versioned strategy from the technical plan (section 3.2), with:
  - range validation;
  - JSON round-trip;
  - schema-checked edits of one or two operations, which create child versions;
  - a per-dimension `diff`;
  - `render()`, which produces the agent's instruction text.
- **Model interface** (`llm/`). A provider-agnostic chat interface and a scripted `MockModel`. `ProviderModel` is the slot for a real client and refuses to run.
- **Baselines** (`baselines/`). B0 (fixed strategy), B1 (reflection/retry) and B2 (best-of-N), run on a small custom agent loop. Each records:
  - model calls;
  - input and output tokens;
  - wall-clock time;
  - dollars, from a frozen price table.

  B1 and B2 are driven by the agent's own checks only. B2 reports oracle pass@N separately, as an upper bound.
- **Environments** (`environments/`). A task/environment interface that keeps the agent's own checks apart from the hidden grade, and a **toy** text-manipulation environment used only to exercise the code.
- **Evaluation harness** (`evaluation/`):
  - seeded, stratified task splits (A/V/M/H) that are fixed once saved;
  - a runner that evaluates a strategy with a baseline on a split under a cost budget, writing one JSONL record per task;
  - a guard that refuses the held-out split outside the final evaluation.
- **Adaptation engine** (`adaptation_engine/`). The interface of one first-order round (run → diagnose → aggregate → propose → select → commit), with trivial rule-based components so it can be tested.

**What does not exist yet.**

- No run on any real benchmark. Terminal-Bench and AppWorld are not integrated, and Harbor is not set up.
- No real model client. No API has been called, and no result in this repository is about agent performance.
- The agent loop reads only some strategy fields as behaviour; the others reach the agent only through the rendered instructions. The full `compile(strategy)`, with a test per field, is Phase 1.
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
* `/llm` - Chat-model interface, the mock model, and the slot for a real provider client.
* `/baselines` - The agent loop, baselines B0–B2, and cost accounting.
* `/environments` - Task/environment interface and the toy environment.
* `/evaluation` - Task splits, the evaluation runner, result records and the price table.
* `/adaptation_engine` - The first-order adaptation round. The second-order loop is not implemented.
* `/tests` - Offline pytest suite.

## Tech Stack
* **Agent Orchestration:** a minimal custom loop for now. LangGraph is still under consideration; see the technical plan, open decision 8.
* **Tracking & Logging:** JSONL result records. MLflow and LangSmith are planned but not set up.
* **Evaluation Benchmarks:** under discussion (see below).

## Documents
* [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - Initial architecture and tooling plan.
* [`docs/TECHNICAL_PLAN.md`](docs/TECHNICAL_PLAN.md) - Detailed technical plan: strategy object, baselines, first- and second-order adaptation, evaluation design, budget, timeline and open decisions.
* [`docs/PRIOR_WORK.md`](docs/PRIOR_WORK.md) - Closest prior work and a comparison of candidate benchmarks.
* [`docs/PHASE0_CHECKLIST.md`](docs/PHASE0_CHECKLIST.md) - Status of each Phase 0 item, the snapshot-support check, and proposed benchmark pins.

**Benchmark choice is under discussion.** The architecture note names SWE-bench Lite and WebArena; the technical plan instead proposes Terminal-Bench 2.0 as the primary benchmark, with AppWorld for transfer, pending Prof. Abdelrazek's view.
