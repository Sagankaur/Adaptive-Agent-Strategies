# Pre-committed decision plan for the synthetic S0 history check (2026-11)

**Status:** written 2026-11-27, before any result from Slurm job `4944139` exists. Runner commit `1cc20c2fae7317b6686d8bb3364df2731c58d7bf`. Rules below are fixed now; they may not be loosened after the artifact is read. Any later amendment must be dated, must say what changed, and must be written without reference to which outcome it would favour.

## 1. Question and non-questions

**Question.** When the real `HarborStrategyAgent` S0 loop (unmodified prompt, tool schema, request/response serializer, setup probes) drives the pinned `gpt-oss-20b-MXFP4.gguf` through a mock, command-discarding environment, at an 8,192-token server window with full history and no truncation, how often does it (a) emit parseable, schema-valid `terminal`/`submit` calls, (b) reach `submit` before a guard or the six-request ceiling, and (c) hit the context guard, for a short versus a long synthetic README observation?

**Not answered.** This is not a benchmark and not a capability estimate. It says nothing about Aider Polyglot or Terminal-Bench performance, about whether the model can solve any task, or about S0's 60-step behavior (the check stops at six requests). It does not exercise Harbor's Unix-socket control channel, task-container egress isolation, the verifier, or S0's visible-test hook (skipped). Submit frequency is not task success: the model receives no real task and the mock applies nothing.

## 2. Recorded metrics (from `04_harbor_s0_history_check.py`)

Per conversation (6 planned: 3 pairs x {short, long}, order alternated by pair):

- `stop_reason` in {`agent_returned`, `context_guard`, `request_ceiling`, `error:<ExceptionClass>`}; `context_guard` object (input tokens, output cap, margin, limit).
- `request_count`; `request_categories` (from `check_tool_call`); `tool_categories` (`terminal`/`submit`/`other`); `step_categories` (terminal, submit, invalid, model_error, terminal_error, token_limit, step_limit, verify*, probe:*).
- `submitted`, `submit_step`, `calls_to_submit`.
- Per request: preflight prompt tokens, reported input tokens, cached tokens, output tokens, response category, tool category, wall and model seconds, prompt_ms, generation_ms.
- Totals: input/output tokens, `mean_call_seconds`, `wall_seconds`; `history_prompt_tokens_after_probes` (first preflight count).
- Safety: `mock_exec_calls`, `workdir_probe_calls`, `readme_probe_calls`, `mock_terminal_calls`, `s0_probes_intercepted_before_first_inference`, `probe_invariant`, `agent_step_log_created`, `raw_content_written`, `tripwire_flags` (url/ip/namespace/mount, counts only), `effective_seed`, S0 budgets, strategy hash.
- Run level: `status`, `started_conversations`, `bounded_loop_conversations_returned`, hashes, GPU peak/minimum-free/samples/stop reason, total wall time.

Not recorded: `finish_reason`, reasoning-token split, raw content, argument values.

## 3. What n = 3 pairs can and cannot show

Six conversations, one model, one seed root, one GPU, one synthetic prompt. It can show **existence** (an outcome occurred at least once, so the interface can produce it) and **gross, deterministic-looking** differences (e.g. 3/3 vs 0/3). It cannot estimate rates: a 0/6 observation is compatible with a true rate up to roughly 40% (rule-of-three, ~95% upper bound 1 - 0.05^(1/6)). It cannot support significance tests, effect sizes, or "short is better than long" claims beyond describing the observed table. All thresholds below are therefore **action triggers for engineering triage**, not inferential cut-offs, and are deliberately conservative toward not proceeding.

Prior context: in the two-call diagnostic at cap 1,024, first-turn valid `terminal` was 23/24 but terminal-then-submit was 1/24, with the model usually calling `terminal` again. The expected null here is therefore a **low submit-before-ceiling rate**, and the check must be read against that.

## 4. Decision table

Validity gates are evaluated first; a failed gate overrides every row below.

