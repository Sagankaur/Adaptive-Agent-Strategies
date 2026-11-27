# Synthetic S0 Harbor agent history check (2026-11)

## Purpose

This engineering check measures whether the pinned local model can continue the project's actual `HarborStrategyAgent` S0 loop as synthetic conversation history grows. It follows the two-call protocol diagnostic and tests the full adapter loop through mock probes and tool results.

It is not a benchmark run. It creates no Harbor trial, task container, verifier, oracle, reference solution, or task episode. It exercises neither the Harbor Unix-socket control channel nor task-container egress isolation.

## Safety and method

- Model: the pinned `gpt-oss-20b-MXFP4.gguf`; server: the pinned llama.cpp Apptainer image.
- Controller: the repository's real `HarborStrategyAgent`, unmodified S0 prompt, tool schema, request/response loop, and standard S0 episode budgets.
- Environment: a mock whose `exec()` discards each command and returns only fixed synthetic responses. It never calls a shell, subprocess, Harbor, or a container runtime.
- The two S0 probes must be intercepted before the first model request. The optional S0 visible-test check has no configured command and is recorded as skipped.
- Logging: replace the production step writer, which otherwise records arguments and reasoning, with an aggregate-only in-memory recorder. The result file contains categories, counts, token/timing metrics, and hashes only.
- Conditions: three paired repetitions of short and long inert synthetic README histories, with short-first and long-first order alternated across pairs. No real task text or user data is included.
- Context: 8,192-token server window; 1,024-token output cap per request and 1,024-token safety margin. The exact message/tool payload is token-counted before every model request. A request is stopped before inference when `input + output cap + margin >= 8192`; no truncation is performed.
- Bound: at most six model requests per conversation. The S0 budgets remain 60 steps, 64,000 generated tokens, and 1,200 seconds; the separate request ceiling makes this a bounded loop check, not a full-budget trial.
- Stop conditions: tokenizer or model-client failure, GPU headroom below 1 GiB, unexpected request/logging output, any nonzero real-executor count, or safety-invariant failure.

## Outcomes to report

For each condition, report planned/started/completed repetitions, submit before a guard/ceiling, model calls and mock terminal calls, prompt/output tokens, call timings, context stops, tripwire categories, and GPU peak/minimum-free memory. The safety claim is by construction: no real Harbor environment or task command executor is created, the mock discards commands, and the production raw step writer is replaced. The run does not exercise Harbor UDS.

Do not interpret submit frequency as task success. S0's visible-test check is skipped because no check command is configured. The model receives no real task and the mock does not apply any generated command. Results describe only model/adapter protocol behavior under synthetic history.

## Execution record

Attempt 1, Slurm job `4890453`, failed before starting a conversation (`FAILED`, `ExitCode=2:0`, 58 seconds). It made zero model requests and zero mock terminal calls; the lowest free VRAM sample was 85,992 MiB. The cause was Harbor 0.23.0's read-only `extra_env` property: the runner assigned it after construction. The runner now passes `extra_env` through the supported constructor argument. This was a runner setup failure, not an experimental outcome.

Slurm job `4890460` was cancelled while pending because the RTX Pro 6000 was fully allocated. The retry now targets an available L40S on Rohan; the same pinned model already fit the L40S in prior serving work. This is a protocol/history check, not a GPU comparison, and no speed comparison will be inferred.

Job `4890462` was submitted with a malformed expected-source-commit value. Cancellation and live status checks could not reach Rohan after workstation DNS stopped resolving both login hosts. The batch script validates the source commit before starting the model server, so this job should fail closed before any model request; its final Slurm state remains unverified until SSH access returns.

Corrected runner: `docs/cluster/aider-pilot/04_harbor_s0_history_check.py`; batch job: `docs/cluster/aider-pilot/04_harbor_s0_history_check.sbatch`. Retry is pending after the corrected resource request is pushed.

