# B1 episode token budget implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enforce one 64,000 generated-token ceiling over B1 agent, judge, and reflection calls, and correct the generic loop to count generated output rather than prompt plus output.

**Architecture:** Add an optional per-request output-token cap to the synchronous and asynchronous OpenAI-compatible clients. A budget wrapper shared by all B1 calls tracks actual output usage, limits each call to the remaining allowance, and makes exhaustion/overrun explicit. Both the sync baseline loop and async Harbor agent pass their remaining episode allowance while tracking generated output tokens.

**Tech Stack:** Python 3.11+, pytest, OpenAI-compatible chat completions API, Pydantic strategy schema.

**Spec:** `docs/superpowers/specs/2026-10-30-b1-episode-token-budget-design.md`

## Global Constraints

- B1 run cap: 64,000 generated/output tokens total across agent, judge, reflection.
- Prompt/input tokens are costed but do not consume the generated-token allowance.
- Judge blindness, retry triggers, no-reset behavior, seeded requests, and cost accounting remain intact.
- Do not change the attempt-cap mixture distribution in this change.

## Review Focus

- An exhausted budget must not result in an unbounded or accidental model request; tests assert no call is made.
- A judge or reflection call must use the shared remaining allowance; tests inspect request caps across call types.
- A provider response that exceeds its requested cap must be charged once and prevent subsequent calls; test records overrun.
- Token limits must use output tokens while input tokens continue to appear in cost totals; test a prompt-heavy low-output case.
- A judge unavailable at exhaustion must not trigger a retry or hidden-reward-based choice; test selection and explicit skip metadata.
- A provider overrun response is charged but its parsed tool action is never executed; test that the environment remains untouched.
- Reflection that consumes the remaining budget must not start a phantom attempt or reset the environment; test attempt and reset counts.
- If the per-attempt cap is reached while shared B1 budget remains, judge the attempt and allow a later attempt; each request uses the minimum of both remaining values.
- A per-call API limit may lower but must not raise the model client's configured maximum.

---

### Task 1: Add request-level generated-token limits

**Files:**
- Modify: `llm/base.py`
- Modify: `llm/__init__.py`
- Modify: `llm/openai_compatible.py`
- Modify: `llm/async_openai_compatible.py`
- Modify: `environments/harbor_agent.py`
- Modify: `strategy_schema/defaults.py`
- Modify: `strategy_schema/model.py`
- Modify: `tests/test_openai_compatible.py`
- Modify: `tests/test_async_openai_compatible.py`
- Modify: `tests/test_harbor_adapter.py`
- Modify: `tests/test_strategy_schema.py`

**Interfaces:**
- `ChatModel.complete(messages, *, seed=None, max_output_tokens=None) -> ChatResponse`
- `MockModel` and `OpenAICompatibleModel` honor a positive `max_output_tokens` request; the HTTP client sends `min(per-call limit, configured client limit)` in the API `max_tokens` field.

- [x] Add offline client tests asserting per-call `max_tokens` and that the cap cannot raise a configured client maximum.
- [x] Add a default-strategy test asserting S0 uses the documented 60-step and 64,000 generated-token caps.
- [x] Run focused tests first; they failed on the missing per-call parameter and old 40/200,000 defaults.
- [x] Implement optional limits in sync/async clients and mocks; per-call value can lower but never raise configured maximum. Update S0 default and rendering.
- [x] Run focused client and Harbor adapter tests; pass.
- [ ] Commit the interface change.

### Task 2: Enforce the shared B1 allowance

**Files:**
- Create: `baselines/token_budget.py`
- Modify: `baselines/agent_loop.py`
- Modify: `baselines/judge.py`
- Modify: `baselines/baselines.py`
- Modify: `evaluation/runner.py`
- Modify: `environments/harbor_agent.py`
- Modify: `llm/async_openai_compatible.py`
- Modify: `tests/test_baselines.py`
- Modify: `tests/test_harbor_adapter.py`

**Interfaces:**
- `GeneratedTokenBudget(model: ChatModel, limit: int)` exposes `remaining`, `used`, `overrun_tokens`, and `complete(...)`; exhaustion raises before a provider call and overrun carries the actual `ChatResponse` to the caller for accounting.
- `run_episode(...)` passes the remaining per-attempt output allowance to every model request and terminates on generated-output exhaustion.
- `TaskOutcome` records an optional `budget_stop_reason` and `budget_overrun_tokens` for B1.

- [x] Add tests for output-only loop budgeting, decreasing request caps, exhaustion preventing calls, overrun tool actions not reaching the environment, reflection exhaustion preventing another attempt/reset, and exact cost totals.
- [x] Run focused tests first; they failed on input-plus-output accounting and missing API caps.
- [x] Implement the budget wrapper and integrate it with B1 and Harbor, including explicit judge-skip metadata and stopping after exhaustion or overrun; retain and charge overrun output without parsing/executing its action.
- [x] Assert outcome cost equals agent plus judge plus reflection costs once, and early budget stop retains the latest completed attempt.
- [x] Run focused checks for baseline/client/Harbor paths; pass.
- [ ] Commit the B1 enforcement change.

### Task 3: Reconcile the research protocol and report

**Files:**
- Modify: `docs/EXPERIMENTS.md`
- Modify: `docs/TECHNICAL_PLAN.md`
- Modify: `docs/PAPER_PLAN.md`
- Modify: `docs/EXECUTION_PLAN.md`
- Modify: `docs/GLOSSARY.md`
- Modify: `docs/experiments/G-BASE-audit-2026-10-30.md`
- Modify: `docs/superpowers/plans/2026-10-28-cluster-next-gates.md`
- Create: `docs/experiments/PROFESSOR_UPDATE_2026-10-30.md`

- [x] Remove the “per attempt for B1” exception and define one shared B1 run cap, including judge/reflection outputs.
- [x] Record that sampled attempt caps remain the planned maximum and realized attempt counts can be lower due to token exhaustion; keep their Stage-2 distribution open pending matching evidence.
- [x] Draft a concise professor update separating synthetic setup evidence from benchmark results and listing the outstanding gates.
- [x] Run `git diff --check` and review all budget statements for consistency.
- [ ] Commit and push the documentation with code after acceptance verification.

## Acceptance

- [x] Run the full offline suite: `python -m pytest -q` — 132 passed in 10.13s. Record the exact result in the G-BASE audit and professor update.
- [x] No task benchmark or model-backed trial was run by this change.
