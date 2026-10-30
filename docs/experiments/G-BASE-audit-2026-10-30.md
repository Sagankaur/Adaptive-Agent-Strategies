# G-BASE acceptance audit — 2026-10-30

## Status

The six explicit acceptance outcomes in `docs/EXECUTION_PLAN.md` are mapped to the implementation and named tests. The B1 token-budget contract is now resolved and implemented: one 64k generated-token limit is shared across agent, judge, and reflection calls in a B1 task/run; prompt/input tokens remain costed but do not consume this limit. The full offline suite passes. **G-BASE remains open** because the seeded B1 attempt-cap mixture is not yet implemented or frozen from the planned compute-matching evidence.

## Six acceptance outcomes

| Acceptance outcome | Implementation | Evidence in the repository | Audit |
|---|---|---|---|
| B1 retries when the blind judge returns fail | `ReflectionRetry.run()` retries when `not judge.passed` or the agent's own check failed | `tests/test_baselines.py::test_b1_reflects_and_retries_when_own_checks_fail` supplies judge scores 0.1 then 0.9, observes reflection, and selects the successful second attempt | Covered |
| B2 can select an attempt other than 0 | `BestOfN.run()` scores every trajectory and calls `select_best_index()` | `tests/test_baselines.py::test_b2_selects_by_own_checks` supplies scores 0.2 and 0.9 and asserts `selected == 1` | Covered |
| Requests carry temperature 0.6, top-p 0.95, top-k 20, and a seed | `OpenAICompatibleModel._request_body()` supplies these fields; `_next_seed()` increments the root | `tests/test_openai_compatible.py::test_requests_use_pinned_sampling_and_distinct_logged_seeds` inspects two captured requests and their seeds | Covered |
| Judge and reflection calls are charged to the calling baseline | B1 and B2 add judge/reflection response costs to `TaskOutcome.extra_cost`; `TaskOutcome.cost` adds this to attempt costs | `tests/test_baselines.py::test_b1_reflects_and_retries_when_own_checks_fail`, `test_b2_selects_by_own_checks`, and `test_b2_judge_time_is_in_aggregate_wall_cost` check extra call counts, total call counts, and judge time; new shared-budget tests assert output tokens sum exactly once | Covered |
| The blind judge cannot read hidden tests | `judge_attempt()` accepts only the model, instruction, and public `Attempt`; it has no environment or filesystem handle | `tests/test_judge.py::test_judge_scores_only_instruction_and_public_trajectory` checks the prompt contains the task and trajectory but no `tests/` path or hidden `success` field | Covered |
| S0 makes no in-run judge call | `FixedStrategy.run()` calls `run_episode()` once and does not invoke `judge_attempt()` | `tests/test_baselines.py::test_s0_does_not_call_the_judge` asserts one model request | Covered |

## B1 episode budget

The protocol defines 64,000 generated/output tokens per episode, including reasoning. A B1 Harbor trial shares one allowance across all agent, judge, and reflection responses. Input tokens remain included in cost accounting but do not consume this generated-token limit. The single-attempt loop checks output tokens and sends the remaining limit to each model request. S0 defaults now match the planned 60-step and 64k-token settings.

If the judge cannot run because no tokens remain, the episode records an explicit skipped judgment and stops without using hidden reward. A provider response exceeding its requested cap is charged, its tool action is not executed, and no further model calls are made. Episode cost is agent attempt cost plus extra judge/reflection cost exactly once.

The sampled attempt cap `k` is distinct from the token ceiling. The seeded `{1,2,3}` attempt-cap mixture must still be frozen from planned compute-matching evidence before Stage 2; budget exhaustion can produce fewer realized attempts than `k`.

## Verification note

Focused checks pass for the sync and async clients, Harbor adapter, baseline, judge, runner, and strategy-schema changes. The complete offline suite passes: `python -m pytest -q` reported **132 passed in 10.13s** on 2026-10-30. Ruff reports `All checks passed!` for the changed source and tests. This verification does not close G-BASE because the seeded attempt-cap mixture remains open.