Rohan access returned on 2026-11-27. `sacct` confirmed job `4890462` ended `FAILED 3:0` after 55 seconds, failing closed at the source-commit check as predicted; no model request was made. The cluster source checkout was clean at `1cc20c2fae7317b6686d8bb3364df2731c58d7bf`, which contains this runner and batch script (the later `c347f25` changes only this note). The retry was submitted as Slurm job `4944139` with `AAS_EXPECTED_SOURCE_COMMIT=1cc20c2fae7317b6686d8bb3364df2731c58d7bf`, targeting one L40S; it was `PENDING (Resources)` at submission. No result yet. Pre-committed interpretation rules: see `s0-history-check-decision-plan-2026-11.md`.

## Result of job 4944139 (2026-11-27)

Slurm `COMPLETED 0:0`, 86 s, L40S (`l40s-f-01`), source commit `1cc20c2fae7317b6686d8bb3364df2731c58d7bf`, runner SHA-256 `7fb2783b28d4b9958dd65d73869cd85a9ca6356bd26867c0141d7d392c8d4170`, model/server hashes as pinned. Result file (cluster scratch): `/scratch/<user>/aider-protocol-diagnostic/results/4944139-s0-history/s0-history-results.json`. Engineering check only; not a benchmark result and not Aider/TB performance.

**Safety/validity.** 6/6 conversations started and returned. S0 probes were intercepted before the first request in all. No tripwire flags; minimum free VRAM 34,295 MiB; no VRAM-guard failure; `mock_exec_calls` 3-4 per conversation (mock only); `agent_step_log_created` false.

**Outcomes.** All 6 conversations ended `agent_returned` with `submitted: true`, after 3 requests (5 in one). No context-guard stop and no request-ceiling stop. No schema-invalid JSON request was recorded (every tool-call request was `valid_schema_A` or `valid_schema_B`). Totals: 20 requests, of which **7 (35%) were `no_tool_call`**, exactly one or two per conversation (one `invalid` step category each). Mean call time 0.43-0.64 s.

**Scored against the pre-committed plan.** R3 is triggered (no-tool responses 35% > 20%); the plan says do not proceed and investigate prompt/schema handling offline. Whether the `invalid` step category counts as an R1/R2 failure under the plan's wording is ambiguous, but under the literal R1 reading R1 is not met. R10 (engineering pass) is therefore **not** satisfied. R5, R6, R7 did not trigger, but see below.

**Instrument defect found: the long-history condition did not test long history.** `history_prompt_tokens_after_probes` is 1,386 in all six runs, short and long alike, and pairs 2 and 3 have near-identical total input tokens across conditions (4,433 vs 4,433; 4,421 vs 4,421). Cause (from `strategy_schema/defaults.py` line 50 and `environments/harbor_agent.py` lines ~390/439/477): S0 sets `max_observation_chars=4000`, and the agent truncates every observation to that, so the 80- vs 260-repeat README collapses to the same ~1.4k-token prompt. Consequently R6-R9 are uninformative: the absence of guard stops says nothing about long histories, and the short-versus-long comparison is void. Sampled differences between conditions reflect only sampling variation (different seeds per request), not history length.

**What this does and does not show.** It shows the loop can reach `submit` through the real adapter path under a short history, with no schema-invalid JSON in 20 requests, which is an improvement on the earlier pilot's interface failures. It does not show context robustness, does not clear the 35% no-tool rate, and does not authorize any task pilot. Not yet determined: at which request the no-tool responses occur and whether the agent's nudge after one recovers the call (the step ordering was not retained in the aggregate output).

**Proposed next step (not run).** A corrected history check whose long condition grows through accumulated multi-turn history (or raises `max_observation_chars` in a clearly labelled amended copy of S0), recording per-request order, `finish_reason` and reasoning-token counts, plus a look at why the first reply lacks a tool call. Any such change is a protocol amendment under Sec. 5 of the decision plan and must be frozen before the run.
