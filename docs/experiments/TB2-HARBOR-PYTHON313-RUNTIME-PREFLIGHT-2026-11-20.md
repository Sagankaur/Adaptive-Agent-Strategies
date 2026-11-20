# TB2 Harbor Python 3.13 runtime preflight

**Status:** Model-free exact-image infrastructure preflight passed. No model episode, benchmark trial, or score was produced. The current TB2 task scope prohibits model or agent runs on TB2.

## Why this follow-up exists

The 2026-11-19 one-task attempt stopped before model execution because Harbor's default bootstrap looked for `/usr/bin/python3` and attempted package installation while the task container had networking disabled. Inspection of the exact pinned `cobol-modernization` SIF then showed Python 3.13.7 and pip 25.2 at `/usr/local/bin/python3`. This follow-up tests that existing interpreter instead of adding another Python runtime.

This is a new model-free engineering gate. It does not revise the result or stop rule of the earlier attempt, and it does not expose additional task instructions, tests, solutions, or outcomes.

## Frozen inputs

- TB2 snapshot: `harborframework/terminal-bench-2.0`, revision `f2e8c75e23add71613117eecc9498f53bcd7e04e`.
- Task: `cobol-modernization`; the task remains excluded from confirmatory use under `evaluation/data/tb2_pilot_exclusions.json`.
- Task image manifest: `sha256:593ab9df3d83f771e927888b2d9436b380cdf7ec4d0af2a9f0802d541edebba0`.
- Task SIF SHA-256: `e7fc37ce09d4ee50e4a71a6e2c9941c0cdacdeb979fcaf99182728b3d0e0dd49`.
- Harbor: 0.23.0. Apptainer: 1.3.3. Existing UDS patch: `docs/cluster/harbor-egress-safety/harbor-0.23.0-uds.patch`.
- Task image Python: 3.13.7 at `/usr/local/bin/python3`; pip 25.2.
- Direct Harbor server dependencies: FastAPI 0.162.0, Pydantic 2.13.5, Uvicorn 0.54.0. The CPU prep job records the exact transitive wheel versions and hashes in a generated lock and manifest.

## Procedure

1. Run `04_prepare_harbor_runtime.sbatch` on the CPU partition. It downloads binary wheels only, using Python inside the pinned SIF; it runs no task setup, task command, model, agent, Oracle, reference solution, or verifier. It writes a hash-locked wheelhouse and performs a network-disabled offline installation into a dedicated runtime directory.
2. Run `05_exact_runtime_preflight.sbatch` with the completed setup job ID. It installs the custom bootstrap and existing UDS patch into a job-local copy of Harbor 0.23.0, mounts the runtime read-only, then checks the exact task SIF through Harbor's `SingularityEnvironment` path.
3. Treat the route as technically available only if Slurm reports both jobs `COMPLETED` and the exact-image record says `status=PASS`. The result is infrastructure evidence only; the current TB2 task scope prohibits model or agent runs on TB2.

The exact-image check must confirm Python/dependency versions and import origins, UDS health and a nonce-bearing `environment.exec` round trip, a harmless `/app` write, read-only dependency mount, path-only sensitive-file scan, loopback-only routes, blocked DNS/external-IP/metadata access, cleanup, actual Apptainer flags, and no fakeroot. The task container is run with `--net --network none --writable-tmpfs --containall`.

## Stop rule

Any missing package, hash mismatch, task-SIF mismatch, unexpected mount, route, successful network probe, failed UDS operation, or argv mismatch after the exact task container starts is a failure. Stop without relaxing network isolation, using fakeroot, or switching tasks. A driver failure before the task container starts is recorded separately; job 4870174 stopped for that reason because the driver initially used system Python without `tomllib`. The driver was corrected to use Harbor's Python 3.12 virtual environment. The successful job below validates this exact configuration only. Under the current task scope, no model or agent may run on TB2, even after this infrastructure check passes.

## Results

| Check | Result |
|---|---|
| Login-side SSH and exact SIF inspection | PASS; Rohan reported the pinned SIF hash and Python 3.13.7/pip 25.2. |
| Hash-locked runtime preparation | PASS; job `4870172`, `COMPLETED 0:0`. Fourteen binary wheels were downloaded and installed offline; `pip check` passed. Lock SHA-256 `4e23d6f973ccd34514c8d33e8642edb84b239bc0d8fc1cfe669f52e7c67fcca9`; runtime tree SHA-256 `e271c9a426b3afa8b4cb7d7d058875424199e5321d9b7d59047d325e0c45bbfc`. |
| Exact-image Harbor UDS/network/mount preflight | Job `4870174`, `FAILED 1:0` after 12 seconds. The host-side driver imported `tomllib` under the cluster system Python and exited before Harbor/Apptainer startup. UDS, egress, mounts, and task paths were not checked. |
| Corrected exact-image Harbor UDS/network/mount preflight | PASS; job `4870175`, `COMPLETED 0:0` in 17 seconds. Harbor 0.23.0 health and `environment.exec` passed over UDS; Python 3.13.7 loaded all three pinned direct dependencies from the read-only runtime; no non-loopback routes were present and DNS, `1.1.1.1:443`, and `169.254.169.254:80` probes failed; path-only workspace guard found no denylisted path names or verifier-like mounts. The captured Apptainer argv included `--net --network none --writable-tmpfs --containall`, UDS, and `/runtime-deps:ro`, with no fakeroot. |
| Model, Harbor task trial, Oracle/reference/verifier | None run. |

The previous pilot remains stopped at job `4869467`; its report and sanitized artifact are unchanged. Job `4870174` started no task container, model, Harbor trial, task setup, Oracle, reference solution, or verifier. Job `4870175` ran only the scripted preflight commands in the exact SIF. It did not run a benchmark task setup, task command, model, agent, Oracle, reference solution, or verifier. The task remains excluded from confirmatory use. The sanitized record is [`artifacts/tb2-harbor-python313-runtime-preflight-2026-11-20.json`](artifacts/tb2-harbor-python313-runtime-preflight-2026-11-20.json).
