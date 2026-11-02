# P-M2 pre-build audit and templates ? 2026-11-03

## Purpose and boundary

Prepare auditable route, overlap-review, and storage records while the TB-Pro image route and license evidence are blocked. This document and the CSV templates do not authorize image builds, task execution, Oracle/reference-solution checks, or model trials. Do not use TB2 agents or Oracle. Static reads of pinned public task text and local, pinned embeddings follow the existing protocol; do not send task text to a generative service.

## GHCR versus TB-Pro image status

The pinned TB-Pro census reports 200 unique task Dockerfiles and 201 `FROM` base-image references: 129 reference `skylensage-registry.cn-hangzhou.cr.aliyuncs.com/instances/1124:t-bench-python-3-13`, 69 reference `...:t-bench-ubuntu-24-04`, and three reference public Python slim bases. These reference counts sum to 201 because one Dockerfile is multi-stage; they do not imply 201 tasks. A source check at the pinned TB-Pro commit confirms the custom Python base reference (example: `advanced-json-to-rfc4180-csv-converter/environment/Dockerfile`).

The Rohan probe showed that Apptainer can pull Laude Institute's public GHCR Terminal-Bench Python 3.13 and Ubuntu 24.04 packages by digest. This is evidence of reachability and OS/runtime-family similarity only. The GHCR package names, publisher, and manifest digests do not prove those layers match TB-Pro's custom Aliyun images. No source Dockerfile provenance link, image configuration comparison, filesystem comparison, or maintainer confirmation has established equivalence. Therefore the GHCR candidates remain unapproved substitutes, and the route is not cleared for builds.

The next static comparison should retrieve the official Laude source Dockerfiles and compare their base-image build recipes against any maintainer-provided TB-Pro source/export or digests. Even recipe similarity cannot prove registry image identity; retain maintainer confirmation or compare immutable manifests/config and filesystem contents after an approved image route is available. Record every finding in `P-M2-route-table-template.csv`; do not substitute based only on matching `python-3-13` or `ubuntu-24-04` labels.

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
