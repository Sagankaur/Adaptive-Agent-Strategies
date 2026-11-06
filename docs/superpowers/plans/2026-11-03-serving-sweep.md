# Synthetic llama.cpp serving sweep Implementation Plan

> **For agentic workers:** Execute the plan task by task. Keep changes on the already-open research PR branch.

**Goal:** Deliver user-submitted Slurm and Python scripts that screen synthetic serving configurations and characterize up to three selected finalists without running benchmark tasks or episodes.

**Architecture:** A Slurm wrapper allocates one user-selected GPU and invokes a standard-library Python runner. The runner verifies pinned artifacts and exact llama.cpp capabilities, starts configurations sequentially, generates synthetic tokenized history prompts, samples GPU memory, and appends JSONL records.

**Tech Stack:** Bash, Slurm, Apptainer, llama.cpp HTTP server, Python 3 standard library.

**Spec:** `docs/superpowers/specs/2026-11-03-serving-sweep-design.md`

## Global Constraints

- Do not submit jobs or claim any model-serving results in this implementation.
- No benchmark task, benchmark-derived prompt, hidden test, Harbor task, reference solution, or scored episode may be used.
- Use the pinned Qwen model SHA and the existing llama.cpp b11515 SIF path.
- The screening matrix is slots `{1,2,4}` x K/V cache `{f16,q8_0}` x per-slot context `{65536,98304}` on one allocated GPU type at a time.
- Set total llama.cpp context to `slots * per_slot_context`; request and log K and V cache precision identically.
- The full measured mode accepts one configuration per invocation; run no more than three selected configurations after reviewing fit screens.
- Record a 1,024 MiB minimum VRAM headroom check and append results incrementally.
- Do not add or run tests in this task; implementation review and static diff checks only.

## Review Focus

- Slurm GPU type/QoS names vary by cluster and are not assumed for A100/RTX Pro 6000; keep GPU selection at `sbatch` invocation.
- The `-c` pool may be mistaken for per-slot context; calculate and log both total and requested per-slot values.
- The pinned b11515 server may lack a flag or endpoint in current upstream docs; runtime help/API preflight must stop instead of silently falling back.
- Long prompts plus generation must not exceed per-slot context; cap longest prompt accordingly and log actual context-use/truncation.
- Concurrent batch throughput must use the measured batch wall interval; do not sum per-request throughput rates.
- A failed model startup or GPU OOM must leave a record before moving on where the process remains alive.

---

### Task 1: Write run protocol

**Files:**
- Create: `docs/experiments/serving-sweep-2026-11.md`

**Interfaces:**
- Consumes: design spec and existing pinned smoke report.
- Produces: exact staged paths, user invocation for screen and measure modes, metric definitions, prerequisites, stop conditions, and empty result tables.

- [x] Describe no-task/no-episode scope and distinguish synthetic throughput from task throughput and E-P0.
- [x] Give one L40S example and leave site-specific GPU type and approved wall-time explicit to the user.
- [x] Document that the workstation cannot currently resolve Rohan; require staging the committed files and confirm inputs on Rohan before `sbatch`.
- [x] Document screen output and the measure invocation for up to three selected configurations.

### Task 2: Implement synthetic request driver

**Files:**
- Create: `docs/cluster/serving-sweep/02_model_sweep.py`

**Interfaces:**
- CLI: `python3 02_model_sweep.py --mode {screen,measure} --server-image PATH --model PATH --output-dir DIR [--gpu-label LABEL] [--slots N --kv-type TYPE --context-per-slot TOKENS]`.
- Produces: JSON Lines, server logs, GPU-memory CSV, and a capability/help capture, all under the output directory.

- [x] Verify model SHA-256; record server image SHA-256, image path, model ID, host GPU name/driver, and all launch settings.
- [x] Run pinned server `--help` inside Apptainer; require `-c`, `-np`, and K/V cache flags before screening.
- [x] Implement one-second VRAM sampling and health/startup wait with a bounded timeout, scoped to the Slurm-allocated GPU UUID.
- [x] Implement `/tokenize` prompt construction from deterministic synthetic agent-history records and `/completion` requests with prompt-cache reuse disabled.
- [x] Use `/tokenize` with explicit BOS handling, send exact token ID arrays to `/completion`, and validate returned input token counts.
- [x] Screen 12 combinations in ascending estimated cache allocation; issue one synchronized 8,192-token / 128-output request per slot after validating effective server slot/context settings.
- [x] Implement measure mode for exact requested config: 8,192, 32,768, 65,536, and per-context near-limit input targets crossed with 512/2,048 output caps, with three repetitions and one concurrent request per slot in each batch.
- [x] Run and separately record one warm-up batch before measured batches.
- [x] Treat outputs as caps, record realized output lengths, and calculate throughput from actual generated tokens.
- [x] Fsync `run_preflight_started`, `config_started`, and terminal records; include raw per-call timings, actual tokens, client wall times, aggregate throughputs, peak VRAM/headroom, errors, and truncation/context information.
- [x] Stop server and sampler after each configuration; preserve JSONL records if a later configuration fails.

### Task 3: Add Slurm job wrapper

**Files:**
- Create: `docs/cluster/serving-sweep/01_serving_sweep.sbatch`

**Interfaces:**
- Default mode `screen`; environment overrides `SWEEP_MODE`, `SWEEP_SLOTS`, `SWEEP_KV`, `SWEEP_CONTEXT_PER_SLOT`, `SWEEP_GPU_LABEL`, and `SWEEP_OUT`.
- User selects GPU type at submit time with a documented `sbatch --gpus=<site-supported-type>:1` option.

- [x] Use the evidenced Rohan GPU partition/QoS and 4 CPU/24 GiB request; leave GPU type and wall-time to explicit site-approved `sbatch` options.
- [x] Load Apptainer, validate model/SIF and Python inputs, set output under `/scratch/$USER/jobs/out/`, then invoke the Python driver.
- [x] In `screen`, pass the 12-combination screen matrix; in `measure`, require the caller to specify one slots/cache/context tuple and reject missing values.
- [x] Keep stdout/stderr and all outputs job-specific; use traps to stop child processes on cancellation.

### Task 4: Independent review and handoff

**Files:**
- Review the spec, scripts, and run protocol.

- [x] Ask the cluster-planning reviewer to check the design against context-pool semantics, QoS, and E-P0 boundaries; resolve independent-review findings on GPU attribution and effective context.
- [ ] Perform a self-review of all generated files and `git diff --check`; do not run tests or submit a cluster job.
- [ ] Summarize user-side staging/submission commands and explain which evidence to paste back.
