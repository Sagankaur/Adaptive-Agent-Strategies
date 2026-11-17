# Aider-style Python runtime preflight

**Status:** job 4801425 passed as a synthetic, no-model Apptainer/provider smoke. It does not run an Aider benchmark task, the Aider adapter's generated image, or a full Harbor CLI trial. A later normal-CLI synthetic follow-up is recorded in [the Harbor CLI egress preflight](harbor-cli-egress-preflight-2026-11-17.md).

## Run

Slurm job **4801425** completed on the Rohan CPU queue in 24 seconds with exit `0:0`. The job used Apptainer `1.3.3+342-g42a8ae13e`, Harbor `0.23.0` on the host's Python `3.12.16` virtual environment, and a Python `3.11.18` task SIF pulled from `python:3.11-slim`. The SIF SHA-256 is recorded in [`artifacts/aider_python_preflight_4801425/sha256sums.txt`](artifacts/aider_python_preflight_4801425/sha256sums.txt).

The Harbor 0.23.0 Singularity provider was patched to use a private Unix socket, then called directly through its provider API. A small read-only local wheelhouse supplied pinned pytest `8.3.4` and the FastAPI/Uvicorn server dependencies. The custom bootstrap starts those dependencies without apt or PyPI access inside the isolated container. The host repository, SSH directory, and credentials were not mounted.

## Results

| Check | Result |
|---|---|
| Harbor provider execution-server health | Pass over UDS; no TCP port was assigned |
| Control round trip | Pass; job-derived nonce returned unchanged |
| Python runtime | Python `3.11.18` |
| Offline pytest installation | Pass from the local wheelhouse; no package index used |
| Synthetic verifier | `1 passed` |
| Network namespace | Only `lo`; zero non-loopback routes |
| External fixed IP | Connection to `1.1.1.1:443` blocked |
| External DNS | `example.com` lookup blocked |
| Metadata address | Connection to `169.254.169.254:80` blocked |
| Sensitive mount/environment audit | Pass for the explicitly checked SSH, credential, Docker, and A2I2 rootless-Docker paths and variable names |
| UDS cleanup | Pass; provider shut down and removed the private socket directory |
| Model, agent, benchmark, Oracle | None ran |

The sanitized JSON result and image/wheel hashes are in [`artifacts/aider_python_preflight_4801425/`](artifacts/aider_python_preflight_4801425/). The audit checks named sensitive paths and environment-variable patterns; it is not a complete inventory of every system mount or every possible credential convention.

## What this establishes

This run shows that Apptainer 1.3.3 can host a Python 3.11 process, install pytest from local wheels with task egress disabled, and preserve the patched Harbor provider's UDS control path in the tested setup. The previous rootless-Docker job remains blocked by missing Slurm cgroup controllers, but a generic Apptainer route is now technically viable for the synthetic workload.

## What it does not establish

The harness constructs `SingularityEnvironment` with `__new__` and calls its private start/exec/cleanup methods. It does not exercise Harbor's normal constructor, CLI trial lifecycle, or Aider adapter-generated task configuration. The SIF is based on `python:3.11-slim`, not Aider's generated Dockerfile (`buildpack-deps:jammy`, Python 3.11, `curl`, `tmux`, and `asciinema`). The server logged that `tmux` is absent. The run also does not prove task-specific dependency completeness, cgroup/resource limits, benchmark correctness, or model behavior.

For that reason this is setup evidence only. Do not start model-driven Aider episodes yet. First create a reproducible Python task image that covers the adapter's needed runtime, then run a synthetic task through Harbor's normal trial path with that exact image and verify its mounts, egress, control channel, cleanup, and resource limits.

The subsequent normal-CLI trial in job 4801512 confirms the generic image works through Harbor's standard trial lifecycle and verifies read-only dependency mounts, but it still uses `python:3.11-slim` rather than the adapter-generated runtime. It also leaves task-level resource enforcement unverified. Those gaps remain open.

## Adapter/runtime references

- [Pinned Aider Polyglot adapter README](https://github.com/harbor-framework/harbor/blob/1e5c5c6db929a10a140d05e606882c671ae20729/adapters/aider_polyglot/README.md)
- [Pinned Aider task Dockerfile template](https://github.com/harbor-framework/harbor/blob/1e5c5c6db929a10a140d05e606882c671ae20729/adapters/aider_polyglot/src/aider_polyglot/task-template/Dockerfile)
- [Pinned Python setup and pytest test-command generation](https://github.com/harbor-framework/harbor/blob/1e5c5c6db929a10a140d05e606882c671ae20729/adapters/aider_polyglot/src/aider_polyglot/utils.py)
- [Pinned Harbor Singularity bootstrap](https://github.com/harbor-framework/harbor/blob/1e5c5c6db929a10a140d05e606882c671ae20729/src/harbor/environments/singularity/bootstrap.sh)
