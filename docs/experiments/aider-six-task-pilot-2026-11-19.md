# Aider Polyglot Python feasibility pilot — protocol and task freeze

**Status:** the original six IDs remain frozen. Two lyric-generation tasks were excluded before execution; all four eligible IDs were attempted. Five Harbor trials ran because Poker needed one harness correction and retry. No trial produced a valid verifier reward, so this is a feasibility failure report, not a benchmark score.

## Purpose and claim boundary

This is an additive exploratory pilot on a benchmark separate from Terminal-Bench Pro and Terminal-Bench 2. It asks whether the pinned local gpt-oss-20b model and the project Harbor agent can complete a small, reproducibly selected set of Aider Polyglot Python coding tasks under the Apptainer network boundary. It is a feasibility check only: four eligible task IDs cannot establish a benchmark score, a treatment effect, or the efficacy of strategy adaptation/compilation.

The original planned pilot used one frozen starting strategy (`S0`), one attempt per task, no strategy editing, and Harbor's official verifier as the sole score source. Before task generation or model execution, the content-only audit identified two prompts that request song lyrics. Those two tasks were not run. The four eligible IDs were attempted; Poker has one additional trial after the initial verifier harness failure. There were no replacements and no six-task benchmark score. `restart_task` remains in the proposal but is not used or validated here. No task from Terminal-Bench 2 or Terminal-Bench Pro is involved. No Aider Oracle/reference solution was executed, inspected, copied, hashed, or encrypted.

## Frozen source and task selection

- Aider Polyglot source repository: `Aider-AI/polyglot-benchmark`, commit `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f` (default branch `main` at selection time).
- Task population: the 34 immediate directory names under `python/exercises/practice` in that commit, enumerated from Git tree metadata only.
- Selection: lexicographically sort those directory names, then use Python's `random.Random(20261119).sample(population, 6)`. The selected IDs below are sorted for display; the draw itself used the sorted full population.
- Freeze time: 2026-11-18 (local workstation; 2026-11-19 AEDT on Rohan).
- At freeze time no `.docs` task instructions, `.meta` config contents, tests, solutions, or outcomes were read. Python's exact version for the `random.Random` draw was not recorded; this is a reproducibility limitation.

| Frozen task ID | Planned Harbor task ID |
|---|---|
| `beer-song` | `polyglot_python_beer-song` |
| `food-chain` | `polyglot_python_food-chain` |
| `hangman` | `polyglot_python_hangman` |
| `poker` | `polyglot_python_poker` |
| `rest-api` | `polyglot_python_rest-api` |
| `variable-length-quantity` | `polyglot_python_variable-length-quantity` |

## Pre-run content and runtime audit amendment (2026-11-19)

This amendment was written before generating any Aider task or running any Aider model episode. The audit was limited to the six frozen tasks' `.docs` instruction files and `.meta/config.json` metadata. It did not open test files, editable source files, examples, solutions, or outcome files. The task names and IDs were frozen before this audit; no replacement IDs were selected.

| Frozen ID | Decision | Runtime note |
|---|---|---|
| `beer-song` | Exclude before execution: the prompt requests reproduction of song lyrics. | No task generated and no model output requested. |
| `food-chain` | Exclude before execution: the prompt requests reproduction of song lyrics. | No task generated and no model output requested. |
| `hangman` | Eligible for the amended feasibility subset. | The appended Python instruction says no third-party library is required; use the pinned Python 3.11 runtime and pytest. |
| `poker` | Eligible for the amended feasibility subset. | No extra dependency is declared in the inspected task instructions/config; use the pinned Python 3.11 runtime and pytest. |
| `rest-api` | Eligible for the amended feasibility subset. | No extra dependency is declared in the inspected task instructions/config; use the pinned Python 3.11 runtime and pytest. |
| `variable-length-quantity` | Eligible for the amended feasibility subset. | No extra dependency is declared in the inspected task instructions/config; use the pinned Python 3.11 runtime and pytest. |

The pinned Harbor adapter's default generator creates an Oracle solve script and encrypted Oracle payload from example/reference files, and its normal test setup copies the entire `.meta` directory. The exploratory path will therefore use [`01_generate_no_oracle_subset.py`](../cluster/aider-pilot/01_generate_no_oracle_subset.py), which imports the adapter at the pinned commit, instantiates only the four eligible frozen IDs, skips Oracle generation, and copies only declared verifier files plus `config.json`/`tests.toml` metadata. It asserts that generated outputs contain no `.oracle` artifact, Oracle solve script, or copied reference-example path. Generated tasks and raw run outputs stay on cluster scratch and will not be committed.

