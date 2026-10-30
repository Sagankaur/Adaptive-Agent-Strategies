# P-M2 source and registry preflight - 2026-10-30

## Status

P-M2 is **not complete and has no GO/NO-GO decision**. This preflight pinned and inspected the public task source, checked metadata/resource requests, and tested one base-image pull. No TB-Pro Dockerfile, solution, test, Oracle, or model agent was run.

## Source pins and license evidence

- Official GitHub release: `v1.0`, commit `321216e78aa4c824f7877f45e3414ea235d7dd5c` ([release](https://github.com/alibaba/terminal-bench-pro/releases/tag/v1.0)).
- Public Hugging Face dataset snapshot: `b79dec3e67acd466f90127cde0d24516d9132e74` ([dataset snapshot](https://huggingface.co/datasets/alibabagroup/terminal-bench-pro/tree/b79dec3e67acd466f90127cde0d24516d9132e74)).
- The 200 task IDs in the pinned dataset match all 200 task directories at the pinned GitHub release, with no missing or extra IDs.
- The GitHub README and Hugging Face card declare Apache-2.0 ([README](https://github.com/alibaba/terminal-bench-pro/blob/321216e78aa4c824f7877f45e3414ea235d7dd5c/README.md), [dataset card](https://huggingface.co/datasets/alibabagroup/terminal-bench-pro)). However, the pinned GitHub release has no root `LICENSE` file. The stricter P-M2 evidence requirement (a `LICENSE` file or written author confirmation) is therefore not yet satisfied.

## Static task census

The Parquet archive is 35,518,851 bytes. It contains 200 unique rows and 200 unique task IDs. Each archive is gzip-compressed; together the 200 task archives are 35,262,041 bytes and contain 1,000 files with 41,378,952 bytes of uncompressed file data.

All 200 tasks use `task.toml` version `1.0`, provide an `environment/Dockerfile`, and omit a prebuilt `docker_image`. Categories are balanced at 25 tasks in each of eight categories. Requested resources:

| Setting | Counts |
|---|---|
| CPUs | 1: 181; 2: 2; 4: 15; 8: 1; 16: 1 |
| Memory | 2,048 MB: 181; 4,096 MB: 1; 8,192 MB: 16; 16,384 MB: 2 |
| Storage | 10,240 MB: 200 |

Under P-M2's provisional filter (>4 CPUs or >8,192 MB), two tasks are excluded: `build-arm64-qemu-linux-with-custom-message` and `ner-eval-conll2003`. The other 198 meet that preliminary resource filter. This is not the final filter, which depends on the pinned host budget and concurrency.

The Dockerfiles use four distinct base images:

| Base image | Tasks |
|---|---:|
| `skylensage-registry.cn-hangzhou.cr.aliyuncs.com/instances/1124:t-bench-python-3-13` | 129 |
| `skylensage-registry.cn-hangzhou.cr.aliyuncs.com/instances/1124:t-bench-ubuntu-24-04` | 69 |
| `python:3.11-slim` | 2 |
| `python:3.13-slim` | 1 |

There is one multi-stage Dockerfile; 199 Dockerfiles contain `RUN`, and 175 contain `COPY` or `ADD`. This confirms that the task archives need real image builds; substituting a stock base image without validating the resulting environment would change the benchmark setup.

## Rohan base-image pull

Slurm job `4408911` ran on `cpu-f-01` with Apptainer 1.3.3. Pulling the Python 3.13 base image from the Alibaba registry failed after about two minutes with a TCP connection timeout to `120.26.27.123:443`. An independent request to the same registry endpoint from the workstation also timed out. No image was written and no task code was executed. Rohan previously pulled Docker Hub's `alpine:3.20` successfully, so this result is specific to the Alibaba registry endpoint rather than evidence that every registry is unreachable.

The pull attempt did not establish an egress allowlist or full network audit. P0-13's public-network fallback is not considered satisfied by this test.

## Decision and next step

Do not start the 200 image builds or Oracle trials yet. The immediate route blocker is that 198 of 200 tasks depend on two base images hosted on the unreachable Alibaba registry; the license evidence also needs to meet the P-M2 rule. Request an approved mirror or OCI image export for those two bases, or written author confirmation of a supported registry path and license. A GitHub Actions/GHCR build-and-pull route is a possible alternative from the private A2I2 notes, but it requires an explicit decision about publishing and storage and must preserve the task environments.

After an accessible base-image route is established, continue P-M2 with the full per-task build report, dedup review against TB2, network/audit decision, Oracle results on TB-Pro only, disk/headroom report, and the final routing table. Keep all TB2 tasks agent- and Oracle-unseen.

## Public repository recheck — 2026-10-30

The current [GitHub README](https://github.com/alibaba/terminal-bench-pro/blob/main/README.md) still declares Apache-2.0 and identifies `yanquan.xx@alibaba-inc.com` for public-set results. The current [repository root](https://github.com/alibaba/terminal-bench-pro) does not show a separate root `LICENSE` file; the pinned v1.0 release still has no such file. This confirms the README declaration but does not satisfy this plan's stricter written-author-confirmation-or-LICENSE requirement. A request for written confirmation and official base-image mirrors/exports has been drafted in [`docs/cluster/OUTREACH_DRAFTS_2026-10-30.md`](../cluster/OUTREACH_DRAFTS_2026-10-30.md); it has not been sent.
