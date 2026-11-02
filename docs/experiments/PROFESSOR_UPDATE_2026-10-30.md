# Professor update draft â€” 30 October 2026

**Status: draft for Sagandeep to send or adapt; not sent.**

## What we have established

- **The cluster model path works on a synthetic task.** On Rohan job `4410693`, Qwen3.6-35B-A3B Q4_K_M served by llama.cpp on an L40S returned a native terminal tool call and completed one Harbor 0.23.0 trial under Apptainer 1.3.3. Harbor reported reward 1.0, one completed trial, zero errors, and no retries. The task was synthetic and internet access was allowed. A post-cap repeat using source commit `8902548` completed as job `4433963` on the L40S: one Harbor trial, reward 1.0, zero errors/retries, 198 generated tokens. This confirms only the updated synthetic execution path, not benchmark performance or network isolation. The offline suite and GitHub Actions also pass.
- **A scripted Harbor CPU smoke also completed** on synthetic data (job `4407435`), reward 1.0. This is setup evidence only.
- **Rohan can reach the public Laude Terminal-Bench GHCR packages.** CPU job `4413248` pulled and inspected Ubuntu 24.04 and Python 3.13 base images in 47 seconds. Their package references and manifest/SIF hashes are recorded in the [P-M2 preflight](P-M2-preflight-2026-10-30.md). These are candidate routes only: equivalence to TB-Pro's custom Aliyun images has not been established.
- **Baseline accounting is more consistent now.** G-BASE repair added pinned sampling/seeds, blind judging, B1 retry accounting, and exact B2 selection. This update also makes S0's default 60-step/64k generated-token budget match the plan, counts generated output rather than prompt plus output against token caps, and shares B1's 64k allowance across agent, judge, and reflection calls. The full offline suite passes 132 tests; Ruff passes on the changed source and tests.

## What we cannot claim yet

There are **no TB-Pro model-performance results**. The synthetic reward-1.0 trials should not be presented as evidence that Qwen solves Terminal-Bench Pro. No TB-Pro task build, Oracle run, or agent trial has been run. TB2 has also remained held out from agent episodes.

## Remaining gates

1. Confirm the TB-Pro v1.0 task license in a root `LICENSE` file or written author reply. The pinned release README declares Apache-2.0 but has no root `LICENSE`; the author request is drafted.
2. Obtain official mirrors/OCI exports for TB-Pro's two Aliyun bases, or maintainer evidence that the GHCR candidates are the intended equivalent images. The Aliyun endpoint times out from both Rohan and the workstation.
3. Get A2I2 guidance on the approved Apptainer route and available cluster egress controls; Mohamed should validate Harbor's required connections and smoke acceptance criteria against those controls.
4. G-BASE is green: the full suite passed in GitHub Actions on Python 3.11 and 3.12. Freeze the numerical B1 attempt-cap mixture at Stage 2 from E1/E-P0 and S* MCU evidence; requiring that future evidence to close G-BASE would create a circular gate.
5. Complete the P-M2 route decision and network/disk checks before the five-task TB-Pro smoke.

## Message to include for Mohamed

Before the five-task TB-Pro smoke, could you confirm which Harbor, task-runner, and local model-server connections must remain available when task internet is restricted, and what evidence the smoke must produce to count as a pass? The written plan requires zero harness errors and Harbor-native reward provenance; please confirm whether you expect any additional per-task completion, logging, or egress-isolation checks. A2I2 support can identify the cluster's supported network controls, while you can validate them against Harbor's actual requirements.

See [the outreach drafts](../cluster/OUTREACH_DRAFTS_2026-10-30.md), [G-BASE audit](G-BASE-audit-2026-10-30.md), and [real-Qwen Harbor report](Qwen-Harbor-real-model-smoke-2026-10.md) for the evidence and exact limitations.
