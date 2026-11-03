# P-M2 pre-build audit and templates - 2026-11-03

## Purpose and boundary

Prepare auditable route, overlap-review, and storage records while the TB-Pro image route and license evidence are blocked. This document and the CSV templates do not authorize image builds, task execution, Oracle/reference-solution checks, or model trials. Do not use TB2 agents or Oracle. Static reads of pinned public task text and local, pinned embeddings follow the existing protocol; do not send task text to a generative service.

## GHCR versus TB-Pro image status

The pinned TB-Pro census reports 200 unique task Dockerfiles and 201 `FROM` base-image references: 129 reference `skylensage-registry.cn-hangzhou.cr.aliyuncs.com/instances/1124:t-bench-python-3-13`, 69 reference `...:t-bench-ubuntu-24-04`, and three reference public Python slim bases. These reference counts sum to 201 because one Dockerfile is multi-stage; they do not imply 201 tasks. A source check at the pinned TB-Pro commit confirms the custom Python base reference (example: `advanced-json-to-rfc4180-csv-converter/environment/Dockerfile`).

The Rohan probe showed that Apptainer can pull Laude Institute's public GHCR Terminal-Bench Python 3.13 and Ubuntu 24.04 packages by digest. This is evidence of reachability and OS/runtime-family similarity only. The GHCR package names, publisher, and manifest digests do not prove those layers match TB-Pro's custom Aliyun images. No source Dockerfile provenance link, image configuration comparison, filesystem comparison, or maintainer confirmation has established equivalence. Therefore the GHCR candidates remain unapproved substitutes, and the route is not cleared for builds.

### Public web-source check (2026-11-03)

