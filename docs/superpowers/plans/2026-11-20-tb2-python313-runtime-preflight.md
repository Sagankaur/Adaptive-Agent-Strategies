# TB2 Python 3.13 Runtime Preflight Plan

> **Status:** In progress. This is a new model-free infrastructure check; it does not resume the stopped 2026-11-19 pilot.

**Goal:** Test whether Harbor 0.23.0 can use Python 3.13 already present in the pinned task SIF while preserving a private UDS control channel and verified network isolation.

**Architecture:** Download binary Harbor-server dependency wheels in a CPU setup job using the task SIF's Python 3.13.7, write a version-and-hash lock, install them offline into a dedicated scratch directory, and mount that directory read-only in a second CPU job. The second job installs the existing UDS patch and custom bootstrap into a job-local Harbor overlay, then runs scripted checks against the exact pinned SIF.

**Tech Stack:** Slurm, Apptainer 1.3.3, Harbor 0.23.0, Python 3.13.7, FastAPI 0.162.0, Pydantic 2.13.5, Uvicorn 0.54.0.

**Spec:** `docs/experiments/TB2-HARBOR-PYTHON313-RUNTIME-PREFLIGHT-2026-11-20.md`

## Global Constraints

- Task: `cobol-modernization`; SIF SHA-256 must remain `e7fc37ce09d4ee50e4a71a6e2c9941c0cdacdeb979fcaf99182728b3d0e0dd49`.
- The new preflight uses no model, agent trial, task setup script, Oracle, reference solution, or verifier.
- The task container must use `--net --network none --writable-tmpfs --containall`, a private UDS, and no `--fakeroot`.
- Network access in the first CPU job is only for downloading binary wheels; installation into the runtime is offline and hash-checked.
- The runtime dependency directory is mounted read-only in the exact-image check.
- Do not start a model episode until this preflight passes and a separate model-run preregistration is reviewed.
- Preserve the stopped status and result of the 2026-11-19 attempt.

## Review Focus

- Runtime wheels must be compatible with Linux x86-64 CPython 3.13 and include pinned transitive versions and hashes.
- Bootstrap must verify Python 3.13.7 and load each server dependency from `/runtime-deps`.
- Harbor's actual provider path, not a direct Apptainer approximation, must pass UDS health and `environment.exec`.
- Effective routes, DNS, fixed-IP egress, metadata egress, read-only mounts, and workspace visibility must all be checked in the exact SIF.
- A failure stops the route; it does not relax isolation or automatically launch a model.

---

### Task 1: Build a reproducible offline runtime

**Files:**
- Create: `docs/cluster/tb2-pilot/04_prepare_harbor_runtime.py`
- Create: `docs/cluster/tb2-pilot/04_prepare_harbor_runtime.sbatch`
- Modify: `docs/cluster/tb2-pilot/bootstrap_harbor_python3.sh`

- [ ] Download only binary wheels for the pinned server packages through the task image's Python 3.13.7.
- [ ] Generate a complete lock containing every wheel's name, version, and SHA-256.
- [ ] Install offline with `--require-hashes`; run `pip check` and import/version/origin checks inside the exact SIF.
- [ ] Make the runtime and wheelhouse non-writable and record their deterministic hashes in a manifest.

### Task 2: Exercise Harbor on the exact task image

**Files:**
- Modify: `docs/cluster/tb2-pilot/03_task_workspace_path_preflight.py`
- Create: `docs/cluster/tb2-pilot/05_exact_runtime_preflight.sbatch`
- Modify: `docs/cluster/tb2-pilot/README.md`

- [ ] Use the exact Python 3.13 bootstrap and a read-only runtime mount in the patched Harbor provider.
- [ ] Check Harbor UDS health, a nonce round trip, harmless `/app` write, dependency origin/version, read-only mount, path-only workspace guard, loopback-only routes, DNS failure, external-IP failure, and metadata-IP failure.
- [ ] Capture and assert the actual Apptainer argv, including network-none and UDS flags, read-only runtime bind, writable tmpfs, containall, and absence of fakeroot.
- [ ] Record pass/fail and hashes without copying raw task logs into Git.

### Task 3: Review and disposition

**Files:**
- Create: `docs/experiments/TB2-HARBOR-PYTHON313-RUNTIME-PREFLIGHT-2026-11-20.md`
- Modify: `docs/DECISIONS.md`

- [ ] Obtain independent review of scripts and protocol without reading task instructions/tests/solutions.
- [ ] Run local static checks, then the CPU setup and exact-image jobs on Rohan.
- [ ] If either job fails, record the failure and stop. If both pass, prepare a separate single-episode preregistration; do not launch it as part of this plan.
