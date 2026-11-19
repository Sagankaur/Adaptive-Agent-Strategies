# Terminal-Bench 2.0 one-task pilot

**Status:** stopped at exact-image infrastructure preflight; no agent episode started.

## Purpose and claim boundary

Run one end-to-end Harbor episode on Rohan to check whether the pinned local gpt-oss model can attempt an actual Terminal-Bench 2.0 task through the project's Harbor agent and receive the official verifier result. This is feasibility evidence for one task only. It is not a benchmark score, treatment comparison, or evidence that strategy adaptation works.

The researcher explicitly requested a pilot after the benchmark snapshot was staged on Rohan. This is a one-task exception to the 2026-11-06 decision not to run models on TB2. It does not authorize additional TB2 episodes or change the main proposal. The selected task is permanently excluded from all confirmatory scores and from later adaptation or candidate selection.

## Frozen task selection

- Source snapshot: `harborframework/terminal-bench-2.0`, revision `f2e8c75e23add71613117eecc9498f53bcd7e04e`.
- Task pool: the committed A/adaptation split, excluding all 19 task IDs listed under Decision 21 as previously exposed to assistant instruction review. This pilot task is then recorded in `evaluation/data/tb2_pilot_exclusions.json` and removed by `evaluation.splits.load_confirmatory_split` from all future confirmatory TB2 split consumers. The historical split file remains unchanged; the effective pool has 88 eligible tasks after this additional exclusion.
- Selection: from remaining A-pool IDs, choose the only task marked easy in the software-engineering category using repository metadata only. No task instruction, test, solution, or environment source was read by Codex to select it.
- Frozen task: `cobol-modernization` (easy; software engineering). Task metadata names image `alexgshaw/cobol-modernization:20251031` and requests 1 CPU / 2 GiB. Docker Registry resolved the tag to the immutable manifest `sha256:593ab9df3d83f771e927888b2d9436b380cdf7ec4d0af2a9f0802d541edebba0` on 2026-11-19; the Apptainer pull must use this digest, then record the resulting SIF SHA-256.
- Exactly one attempt; no replacement task and no retry for an agent or verifier failure.

## Run configuration

- Model: pinned `gpt-oss-20b-MXFP4.gguf`, served locally on Rohan's RTX Pro 6000; server binds to `127.0.0.1`, logs disabled, context 32,768, one slot.
- Agent: project `HarborStrategyAgent`, fixed S0 strategy with its optional visible-test self-check disabled so the official Harbor verifier is the only score source; sampling temperature 0.6, top-p 0.95, top-k 20, one frozen seed. No Oracle/reference solution is run.
- Harness: Harbor 0.23.0 and the already tested Apptainer 1.3.3 UDS provider patch. Task-container execution must use `--net --network none --writable-tmpfs --containall`, with no `--fakeroot`; Harbor control stays on the private Unix socket.
- Scoring: Harbor's official task verifier only. Do not generate or run an Oracle, inspect or invoke a reference solution, or expose verifier tests to the model.
- Telemetry: set `HARBOR_TELEMETRY=off` before invoking Harbor.
- Resources: one RTX Pro 6000, 8 Slurm CPUs, 64 GiB RAM requested, one task attempt, short QoS, 1-hour limit. Record observed allocation and limits; do not claim container-level CPU/RAM enforcement.
- Raw task/model logs remain on scratch and are not copied to Git. The repository receives only a sanitized summary containing task ID, Harbor reward/status, model and image hashes, resource facts, and failure class if applicable.

## Preconditions and stop rules

1. Verify model, server image, source commit, and task snapshot revision before launch.
2. Pull the task image by the frozen Docker Registry manifest digest into the Apptainer cache before starting the model server. Record the image manifest and SIF SHA-256. If the image pull or task startup fails, record an infrastructure failure and stop; do not choose another task.
3. Confirm captured Apptainer argv contains network-none and UDS settings and omits fakeroot. If any condition differs, stop before the model episode.
4. Stop on server failure, lost control socket, any task-container egress, unexpected Oracle/reference artifacts, or missing verifier result. No retries or task replacements.
5. Do not use the outcome to tune S0, prompts, or the main selection rule. Any future pilot or benchmark evaluation requires a separate preregistered decision.

## Durable exclusion

The canonical split remains unchanged as historical provenance. The task is listed in `evaluation/data/tb2_pilot_exclusions.json`; future confirmatory split consumers must call `evaluation.splits.load_confirmatory_split`, which removes pilot-exposed tasks and recomputes effective split sizes and the task fingerprint. A regression test asserts the task is absent from all eligible split partitions.

## Research-integrity note

The earlier assistant review exposed instruction text for 13 candidate pairs (19 distinct task IDs). `cobol-modernization` does not appear in that exposure list. This new run exposes one additional task instruction to the local model and makes the selected task unsuitable for later confirmatory evaluation. The historical 26-pair exposure remains a limitation for TB2 as a whole and must remain disclosed in any pre-registration.

## Results

The pilot stopped before model startup because Harbor could not start its execution server in the selected task image.

| Check | Evidence |
|---|---|
| Snapshot provenance | Revision `f2e8c75e23add71613117eecc9498f53bcd7e04e` verified against Hugging Face file metadata and content IDs; tree SHA-256 `ff1b9e47c776786c7b82757a5af006921600e7283082c802d6785c2c769522f6`. |
| Image provenance | Docker Registry manifest `sha256:593ab9df3d83f771e927888b2d9436b380cdf7ec4d0af2a9f0802d541edebba0`; pulled SIF SHA-256 `e7fc37ce09d4ee50e4a71a6e2c9941c0cdacdeb979fcaf99182728b3d0e0dd49`. |
| Exact-image Harbor preflight | Job `4869467`, `FAILED 1:0`, 2:15. Apptainer launched with `--net --network none --writable-tmpfs --containall` and no fakeroot, but Harbor's server failed before UDS health because `/usr/bin/python3` was absent and Harbor could not install it with task networking disabled. |
| Network/control result | Not established for this image: the server failed before the UDS control check and external/metadata probes. The prior synthetic-image egress tests do not substitute for this task-image check. |
| Workspace exposure check | Not reached. |
| Model / agent / Harbor trial | None. No Oracle, reference solution, or task verifier was run. No benchmark reward exists. |

Two earlier model-free attempts failed in preflight code before the image was pulled: job `4869462` used the cluster default Python without `tomllib`; job `4869464` mishandled Hugging Face LFS metadata. Those implementation issues were fixed. Job `4869467` reached the exact task-image startup check and exposed the blocker above. Per the frozen stop rule, the pilot stops here; no runtime injection, replacement task, or model episode was attempted.

The sanitized record is [`artifacts/tb2-one-task-pilot-2026-11-19.json`](artifacts/tb2-one-task-pilot-2026-11-19.json). Raw startup logs remain on Rohan scratch and are not copied to Git.
