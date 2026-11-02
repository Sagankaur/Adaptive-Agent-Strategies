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

A2I2 support advised that scratch is for active data and workloads, while home is limited and intended for frequently needed files/code. Scratch data may be removed when the filesystem becomes too full. For longer-term persistent storage, use the Research Data Store (RDS). They referred us to the A2I2 support site's storage-structure documentation.

This answers the general storage policy but not the project's specific scratch quota, current free space, purge thresholds/notification, RDS access from Rohan/Gondor jobs, or best location for pinned SIFs and reproducibility artifacts. Review the authenticated [A2I2 storage documentation](https://deakin365.sharepoint.com/sites/A2I2Support) and ask support only for those remaining cluster-specific details, Apptainer compatibility approval, and the egress controls the cluster provides. The SharePoint page could not be opened through the public web reader, so its detailed storage values have not been independently checked here. The message above is the original sent message, not a pending draft.

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
