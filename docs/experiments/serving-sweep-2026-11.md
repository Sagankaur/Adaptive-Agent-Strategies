# Synthetic serving sweep — 2026-11

## Purpose and boundary

This is an engineering preflight for the pinned Qwen3.6-35B-A3B Q4_K_M server on the A2I2 cluster. It uses made-up agent-history prompts only. It runs **zero episodes**, no Harbor task, no TB-Pro/TB2 data, no task image, no hidden test, and no reference solution.

The preflight screens fit for the 12 combinations of slots `{1, 2, 4}`, K/V cache `{f16, q8_0}`, and context-per-slot `{65,536, 98,304}` on one explicitly allocated GPU type per job. After comparing GPUs and fit results, use measurement mode for no more than three selected configurations. This does not measure task throughput, episode timeouts, solve rate, or close E-P0/G-SWEEP. The E-P0 task-based sweep remains required.

## Pinned inputs

- Model: `/scratch/$USER/models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`
- Required SHA-256: `ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61`
- Existing server image: `/scratch/$USER/images/llama-server-cuda12-b11515.sif`
- Existing server image reference: `ghcr.io/ggml-org/llama.cpp:server-cuda12-b11515`
- Scripts: `docs/cluster/serving-sweep/01_serving_sweep.sbatch` and `02_model_sweep.py`

The runner recomputes the model hash and stops on a mismatch. It records the SIF hash, but there is no earlier SIF digest in the repo to compare against; make sure the SIF is the same b11515 image used by the prior smoke. At job start, it saves `llama-server --help` from that image and stops if required flags are absent.

## Before submission

On Rohan, stage this committed directory under a scratch path and submit from the directory containing both files. The batch wrapper uses Slurm's `SLURM_SUBMIT_DIR` because Slurm copies the `.sbatch` file into its spool directory before execution.

Check the GPU types and time limits offered to your account before submission. Existing run evidence supports Rohan `gpu`/`short`, one L40S, 4 CPUs and 24 GiB RAM. The job uses the `gpu` partition, `short` QoS, 4 CPUs and 24 GiB RAM. It deliberately has no GPU-type or wall-time default: pass the exact GPU type and an approved time on the `sbatch` command. The one-hour `short` request and A100/RTX Pro resource labels are not verified. The runner also requires Slurm to expose exactly one unambiguous GPU and records/samples that GPU by UUID.

Examples after staging and confirming the site GPU type string:

```bash
# Screen all 12 configurations on one L40S.
cd /scratch/$USER/jobs/serving-sweep/repo/docs/cluster/serving-sweep
SWEEP_GPU_LABEL=l40s sbatch --gpus=l40s:1 --time=01:00:00 01_serving_sweep.sbatch

# After reviewing screens, measure one selected configuration.
SWEEP_MODE=measure \
SWEEP_GPU_LABEL=l40s \
SWEEP_SLOTS=2 \
SWEEP_KV=q8_0 \
SWEEP_CONTEXT_PER_SLOT=65536 \
sbatch --gpus=l40s:1 --time=01:00:00 01_serving_sweep.sbatch
```

For A100 or RTX Pro 6000, replace `l40s` with the exact type shown by the cluster and confirm it is allowed by the selected QoS. Run each GPU screen sequentially; concurrent jobs would distort throughput and VRAM measurements. If the short QoS rejects one hour, use the supported time/QoS or shorten the screen allocation according to support guidance.

## What the scripts do

### Fit screen

The Python runner sorts the 12 configurations by estimated KV allocation from smaller to larger. Each configuration gets its own server startup and log. Total llama.cpp context is set to `slots * context_per_slot`, with `-np` set to slots and both `-ctk` and `-ctv` set to the selected precision. It verifies `/slots` reports the requested slot count and exact effective per-slot context before any fit pass is accepted. The runner starts one synthetic 8,192-token prompt and 128-token output request per slot concurrently, then records startup time and one-second VRAM samples for the allocated GPU UUID. Failures remain in the JSONL record; settings are not silently changed.

A configuration is a fit-screen pass only when the server loads, all concurrent probe requests return valid timing data, and sampled peak VRAM leaves at least 1,024 MiB free. Server logs and `server_props` are saved so requested and effective context settings can be audited. The screen probe does not measure long-prompt throughput.

### Measurement mode

Measurement mode handles exactly one configuration per job. It runs a warm-up batch, then three synchronized concurrent repetitions for each valid prompt/output cell. Prompt targets are 8,192, 32,768, 65,536, plus a near-limit prompt target of `context_per_slot - output_cap - 128` (duplicate targets are omitted). Output values 512 and 2,048 are caps; the model may stop early, and calculations use actual generated tokens.

The script constructs deterministic synthetic user/assistant/tool-history text, asks that same pinned server to tokenize it with an explicit BOS policy, sends the exact token IDs to `/completion`, disables prompt-cache reuse, and checks reported prompt-token counts against the sent token IDs. Each call uses a distinct seed. The runner records server timing fields (`prompt_n`, `cache_n`, `prompt_ms`, `predicted_n`, `predicted_ms`), client wall time, generated tokens, context/truncation information, and batch throughput.

