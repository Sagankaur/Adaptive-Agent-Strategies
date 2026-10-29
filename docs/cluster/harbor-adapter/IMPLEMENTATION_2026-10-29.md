# Harbor adapter implementation record — 2026-10-29

## Scope and status

This is the first local G-INFRA adapter slice following the real-model client/toy-runner smoke. It adds the Harbor v0.23 agent lifecycle, per-step telemetry, a post-run reward reader, and a helper that applies the project concurrency and timeout settings. It is not a Harbor trial result and does not close G-INFRA.

## Source/API basis

The pinned Harbor v0.23.0 `BaseAgent` defines async `setup(environment)` and `run(instruction, environment, context)` methods, and `BaseEnvironment.exec(command, cwd, env, timeout_sec, user)` returns an `ExecResult`. `TrialResult` carries `id`, `task_name`, and `verifier_result`; `VerifierResult.rewards` is a mapping of reward names to numeric values. `AgentContext` carries usage counters and metadata, and the job config supports `n_concurrent_trials` and `agent_timeout_multiplier`.

Sources: [BaseAgent](https://github.com/harbor-framework/harbor/blob/v0.23.0/src/harbor/agents/base.py), [BaseEnvironment](https://github.com/harbor-framework/harbor/blob/v0.23.0/src/harbor/environments/base.py), [TrialResult](https://raw.githubusercontent.com/harbor-framework/harbor/v0.23.0/src/harbor/models/trial/result.py), [VerifierResult](https://raw.githubusercontent.com/harbor-framework/harbor/v0.23.0/src/harbor/models/verifier/result.py), [AgentContext](https://raw.githubusercontent.com/harbor-framework/harbor/v0.23.0/src/harbor/models/agent/context.py), [JobConfig](https://github.com/harbor-framework/harbor/blob/v0.23.0/src/harbor/models/job/config.py).

## Implementation

- `environments/harbor_agent.py` implements `HarborStrategyAgent` with the v0.23 lifecycle and per-trial `AsyncOpenAICompatibleModel` client.
- Strategy JSON is supplied through `AAS_STRATEGY_PATH`; model endpoint, run/provenance identity, seed root, timeout, and optional check commands use `AAS_*` settings.
- Probes and experimenter-configured own checks run through `environment.exec`; probe and check observations are returned to the model. `inspect_tests` is explicitly skipped because Harbor makes verifier tests unavailable during agent execution.
- Native `terminal` and `submit` tool calls are JSON-validated, preserved with `tool_call_id` in the next tool message, and recorded to `aas_steps.jsonl`.
- The model-request timeout and each environment command timeout are bounded by the remaining strategy wall-clock budget; Harbor's job-level timeout remains the outer backstop.
- Commands mentioning verifier or solution paths, plus the strategy's forbidden patterns, are refused. The agent does not read verifier results or call a hidden grader.
- Probe/check commands run only when the strategy permits shell use; terminal calls are blocked unless `bash` is allowed. Strategy action, check, and probe steps count against the episode step budget.
- `evaluation/harbor_results.py` reads reward only from a completed Harbor trial result's `verifier_result.rewards.reward`; missing, non-numeric, non-finite, or out-of-range values raise `HarborResultError`. It joins the Harbor trial ID to step JSONL and writes an episode-level JSONL record, aggregating token usage once per request seed.
- `evaluation/harbor_job.py` provides `configure_harbor_job()` and a runnable config resolver. It copies a supplied Harbor job mapping and forces `n_concurrent_trials` to the supplied llama.cpp slot count and `agent_timeout_multiplier` to 2.0.

## Configuration contract

Required per agent: `AAS_STRATEGY_PATH`, `AAS_MODEL_BASE_URL`, and a Harbor `model_name` or `AAS_MODEL`. Optional: `AAS_MODEL_API_KEY`, `AAS_MODEL_TIMEOUT_S` (default 7200 seconds), `AAS_SEED_ROOT` (default 20261015), `AAS_RUN_ID`, `AAS_ATTEMPT_INDEX`, `AAS_PROVENANCE_TAG`, and `AAS_CHECK_<CHECK_NAME>` for each configured own check. API keys are not written to telemetry.

Resolve a job file for the allocated model-server slots with `python -m evaluation.harbor_job --input harbor_job.yaml --output harbor_job.resolved.yaml --llama-cpp-slots 2`. The input supplies all other Harbor choices, including task data and the local Docker provider; the resolved file applies concurrency and the agent timeout multiplier.

The seed root, run identity, task name, and attempt index are combined via SHA-256 to create a stable per-attempt client seed. The client increments it per request. Harbor does not expose an attempt index on the agent lifecycle, so an orchestrator running multiple attempts for one task must provide a distinct `AAS_ATTEMPT_INDEX` to avoid repeating the same seed stream.

## Verification status and remaining gates

An independent code review found no remaining major blocker. It confirmed that command timeouts now respect the remaining strategy wall-clock budget; it also identified that repeated Harbor attempts need distinct `AAS_ATTEMPT_INDEX` values from the launcher.

### CPU smoke status

The requested scripted CPU Harbor run was attempted on 2026-10-29 but could not start because the execution host lacks its runtime prerequisites:

- `harbor` is not installed in the active Python interpreter; it is also absent from the repository `.venv` (which contains a Linux-style environment layout that is not runnable from this Windows shell).
- No `docker` executable is on PATH, the standard Docker Desktop executable path is absent, and no Docker service is registered.
- WSL distribution enumeration returned `E_ACCESSDENIED`, so no WSL container runtime could be checked or used.
- Python 3.12 is available locally, but Harbor, Pydantic, and PyYAML were absent from that interpreter. The global Python 3.14 has Pydantic/PyYAML but no Harbor. The project requires Python 3.11 or newer; Harbor 0.23.0 requires Python 3.12 or newer.

The local Windows host still cannot run Harbor because it lacks Docker and a compatible local runtime. Harbor 0.23.0 and the project's Pydantic pin are installed in the dedicated Python 3.12.16 scratch virtual environment on Rohan; see [`SSH_RETRY_2026-10-29.md`](../SSH_RETRY_2026-10-29.md) for the cluster attempts. Two CPU Slurm trials were attempted. Harbor rejected the first because Singularity cannot enforce `no-network`; the second reached image conversion but the site runtime disabled writable tmpfs under underlay, so bootstrap could not create `/app` or install the missing `/usr/bin/python3`. No agent action, verifier, reward extraction, or episode telemetry completed. Therefore the Harbor adapter still has no successful integration run; the five-task TB-Pro smoke remains gated on a Harbor-compatible runtime and the documented provider, route, network, license, budget, disk, G-BASE, and G-ROUTE checks.

### Local fixture verification — 2026-10-30

Added `tests/test_harbor_adapter.py` with offline coverage for the terminal/submit tool round trip, hidden-test-path refusal, reward validation, post-trial result joining, usage aggregation by request seed, and Harbor job settings. Conflicting token usage attached to the same request seed now fails explicitly; identical repeated rows from a multi-tool response are counted once. The full suite passed **125 tests** on local Python 3.14.5. These fixtures validate adapter logic but do not substitute for the blocked Harbor container integration run.
