# HPC and TB-Pro outreach drafts: 2026-10-30

The A2I2 support message has been sent and received a general storage response on 2026-11-02. The TB-Pro author draft below remains unsent. The Harbor-specific questions should be directed to Mohamed, as A2I2 support recommended.

## A2I2 HPC support — sent message

**To:** a2i2-it-support@deakin.edu.au
**Subject:** Rohan: approved Apptainer network policy and TB-Pro image import route

Hello A2I2 support,

I have Harbor 0.23.0 running in my Rohan scratch virtual environment. A synthetic Harbor trial has now completed on an L40S allocation using the Apptainer 1.3.3 module and a job-local `singularity` compatibility wrapper. Docker is unavailable to my account.

Could you advise on the following before I start the five-task TB-Pro infrastructure smoke?

1. Is the Apptainer 1.3.3 module and the compatibility wrapper an approved Slurm setup for Harbor jobs?
2. What supported network policy can block task-container egress while preserving Harbor's required localhost control connection and the local model-server endpoint?
3. Is there an approved mirror or OCI import/export route for these two TB-Pro base images, which are timing out from Rohan?
   - `skylensage-registry.cn-hangzhou.cr.aliyuncs.com/instances/1124:t-bench-python-3-13`
   - `skylensage-registry.cn-hangzhou.cr.aliyuncs.com/instances/1124:t-bench-ubuntu-24-04`
4. What persistent storage/quota limit and image-retention policy should I use for the image census and resulting SIF/OCI artifacts?

I will keep the planned smoke to five public TB-Pro tasks and will not run TB2 tasks. The current synthetic smoke report is available at [Qwen Harbor real-model smoke](../experiments/Qwen-Harbor-real-model-smoke-2026-10.md).

Thank you,

Sagandeep

### Response and follow-up: 2026-11-02

A2I2 support documentation says `/home` is 20 GB per user; Rohan `/scratch` maps to a 100-TB shared VAST filesystem, with no per-user quota; and Gondor uses a separate 100-TB shared WEKA filesystem. Scratch is not backed up. Old data may be removed as capacity nears, with no fixed purge schedule or exact trigger. The guidance is to check `df -h /scratch` and keep shared filesystem usage below 80% after planned data generation. RDS is the primary long-term store. Create an Activity and Collection, request quota, configure SSH-key access, and transfer retained data from the cluster. Collections over 2 TB require a Data Management Plan.

This resolves the general storage policy. Rohan `/scratch` fullness was checked on 2026-11-03 (65% globally used). Still unknown are RDS collection access/quota for this project and RDS connectivity from the allocated compute jobs. The 100-TB shared capacity is not a project allocation. Use [A2I2 storage workflow](STORAGE_WORKFLOW_A2I2_2026-11-02.md) for the project's staging/backup steps. Ask support only about project-specific access/runtime/egress facilities; Mohamed should validate Harbor connection requirements against those facilities. The message above is the original sent message, not a pending draft.

Support said Mohamed may be better placed to advise on Harbor-specific requirements and testing. Ask Mohamed separately to validate the Harbor adapter's Apptainer compatibility, identify the Harbor connections that must remain available, review whether the proposed cluster egress controls preserve them, and confirm the five-task smoke acceptance criteria. Do not ask A2I2 to validate Harbor behavior beyond cluster-runtime and network facilities.

## TB-Pro authors / maintainers

**To:** yanquan.xx@alibaba-inc.com  
**Subject:** Terminal-Bench Pro v1.0: license confirmation and base-image exports

Hello,

I am preparing a small, public-set Terminal-Bench Pro route pilot for academic research. The pinned v1.0 task source is commit `321216e78aa4c824f7877f45e3414ea235d7dd5c`; the matching public dataset snapshot is `b79dec3e67acd466f90127cde0d24516d9132e74`.

