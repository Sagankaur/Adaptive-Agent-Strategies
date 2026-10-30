# Qwen Harbor real-model smoke — 2026-10-30

## Status

**Passed as a synthetic infrastructure smoke.** Slurm job `4410693` ran one real Qwen-backed Harbor trial on Rohan's L40S with reward `1.0` and zero harness errors. This establishes that the project adapter receives and executes native Qwen tool calls inside Harbor on this runtime. It is not a Terminal-Bench result and does not close the TB-Pro route, network-isolation, or baseline gates.

## Question and scope

Does the project's `HarborStrategyAgent` complete the already-used synthetic terminal task with native tool calls from the real Qwen server, when Harbor and llama.cpp run in the same L40S Slurm allocation?

Only the synthetic file-write task was run. No TB-Pro or TB2 data, benchmark credentials, or hidden tests were used. The task has `allow_internet = true`; egress restriction was not tested. Cluster use approval was confirmed before submission.

## Pinned setup

| Component | Value |
|---|---|
| Slurm | Job `4410693`; partition `gpu`; QoS `short`; one L40S; 4 CPUs; 24 GiB RAM; 30-minute limit; completed in 1:34 with exit `0:0` |
| Node/GPU | `l40s-f-03`; NVIDIA L40S, 46,068 MiB; driver `565.57.01` |
| Harbor | `0.23.0`; host venv `/scratch/$USER/venvs/harbor-0.23.0` |
| Task runtime | Apptainer `1.3.3+342-g42a8ae13e`; the task SIF's writable `/app` probe passed on the GPU node; its Python is `3.12.16` |
| Model | `Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`, revision `a483e9e6cbd595906af30beda3187c2663a1118c`, SHA-256 `ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61`; model size and source are recorded in the [L40S client report](../cluster/l40s-client-smoke/REPORT.md) |
| Server | llama.cpp build `b11515`, image `ghcr.io/ggml-org/llama.cpp:server-cuda12-b11515`, Apptainer with `--nv`, `--jinja`, one slot, 16,384 context; bound to `127.0.0.1:32693` |
| Sampling | temperature `0.6`, top-p `0.95`, top-k `20`; request seeds logged by the project client |
| Project source | Runtime source snapshot at commit `639ba1d`; Slurm script added in commit `ecaa114` |
| Task/strategy | Reused `/scratch/$USER/harbor-smoke/task_apptainer` and `strategy.json` from scripted job `4407435`; task ID `task_apptainer`; strategy ID `s0`, hash `775e61943df0c399843103d207226d9987dd350dabf4fde00b960fdbe5edc178` |

The reused `s0` fixture is the bounded strategy saved for the scripted smoke: 8 steps, 1,000 generated tokens, 90 seconds, no probes, and no own checks. It is not the full default S0 configuration and this run is not a baseline score.

## Results

The model server became healthy after about 64 seconds. Before starting Harbor, the project's async client sent the adapter's `terminal` and `submit` schemas to Qwen. Qwen returned a parseable native `terminal` call with command `echo "harbor smoke passed" > /app/output.txt`: 379 prompt tokens, 191 generated tokens, 1.77 seconds, seed `20261030`.

Harbor then completed exactly one trial, with no retries or exceptions. The agent made three model requests and logged the actions `terminal`, `terminal`, `submit`; the second terminal call read back the file contents. All tool calls returned exit code 0. The persisted Harbor trial result reported `verifier_result.rewards.reward = 1.0`; `evaluation.harbor_results` read that saved reward and wrote the episode record.

| Trial measure | Result |
|---|---:|
| Harbor trial ID | `da8780a6-c048-4af2-9774-0e2e14a04634` |
| Completed / errored / retried | `1 / 0 / 0` |
| Reward / success | `1.0 / true` |
| Adapter actions | `terminal`, `terminal`, `submit` |
| Harbor prompt / cached / generated tokens | `2,014 / 1,405 / 201` |
| Sum of model-request elapsed times | `1.76 s` |

## Artifacts

Cluster scratch output is at `/scratch/$USER/harbor-smoke/real-qwen/4410693/`. The job stdout is `/scratch/$USER/harbor-smoke/real-qwen-4410693.out`; stderr is `/scratch/$USER/harbor-smoke/real-qwen-4410693.err`. The folder contains the server log, native-tool-call preflight, Harbor job config, Harbor job/trial results, project episode record, and adapter step log.

SHA-256 hashes for the result artifacts:

| Artifact | SHA-256 |
|---|---|
| `tool-call-preflight.json` | `50c5b11f90afcdb67140c5879457bb28364cee0418b6b8e26859ecd86d970054` |
| `harbor-evaluation.json` | `abc2decfe0bee5555182c440ca43c57cfc3609a6fbca6f3bda021114b9d9fde4` |
| `episode.jsonl` | `d7e2b490ae9bcfb75070a491aed1f7b95a6886eb108ef2ef2183c053d75ac6e8` |
| Harbor job `result.json` | `04ad5f9d00be1fc78a06b6f39ca32d1b0b2fd0e150401f77391fc118fe7b2e81` |
| Harbor trial `result.json` | `9b1d1b4ba3fd6cbccef420e7e214aa88ca57a0f1c96621fda0cbe2c6e4abbf39` |
| `aas_steps.jsonl` | `9a1e4afdf455266a1474be473b768d2167a47cdc8e079254fc742acb11c3c3a3` |
| `server.log` | `d63fcb373edd571e10f702d26dc32d9743bd8fe2cedc0adfad043ed89811f20d` |

The reusable Slurm job is [`01_qwen_harbor_smoke.sbatch`](../cluster/harbor-real-model-smoke/01_qwen_harbor_smoke.sbatch). The raw step log remains on scratch; its hash is recorded above.

## Interpretation and remaining gates

This closes the real-model-on-Harbor toy smoke: Qwen produced native function calls, the adapter executed them, Harbor ran the task container on an L40S allocation, and reward was joined from Harbor's persisted result. The pass is limited to this one synthetic task and the bounded `s0` fixture.

Network isolation remains untested because the task allowed internet. The five-task TB-Pro smoke is still gated on the P-M2 image/license route, the G-BASE audit, approved egress controls, and the remaining cluster-use conditions. No benchmark episode has run.
