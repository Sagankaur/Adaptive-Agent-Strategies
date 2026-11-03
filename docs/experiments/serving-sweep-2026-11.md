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

On 2026-11-03, key-only access became available and the L40S one-hour request passed `sbatch --test-only`; Slurm confirmed the `short` QoS permits up to two hours. Job `4504950` failed before starting the runner because Slurm executes a spool copy of the batch script and the wrapper looked for the Python file beside that copy. Job `4504952` reached `l40s-f-01`, recorded the L40S (46,068 MiB, driver 565.57.01), Apptainer 1.3.3, and Python 3.10.12, then failed the `--help` preflight: its command omitted the SIF's `LD_LIBRARY_PATH`. No model inference ran. Both startup issues are fixed. Job `4504954` completed all 12 fit checks with 1,024 MiB headroom exceeded by at least 16,817 MiB, but Slurm marked the batch job `FAILED (1:0)` despite a `run_finished` record showing all 12 statuses as `fit_probe_passed`. Job `4504968` completed the first measured configuration (`measured`, all 21 measured batches plus warm-up recorded), but Slurm likewise marked the job `FAILED (1:0)`. The wrapper now logs the Python exit code, and the runner writes each measurement batch incrementally for the remaining configurations so the cause and any partial run are diagnosable. The first login attempt had failed DNS resolution for Rohan and Gondor, then succeeded on retry.