The pinned TB-Pro README and the official Hugging Face dataset card state Apache-2.0: [pinned README](https://github.com/alibaba/terminal-bench-pro/blob/321216e78aa4c824f7877f45e3414ea235d7dd5c/README.md), [dataset card](https://huggingface.co/datasets/alibabagroup/terminal-bench-pro). This is positive public evidence of the authors' stated license, but it does not meet this project's explicit P-M2 criterion, which requires a root `LICENSE` file or written maintainer confirmation covering the pinned release. Keep that gate open unless the protocol is formally revised; do not silently relax it after preregistration.

The public Laude GHCR packages remain the only accessible candidate bases found in the official sources checked. Their public availability and successful Rohan pulls do not establish equivalence to the custom Aliyun TB-Pro bases. No official TB-Pro OCI export or mirror was found in those sources; the author request remains the direct route to obtain one.

### Direct manifest and filesystem comparison attempt (2026-11-03)

To compare actual image content rather than names or recipes, a read-only GitHub Actions job ran on an x86-64 Linux runner after the comparison workflow was pushed to the research branch. It pulled each GHCR reference by immutable linux/amd64 digest, attempted each TB-Pro Aliyun tag, inspected image config and uncompressed layer IDs, and exported and hashed the stopped images' merged filesystems. No container was started, and no task code ran. The workflow and script are [`pm2-image-compare.yml`](../../.github/workflows/pm2-image-compare.yml) and [`pm2_compare_base_images.py`](../../scripts/pm2_compare_base_images.py); the [run and retained artifact](https://github.com/Sagankaur/Adaptive-Agent-Strategies/actions/runs/41636341190) contain the full report and path-hash inventories.

Both GHCR pulls and exports succeeded, but both Aliyun pulls failed before authentication: Docker timed out waiting for headers from `https://skylensage-registry.cn-hangzhou.cr.aliyuncs.com/v2/`. Thus, no Aliyun manifest, config, layer IDs, or filesystem content was obtained; the pairwise comparisons are **incomplete**, not mismatches.

| Candidate image | Pulled linux/amd64 manifest digest | Docker config image ID | Config SHA-256 | Uncompressed layers | Exported rootfs entries | Rootfs inventory SHA-256 |
|---|---|---|---:|---:|---:|---|
| Laude Python 3.13 | `sha256:10dd0648b5339468ba39b2df90c1a28745faf8622e7552f85446611e2e992110` | `sha256:75cb41dc2d4f832786b0d4be2c474eb2177ece9d173bdfdff74af6509484dcc9` | `9539433740e1a5396cff01670865c6e6a7bb99b2c5e0e91ad020f7f2e908ff01` | 6 | 8,151 | `a50f8174385460d69725188282bf42d507be12bb6692c08013009138dc34d1bc` |
| Laude Ubuntu 24.04 | `sha256:9ae5033b4f62fbffd63896353f2c8e02939764fac81311608e4e731f0b4a8db5` | `sha256:2591fd9a98fc54fc79cddd50700fa320a77880cfdee1e06169b22e7708b48ad1` | `0c4c89424561931e0b5db48a8996435beab7ebc85e87085921faf0ba8aa006e3` | 3 | 6,163 | `54ff2b600f723d26c14855e4434ebc6a0a7e2fca9c516b0e84a0eab98582f487` |

The captured GHCR config summaries show both use `/app` as the working directory; the Python image has `CMD ["python3"]`, while Ubuntu has `CMD ["/bin/bash"]`. These are fingerprints for the candidate images only. They cannot be compared against TB-Pro until the two Aliyun images are reachable or the maintainers supply immutable digests/OCI exports. The image-equivalence route therefore remains unresolved.

### Static source-recipe comparison (2026-11-03)

I inspected the official Laude/Terminal-Bench base-image Dockerfiles exposed on the repository's `main` branch as retrieved on 2026-11-03: [`python-3-13`](https://raw.githubusercontent.com/laude-institute/terminal-bench/main/docker/base-images/python-3-13/Dockerfile) and [`ubuntu-24-04`](https://raw.githubusercontent.com/laude-institute/terminal-bench/main/docker/base-images/ubuntu-24-04/Dockerfile). The Python recipe starts from `python:3.13-slim-bookworm`; both recipes add `tmux` and `asciinema`, remove apt package lists, and set `/app` as the working directory. The Ubuntu recipe starts from `ubuntu:24.04`. The source links use a moving branch and are not an immutable recipe pin; an immutable commit for these exact files was not established in this audit.

This comparison does **not** establish that these current recipes produced the previously probed GHCR digests (`20250620` and `20250624`), nor that those GHCR images match TB-Pro's custom Aliyun images. The audited TB-Pro task Dockerfiles reference the custom Aliyun tags; no corresponding TB-Pro base-image build recipe, immutable source-image digest, or maintainer equivalence statement is available in the audited records. Thus, the recipes overlap in broad OS/runtime family and terminal tooling, but key provenance and resulting package/filesystem state remain unknown. This is not an image equivalence result and does not clear any task for image substitution or build.

The next valid comparison requires maintainer-provided source recipes or OCI exports/digests for the two TB-Pro bases. Once an authorized route exists, compare immutable manifests/configuration and filesystem contents, then record per-task mapping in `P-M2-route-table-template.csv`. Recipe similarity alone cannot prove registry image identity.

## Routing table schema

`P-M2-route-table-template.csv` is exactly one row for each of the 200 unique pinned TB-Pro tasks. It captures source pins, requested resources, Dockerfile hash/base reference, image provenance/equivalence evidence, disposition, image digest, build and Oracle status, host allowlist, and exclusion rationale. Keep rows for excluded tasks so the final census accounts for all 200. Until permission and image route are resolved, leave build and Oracle fields empty; do not enter invented outcomes.

## Overlap review schema

`P-M2-overlap-review-template.csv` is one row per TB-Pro task and each of its three nearest TB2 candidates. Record the pinned source commits, pinned local embedding model and implementation, similarity, and owner review of shared artifact, algorithm, toolchain, and goal. Apply the already specified same-artifact/same-algorithm/same-toolchain rule consistently; freeze decisions before any outcome data and provide a one-line rationale for every removal. The template is empty and does not imply overlap has been measured.

## Storage measurement plan

`P-M2-disk-census-template.csv` separates shared scratch occupancy from the project footprint and labels each value as a current snapshot, projection, or measured peak. Measure at least:

- `df -h /scratch` before/after work and keep the shared filesystem below A2I2's 80% guidance;
- pulled/compressed and expanded TB2 images, GHCR or approved source bases, and each permitted task image;
- temporary build layers/cache and concurrent-build peak, retained SIF/OCI artifacts, logs, and RDS backup size/quota;
- RDS allocated quota separately from scratch availability.

For the G-ROUTE check, compare measured peak project footprint with usable granted space and retain at least 20% headroom, or use a logged digest-pinned build-run-prune plan. Current Rohan scratch snapshot (2026-11-03): 91T total, 59T used, 33T available, 65% used. This is global filesystem occupancy, not project allocation. TB2 image archives are documented as 48.98 GB compressed; TB-Pro task archives are about 35 MB total. Neither archive size predicts expanded images, image layers, or build-cache peaks, so no defensible total TB-Pro disk estimate exists before approved representative measurements. RDS Activity, Collection, and quota are still pending.

## Gate and stop conditions

Do not start TB-Pro builds, Oracle/reference-solution checks, or model runs until the license requirement, authorized image route, and cluster egress decision are resolved. After those are resolved, execute the pinned census and disk measurements, review overlap, and make the P-M2 route decision before the five-task smoke. Templates alone do not demonstrate the 120-task survivor threshold or close G-ROUTE.