| ID | Observed pattern | Interpretation | Action |
|---|---|---|---|
| G1 | Any nonzero real-executor/Harbor evidence: `agent_step_log_created` true, `raw_content_written` true, nonzero `tripwire_flags` from an unexpected path, `status` = `aborted_safety_invariant`, or any evidence a real shell/Harbor environment ran | Run invalid | Discard results, no interpretation, root-cause the safety breach, fix, and re-register before any rerun. |
| G2 | `s0_probes_intercepted_before_first_inference` false or `probe_invariant` != `s0_probes_intercepted` in any started conversation; `mock_exec_calls` < 2 | Harness did not model S0 | Run invalid for that conversation; treat as harness bug, not model outcome. |
| G3 | Job fails before conversation 1, GPU headroom stop, hash/commit mismatch, `aborted:*` before all 6 conversations start | Incomplete | Record as setup failure (as for jobs `4890453`, `4890462`); fix cause; one resubmission allowed with unchanged analysis. Partial data are reported but not used for rows below. |
| G4 | `stop_reason` = `error:*` in any conversation (the runner then aborts remaining conversations) | Model/client/adapter fault | Report error class; investigate offline; no pilot. Not counted as invalid-JSON unless the class and `step_categories` show it. |
| R1 | Invalid tool-call JSON or `invalid` step: 0 of all requests | Not observed | No action from this row. |
| R2 | Invalid-JSON/schema-invalid requests >= 1 in any conversation, or > 5% of all requests | Interface still unreliable (this failure caused 3 of 4 Aider task failures) | Do not proceed. Treat as adapter/model blocker: examine parser and cap handling offline; consider pinned-model alternatives. A single occurrence suffices because the prior pilot's failure was a hard stop in one trial. |
| R3 | `other`/no-tool responses > 20% of requests, in either condition | Tool contract not met | Do not proceed; investigate prompt/schema handling (reasoning channel, cap) offline. |
| R4 | `submit` reached in >= 2 of 3 short conversations before any guard/ceiling | Loop can terminate under favorable history | Necessary, not sufficient; proceed to row R7 checks. |
| R5 | `submit` in 0 of 6 conversations (all end at ceiling or guard) | Consistent with prior 1/24; model keeps calling `terminal` against the instruction | Do not proceed. Paused: investigate prompt/termination handling offline (e.g. whether S0 instruction wording or the identical mock result induces repetition); any prompt change is a protocol amendment (Sec. 5). |
| R6 | Context guard fires in short condition in any pair | History budget insufficient even for short | 8,192 window is unfit for S0; require larger window or history policy (Sec. 5) before any pilot. |
| R7 | Context guard fires in long conditions (>= 2 of 3) before `submit` or ceiling | Expected by design given ~5k-token observation plus 1,024 cap plus 1,024 margin; guard stops are deterministic arithmetic, not model behavior | Do not read as model failure. Record `context_guard.input_tokens`; confirm a history policy is needed; do not proceed with 8,192 + full history. |
| R8 | Short vs long differ in submit count by 2 or more pairs (e.g. 3 vs 1) with no guard stop in the lower arm | Descriptive signal that history length affects behavior | Report as hypothesis only; motivates a context policy; not an estimate. |
| R9 | Short and long agree (all three pairs same terminal outcome class) | No detectable effect at n = 3 | Not evidence of no effect; states only that the check did not discriminate. Do not cite as "history length is harmless". |
| R10 | R1, R4 satisfied, no R2/R3/R5/R6 trigger, G1-G4 clean | Check passes its engineering gate | Permits only the amendments in Sec. 5; does **not** authorize a task pilot by itself. |

Any pattern not covered defaults to "do not proceed; write a dated note".

## 5. Required amendments before any fresh task pilot

Frozen in a dated, hash-recorded protocol document before the first task episode, with the decision plan above committed first:

