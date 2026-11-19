# TB2 One-Task Pilot Plan

> **Status:** Execute the researcher-approved one-task feasibility pilot after independent protocol review.

**Goal:** Run one safely isolated Harbor attempt on one previously unexposed TB2 task and record only a sanitized feasibility result.

**Architecture:** Stage the pinned TB2 snapshot and its task image on Rohan scratch. Run the local gpt-oss model behind the existing UDS Harbor adapter, with task-container networking disabled and Harbor's official verifier as the only score source.

**Tech Stack:** Slurm, Apptainer 1.3.3, Harbor 0.23.0, gpt-oss-20b MXFP4, Python.

**Spec:** `docs/experiments/TB2-ONE-TASK-PILOT-2026-11-19.md`

## Global Constraints

- Exactly one task and one attempt; no retries or replacements.
- Task: `cobol-modernization`, selected from the A pool excluding the 19 IDs in Decision 21, then added to the durable pilot-exclusion registry.
- No Oracle or reference solution; Harbor's official verifier only.
- Task execution must use `--net --network none --writable-tmpfs --containall`, private UDS control, and no fakeroot.
- Model/server binds localhost only; Harbor telemetry is off; no raw outputs are committed.
- Permanently exclude this task from confirmatory scoring and future candidate selection.

## Review Focus

- Docker image pull is pinned by the task tag, then SIF digest is recorded before execution.
- Actual Apptainer argv must match the network and UDS preconditions.
- The server or Harbor provider can fail without emitting raw task/model output into public logs.
- The verifier may return no reward; that is a recorded single-attempt result, not a replacement trigger.
- The task path must not include Oracle/reference artifacts in the agent-visible workspace.

---

### Task 1: Freeze and review pilot inputs

**Files:**
- Create: `docs/experiments/TB2-ONE-TASK-PILOT-2026-11-19.md`
- Modify: `docs/DECISIONS.md`

- [ ] Record the one-task exception, selection, exclusion rule, and no-Oracle boundary before model execution.
- [ ] Resolve and freeze the Docker Registry manifest digest; do not rely on the mutable task image tag.
- [ ] Add a durable exclusion manifest and a tested filtered split loader for all future confirmatory TB2 consumers.
- [ ] Get independent review of the protocol and existing Harbor/Apptainer route without reading task instructions/tests/solutions.
- [ ] Commit and push the preregistration to the current experiment branch.

### Task 2: Preflight and run one task

**Files:**
- Create: `docs/cluster/tb2-pilot/01_task_image_preflight.sbatch`
- Create: `docs/cluster/tb2-pilot/02_one_task_pilot.sbatch`
- Create after execution: `docs/experiments/artifacts/tb2-one-task-pilot-2026-11-19.json`

- [ ] Pull the frozen Docker image by immutable manifest digest into the Apptainer cache and record its SIF hash. Stop on failure.
- [ ] Run a scripted, model-free startup/network/control check for the exact task image. Stop on any mismatch.
- [ ] Submit one RTX Pro 6000 Slurm job with one model attempt and no Oracle/reference solution.
- [ ] Extract only task status, Harbor reward, timings, hashes, and resource metrics; keep raw logs on scratch.
- [ ] Update the report and decision log with the outcome, then commit/push the sanitized record.
