# Aider Python runtime preflight — 2026-11-19

## Purpose

Determine whether the pinned Harbor Aider Polyglot Python runtime can be represented by an Apptainer SIF and execute a **synthetic, no-model Harbor CLI trial** with task egress blocked and Harbor's private Unix-socket control channel intact. This is an infrastructure preflight, not an Aider benchmark run.

## Runtime specification

Follow the Python branch of Harbor's pinned Aider Polyglot adapter at commit `1e5c5c6db929a10a140d05e606882c671ae20729`: `buildpack-deps:jammy`; `tmux`, `asciinema`, and `curl`; Python 3.11 plus its venv/development packages and pip; and pytest 8.3.4 preinstalled so the adapter's `pip install pytest` step can complete without task-container egress. Docker Hub's multi-architecture `jammy` index is pinned at `sha256:3dbfcff54e02773819d50726a21517583fa71c115282d26aad87f9cd22333ae1`; Rohan's `linux/amd64` child manifest is pinned directly in the definition file at `sha256:772a4d3210ef96e658ca2dd2511461ac8bc623aa5331111249c75a883d8f0e6d`. Record host architecture and resulting SIF hash at build time. The image is built in a CPU Slurm job. `--fakeroot` is limited to the image-build command if the site permits it; it is not passed to the Harbor task container.

## Checks

1. Record Slurm job ID, host, versions, image labels, recipe/input hashes, and SIF SHA-256.
2. In an Apptainer invocation with `--net --network none --writable-tmpfs --containall` and no `--fakeroot`, check Python 3.11, pip, pytest, curl, tmux, asciinema, Git, and the common compiler/build commands expected from `buildpack-deps:jammy`.
3. Run the adapter's actual `pip3 install pytest` command in that network-isolated container and confirm it succeeds from the preinstalled package without querying an index.
4. Run one normal Harbor CLI trial using only the repository's synthetic isolation fixture and built-in no-op agent. Require the recorded network probes, read-only dependency mounts, writable `/app`, private UDS nonce round trip, Harbor reward provenance, and cleanup checks to pass.
5. Record process affinity and visible cgroup CPU/memory controls. Do not claim task-level resource limits unless the evidence demonstrates an enforced limit.

## Stop conditions

- Stop if image build requires an unsupported privilege, task egress becomes available, a sensitive host path or credential is mounted, UDS control fails, or any required runtime command is missing.
- This run does not fetch/generate Aider tasks, read task instructions, run tests/reference solutions/oracles from Aider, or invoke a model.
- Passing this preflight is necessary but insufficient for the six-task pilot. The exact per-task dependency/image route, resource limits, and artifact behavior must be resolved, and the six task IDs must be frozen before reading their instructions.
- No Terminal-Bench 2.0 content is read or run. No Terminal-Bench Pro task is built or run.

## Decision rule

If the runtime/control/isolation checks pass, retain the gpt-oss-20b + Aider Python pilot as a candidate and continue with a separate task-image/dependency audit. Do not start model episodes from this result alone. If the image cannot be built or the runtime contract fails, record a no-go for this route and propose another permitted benchmark/runtime combination before spending model episodes.

## Run record

The build/runtime preflight ran on Rohan as Slurm job `4802966` on 2026-11-19 AEDT. Slurm reports `COMPLETED`, exit `0:0`, elapsed `00:02:49`; `.batch` peak RSS was `2613012K`.

| Check | Result |
|---|---|
| Host architecture | `x86_64` (the image definition pins the matching Docker Hub child manifest) |
| Harbor Aider runtime base | `buildpack-deps:jammy`, linux/amd64 manifest `sha256:772a4d3210ef96e658ca2dd2511461ac8bc623aa5331111249c75a883d8f0e6d` |
| Apptainer build | Passed with `--fakeroot` for image construction only |
| Final SIF SHA-256 | `1188aca02532530596e5e2c4642244ebb1020469ef489fe60ed55a5ea8ec56d8` |
| Runtime Python / pip / pytest | Python `3.11.18`; pip `26.3`; pytest `8.3.4` |
| Required commands | `curl`, `tmux`, `asciinema`, `git`, `gcc`, and `make` found |
| Isolated execution | `apptainer exec --net --network none --writable-tmpfs --containall`; no `--fakeroot`; confirmed task process UID is non-root |
| Aider's pytest setup command | `pip3 install pytest` passed with `Requirement already satisfied`; no index lookup was logged |

This only validates that the intended runtime image can be constructed and that the adapter's pytest installation is already satisfied in the isolated container. The first normal Harbor CLI synthetic trial, job `4802968`, ended `FAILED`, exit `1:0`, after `00:01:15`; no verifier ran and no model or benchmark task was involved. Harbor's Apptainer process log stopped at “Converting SIF file to temporary sandbox...” and did not reach the UDS health check within the provider's 60-second startup window. This suggests shared-storage SIF conversion/startup latency, but the cause is not confirmed.

The synthetic CLI recipe was then changed to put Apptainer's temporary extraction on the compute node's local `/data` NVMe, which had 5.8 TiB free. The rerun, job `4802971`, completed `COMPLETED`, exit `0:0`, in `00:00:32`; `.batch` peak RSS was `400300K`. Harbor ran one synthetic task with its built-in no-op agent and reported reward `1.0`; the synthetic verifier reported `1 passed`. The recorded checks passed for the exact Python runtime, normal Harbor CLI lifecycle, `--net --network none`, no `--fakeroot`, no TCP control port, private UDS, read-only dependency mounts, writable `/app`, no unexpected mounts from the checked set, blocked IPv4/IPv6/DNS/metadata requests, and UDS cleanup. Harbor telemetry was disabled. This is setup evidence only, not a benchmark result.

The failed trial recorded one Slurm-allocated CPU (`Cpus_allowed_list=196`), `cpu.max=max 100000`, and an effective cgroup-v2 memory limit of `4294967296` bytes from the job allocation. Harbor itself advertises no per-task CPU or memory limit controls. For a sequential pilot, a Slurm job allocation may bound the single task process tree, but the present failed trial does not establish the adequacy of any particular Aider task's memory needs.

The local-NVMe rerun supports the hypothesis that shared-filesystem conversion caused the first timeout, but does not prove it: no matched timing study was run. The preflight's core synthetic CLI checks now pass; the overall result remains **partial** because task-specific dependencies, Aider artifact collection, and the adequacy of the resource budget for actual tasks remain unverified.

## Primary source

The exact upstream adapter files are pinned at Harbor commit [`1e5c5c6db929a10a140d05e606882c671ae20729`](https://github.com/harbor-framework/harbor/tree/1e5c5c6db929a10a140d05e606882c671ae20729/adapters/aider_polyglot). Its task Dockerfile starts from `buildpack-deps:jammy`, installs `tmux`, `asciinema`, and `curl`, then installs Python 3.11 through deadsnakes and verifies Python/pip. The Python verifier installs pytest before running tests. This preflight reproduces the runtime contract but omits task workspaces and tests.