1. **Fresh sample.** Newly drawn, unattempted Aider tasks (seed, source commit, selection code and filter recorded before drawing). The four attempted IDs are excluded; the two lyric exclusions persist as pre-run safety exclusions; any further exclusions must be stated before execution.
2. **Context window and history policy.** Choose and freeze one of: larger server window (verify VRAM headroom on the target GPU), truncation of oversized tool observations, or a sliding-window/summarized history. State the policy, token budget, margin, and the cap (1,024 output tokens was the best-performing prior setting; its saturation is only a proxy because `finish_reason` is not recorded). The six-task pilot used 8,192 tokens with full history; reusing that unchanged is not permitted if R6 or R7 triggered.
3. **Protocol.** S0 prompt, tool schema, sampler, seed policy, step/token/wall budgets, retry rules, scoring rule, and failure classification (invalid JSON, context error, no-submit) fixed in advance. Add `finish_reason` capture and reasoning-token accounting if available.
4. **One-task lifecycle check** under verified egress isolation before the multi-task pilot; egress safety remains a separate gate (UDS/container isolation is untested here).
5. **Stopping and reporting rules** for the pilot, including that results are feasibility counts, not a pass rate.

## 6. Threats to validity and design weaknesses

- **8,192 tokens may be uninformative.** With the long README (260 repeats of a ~17-token filler, order of 4-5k tokens) plus system prompt/schema, input + 1,024 cap + 1,024 margin leaves room for only about one to two further turns. The guard may fire by arithmetic before model behavior diverges, so "long" may measure the guard, not the model. `history_prompt_tokens_after_probes` should be checked to see how far apart the two histories actually are.
- **The short/long contrast is confounded.** Conditions differ only in README length, but length also changes the probe observation's share of context, the number of turns the guard permits, and (through different prompts) the sampled trajectory; the seed is shared per pair but the divergent prompt breaks any trajectory pairing. Pair order is alternated but 3 pairs cannot balance it (2 vs 1). The comparison also never varies history by turn count, which is how real histories grow; one large inert README is not equivalent.
- **Mock output is identical and uninformative** for every `terminal` call. This may itself induce repeated `terminal` calls (the prior diagnostic's dominant failure), conflating protocol failure with an uninformative environment. Conversely, a mock that never errors cannot test recovery paths.
- **Ceiling truncates the target.** Six requests cannot distinguish "never submits" from "submits at step 8"; R5 is read as pause, not as proof of inability.
- **Unmeasured safety claims.** `tool_executor_created`, `harbor_trial_created`, and similar fields are hard-coded constants, not measurements; the only empirical safety signals are `mock_exec_calls`, `agent_step_log_created`, and tripwire counts. There is no explicit "real executor count" field; G1 relies on these proxies and on the code review of the runner.
- **Exception handling ambiguity.** `ContextGuardStop` is raised inside `complete`; if the agent loop catches generic exceptions and records `model_error`, `stop_reason` could be misclassified. Cross-check `context_guard` is non-null versus `stop_reason`, and `step_categories`.
- **Single run on one model, seed root, L40S.** No replication, no speed comparison across hardware; results may not transfer to other windows, caps, or sampler settings. The result also depends on synthetic text that is not code-like.
- **Aborts truncate the sample.** An `error:*` stops all remaining conversations, so a late error leaves paired data incomplete.

## 7. What not to do

- Do not rerun the four attempted Aider tasks (Poker, Rest API, variable-length-quantity, Hangman), even under a revised parser.
- Keep the two lyric exclusions (`beer-song`, `food-chain`); do not replace them post hoc.
- No Terminal-Bench 2 or Terminal-Bench Pro in this follow-up.
- Do not retry, resample, or change runner settings after seeing outcomes, other than one resubmission for a G3 setup failure.
- Do not report submit frequency, pass/fail, or any inferential statistic from this check; do not describe a pass (R10) as readiness for benchmarks.
- Do not store prompts, completions, or arguments; do not touch task content.

## Addendum (2026-11-27): verified code check on `stop_reason`

Checked in `environments/harbor_agent.py` (lines ~276-283) and the runner (lines ~245-253). `HarborStrategyAgent.run` catches any exception from `model.complete`, writes a step of category `model_error`, then re-raises. The runner then classifies the re-raised exception, so `stop_reason` is correct (`context_guard`, `request_ceiling` or `error:*`). Consequence: the aggregate `model_error` step count also counts every guard stop and request-ceiling stop. When scoring, **do not read `model_error` as a provider failure**. Count provider failures only from `stop_reason` starting with `error:`. This resolves design concern (e) of the draft without any code change; concern (d) (executor flags hard-coded False) remains.
