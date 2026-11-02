# HPC and TB-Pro outreach drafts — 2026-10-30

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

### Response and follow-up — 2026-11-02

A2I2 support documentation says `/home` is 20 GB per user; Rohan `/scratch` maps to a 100-TB shared VAST filesystem, with no per-user quota; and Gondor uses a separate 100-TB shared WEKA filesystem. Scratch is not backed up. Old data may be removed as capacity nears, with no fixed purge schedule or exact trigger. The guidance is to check `df -h /scratch` and keep shared filesystem usage below 80% after planned data generation. RDS is the primary long-term store. Create an Activity and Collection, request quota, configure SSH-key access, and transfer retained data from the cluster. Collections over 2 TB require a Data Management Plan.

This resolves the general storage policy. Still unknown are current `/scratch` fullness, RDS collection access/quota for this project, and RDS connectivity from the allocated compute jobs. The 100-TB shared capacity is not a project allocation. Use [A2I2 storage workflow](STORAGE_WORKFLOW_A2I2_2026-11-02.md) for the project's staging/backup steps. Ask support only about project-specific access/runtime/egress facilities; Mohamed should validate Harbor connection requirements against those facilities. The message above is the original sent message, not a pending draft.

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

Is there an official mirror or a pair of OCI image exports, preferably with immutable digests and redistribution/use terms, that we may use for this evaluation?

Thank you,

Sagandeep