The repository README declares Apache-2.0, but the pinned release has no root `LICENSE` file. Could you confirm in writing that Apache-2.0 applies to the public task files and assets at this pinned release?

Also, 198 of the 200 public tasks use one of these two Aliyun-hosted bases, and pulls from the registry time out from both Rohan HPC and my workstation:

- `skylensage-registry.cn-hangzhou.cr.aliyuncs.com/instances/1124:t-bench-python-3-13` (129 tasks)
- `skylensage-registry.cn-hangzhou.cr.aliyuncs.com/instances/1124:t-bench-ubuntu-24-04` (69 tasks)

Is there an official mirror or a pair of OCI image exports, preferably with immutable digests and redistribution/use terms, that we may use for this evaluation? Also, are the Laude Institute GHCR images `ghcr.io/laude-institute/t-bench/python-3-13:20250620` and `ghcr.io/laude-institute/t-bench/ubuntu-24-04:20250624` official equivalents of your two custom bases? If so, could you confirm the intended immutable digests and that using them preserves the released task environments?

Thank you,

Sagandeep


## A2I2 follow-up draft: outstanding technical questions

**To:** a2i2-it-support@deakin.edu.au
**Subject:** Follow-up: approved Apptainer setup and task egress controls on Rohan

Hello A2I2 support,

Thank you for the storage guidance. I have completed a key-only login to Rohan and confirmed the shared scratch filesystem is currently 65% used. I am following up on the outstanding cluster-runtime and Slurm-accounting questions:

1. Is the Apptainer 1.3.3 module with a job-local `singularity` compatibility wrapper an approved setup for Slurm jobs using Harbor?
2. Which supported cluster control can restrict task-container internet egress while preserving required host-to-container localhost control traffic and access to a model server running in the same allocation?

I will ask Mohamed to validate Harbor's actual connection requirements and the five-task smoke acceptance criteria. I am not asking A2I2 to certify Harbor behavior; I need the supported cluster runtime and network-control options.

3. I ran six synthetic llama.cpp serving jobs on Rohan under the `gpu` partition and `short` QoS. For jobs `4505001`, `4505018`, and `4505019`, the batch output records `runner_exit_status=0`, the JSONL ends with successful `run_finished` statuses, and `sacct` reports `DerivedExitCode=0:0`; however, both the allocation and `.batch` step are `FAILED`, `ExitCode=1:0`. The `.err` files are empty. The earlier three runs show the same Slurm state, though their wrapper did not log the Python exit status. Could you identify where the `1:0` is coming from (for example, a site epilog or Slurm step/accounting issue), and advise which cluster logs or exit status I should use to diagnose it? Should I change the job wrapper or request parameters?

The run record and captured outputs are in the public repository under `docs/experiments/serving-sweep-2026-11.md` and `docs/experiments/artifacts/`.

Thank you,

Sagandeep

## Digital Services: RDS host-key verification

**To:** Deakin IT Help / Digital Services (RDS)
**Subject:** Verify RDS storage SSH host key from Rohan HPC

Hello,

I am setting up cluster-to-RDS transfers from Rohan HPC. The dedicated RSA client key is present on Rohan, but `ssh -i ~/.ssh/id_rsa_rds kasag@rds-storage.deakin.edu.au collections` stopped at host-key verification because `rds-storage.deakin.edu.au` has no entry in Rohan's `known_hosts`. The attempt did not reach client-key authentication.

Could you provide the official SSH host-key fingerprint for `rds-storage.deakin.edu.au`, or the approved first-connection procedure for users connecting from A2I2 Rohan? I will verify the fingerprint before caching the host key. Please also confirm whether the RDS SSH Key Management Utility is the right place to register the Rohan-generated RSA public key for this transfer path.

Thank you,

Sagandeep

**Status:** Both A2I2 and Digital Services messages are drafts only; no connected email account is available in this workspace. The A2I2 draft also includes the still-open Apptainer approval and egress-control questions.
