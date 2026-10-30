# G-BASE acceptance audit — 2026-10-30

## Status

The six explicit acceptance outcomes in `docs/EXECUTION_PLAN.md` have been mapped to the current implementation and named tests. The repository's last recorded full-suite result is 125 passing tests, but this audit did not rerun tests. **G-BASE remains open** because B1 cap randomization is not implemented and the cumulative token-budget wording conflicts with the approved per-attempt budget text.

## Six acceptance outcomes

| Acceptance outcome | Implementation | Evidence already in the repository | Audit |
|---|---|---|---|
| B1 retries when the blind judge returns fail | `ReflectionRetry.run()` retries when `not judge.passed` or the agent's own check failed | `tests/test_baselines.py::test_b1_reflects_and_retries_when_own_checks_fail` supplies judge scores 0.1 then 0.9, observes the reflection, and selects the successful second attempt | Covered |
| B2 can select an attempt other than 0 | `BestOfN.run()` scores every trajectory and calls `select_best_index()` | `tests/test_baselines.py::test_b2_selects_by_own_checks` supplies scores 0.2 and 0.9 and asserts `selected == 1` | Covered |
| Requests carry temperature 0.6, top-p 0.95, top-k 20, and a seed | `OpenAICompatibleModel._request_body()` supplies these fields; `_next_seed()` increments the root | `tests/test_openai_compatible.py::test_requests_use_pinned_sampling_and_distinct_logged_seeds` inspects two captured requests and their seeds | Covered |
| Judge and reflection calls are charged to the calling baseline | B1 and B2 add judge/reflection response costs to `TaskOutcome.extra_cost`; `TaskOutcome.cost` adds that to attempt costs | `tests/test_baselines.py::test_b1_reflects_and_retries_when_own_checks_fail`, `test_b2_selects_by_own_checks`, and `test_b2_judge_time_is_in_aggregate_wall_cost` check extra call counts, total call counts, and judge time | Covered for call counts and judge wall time; no separate token-by-token ledger assertion was found in the audited tests |
| The blind judge cannot read hidden tests | `judge_attempt()` accepts only the model, instruction, and public `Attempt`; it has no environment or filesystem handle | `tests/test_judge.py::test_judge_scores_only_instruction_and_public_trajectory` checks the prompt has the task and trajectory but no `tests/` path or hidden `success` field | Covered |
| S0 makes no in-run judge call | `FixedStrategy.run()` calls `run_episode()` once and does not invoke `judge_attempt()` | `tests/test_baselines.py::test_s0_does_not_call_the_judge` asserts one model request | Covered |

## B1 budget mismatch to resolve

The main experiment specification says 64k generated tokens per attempt for B1 and randomizes the attempt cap per `(task, run)` from `{1, 2, 3}`. `P0-05` requires the seeded attempt-cap draws to sum to at most 1,024 for five runs per task (or 614 for three runs). The current implementation accepts a fixed `ReflectionRetry(k)` and enforces `strategy.budget.max_tokens` inside each `run_episode()` only. B1's judge and reflection requests are added to `extra_cost` but are outside that per-attempt token cap.

The cluster next-gates ledger additionally says “cumulative token-cap enforcement” is unfinished. That could mean a cap over all B1 attempts and auxiliary calls, which would change the documented per-attempt contract. Before implementing, decide whether to:

1. Keep the written research contract: 64k per attempt, plus the seeded `{1,2,3}` attempt-cap mixture; separately ensure all auxiliary calls are charged and no arm exceeds its declared run-count cap.
2. Amend the research contract to a per-run generated-token cap covering agent, judge, and reflection requests, and predeclare how the cap is drawn/matched before runs.

Do not silently add a cumulative cap or call G-BASE green until this wording is reconciled across `TECHNICAL_PLAN.md`, `EXECUTION_PLAN.md`, `EXPERIMENTS.md`, and the implementation plan.

## Verification note

This is a source-and-test audit, not a fresh execution of the test suite. The previous cluster-next-gates ledger records a full 125-test pass on 2026-10-30 and the baseline/judge checks passing, but no current CI log is linked here. Re-run the baseline acceptance suite after the budget contract and implementation are settled, then record the exact CI/test result before closing G-BASE.
