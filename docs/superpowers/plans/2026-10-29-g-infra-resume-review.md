# G-INFRA resume review — 2026-10-29

> Historical planning snapshot from before the Harbor adapter implementation. Its “Current evidence” and recommendation sections describe the repository at the time of review, not the current state. For the implementation and latest Rohan runtime attempts, see [`docs/cluster/harbor-adapter/IMPLEMENTATION_2026-10-29.md`](../../cluster/harbor-adapter/IMPLEMENTATION_2026-10-29.md) and [`docs/cluster/SSH_RETRY_2026-10-29.md`](../../cluster/SSH_RETRY_2026-10-29.md).

## Scope

Resume the local G-INFRA engineering gate after the real-model client/toy-runner smoke. This work does not authorize provider-backed task runs, TB2 episodes, or a claim that G-INFRA is closed.

## Current evidence

- `llm/async_openai_compatible.py` exists as a standalone async client. Its fixture coverage is in `tests/test_async_openai_compatible.py`.
- The async response retains nullable content, reasoning, tool calls, cached tokens, llama.cpp timings, and request seed.
- `evaluation/runner.py` remains synchronous, while `baselines/agent_loop.py` grades through `Environment.grade()`.
- No Harbor agent adapter, Harbor job configuration, or Harbor trial-result reward join is present.
- The project plan proposes Harbor v0.23.0. Existing notes mention a newer v0.24.0, so the adapter API must be verified against the selected pin before implementation.
- The upstream v0.23.0 `BaseAgent` source confirms `async setup(environment)`, `async run(instruction, environment, context)`, and the `module.path:ClassName` import-path convention. `AgentContext` is intended to be populated during execution so partial usage survives timeout/error.
- The upstream v0.23.0 job config exposes `n_concurrent_trials` (default 4) and `timeout_multiplier` (default 1.0), with separate agent/verifier multiplier fields. The planned multiplier 2 should be applied to the intended timeout field explicitly.
- The v0.23.0 source review does not establish a reward field on the agent context or `TrialResult` from the checked file alone. The concrete result/join shape still needs source inspection before coding; keep grading outside `run()`.
- Current working tree has an unrelated untracked `.pytest-workspace-tmp/` directory. Preserve it.

## Recommended implementation sequence

1. Verify Harbor's exact pinned package API: import path, async lifecycle, environment execution interface, timeout/cancellation behavior, and post-trial reward result shape. Record the resolved version or commit.
2. Add a Harbor-specific adapter behind isolated imports. Construct one model client per trial, translate Harbor tool execution to the existing strategy behavior, and keep hidden reward inaccessible inside `run()`.
3. Join reward from Harbor's completed trial result by trial ID. Missing or malformed reward must be an explicit error, never inferred as success from a submitted answer.
4. Emit per-step JSONL with run/trial/task identity, strategy hash, provenance, seed, model timing and token fields, action/tool result, and errors.
5. Add job configuration with concurrency equal to the pinned llama.cpp slot count and timeout multiplier 2.
6. Run the scripted CPU toy Harbor trial and verify reward provenance, step logs, timeout handling, and cleanup. Only after route/provider/network/budget/license/disk gates pass may the five-task TB-Pro infrastructure smoke run.

## Independent review checklist

- [ ] Adapter lifecycle matches the exact Harbor pin.
- [ ] Harbor owns final grading; the agent never calls `env.grade()` or observes hidden tests/reward.
- [ ] Tool-call IDs and tool-role messages round-trip; tool arguments are validated before execution.
- [ ] Request seeds are unique under concurrent trials and reproducible from task/run identity.
- [ ] Logs preserve trial identity and distinguish model timing from elapsed step/trial time.
- [ ] Missing reward, malformed tool calls, timeout, and cancellation fail explicitly and clean up resources.
- [ ] CPU scripted Harbor toy run produces a complete Harbor result and logs.
- [ ] G-INFRA remains open until the five-task smoke has zero harness errors and G-BASE is green.

## Decision

Proceed next with Harbor API/pin verification, then implement the smallest adapter slice. The independent reviewer did not recommend extending the existing parser before the Harbor lifecycle is understood. Do not use the October 29 project-client/toy-runner result as Harbor or Terminal-Bench evidence.

## Source verification

- Harbor v0.23.0 [`BaseAgent`](https://github.com/harbor-framework/harbor/blob/v0.23.0/src/harbor/agents/base.py) defines the async lifecycle and import-path format.
- Harbor v0.23.0 [`AgentContext`](https://github.com/harbor-framework/harbor/blob/v0.23.0/src/harbor/models/agent/context.py) includes token/cache usage and metadata fields for agent execution.
- Harbor v0.23.0 [`JobConfig`](https://github.com/harbor-framework/harbor/blob/v0.23.0/src/harbor/models/job/config.py) defines concurrency and timeout multipliers.
- Harbor v0.23.0 [`TrialResult`](https://github.com/harbor-framework/harbor/blob/v0.23.0/src/harbor/models/trial/result.py) is the next source to inspect for the exact verifier reward field and persisted trial ID; no reward field is assumed here.

## Independent review attribution

Plan and review prepared by a subagent from the repository's G-INFRA gate, execution plan, current client/runner code, and test inventory. Review was read-only; no code or test files were changed by the reviewer.