This amendment is a pre-run safety eligibility exclusion, not an outcome-based exclusion. This report retains the original six IDs and states **4 unique IDs attempted / 2 safety-excluded**, with no replacements and no interpretation as a six-task pass rate.

### No-Oracle task generation preflight

The pinned Harbor adapter source was reviewed without reading any benchmark tests, editable source contents, example implementations, or solutions. Its standard generation path calls `_create_solution_script`, which builds an encrypted Oracle payload from example files, and recursively copies `.meta` into the hidden verifier inputs. The custom [no-Oracle generator](../cluster/aider-pilot/01_generate_no_oracle_subset.py) instantiates only the four eligible IDs, bypasses task discovery across the full benchmark, skips Oracle script/payload creation, copies only declared verifier files and the allowlisted `config.json`/`tests.toml` metadata, and sets all three Harbor network declarations (`environment`, `agent`, and `verifier`) to `no-network` while pointing the environment at the already-built Python 3.11 SIF.

Generation succeeded for all four eligible task IDs at the pinned source commits. The manifest records `oracle_artifacts_generated: false` and `reference_example_files_copied: false`; path-only checks found zero `.oracle` directories, encrypted Oracle payloads, `solution/solve.sh` files, or copied `.meta/example*` paths. Generated task files are staged on Rohan scratch and are not in this repository. Test files are retained only as hidden inputs for Harbor's ordinary official verifier; their contents have not been opened by the audit.

The no-model runtime check has already established the pinned SIF's Python 3.11/pytest environment and Harbor's normal CLI/UDS path under `--net --network none`. The planned pilot job requests one RTX Pro 6000, 8 CPUs, and 64 GiB for the combined model and task process tree, and records the actual Slurm cgroup limits and peak RSS. Harbor itself has no hard per-task CPU/memory controls, so this is a job-level bound. The four tasks will run sequentially, one attempt each. The job is submitted only after the sbatch syntax/resource check passes.

The exact IDs and source commit are frozen before reading their task instructions. Any task that later proves incompatible with the pinned adapter/runtime remains a recorded infrastructure failure; it will not be silently replaced after inspection.

## Execution and measurements

After task generation, record each task's generated directory hash, official runtime setup, and whether its dependencies are available without task-network access. Do not run the Oracle agent, `solution/solve.sh`, or a reference implementation. Run at most one model attempt per task, sequentially, with Harbor's normal CLI lifecycle and the project `HarborStrategyAgent`.

Record for every selected task:

- Harbor verifier reward and completion status;
- whether the trial used the pinned model and frozen `S0`;
- tool/protocol errors, timeouts, retries, and tripwire flags;
- input, cached, and generated tokens; model-call and wall-clock time;
- exact SIF/model/source hashes and Slurm resource allocation;
- container egress and control-channel checks from the verified preflight.

The denominator remains six. An unrun or infrastructure-failed task is reported as such and is not dropped from the selection record. The project does not compare this pilot's rate numerically to other benchmarks or to the main proposal's planned experiments.

## Gates before the first episode

1. Keep the pinned runtime image digest/SIF hash from [the runtime preflight](aider-runtime-preflight-2026-11-19.md).
2. Generate only the four eligible frozen tasks from the pinned source commit; keep source data, generated tasks, and raw run outputs on scratch, outside the public repository.
3. Repoint each generated task to the pinned Python SIF; do not build or pull Docker images.
4. Confirm each task's runtime/setup can complete with task egress blocked and without privileged operations. If a selected task requires network access or unsupported privilege, record a failed/incompatible selected task and do not substitute another.
5. Run a model-free, official-verifier startup check only if it does not invoke an Oracle/reference solution; then run the four eligible task IDs with the same configuration. Any infrastructure retry is recorded separately and cannot replace the frozen attempt.
6. Stop before model execution if a task cannot be kept inside the verified Apptainer network namespace with Harbor control over the private Unix socket.

## Model and execution pins

- Model: `ggml-org/gpt-oss-20b-GGUF`, revision `41e8a94d15d62070b36cf4553a0250717ecf46b8`, file `gpt-oss-20b-MXFP4.gguf`, SHA-256 `27cd6c432c7672cb812a92f611cf3ba7bbc35928262bb1e1253ff4ee6ae35901`.
- Serving image: llama.cpp CUDA 12 `b11515`, SIF SHA-256 `dd8110164788b9deb354e06cb984214b2ef8b6b0598c2ef73dd0ab9828957d56`.
- Harbor: `0.23.0`, source pin `1e5c5c6db929a10a140d05e606882c671ae20729`.
- Task runtime: the pinned Aider Python runtime SIF recorded in [the preflight report](aider-runtime-preflight-2026-11-19.md).
- Attempt policy: `n_attempts=1`, `n_concurrent_trials=1`; no retries or outcome-driven tuning.
- Strategy: the repository's frozen default `S0`, serialized once before the run and hashed in the run record.

