# Professor update draft â€” 30 October 2026

**Status: draft for Sagandeep to send or adapt; not sent.**

## What we have established

- **The cluster model path works on a synthetic task.** On Rohan job `4410693`, Qwen3.6-35B-A3B Q4_K_M served by llama.cpp on an L40S returned a native terminal tool call and completed one Harbor 0.23.0 trial under Apptainer 1.3.3. Harbor reported reward 1.0, one completed trial, zero errors, and no retries. The task was synthetic and internet access was allowed. This validates the integration path only; it is not a benchmark result and says nothing about TB-Pro performance. This cluster smoke predates the current per-call token-cap change. A repeat on source commit `8902548` is queued as Rohan job `4433963`; DNS failed for both cluster hostnames, but a direct Rohan connection passed host-key verification. Slurm last reported `PENDING (Resources)` with estimated start 2026-10-31 02:59 AEDT, so the updated cluster result is not available yet. The new cap also passes offline tests.
- **A scripted Harbor CPU smoke also completed** on synthetic data (job `4407435`), reward 1.0. This is setup evidence only.
- **Rohan can reach the public Laude Terminal-Bench GHCR packages.** CPU job `4413248` pulled and inspected Ubuntu 24.04 and Python 3.13 base images in 47 seconds. Their package references and manifest/SIF hashes are recorded in the [P-M2 preflight](P-M2-preflight-2026-10-30.md). These are candidate routes only: equivalence to TB-Pro's custom Aliyun images has not been established.
- **Baseline accounting is more consistent now.** G-BASE repair added pinned sampling/seeds, blind judging, B1 retry accounting, and exact B2 selection. This update also makes S0's default 60-step/64k generated-token budget match the plan, counts generated output rather than prompt plus output against token caps, and shares B1's 64k allowance across agent, judge, and reflection calls. The full offline suite passes 132 tests; Ruff passes on the changed source and tests.

## What we cannot claim yet

There are **no TB-Pro model-performance results**. The synthetic reward-1.0 trials should not be presented as evidence that Qwen solves Terminal-Bench Pro. No TB-Pro task build, Oracle run, or agent trial has been run. TB2 has also remained held out from agent episodes.

## Remaining gates

1. Confirm the TB-Pro v1.0 task license in a root `LICENSE` file or written author reply. The pinned release README declares Apache-2.0 but has no root `LICENSE`; the author request is drafted.
2. Obtain official mirrors/OCI exports for TB-Pro's two Aliyun bases, or maintainer evidence that the GHCR candidates are the intended equivalent images. The Aliyun endpoint times out from both Rohan and the workstation.
3. Get A2I2 guidance on whether the Apptainer 1.3.3 wrapper is an approved Harbor setup, and on blocking task egress while preserving Harbor's localhost control/model-server traffic.
4. Freeze and implement B1's seeded attempt-cap mixture from the planned MCU matching evidence. The shared token ceiling is implemented, but this mixture is still open.
5. Complete the P-M2 route decision and network/disk checks before the five-task TB-Pro smoke.

See [the outreach drafts](../cluster/OUTREACH_DRAFTS_2026-10-30.md), [G-BASE audit](G-BASE-audit-2026-10-30.md), and [real-Qwen Harbor report](Qwen-Harbor-real-model-smoke-2026-10.md) for the evidence and exact limitations.