For each concurrent batch, aggregate prompt, generated, and total token throughput are sums of realized token counts divided by the measured batch wall interval. Per-call speeds and latency are also retained. Report medians and ranges over the three repetitions. Do not pool timings across GPUs, models, cache modes, context sizes, or server builds when fitting provisional timing coefficients.

## Outputs and interpretation

The job writes under `/scratch/$USER/jobs/out/serving_sweep_$SLURM_JOB_ID/`:

- `metadata.json`: host/GPU/driver, model and SIF hashes, server image reference, sampling, and job information;
- `screen.jsonl` or `measure.jsonl`: append-and-fsync run, config-start, batch and config-finish records;
- `gpu-memory.csv`: per-configuration VRAM/utilization samples;
- `llama-server-help.txt` and one server log per configuration.

Paste `metadata.json`, the JSONL result, GPU type/Slurm job ID, and any relevant server log excerpt back for review. Keep the raw files on scratch until copied to RDS. Do not report a synthetic result as episodes per GPU-day or task-level cost. The 213.5 episodes/GPU-day value remains a planning proxy; this sweep can compare synthetic request throughput only. E-P0 still measures task-level throughput, timeouts, and its registered MCU fit.

## Research record

Record the GPU name, requested resource string, Slurm QoS, driver, model/SIF hashes, every flag, exact prompt/output token counts, cache hits, timing fields, repeated-batch summaries, peak VRAM/headroom, and all failed configurations. The upstream server API options are documented in the [llama.cpp server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md); that current documentation is a reference only, and the job checks the exact pinned b11515 binary before using its flags/endpoints.

## Completed engineering run (2026-11-03)

Key-only SSH access worked through Rohan's pinned login IP. The synthetic sweep ran sequentially on one Rohan L40S and one Rohan RTX Pro 6000 Blackwell. Slurm allowed one-hour jobs on `gpu`/`short`. The six completed experiment jobs used Apptainer 1.3.3, Python 3.10.12, llama.cpp build `b11515-3d65c90d0`, the same pinned Qwen model SHA-256 above, and SIF SHA-256 `dd8110164788b9deb354e06cb984214b2ef8b6b0598c2ef73dd0ab9828957d56`. No Harbor task, benchmark task, dataset, hidden test, reference solution, or episode was run.

### Fit screens

| Job | GPU | Fit results | Highest sampled use | Lowest sampled headroom | Startup range |
| --- | --- | ---: | ---: | ---: | ---: |
| 4504954 | L40S, 46,068 MiB | 12/12 pass | 29,251 MiB | 16,817 MiB | 14.35–14.71 s |
| 4505018 | RTX Pro 6000 Blackwell, 97,887 MiB | 12/12 pass | 29,427 MiB | 68,460 MiB | 27.46–41.06 s |

Every requested slot count, KV precision, and per-slot context matched the server's effective settings. All fit probes passed with more than the 1 GiB minimum. The RTX startup range differs from its later measurement run (13.10 s); startup time was not isolated from node and filesystem cache state, so treat these as observed run values, not a controlled GPU startup comparison.

### Measurement jobs

Each measured configuration recorded one warm-up batch plus 21 measured batches: seven prompt/output cells, three synchronized concurrent repetitions per cell. The cells use prompt targets of 8,192, 32,768, 63,360, and 64,896 tokens (duplicate near-limit targets omitted) and output caps of 512 or 2,048. At four slots, this is 12 calls per cell. The runner marked every configuration `measured`; all calls succeeded. Exact prompt lengths, actual generated lengths, llama.cpp timings, client wall times, and one-second GPU samples are in the JSONL artifacts.

| Job | GPU | Slots / KV / context per slot | Peak sampled use | Headroom at peak | Startup |
| --- | --- | --- | ---: | ---: | ---: |
| 4504968 | L40S | 1 / q8_0 / 65,536 | 22,107 MiB | 23,961 MiB | 14.44 s |
| 4504971 | L40S | 4 / q8_0 / 65,536 | 24,721 MiB | 21,347 MiB | 14.65 s |
| 4505001 | L40S | 4 / f16 / 65,536 | 26,661 MiB | 19,407 MiB | 14.31 s |
| 4505019 | RTX Pro 6000 Blackwell | 4 / q8_0 / 65,536 | 24,897 MiB | 72,990 MiB | 13.10 s |

The following representative cell uses a 64,896-token prompt and a 512-token output cap (the near-context-limit prompt cell). Prompt and generation speeds are medians of per-call llama.cpp timing fields across 12 calls. “Aggregate prompt + generated” is the median across three concurrent batches of realized prompt plus output tokens divided by batch wall time. Throughput ranges cover the three batches; per-call speed, latency, and realized-output ranges cover the 12 calls.