## Results and attempt accounting (2026-11-19)

The four eligible IDs were run on Rohan's RTX Pro 6000 with the pinned local gpt-oss-20b model, Harbor 0.23.0, the pinned Python 3.11 SIF, frozen `S0`, and task/agent/verifier network mode set to `no-network`. Each Slurm job requested 8 CPUs and 64 GiB; the recorded job cgroup CPU and memory limit files were empty, so hard process-tree limits were not confirmed. The model endpoint was bound to localhost and Harbor used its private Unix-socket control channel. The separate synthetic egress preflight had passed before task execution. The task-run tripwire recorded no flagged commands. This records the configured and preflight-checked boundary; it is not a fresh per-trial external-network probe.

### Run pins and request settings

- Project source commit used by the cluster job: `e09485610ba65c18ff9bda6f4d96f828c83be17f`; Harbor: `1e5c5c6db929a10a140d05e606882c671ae20729`; Aider Polyglot: `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`.
- SHA-256: model GGUF `27cd6c432c7672cb812a92f611cf3ba7bbc35928262bb1e1253ff4ee6ae35901`; llama.cpp server SIF `dd8110164788b9deb354e06cb984214b2ef8b6b0598c2ef73dd0ab9828957d56`; Python task SIF `1188aca02532530596e5e2c4642244ebb1020469ef489fe60ed55a5ea8ec56d8`; Harbor UDS provider patch `cc0aa94d13de99681d727b110e96e36ed246a8085a851f25a40d659f919fd48f`; generated-task manifest `efe21e8c51ae610cc23a77145adb95a7b9e652bb084193edd02738dd1aa84e7d`.
- The frozen S0 JSON had SHA-256 `f188aec01596b279f90867a9c7770935d4a7f917d8da0bc402631c86d48f273a`. It used full conversation history, 60 maximum steps, a 64,000-token episode budget, a 1,200-second episode wall limit, a 120-second tool-command timeout, and `run_visible_tests` before submission.
- The model client used temperature `0.6`, top-p `0.95`, top-k `20`, non-streaming requests, and a 180-second provider timeout. A deterministic seed was derived from root `20261119`, run ID, task environment name, and attempt index, then advanced per request. The server ran with one slot, `-c 8192`, `-ngl 999`, 8 generation/batch threads, `--jinja`, and metrics enabled.
- The runner used for job `4868765` had SHA-256 `03443b68d24f55af7d3869670ff79d48ae3b3ce1eeab6f032395cb262b72cb96`. After the run, the checked-in script's failure-status labeling and formatting were cleaned up; it now hashes to `f9b2d3f1821608f4ebd161f40177df67144f53333848a4e8900a328b2660786d`. No model trial was rerun after that reporting-only change.
- The per-task package hashes below cover the generated task descriptor, instructions, and verifier inputs; they exclude the agent-writable `environment/workspace` and do not encode file permissions. They were computed after the run, but these verifier inputs were not mounted writable by the agent. The sample-draw Python version was not recorded, so exact `random.Random` replay has that limitation.

| Task ID | Generated task-package SHA-256 |
|---|---|
| `hangman` | `b609f3bb026c16f7a35bb723a14540cc6882c9bee1a18352ab9add82643dd5d1` |
| `poker` | `ca3b4ddff3c485ed5d127cb64d9a903183cfb27ab5f883e5d0a0cf8f02484aa1` |
| `rest-api` | `31cae0cfccfadeba42c73ec8a4199aab0676b4c8703733bea370afc63cccb1de` |
| `variable-length-quantity` | `9f463c679eea5344ff34b8b112895b2ef482cda69f953bf36a5d679be6e896a6` |

| Task ID | Harbor trials | Result | Model calls | Tokens (input / output) |
|---|---:|---|---:|---:|
| `hangman` | 1 | Provider HTTP 400 with a context-related error; no verifier result | 10 | 39,677 / 4,895 |
| `poker` | 2 | First trial: Harbor could not execute staged `tests/test.sh`, so no verifier reward. Second trial: `HarborAgentProtocolError` because tool-call arguments were invalid JSON | 25 | 115,140 / 9,033 |
| `rest-api` | 1 | `HarborAgentProtocolError`; invalid JSON tool-call arguments | 6 | 16,572 / 4,213 |
| `variable-length-quantity` | 1 | `HarborAgentProtocolError`; invalid JSON tool-call arguments | 9 | 39,109 / 4,675 |

