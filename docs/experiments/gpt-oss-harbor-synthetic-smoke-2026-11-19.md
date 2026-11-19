# gpt-oss in Harbor: synthetic task smoke

**Result: passed as an engineering integration check.** Slurm job `4802977` ran one real-model Harbor trial on an RTX Pro 6000. The model created the requested file in a made-up task, and Harbor's verifier awarded `1.0`. This is not an Aider Polyglot result or evidence of benchmark performance.

## What ran

- Local model: `gpt-oss-20b-MXFP4.gguf`, pinned SHA-256 `27cd6c432c7672cb812a92f611cf3ba7bbc35928262bb1e1253ff4ee6ae35901`.
- Harbor `0.23.0`, using the project's `HarborStrategyAgent` and frozen default strategy `S0`.
- Task runtime SIF SHA-256 `1188aca02532530596e5e2c4642244ebb1020469ef489fe60ed55a5ea8ec56d8`; Apptainer `1.3.3`.
- The task only asked the model to write the exact text `harbor smoke passed` to `/app/output.txt` and submit.
- Harbor retained its private Unix-socket control channel. The task used Apptainer `--net --network none --writable-tmpfs --containall`, without `--fakeroot`; telemetry was disabled.

## Observed result

| Measure | Result |
|---|---:|
| Slurm state / exit | `COMPLETED`, `0:0` |
| Slurm elapsed / peak RSS | `00:01:08` / `5194580K` |
| Harbor trials / exceptions | 1 / 0 |
| Verifier reward | 1.0 |
| Agent actions | two setup probes, one model terminal command, configured check hook skipped, submit |
| Model requests | 2 |
| Input / cached / output tokens | 1,132 / 550 / 98 |
| First request prompt / generation speed | 2,833 / 254 tokens/s (llama.cpp timing fields) |
| Adapter command tripwire flags | 0 |

The two model requests consisted of one file-writing tool call and one submission. The actual verifier ran one pytest test and reported `1 passed`. It is a trivial synthetic task intentionally designed to validate the model → tool call → private Harbor control channel → task filesystem → verifier path.

## What this supports

The previous no-model CLI preflight plus this run show that, for this synthetic fixture, Harbor 0.23.0 can carry a real gpt-oss tool call into an Apptainer task while the verified network-isolated task runtime and private Unix-socket control path remain in place. No task from Aider Polyglot, Terminal-Bench 2, or Terminal-Bench Pro was generated or run. No Oracle or reference solution was used.

## What remains unproven

- This does not measure coding ability, pass rate, adaptation, or any benchmark score.
- Isolation probes were run in the matched no-model preflight job `4802971`, not repeated by this trivial file-writing task. The real-model task used the same pinned SIF and `network=none` provider path; no benchmark task has yet been tested under it.
- Aider task-specific dependency, setup, and artifact behavior still needs auditing before episodes. In particular, the pinned adapter's task-generation path may create an encrypted Oracle artifact from reference material; the pilot protocol forbids Oracle use and needs a generation path that does not process or retain it.
- `restart_task` was not invoked or tested.

## Files and evidence

- Sanitized machine-readable result: [`artifacts/gpt_oss_harbor_synthetic_4802977/result.json`](artifacts/gpt_oss_harbor_synthetic_4802977/result.json).
- Job outputs and raw logs remain on Rohan scratch, not in the public repository.
- The reproducible Slurm entry point and made-up fixture are in [`../cluster/harbor-egress-safety/07_gpt_oss_harbor_synthetic.sbatch`](../cluster/harbor-egress-safety/07_gpt_oss_harbor_synthetic.sbatch) and `docs/cluster/harbor-egress-safety/07_gpt_oss_harbor_fixture/`.
