# Synthetic llama.cpp serving sweep design

## Intent

Prepare a reproducible, no-task serving characterization for the pinned Qwen3.6-35B-A3B Q4_K_M model and llama.cpp b11515 Apptainer image on A2I2 GPUs. The user submits the Slurm jobs and returns the JSON artifacts. The sweep screens which slot, KV-cache, and per-slot context settings fit, then measures synthetic request throughput on at most three selected configurations.

## Goals

- No benchmark tasks, task images, hidden tests, Harbor trials, or scored episodes.
- Hold the model file, server image, server flags, sampling values, and synthetic prompt format fixed across configurations except for the requested GPU, slot count, KV cache type, and per-slot context.
- Resolve the single Slurm-allocated GPU by UUID and record GPU identity, model/image hashes, server startup time, peak used VRAM, remaining VRAM, the 1 GiB headroom criterion, per-call server timings, and concurrent-batch throughput.
- Emit append-only JSON Lines in cluster scratch so an interrupted Slurm allocation retains completed configuration records.
- Keep this explicitly separate from E-P0 and G-SWEEP. It cannot estimate task-level timeouts, task throughput, solve rate, or close E-P0.

## Approaches considered

1. Run the complete 3 GPU x 3 slot x 2 cache x 2 context workload matrix at once. Rejected: 36 full benchmark configurations would consume substantial queue time, assume all GPU types/QoS are available, and obscure which configurations are worth measuring.
2. Submit every single configuration manually. Rejected: 36 submissions are cumbersome and increase the chance of inconsistent flags or logs.
3. **Chosen: two-stage, sequential workflow.** On one explicitly requested GPU type, a one-hour job starts each of the 12 slot/cache/context combinations in increasing estimated KV footprint, probes all slots with a short synthetic request batch, records fit/startup/VRAM, and stops cleanly on per-configuration failures where possible. After reviewing screens from the GPUs the user can access, run the full synthetic workload only for up to three selected configurations on one GPU, one configuration at a time. This keeps GPU selection explicit and reserves the measured workload for plausible finalists.

## Workload and measurement rules

- Per-slot contexts are 65,536 and 98,304 tokens. Because the pinned b11515 help must be checked at runtime and the documented `-c` setting represents a shared pool, set total context to `slots * per_slot_context`; set `-np` to slots. Save the server startup log so the effective context can be audited. If required flags are absent, fail before the matrix rather than silently changing settings.
- Set both K and V cache types to the selected value (`f16` or `q8_0`). Hold GPU offload at the existing smoke value, `-ngl 999`, and preserve `--jinja` and `--metrics`.
- Synthetic prompts consist of made-up user/assistant/tool-history records. Use the pinned server's `/tokenize` endpoint to produce exact token arrays; send requests to `/completion` with `cache_prompt=false`, no benchmark or task text, and a distinct deterministic seed per request.
- Fit screen: verify the running server reports the exact requested slot count and per-slot context, then concurrently submit one request per configured slot with an 8,192-token prompt and 128 generated tokens. Accept a fit only when the server, effective context, concurrent probe, and headroom checks all pass.
- Measurement mode: for each chosen configuration, submit slot-count concurrent requests at prompt targets 8,192, 32,768, 65,536, and a near-limit target of `per_slot_context - output_cap - 128` (omit duplicate targets), with output caps 512 and 2,048. This deliberately exercises the 96k context beyond the original 64k history target. Record actual timings and context-use/truncation fields. Disable prompt-cache reuse.
- Use `/tokenize` with an explicit BOS policy to build exact token ID arrays, then send numeric-token prompts to `/completion`; verify returned `prompt_n`/`tokens_evaluated` against the intended token count. Runtime preflight must establish both endpoint shapes on b11515.
- Output values are requested caps, not guaranteed generation lengths. Record realized `predicted_n` and compute throughput from realized token counts. Do not force EOS suppression unless pinned-build preflight proves that option and a separate decision is recorded.
- Measurement mode runs a warm-up batch and three measured repetitions per prompt/output cell with distinct deterministic seeds. Report median and range across repetitions; all calls in a batch start concurrently.
- Append and fsync a `config_started` JSON record before starting each server. Sample `nvidia-smi` by allocated GPU UUID at one-second intervals through startup and workload; append/flush a terminal status for each configuration. `fit` means server startup, exact effective slot/context checks, and concurrent probe succeeded and peak used VRAM leaves at least 1,024 MiB free. A server startup/OOM failure is recorded as a failed configuration, not retried with altered settings.
- Per-call `prompt_n`, `cache_n`, `prompt_ms`, `predicted_n`, `predicted_ms`, and client wall time support a provisional timing fit. Do not pool rows across GPU/model/cache/context configurations. The resulting coefficients are engineering-only; the preregistered E-P0 MCU fit still uses task-relevant calls.
- Aggregate throughput is reported for a synchronized concurrent batch as total generated tokens divided by batch wall time, alongside aggregate prompt tokens and all-token throughput. It is not called episodes per GPU-day.

## Constraints and open risks

- Existing cluster evidence is only for the Rohan `gpu` partition, `short` QoS, L40S, and the pinned b11515 image. A100 and RTX Pro 6000 type strings, QoS, driver compatibility, and runtime compatibility must be confirmed by the user's `sinfo`/site guidance before submission.
- The workstation currently cannot resolve the Rohan login hostname. Do not assume new files are staged on Rohan; the user must copy the committed files to the cluster using the working access route.
- The exact b11515 binary must accept the selected flags and expose `/tokenize` and per-call `timings`; the job performs those capability checks on the allocated node and records `--help`.
- One-hour `short` QoS eligibility is unconfirmed. Users must adjust only the requested time/QoS according to cluster policy before submission.
- Slurm must expose one unambiguous physical GPU through `CUDA_VISIBLE_DEVICES`; the runner fails closed for ambiguous mappings rather than attributing memory to another card.
- Measurements do not test Harbor, the network boundary, task behavior, or hidden tests.

## Files

- `docs/cluster/serving-sweep/01_serving_sweep.sbatch`: Slurm allocation, module setup, artifact checks, user-selected fit/measure mode, and output location.
- `docs/cluster/serving-sweep/02_model_sweep.py`: exact-token synthetic workload, server lifecycle/configuration matrix, GPU sampling, timing/throughput records, and per-configuration JSONL persistence.
- `docs/experiments/serving-sweep-2026-11.md`: prerequisites, commands, definitions, result interpretation, and empty results tables.

## Approval context

The user supplied the grid, metrics, synthetic-only boundary, approximate one-hour job budget, and asked for the Slurm job and benchmark script. Proceed with the two-stage implementation above; do not submit a Slurm job.
