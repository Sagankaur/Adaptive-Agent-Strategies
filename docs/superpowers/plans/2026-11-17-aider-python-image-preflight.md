# Aider Python Image Preflight Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Determine whether a Python 3.11 Aider-style task runtime can run a synthetic pytest check inside Apptainer with task egress disabled while Harbor control continues over its private Unix socket.

**Architecture:** Pull a Python 3.11 OCI image into a SIF on a CPU Slurm job and stage pinned pytest plus Harbor execution-server wheels outside the task container. Run a no-model Harbor 0.23.0 provider smoke using the existing Unix-socket patch and a network-free bootstrap, then check offline pytest, a synthetic fixture, mounts, external-IP/DNS/metadata blocking, and socket cleanup.

**Tech Stack:** Rohan Slurm CPU queue, Apptainer 1.3.3, Harbor 0.23.0, the existing UDS provider patch, Python 3.11, pytest with a local wheelhouse.

**Spec:** `docs/experiments/ALT-MODEL-BENCHMARK-PILOT-2026-11-16.md` and `docs/experiments/harbor-egress-safety-2026-11.md`.

## Global Constraints

- No model, agent, benchmark task, task instructions, Oracle, or reference solution runs during this preflight.
- Keep task network disabled with `--net --network none`; preserve Harbor control only through the per-run Unix socket.
- Do not use `--fakeroot`; use `--writable-tmpfs` for the test run.
- Do not work around missing Slurm cgroups or claim resource limits are verified.
- Keep run artifacts under scratch and publish only sanitized, minimal evidence.
- Preserve the separate pilot branch and leave the primary proposal unchanged.

## Review Focus

- **Image drift:** record source tag and SIF SHA-256; do not call a mutable tag immutable.
- **Offline dependency install:** prove pip uses only the local wheelhouse and fails if a wheel is missing.
- **Isolation evidence:** require external fixed-IP, DNS, and metadata requests to fail inside the generic Python 3.11 SIF; do not claim it is the Aider adapter image.
- **Control-channel evidence:** require a nonce round trip over UDS with no TCP fallback and socket cleanup. Label this provider-level testing, not a Harbor CLI trial.
- **Scope clarity:** report this only as synthetic runtime compatibility, not an Aider benchmark episode or task-image equivalence.

---

### Task 1: Stage a Python 3.11 runtime and pinned pytest wheelhouse

**Files:**
- Create: `docs/cluster/harbor-egress-safety/04_aider_python_preflight.sbatch`
- Create: `docs/cluster/harbor-egress-safety/04_aider_python_preflight.py`
- Test: the Slurm preflight itself, using only synthetic fixture code.

**Interfaces:**
- The batch script pulls `python:3.11-slim` to a SIF, records the resulting SIF checksum, downloads a pinned pytest wheel set with the Harbor venv's pip, and invokes the Python harness.
- The harness accepts explicit `--image`, `--wheelhouse`, `--fixture-dir`, and `--output` paths and uses the existing Harbor 0.23.0 `SingularityEnvironment` UDS patch.

- [x] Stage the new files and the existing UDS patch on Rohan using key-only SSH.
- [x] Check available scratch and keep use at 66%, below the cluster's 80% guidance threshold.
- [x] Submit the short CPU preflight. Python 3.11 SIF and wheel hashes are recorded; no model or benchmark task was invoked.

### Task 2: Run the no-model offline pytest and isolation probe

**Files:**
- Modify: `docs/cluster/harbor-egress-safety/04_aider_python_preflight.py`
- Record: `docs/experiments/aider-python-image-preflight-2026-11-17.md`

**Interfaces:**
- The harness starts the patched provider with `--net --network none --writable-tmpfs --containall` and binds the wheelhouse and one synthetic pytest file read-only.
- The synthetic test checks Python 3.11 and a trivial deterministic function. It contains no benchmark data or task instructions.

- [x] Require provider UDS health and nonce `environment.exec` to pass with no TCP port.
- [x] Require offline pytest installation and the synthetic test to pass.
- [x] Require egress checks to block a fixed external IP, external DNS, and `169.254.169.254`.
- [x] Require provider shutdown and UDS cleanup.
- [x] Record `sacct`, image and wheel hashes, pip's offline configuration, check outcomes, and limitations in the run report.
- [x] Independent review found and fixed a missing rootless-Docker socket/environment audit; the final job passed the expanded check.

### Task 3: Review and update the draft pilot PR

**Files:**
- Modify: the Aider pilot and serving-smoke run records as needed.

- [x] Ask an independent reviewer to check safety scope, reproducibility, privacy, and claim strength; retain the limitations that this bypasses the normal Harbor constructor/trial and uses a generic image.
- [x] Run `git diff --check` and `bash -n` on the Slurm script; the patch also passed a dry-run against the installed Harbor 0.23.0 source.
- [x] Complete a normal Harbor CLI synthetic trial (job 4801512), confirm effective `:ro` mounts from both argv and `/proc/self/mountinfo`, UDS cleanup, egress probes, and the pinned offline pytest run. Record the earlier writable-mount finding, failed setup attempts, and best-effort artifact `su root` failure in `docs/experiments/harbor-cli-egress-preflight-2026-11-17.md`.
- [ ] Build the task image matching the pinned Aider adapter runtime, establish whether its tasks need root operations or complete artifact collection, and resolve task-level resource enforcement.
- [ ] Commit and push only to `experiment-aider-nonqwen-pilot`; do not merge PR #1 or PR #2.
- [ ] Report CI status and keep model episodes paused until an exact Aider task image passes a no-model Harbor CLI trial with egress, UDS, mount, cleanup, and resource checks.
