# A2I2 storage workflow — 2026-11-02

## Storage facts from the A2I2 support documentation

- `/home` is 20 GB per user and is for configuration, scripts, keys, and frequently used code. Do not keep research datasets or environments there.
- Rohan `/scratch` maps to the 100-TB shared VAST filesystem. There is no per-user scratch quota; 100 TB is the shared filesystem capacity, not an allocation for this project. Gondor uses its separate 100-TB shared WEKA filesystem. Data does not replicate between these filesystems.
- Scratch is fast working storage, is not backed up, and older data can be removed when the filesystem nears capacity. The support documentation says there is no fixed purge schedule or exact trigger. Check `df -h /scratch` and keep total filesystem usage below 80% after generating planned data. Local `/data` is job/server-local and must be copied off before the job ends.
- RDS is the primary long-term source of record. Important data and results must be backed up there; copy inputs from RDS to scratch for processing and copy retained outputs back to RDS. RDS collections can request more quota; a request above 2 TB requires a Data Management Plan.
- RDS setup: create an Activity for the project, create a Collection to provision storage, request an appropriate quota, set up SSH-key access, identify the collection path, and transfer from the cluster with `rsync` or `scp` (use `tmux`/`screen` for long transfers). The supplied RDS instructions describe a cluster-to-RDS RSA key generated on Rohan/Gondor and registered in the SSH Key Management Utility; treat this as a separate access path from the workstation-to-cluster login key in A2I2 guide §3.4 unless support documentation explicitly says they can be shared.

These facts come from the storage documentation supplied in the project conversation. Current free scratch capacity, current RDS collection/quota, exact purge trigger, and transfer completion have not been checked.

## Workflow for this project

1. On Rohan, check and record `df -h /scratch` before any large image build. Estimate candidate artifact growth, then ensure shared filesystem usage remains below 80% after the planned writes. Do not assume the full 100 TB is available to this project.
2. Create an RDS Activity and Collection for the research project. Request a quota based on measured needs; if the request exceeds 2 TB, prepare the required Data Management Plan. Configure the cluster-to-RDS SSH key access and test a small transfer before relying on RDS for archives.
3. Keep disposable build caches, active SIF/OCI work, temporary task data, and current job outputs on `/scratch`. Preserve source pins, final reports, logs, selected artifacts needed for reproduction, and backups on RDS. Remove disposable scratch data when no longer needed.
4. For P-M2, measure actual build and image footprints rather than guessing from task archive sizes. Record compressed/pulled and expanded image storage, plus TB2 digest-pinned image use. The existing G-ROUTE rule still requires at least 20% headroom for the measured project footprint within available storage, or an explicitly logged build-run-prune plan. This is separate from A2I2's requirement to keep the shared scratch filesystem below 80% full.

## Immediate actions

- [ ] Run `df -h /scratch` on Rohan and record capacity/used/available/percentage.
- [ ] Create the RDS Activity and Collection; note its path and approved quota.
- [ ] Configure the RDS SSH key following A2I2 instructions and verify a small `rsync`/`scp` transfer.
- [ ] Do not start the full TB-Pro build census until license, image route, runtime/network gates, and a storage estimate satisfy the documented G-ROUTE and shared-scratch limits.
