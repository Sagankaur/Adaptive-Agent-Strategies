# HPC and TB-Pro outreach drafts — 2026-10-30

These drafts are prepared for the next route-gating step. They have **not been sent**.

## A2I2 HPC support

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
