# Qwen Harbor real-model smoke — 2026-10-30

## Status

**Not run.** This is the next infrastructure experiment after the scripted Harbor smoke. It is limited to one synthetic task, one Qwen request path, and one L40S allocation. It must not be reported as a Terminal-Bench result.

The current workstation could not authenticate to Rohan using its configured non-interactive SSH identity (`Permission denied (publickey,password)`). The cluster guide also requires asking A2I2 support whether an AI coding assistant operating under the user's login may run cluster commands. The prior support message added the account and recommended Apptainer but did not answer that specific question. No job was submitted in this session.

## Question

Does the project's `HarborStrategyAgent` complete the already-used synthetic terminal task with native tool calls from the real Qwen server, when Harbor and llama.cpp run in the same L40S Slurm allocation?

This smoke tests the real model-to-adapter tool-call path. It does not measure task-solving performance, validate egress isolation, or unblock TB-Pro image builds.

## Proposed run

- Allocate one L40S GPU, one model-server slot, one Harbor trial, and one attempt in a single Slurm job. Start from the existing L40S smoke request (4 CPUs, 24 GiB RAM, 20 minutes); increase wall time only if the pinned model startup needs it.
- Use the recorded Qwen3.6 GGUF, llama.cpp server image/build, and `aas-client-smoke` virtual environment. Bind the server to a job-specific `127.0.0.1` port and use the existing Qwen sampling configuration.
- Run Harbor 0.23.0 from its scratch virtual environment. The Harbor adapter and Python dependencies run in that environment; the synthetic task runs in its Apptainer container through the established job-local `singularity` shim.
- Use only the fixed synthetic file-write task. Keep task internet behavior as previously configured and explicitly mark network isolation as untested. Do not use TB-Pro, TB2, benchmark credentials, or hidden tests.
- Set a fixed run ID, unique provenance tag, and recorded seed root. Preserve the resolved Harbor job config, Slurm script/output, model server log, Harbor trial result, `aas_steps.jsonl`, and `evaluation.harbor_results` output.

## Preflight gates

1. **Access and policy:** restore authorized SSH access and obtain A2I2 support's answer about AI-assistant-operated cluster commands. The existing account-added message is not evidence of this approval.
2. **Recover the task:** locate the exact task directory and Harbor job config used by job `4407435`, or reconstruct and document an equivalent synthetic task. The repository currently records the outcome but not these task files/configuration.
3. **Validate the GPU-node runtime:** in the allocated job, confirm Apptainer 1.3.3, the job-local `singularity` shim, the SIF's `/app` working directory, and writable tmpfs. CPU-node success does not establish GPU-node behavior.
4. **Validate Qwen tool calls:** send the adapter's `terminal` and `submit` schemas to the local model endpoint and confirm the response contains parseable OpenAI-compatible `tool_calls`. If it returns text-only output, stop before Harbor and record that result.
5. **Run one trial:** after gates 1–4, launch Harbor with `n_attempts=1`, `n_concurrent_trials=1`, `agent_timeout_multiplier=2.0`, and no retries.

## Success criteria and interpretation

Pass only if Harbor records exactly one completed synthetic trial with zero harness errors, the adapter log shows a real Qwen response followed by the expected terminal and submit actions, the task artifact matches the synthetic target, and the reward is read from Harbor's persisted verifier result. Report the model/server/runtime/source pins, seed, Slurm job and GPU, trial ID, token/timing telemetry, reward, and all deviations.

A failed preflight or trial is an engineering result, not a benchmark failure. Even a pass demonstrates only that this model, adapter, and Harbor runtime can complete one toy task; it does not establish network isolation, general tool-use capability, or benchmark performance.

## Reviewed constraints

The repo's L40S client smoke requested `gpu`, QoS `short`, one L40S, 4 CPUs, 24 GiB, and 20 minutes. The Harbor adapter requires `AAS_STRATEGY_PATH` and `AAS_MODEL_BASE_URL`; it writes per-step telemetry and leaves reward extraction to Harbor's trial result reader. Harbor's pinned v0.23 CLI accepts a config file with `harbor run --config <file>`. These choices were independently reviewed against the repository notes; no remote job or local test was run for this plan.