Across five trials there were 50 model calls, 210,498 input tokens and 22,816 output tokens. No numeric Harbor verifier reward was returned. These are **unscored failures**, not four zero scores: task correctness was not established. The run therefore yields no pass rate and no task-quality claim. The full sanitized attempt record is in [the result artifact](artifacts/aider_six_task_pilot_2026-11-19/results.json); raw prompts, commands, task files and logs remain on cluster scratch.

Three execution details matter for interpretation:

1. Job `4868759` attempted Hangman. The model reached a context-related HTTP 400 after repeated long-running tool calls; the first runner version then stopped when it assumed every trial had a reward. Slurm marked the wrapper `FAILED 1:0`; this does not indicate a Slurm allocation failure.
2. Job `4868761` ran only Poker because the task-list environment variable was truncated by Slurm's comma-separated `--export` syntax. The Harbor verifier then reported that `tests/test.sh` was not executable. The task staging code now preserves the executable bit, and the task selection is passed through the job environment correctly. The later Poker retry ended before verification, so the executable-bit fix has not yet been confirmed end to end.
3. Job `4868765` ran the corrected Poker retry, Rest API, and variable-length-quantity. The corrected job completed at Slurm level, but each trial ended with malformed JSON tool-call arguments before a verifier reward was produced.

The harness correction is documented and retained in the generator. It does not change the task sample, model, prompt, strategy, or scoring rule. Poker's first trial remains part of the attempt record; it is not silently dropped. The summary reports four unique eligible task IDs attempted, two safety exclusions, and one extra harness-retry trial.

### Interpretation and next gate

The setup stack can launch gpt-oss inside Harbor and execute task tools with the configured no-network mode, but the current model-to-agent interface is not reliable enough for a task benchmark: malformed tool-call JSON occurred on three task IDs, and the remaining task stopped at a context-related provider error. The server context was only 8,192 tokens while S0 retained the full history. That is a plausible contributor to the context error and possibly the malformed tool calls, but the run does not establish causality. The synthetic one-tool smoke did not predict this multi-step behavior.

Do not rerun these same tasks under a changed parser and present the result as this pilot. The next step is a separately logged, no-benchmark **tool-contract diagnostic** using synthetic tool schemas: quantify valid/invalid gpt-oss argument JSON over a fixed request set, then fix or reject the model/adapter combination. If a follow-up task pilot is justified, amend its protocol first and use a fresh predeclared task sample. The main proposal and its existing gates remain unchanged.

## Why these are not benchmark results

The four selected Aider tasks did run, but Harbor returned no numeric verifier reward for any trial. The completed runtime preflight and synthetic gpt-oss Harbor smoke establish setup behavior only. This pilot establishes a model/agent integration failure, not Aider task performance.

## Sources

- Harbor's pinned [Aider Polyglot adapter](https://github.com/harbor-framework/harbor/tree/1e5c5c6db929a10a140d05e606882c671ae20729/adapters/aider_polyglot) and [Python runtime generator](https://github.com/harbor-framework/harbor/blob/1e5c5c6db929a10a140d05e606882c671ae20729/adapters/aider_polyglot/src/aider_polyglot/utils.py).
- Aider Polyglot source repository at frozen commit [`7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`](https://github.com/Aider-AI/polyglot-benchmark/tree/7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f).
- gpt-oss model pin and serving result in [the serving-only smoke report](gpt-oss-serving-smoke-2026-11-17.md).

## Post-pilot update (2026-11-25 AEDT)

The task-free tool-contract follow-up is now recorded in the [tool protocol diagnostic](aider-tool-protocol-diagnostic-2026-11-20.md). At a 1,024-token cap, 23/24 first requests returned a valid terminal call, up from 10/24 at 512 tokens, but terminal-then-submit completed only 1/24 at either cap under that synthetic prompt. This does not establish Aider performance. Separately, the earlier [real-model Harbor synthetic smoke](gpt-oss-harbor-synthetic-smoke-2026-11-19.md) completed its simple file-write task in two requests; it establishes basic integration only. The [current no-model egress/UDS recheck](harbor-egress-safety-2026-11.md#reverification-on-rohan-2026-11-25-aedt) passed on Rohan as job `4889803`.

**Recommended next gate:** run a task-free, real-model Harbor stress check through the actual `HarborStrategyAgent` and `S0` prompt at longer synthetic history, with the verified Apptainer network isolation and UDS control channel. Do not rerun the four attempted Aider tasks. If the actual Harbor flow remains stable at the tested history lengths, then predeclare a fresh Aider task sample and protocol before any new benchmark episode. Keep the two lyric-related exclusions, and do not involve Terminal-Bench 2 or Terminal-Bench Pro in this follow-up.
