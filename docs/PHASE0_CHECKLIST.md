# Phase 0 checklist

Status of the Phase 0 items in [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 10, as of 2026-10-30. The snapshot check is from 2026-10-04 and the split rows from 2026-10-15; the split commit, task-source date and pins table were updated on 2026-10-20. Phase 0 is "Setup" (weeks 1–2). Its deliverables are a split file, the price table and a smoke-test report.

No agent has been run on a real benchmark. A low-level llama.cpp serving smoke and one-task project-client/toy-runner smoke passed on the A2I2 L40S on 2026-10-28/29. Scripted and real-Qwen one-task Harbor smokes passed on Rohan with Apptainer 1.3.3 on 2026-10-30; these validate the synthetic container lifecycle and native tool-call path only. The five-task TB-Pro infrastructure smoke remains gated on P-M2, G-BASE and network policy. The portable project-client report, Slurm job, summary and result JSONL are in [`docs/cluster/l40s-client-smoke/`](cluster/l40s-client-smoke/); Harbor details are in [`docs/experiments/Qwen-Harbor-real-model-smoke-2026-10.md`](experiments/Qwen-Harbor-real-model-smoke-2026-10.md).

| Item | Status |
|---|---|
| Pin the benchmark version | **Done for the task source (2026-10-15).** `laude-institute/terminal-bench-2` at commit `2fd12b88aafdd04a52c298e3940bcb189f9766d6`; the 89 task directories were read. Harbor v0.23.0 has passed a synthetic Apptainer smoke; compatibility with the benchmark route is not confirmed. See [`evaluation/data/tb2_tasks.README.md`](../evaluation/data/tb2_tasks.README.md). |
| Fix the splits and commit the split file | **Done (2026-10-15), committed in `92c1621`.** `splits/terminal-bench-2.0.json` was made from `evaluation/data/tb2_tasks.jsonl` with seed 20261015 and the default sizes A=25, V=12, M=15, H=37. A test in `tests/test_splits.py` checks that the file is disjoint, covers all 89 ids and matches the task list. The split is stratified by category and difficulty; there are 16 categories, 5 of them with one task, so small categories are not represented in every split. |
| Get Harbor running in a cloud sandbox | **Not done.** Needs a sandbox provider account and budget. |
| Choose the model: run S0 on 20 tasks from A∪V (starting-score check) | **Not done.** The project client and Harbor have passed synthetic tasks on the L40S; the 20-task starting-score check, benchmark route and budget gates remain open. Candidate models are listed in [`SMALL_MODELS.md`](SMALL_MODELS.md); see [`LOCAL_MODELS.md`](LOCAL_MODELS.md) for client status. |
| Check `terminal-bench-pro` | **Partly done.** Pinned the public v1.0 source, confirmed all 200 task IDs match the official release, and recorded resource requests/base images. The Alibaba registry hosting two base images used by 198 tasks is unreachable from Rohan, so image builds, dedup review, and Oracle checks have not run. See [`P-M2-preflight-2026-10-30.md`](experiments/P-M2-preflight-2026-10-30.md). |
| Check snapshot support | **Done (source and docs check, nothing run).** See below. |
| Agree the budget | **Not done.** This is Prof. Abdelrazek's decision (Q5 in [DECISIONS.md](DECISIONS.md#q5-compute-meeting-point-6); formerly open decision 2). |
| Price table | **Drafted, not frozen.** `evaluation/price_table.json` holds the GPT-5-mini and gpt-oss-120b prices from [PRIOR_WORK.md](PRIOR_WORK.md), seen on 2026-10-02 and not re-checked, and placeholder entries for three local models without a compute rate ([LOCAL_MODELS.md](LOCAL_MODELS.md)). It is to be frozen once the model is chosen. |
| Smoke-test report | **Partly done.** Model serving, project-client/toy-runner, scripted Harbor and real-Qwen Harbor smokes are recorded. The end-to-end real-model smoke used one synthetic task; the five-task TB-Pro smoke remains **not done**. The offline test suite (`make test`) runs every component on a toy environment with a mock model; that is a software check, not a benchmark smoke test. |

## Snapshot support in Harbor

**Question.** Can a task environment be snapshotted or checkpointed during a run and restored later? Rollback (section 8 of the plan) needs this.

**Answer: not through Harbor's interface.** Harbor gives an agent no snapshot, checkpoint or restore operation. Two sandbox backends use provider snapshots, but only as start-up caches, not as mid-run checkpoints.

What was checked, at Harbor commit [`3e30cca`](https://github.com/laude-institute/harbor/tree/3e30cca047a4d0dc1fb209bf5a74ff761b794b90) (main on 2026-10-04; latest release [v0.23.0](https://github.com/laude-institute/harbor/releases/tag/v0.23.0), 2026-09-12):

- **The environment interface.** [`src/harbor/environments/base.py`](https://github.com/laude-institute/harbor/blob/3e30cca047a4d0dc1fb209bf5a74ff761b794b90/src/harbor/environments/base.py) defines:
  - lifecycle: `start`, `stop`;
  - command execution: `exec`;
  - file transfer: `upload_*`, `download_*`;
  - directory helpers: `reset_dirs`, `ensure_dirs`, `empty_dirs`.

  It defines no snapshot, checkpoint or restore method. Its only matches for "restore" are about saving and restoring a default-user attribute.
- **Capability flags.** [`src/harbor/environments/capabilities.py`](https://github.com/laude-institute/harbor/blob/3e30cca047a4d0dc1fb209bf5a74ff761b794b90/src/harbor/environments/capabilities.py) has no snapshot capability.
- **What an agent receives.** In [`src/harbor/agents/base.py`](https://github.com/laude-institute/harbor/blob/3e30cca047a4d0dc1fb209bf5a74ff761b794b90/src/harbor/agents/base.py), an agent's `setup` and `run` receive a `BaseEnvironment`, so the operations above are all it has.
- **Modal backend.** [`modal.py`](https://github.com/laude-institute/harbor/blob/3e30cca047a4d0dc1fb209bf5a74ff761b794b90/src/harbor/environments/modal.py) has no use of snapshots.
- **Daytona and Vercel backends.** These are the only modules that mention snapshots: [`daytona/snapshots.py`](https://github.com/laude-institute/harbor/blob/3e30cca047a4d0dc1fb209bf5a74ff761b794b90/src/harbor/environments/daytona/snapshots.py) and [`vercel/snapshots.py`](https://github.com/laude-institute/harbor/blob/3e30cca047a4d0dc1fb209bf5a74ff761b794b90/src/harbor/environments/vercel/snapshots.py).
  - Daytona creates sandboxes *from* snapshot templates keyed by a hash of the task environment (`auto_snapshot`, `snapshot_template_name`).
  - Vercel caches a Docker host and pre-built task images. Its module docstring says "a cache hit must not be able to change trial behavior, only its speed".
  - Neither is exposed to agents, and neither checkpoints a running trial.
- **Docs.** The [custom sandbox](https://docs.harborframework.com/sandboxes/custom-sandboxes.md) and [pre-integrated sandbox](https://docs.harborframework.com/sandboxes/pre-integrated-sandboxes.md) pages contain no occurrence of "snapshot", "checkpoint" or "restore". The pages and the source files above were searched for these words, and the matching modules were read.

**Not determined.**

- Whether the providers' own SDKs (Modal, Daytona, E2B, Runloop and others) offer mid-run snapshot and restore was not checked. Using them would mean writing a custom Harbor environment backend.
- How long it takes to restart a task container from scratch was not measured.

**Consequence for the plan.** Rollback has to be done inside the container. The plan's simplest version keeps the working directory under git and rolls back files and context together. That covers files only: installed packages, running services and files outside the working directory are not rolled back. `restart_task` (a fresh environment) is the only full reset. This limitation should be stated wherever the rollback sub-question (RQ4, section 8) is reported.

## Pinned versions and sources (proposed)

| What | Pin | Source |
|---|---|---|
| Primary benchmark | Terminal-Bench 2.0, Harbor dataset id `terminal-bench@2.0` | Harbor README run example (`harbor run --dataset terminal-bench@2.0 ...`), https://github.com/laude-institute/harbor; the same id in https://github.com/laude-institute/terminal-bench-2 |
| Task source | `laude-institute/terminal-bench-2` at commit [`2fd12b8`](https://github.com/laude-institute/terminal-bench-2/tree/2fd12b88aafdd04a52c298e3940bcb189f9766d6) (main; committed 2026-04-30 05:53 UTC, which is 2026-04-29 in US time zones) | GitHub API, author and committer date (the two are equal). The API now redirects the repository to `harbor-framework/terminal-bench-2`; `git ls-remote` on 2026-10-20 still gives this commit as `HEAD`. The repo root has 89 task directories, and the `task.toml` of each was parsed; see [`evaluation/data/tb2_tasks.README.md`](../evaluation/data/tb2_tasks.README.md) |
| Harness | Harbor v0.23.0 (GitHub release 2026-09-12; PyPI `harbor` is also at 0.23.0) | https://github.com/laude-institute/harbor/releases, https://pypi.org/project/harbor/ |
| Transfer benchmark | AppWorld v0.1.3.post1 (PyPI, uploaded 2026-02-17) | https://pypi.org/project/appworld/, https://github.com/stonybrooknlp/appworld. The release notes say the main branch is "significantly ahead" of this release, so whether to pin the release or a commit is still open |
| Not used | Terminal-Bench "continuous" (4.0) | A moving target with 8-hour timeouts (https://www.tbench.ai/news/terminal-bench-4-0) |

Before the split file is committed, the task list should be taken from the pinned dataset. A run of `harbor` itself is preferable, so the ids match what the harness runs. Each task's category and difficulty go into a JSONL file, and then:

```
python -m evaluation.splits --tasks tb2_tasks.jsonl --benchmark terminal-bench@2.0 --seed <seed> --out splits/terminal-bench-2.0.json
```

The seed should be chosen and recorded before the file is generated, and the file committed before any agent run.

*(Updated 2026-10-20.)* The split file was committed in `92c1621`, before any agent run, with seed 20261015. Its task list was read from the repository at the pinned commit, not from a run of `harbor`, so checking the ids against a `harbor` run is still to do.
