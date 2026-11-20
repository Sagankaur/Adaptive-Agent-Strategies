# TB2 Harbor Python 3.13 runtime preflight

**Status:** Prepared; cluster jobs not yet run. No model episode is authorized by this preflight record.

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
3. Continue only if Slurm reports both jobs `COMPLETED` and the exact-image record says `status=PASS`.

The exact-image check must confirm Python/dependency versions and import origins, UDS health and a nonce-bearing `environment.exec` round trip, a harmless `/app` write, read-only dependency mount, path-only sensitive-file scan, loopback-only routes, blocked DNS/external-IP/metadata access, cleanup, actual Apptainer flags, and no fakeroot. The task container is run with `--net --network none --writable-tmpfs --containall`.

## Stop rule

Any missing package, hash mismatch, task-SIF mismatch, unexpected mount, route, successful network probe, failed UDS operation, or argv mismatch is a failure. Stop without relaxing network isolation, using fakeroot, switching tasks, or launching a model. A pass permits preparation of a separate one-episode preregistration; it does not itself authorize model execution.

## Results

| Check | Result |
|---|---|
| Login-side SSH and exact SIF inspection | PASS; Rohan reported the pinned SIF hash and Python 3.13.7/pip 25.2. |
| Hash-locked runtime preparation | Not run. |
| Exact-image Harbor UDS/network/mount preflight | Not run. |
| Model, Harbor task trial, Oracle/reference/verifier | None run. |

The previous pilot remains stopped at job `4869467`; its report and sanitized artifact are unchanged. This report will be updated with job IDs, Slurm states, runtime manifest hash, and sanitized check results after the CPU jobs finish.