| GPU / setting | Per-call prompt tok/s | Per-call generation tok/s | Aggregate prompt + generated tok/s | Median call wall | Actual output tokens, median (range) |
| --- | ---: | ---: | ---: | ---: | ---: |
| L40S, 4 slots, q8_0 | 4,889 (4,770–5,244) | 20.4 (2.6–66.5) | 4,504 (4,450–4,525) | 57.4 s | 512 (78–512) |
| L40S, 4 slots, f16 | 4,989 (4,854–5,320) | 20.2 (6.8–51.2) | 4,353 (4,346–4,625) | 59.2 s | 512 (180–512) |
| RTX Pro 6000, 4 slots, q8_0 | 6,803 (6,671–7,315) | 27.6 (12.4–76.8) | 6,062 (6,045–6,072) | 42.8 s | 512 (376–512) |

The full 28-cell summary across all four measured GPU configurations is in [serving-sweep-cells-2026-11.md](serving-sweep-cells-2026-11.md); the JSONL files retain each individual call and batch.

In this cell, the RTX Pro's median aggregate throughput was about 1.35× the L40S q8_0 result. This is an engineering comparison for one model, build, and synthetic input shape, based on three batch repetitions; it is not a general GPU ranking. The output cap is not a fixed generation length: the model stopped early on some calls, as the ranges show. At a 63,360-token prompt with a 2,048-token cap, median aggregate throughput was 3,143 tok/s on L40S q8_0 and 2,883 tok/s on L40S f16; both had a median realized output of 2,048 tokens. The f16 and q8_0 order therefore depends on workload shape, and this sweep does not justify a universal cache-precision choice.

### Slurm exit-status cause

The six experiment jobs (`4504954`, `4504968`, `4504971`, `4505001`, `4505018`, `4505019`) remain recorded by Slurm as `FAILED`, exit `1:0`, although their runner records completed successfully. The wrapper used `#!/bin/bash -l` and ended with the `exit` builtin. In an Ubuntu login shell, that invokes `~/.bash_logout`; the default logout command's `clear_console` condition can return 1 and replace the intended job status. This was reproduced in an Ubuntu 24.04 container (`exit 0` yielded status 1; reaching end-of-file after a successful command yielded status 0).

The wrapper now ends with `(exit "$STATUS")` as its last command. This returns the runner status without invoking the login-shell `exit` builtin and leaves the signal handler unchanged. A one-minute CPU-only Rohan job is still required to confirm `sacct` reports `COMPLETED 0:0`; the current key-only SSH attempt could not resolve the Rohan hostname, so that cluster confirmation is pending.

### Interpretation and limits

- All 12 settings fit on the L40S, with at least 16.8 GiB of sampled headroom. The L40S is memory-sufficient for this pinned model and these contexts. The RTX Pro delivered about 35% higher aggregate throughput in the matched 64.9K/512 cell and substantially more memory headroom; request the RTX Pro when available throughput matters. An A100 was not tested.
- The one-second sampler reads whole-device memory and can miss brief peaks. GPU utilization by other processes was not independently audited.
- Inputs are repetitive synthetic token-ID histories, not real Harbor or agent traces. The per-call timings do not measure task/tool overhead, solve rate, timeouts, episode throughput, or cost per task.
- These data do not fit MCU coefficients or validate the 213.5 episodes/GPU-day planning proxy. They do not count as E-P0 and do not close any benchmark gate.
- The raw outputs are under `docs/experiments/artifacts/serving_sweep_<job-id>/`. They have been copied to this repository, but an RDS collection has not yet been configured; cluster scratch remains volatile.

### Professor-ready update

> We completed a synthetic serving preflight for the pinned Qwen model on Rohan. All 12 tested slot/cache/context settings fit on an L40S with at least 16.8 GiB sampled headroom. On a matched 4-slot q8_0 near-limit prompt cell, the RTX Pro 6000 delivered about 1.35× the L40S aggregate throughput (6,062 vs. 4,504 realized prompt-plus-generation tokens/s, three batch repetitions). These are engineering measurements from synthetic histories only; no benchmark episodes ran and E-P0 remains open. Slurm marks the jobs failed despite complete runner records (including exit status 0 for the latest jobs), so we are asking cluster support to explain the accounting discrepancy.

### Next steps

1. Ask A2I2 support why these batch steps are `FAILED 1:0` while the wrapper exits 0 and the derived exit code is 0; include jobs `4505001`, `4505018`, and `4505019`.
2. Configure the RDS Activity/Collection and copy the report and raw artifacts there. Keep the local/GitHub copies as convenient working copies, not the sole long-term research-data store.
3. When the TB-Pro image/licence route and Harbor network questions are resolved, run the registered task-based E-P0 with the RTX Pro as the preferred throughput option and the L40S as the available fallback. Use actual task/episode measurements to pick the production serving configuration and fit any MCU coefficients.
