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

Corrected runner: `docs/cluster/aider-pilot/04_harbor_s0_history_check.py`; batch job: `docs/cluster/aider-pilot/04_harbor_s0_history_check.sbatch`. A retry is pending after the correction is pushed.
