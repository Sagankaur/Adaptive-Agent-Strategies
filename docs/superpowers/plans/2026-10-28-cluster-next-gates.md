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
- [x] Verify links and consistency checks; commit the evidence with the documentation.

### Task 2: G-BASE baseline repair

**Files:** `llm/openai_compatible.py`, `llm/base.py`, `baselines/agent_loop.py`, `baselines/baselines.py`, new `baselines/judge.py`, tests.

- [x] Add pinned sampling and unique per-request seed logging.
- [x] Add a test proving request settings and distinct seeds.
- [x] Add blind judge scoring with no filesystem access to hidden tests.
- [x] Repair B1 in-episode retries, no-reset behavior, attempt limits, reflection and judge cost accounting.
- [x] Repair B2 post-trial selection with seeded tie-breaking and correct cost accounting.
- [x] Add exact pooled BoN expectation over all subsets with analytic random tie handling.
- [ ] Verify all six G-BASE acceptance outcomes and the full offline suite; focused acceptance tests pass, but full-suite pytest setup remains blocked by Windows temporary-directory permissions.

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
- Focused baseline, judge, OpenAI client, and async parser tests pass: 44 passed, 1 skipped from the focused command because it exercises a live model server. After the final baseline accounting and seed logging fixes, the baseline and judge tests pass 22/22.
- Ruff passes across `llm`, `baselines`, `evaluation`, and the affected tests.
- The full suite currently reaches 98 passes and 12 temporary-directory setup errors under Windows. The errors are `PermissionError` while pytest enumerates `C:\Users\sagan\AppData\Local\Temp\pytest-of-sagan`; rerun under the supported Python 3.11 environment before diagnosing these as project failures.
- The Harbor adapter, route pilot, five-task smoke, and E-P0/G0 are still open.
- An async OpenAI-compatible client slice now parses nullable content, reasoning, native tool calls, cached tokens, and top-level llama.cpp timings. It can send tool schemas, chat-template kwargs, and a task/run-specific seed root; tool-role messages round-trip through the shared request type. Fixture tests pass. This slice is not connected to the synchronous `ChatModel` cost records or an agent trajectory log. The Harbor agent adapter remains unimplemented because Harbor is not installed in this environment and cluster access currently fails DNS resolution for `login-f.ai.deakin.edu.au`.
- Independent review confirmed the need for top-level timings (now corrected), per-task seed roots, and advertised tool schemas (now supported). It also confirmed that the overall G-INFRA gate remains open: no Harbor adapter or five-task smoke exists. B1's per-task/run attempt-cap mixture and cumulative cap enforcement also remain open beyond the current 1–3 cap validation.
- B1/B2 judge elapsed time is now included in aggregate `extra_cost.wall_s`; B1 reflection instructions are trigger-neutral and include the judge's public score and reason. B1's seeded attempt-cap mixture and cumulative token-cap enforcement remain unfinished.
- B1 reflection calls are recorded in each result's `extra_calls` field with their seed, text, and token/time cost so the seed audit trail includes non-trajectory calls.
- The latest cluster SSH retry on 2026-10-28 failed before authentication: hostname resolution failed. No model or task run was started.
- The five-task TB-Pro smoke remains gated on the approved provider, network route, budget, task licensing, and disk allocation; those approvals and route results are not recorded in the repository.
