# Cluster Next Gates Implementation Plan

> **For agentic workers:** Use this checklist to execute the authorized cluster follow-up work.

**Goal:** Convert the L40S smoke into portable evidence, close the baseline and infrastructure gates, and run the approved task-route and throughput pilots without consuming held-out TB2 episodes.

**Architecture:** Keep toy/model-server integration evidence separate from benchmark outcomes. Repair the existing baseline layer first, then add the async Harbor path required by G-INFRA. Run task-image and model work only through approved routes and record exact pins, logs, rewards, and costs.

**Tech Stack:** Python 3.11, pytest, OpenAI-compatible llama.cpp, Slurm/Apptainer, Harbor v0.23.0 per current project pin, Docker-based approved task sandbox.

**Spec:** `docs/EXECUTION_PLAN.md` (P0-01 through P0-06), `docs/EXPERIMENTS.md` (G-BASE, G-INFRA, P-M2, E-P0), `docs/DECISIONS.md` (M2 and M8).

## Global Constraints

- Keep TB2 tasks held out; do not run TB2 agent episodes before the Stage-2 pre-registration gate.
- Use the pinned Qwen sampling values: temperature 0.6, `top_p` 0.95, `top_k` 20, and log a unique per-request seed.
- B1 may retry only on an in-run judge failure or agent-written-test failure; never use hidden reward to trigger retries; max 3 attempts and no environment reset.
- B2 scores S0 trajectories after trial completion; the judge receives no `tests/` path; ties use a logged seed.
- Charge every judge/reflection/model call to the arm that made it.
- Do not launch provider-backed task runs until the provider, network policy, and budget are approved.

## Review Focus

- Sampling seeds must be unique, recorded, and reproducible when the trial order is fixed.
- Judge inputs must exclude hidden reward, hidden tests, and task filesystem paths.
- Failed or malformed judge output must not silently count as success.
- B1 retries must preserve the same task environment and remain inside its attempt and token limits.
- Harbor reward and task results must come from Harbor's trial result, not the agent loop's hidden grader.

## Tasks

### Task 1: Portable model-smoke evidence

**Files:** `docs/cluster/l40s-client-smoke/`, `docs/LOCAL_MODELS.md`, `docs/PHASE0_CHECKLIST.md`.

- [x] Copy the report, Slurm script, driver, summary JSON, and runner JSONL into the repository.
- [x] Record model revision/hash, server image/build, source commit, GPU, runtime, Slurm allocation, and limitations.
- [x] Update repository documentation to use in-repository links.
- [ ] Verify links and consistency checks; commit the evidence with the documentation.

### Task 2: G-BASE baseline repair

**Files:** `llm/openai_compatible.py`, `llm/base.py`, `baselines/agent_loop.py`, `baselines/baselines.py`, new `baselines/judge.py`, tests.

- [ ] Add pinned sampling and unique per-request seed logging.
- [ ] Add a test proving request settings and distinct seeds.
- [ ] Add blind judge scoring with no filesystem access to hidden tests.
- [ ] Repair B1 in-episode retries, no-reset behavior, attempt limits, reflection and judge cost accounting.
- [ ] Repair B2 post-trial selection with seeded tie-breaking and correct cost accounting.
- [ ] Add exact pooled BoN expectation over all subsets with analytic random tie handling.
- [ ] Verify all six G-BASE acceptance outcomes and the full offline suite.

### Task 3: G-INFRA Harbor integration

**Files:** async model client, Harbor agent module, job configuration, JSONL step logging, fixture-based tests.

- [ ] Implement the async per-trial client, including nullable content, reasoning, native tool calls, llama.cpp timings, cached tokens, and the `tool` message role.
- [ ] Implement the async Harbor agent and source reward from the Harbor trial result.
- [ ] Log strategy hash, provenance tag, seed, timings, and Harbor trial id per step.
- [ ] Set Harbor concurrency equal to the pinned llama.cpp slot count and timeout multiplier to 2.
- [ ] Verify the CPU scripted-agent Harbor toy run before using real task images.

### Task 4: P-M2 route pilot

- [ ] Confirm task license, provider, budget, network policy, and disk allocation.
- [ ] Build census, resource filtering, dedup review, Oracle/network pilot, license check, and routing-table export.
- [ ] Apply the published GO rule and record the route decision.

### Task 5: Five-task smoke and E-P0/G0

- [ ] Run five TB-Pro infrastructure tasks only after G-INFRA and G-ROUTE prerequisites pass; require zero harness errors.
- [ ] Sweep only configurations that fit the available GPU memory and retain required headroom.
- [ ] Estimate task-level throughput, timeouts, MCU coefficients, occupancy, and costs from episode records.
- [ ] Apply the written G0 criteria before any budgeted episode run.

## Current ledger

- The A2I2 L40S model-server smoke and one-task project-client/toy-runner smoke passed; see `docs/cluster/l40s-client-smoke/REPORT.md`.
- The 15 tests in `tests/test_baselines.py` pass under the local Python 3.14 interpreter.
- The full suite currently reaches 86 passes and 12 temporary-directory setup errors under Windows. The errors are `PermissionError` while pytest enumerates temporary directories; re-run under the cluster's supported Python 3.11 environment before diagnosing these as project failures.
- The Harbor adapter, route pilot, five-task smoke, and E-P0/G0 are still open.
