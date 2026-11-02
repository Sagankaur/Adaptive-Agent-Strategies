# Path to actual benchmark experiments — 2026-10-30

## Current evidence

No Terminal-Bench Pro task has been built, Oracle-checked, or run with an agent. The successful Harbor runs used synthetic tasks and establish integration only. Job `4433963` was submitted as a repeat synthetic real-Qwen smoke after the shared output-token cap landed. Its last recorded state was `PENDING (Resources)`, with an estimated start of 2026-10-31 02:59 AEDT. That status is stale as of 2026-11-02: the workstation could not poll it in this review because the configured SSH alias failed authentication, and the local Python used by the saved Paramiko polling helper does not have Paramiko installed. Its current state is unknown. Do not count this job as evidence until its terminal Slurm state and result files are retrieved.

## Decision

Do not start TB-Pro task builds, Oracle runs, or agent episodes yet. G-BASE is now green, but the required license evidence is incomplete; 198 tasks rely on two custom Alibaba base images that are unreachable; equivalent GHCR images have not been validated; the supported network isolation path is unresolved; P-M2/G-ROUTE is open; and live scratch usage/RDS readiness have not been checked. Launching tasks before these are settled risks producing results that cannot support a paper claim.

## Staged execution plan

### 1. Close G-BASE

- Audit the six acceptance criteria against concrete tests and assertions, including retries, attempt selection, sampling/seeds, judge cost accounting, hidden-test isolation, and B0/S0 judge behavior.
- Record the evidence map and test IDs in the G-BASE audit. Close G-BASE against its six registered baseline checks; freeze the numerical B1 cap mixture at Stage 2 from E1/E-P0 and S* MCU evidence, as specified in the preregistration. Do not invent mixture probabilities early to satisfy G-BASE.

### 2. Resolve the task and cluster route (P-M2)

While awaiting external answers, limit work to public metadata and reproducibility tooling: compare the pinned task Dockerfiles to candidate bases, prepare the routing/dedup report format, and estimate storage needs. Do not execute task Dockerfiles or Oracle code yet.

Before building task images, obtain and record:

- a root `LICENSE` or written TB-Pro author confirmation that covers the pinned task release;
- an accessible, authorized source for both required base images, with immutable digests and an equivalence check before any substitution;
- A2I2 confirmation of Apptainer 1.3.3 approval and available cluster egress controls. Separately, Mohamed should validate Harbor compatibility, identify its required connections, and confirm that the proposed controls preserve them;
- check and record current shared scratch occupancy before large builds. Rohan `/scratch` is shared 100-TB VAST with no per-user quota; keep it below 80% full after planned writes. `/home` is 20 GB. Create an RDS Activity/Collection and request quota for the RDS source of record and backups; requests above 2 TB require a Data Management Plan. See [A2I2 storage workflow](../cluster/STORAGE_WORKFLOW_A2I2_2026-11-02.md). Current free scratch capacity and this project's RDS quota remain unknown.

Then build each eligible task image once, pin its digest, apply the resource filter, owner-review the three nearest TB2 tasks for every candidate using static public text as allowed by LEDGER, and run the allowlisted Harbor Oracle on TB-Pro only. Before the full census, record `df -h /scratch` and a representative build size. After measuring actual task and pinned TB2 image footprints, publish the routing table, host lists, image pins, and disk report, and back up retained artifacts to RDS. Do not give a model, agent, or Oracle access to TB2 tasks or run a TB2 Oracle.

Make the documented G-ROUTE decision mechanically from these criteria: confirmed license; at least 120 tasks survive build, resource, dedup, and Oracle checks before removing the development slice; adapter work remains within five engineer-days; and disk has at least 20% headroom or a logged build-run-prune plan is adopted. If criteria (1)–(3) fail, use the preregistered E-RESPLIT route and document the deviation; do not quietly replace the task source.

### 3. Close the remaining infrastructure controls

Use a single explicitly approved Apptainer/Harbor launch route for the CPU route pilot, or the cluster runtime explicitly approved by A2I2. Demonstrate that unapproved egress is blocked, that every permitted package/task destination is explicit and logged, and that Harbor can still communicate with the model server through the intended local channel. Record probes for a blocked destination and successful approved destinations and local control channel. GHCR reachability alone is not evidence of task isolation or base-image equivalence.

### 4. Run the infrastructure smoke, then the first scored experiment

After G-BASE, G-ROUTE, and the approved isolation route are green, run the preregistered five-task TB-Pro smoke. This smoke closes the final G-INFRA criterion; it is not a prerequisite that G-INFRA be marked green beforehand. Require zero harness errors and preserve task/image digests, seeds, model/serving settings, per-step logs, tool calls, timings, and Harbor's trial-result reward provenance.

Only after the smoke passes should the team start E0 on the reserved TB-Pro non-development pool under the registered protocol. E0 is the first actual benchmark experiment. Keep the TB2 held-out set agent- and Oracle-unseen until the registered final phase. Report task-level outcomes and uncertainty; do not present the one-task synthetic reward as a benchmark score.

## Immediate actions

1. Retrieve job `4433963` status and artifacts from Rohan; update this record with terminal state and clearly label it as synthetic integration evidence.
2. Check `df -h /scratch`, create the RDS Activity/Collection, and configure/test access. Follow up with A2I2 on runtime and egress facilities; ask Mohamed about Harbor-specific requirements. The TB-Pro author license/base-image request remains unsent; status and response notes are in [`OUTREACH_DRAFTS_2026-10-30.md`](../cluster/OUTREACH_DRAFTS_2026-10-30.md).
3. Complete the G-BASE six-check evidence map and its CI evidence. Freeze and implement the numerical B1 cap mixture at Stage 2, after the registered compute-matching data are collected.
4. Resume P-M2 only when license, image route, approved network/runtime controls, and measured storage capacity are available.

## What can be told to the professor now

The system has completed synthetic Harbor integration smokes, including a one-task real-Qwen run on Rohan. The adapter records Harbor's trial reward and tool interactions. These results show the execution path works for the synthetic task; they do not measure task-solving performance. No TB-Pro benchmark result exists yet. The immediate research decision is whether the licensed, reproducible TB-Pro image route can be made available; if it cannot meet the prespecified G-ROUTE criteria, the protocol already defines the TB2 re-split fallback.
