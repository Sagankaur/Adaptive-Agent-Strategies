# E-N4: expressiveness audit

**Status:** desk audit, zero episodes. This is a source-to-implementation mapping for the current repository snapshot, not a claim that the external papers' complete harnesses can be reproduced here.

**Question.** Which reported harness edits can this project's current strategy schema and runtime express as executable behavior, which can only be advised in rendered instructions, and which lack a corresponding mechanism?

## Classification rule

- **Code-enforced:** a schema field reaches a runtime branch that changes execution. Existing tests are cited as implementation evidence where available. A field's presence in the Pydantic schema alone is insufficient.
- **Prompt-text-only:** `Strategy.render()` can tell the model to do the behavior, but the runtime does not enforce it.
- **Not expressible:** there is no suitable runtime mechanism. A text instruction or a coarse field is noted as an approximation where useful.

The audited implementation is `strategy_schema/model.py`, `baselines/agent_loop.py`, and `environments/harbor_agent.py`. The latter is the Harbor controller; code-enforcement conclusions are specific to it unless otherwise stated. The schema has typed values for more behaviors than the controller currently executes.

## Summary

| Source | Operation-level rows | Code-enforced | Prompt-text-only | Not expressible |
|---|---:|---:|---:|---:|
| Self-Harness, four retained Qwen edits | 4 | 0 | 3 | 1 |
| AHE, changes in four winning rounds | 10 | 0 | 3 | 7 |
| MemoHarness, six published control dimensions | 9 | 1 | 3 | 5 |

Counts describe operation-level rows below, not independent evaluations of the papers' full systems. MemoHarness's six dimensions are operation families, not six retained edits; some dimensions expand into multiple operations. A separate verification analogue is discussed below but is not counted as MemoHarness output processing.

## Self-Harness: four retained Qwen edits

The paper reports the four themes as dependency prechecking, loop breaking, command-retry discipline, and artifact-focused recovery. The paper describes merged code edits and does not isolate each edit's effect. Mapping follows the published behavior descriptions, not a port of its code.

| Published edit | Nearest schema path | Class | Reason and limitation |
|---|---|---|---|
| Dependency prechecking before acting | `/exploration/probes`, `/exploration/probe_budget_steps`, `/exploration/read_tests_first` | Prompt-text-only | The Harbor adapter can execute its fixed, safe probes, including checking installed packages. It does not inspect project dependency declarations, resolve whether task-required packages are missing, or enforce a dependency preflight policy. `Strategy.render()` can advise the model to precheck dependencies. |
| Break out of repetitive/looping command behavior | `/recovery/on_repeated_failure`, `/planning/replan_trigger` | Prompt-text-only | These values are rendered as instructions. The controller does not detect repeated commands or invoke a loop-breaking branch from these settings. |
| Retry failed commands with disciplined limits | `/recovery/max_retries`, `/recovery/retry_on` | Prompt-text-only | Retry guidance is rendered, but Harbor does not automatically rerun a failed command based on return code or timeout. |
| Recover around expected output artifacts after tool failures | `/verification/checks`, `/recovery/*` (coarse approximation) | Not expressible | The controller can run configured end checks, but it has no conditional recovery middleware that identifies a missing expected artifact after a tool error and chooses a targeted recovery action. A generic output check is only a partial approximation. |

## AHE: changes shipped on four winning rounds

AHE Appendix C.2 groups the shipped changes into four winning iterations, with a prompt edit and a harness mechanism in each. We split those eight described components into separate rows. The paper's descriptions are summarized at the behavior level; these rows do not reproduce its implementation.

| Source locator | Published change | Nearest schema path | Class | Reason and limitation |
|---|---|---|---|---|
| Appendix C.2.1, iteration 2 | Eight system-prompt rules: acceptance-contract extraction, evaluator mirroring, minimal edits, candidate scoring, generalization, time budgeting, end-state readiness, and a stop rule | `/notes/plan`, `/notes/act`, `/notes/verify` | Prompt-text-only | Notes are rendered into the agent instruction; the runtime does not enforce these procedural rules. |
| Appendix C.2.1, iteration 2 | Supply a shell timeout argument dynamically for the current command | `/tool_policy/command_timeout_s` | Not expressible | The adapter applies one configured timeout value (clipped to remaining episode time); it does not dynamically add a timeout argument to each shell command based on command type or risk. |
| Appendix C.2.2, iteration 5 | Prompt rules for publish-state discipline, constrained delivery layouts, and literal outputs | `/notes/act`, `/notes/verify` | Prompt-text-only | The model can be instructed to preserve publish state and respect output formats, but no publish-state model is maintained by the runtime. |
| Appendix C.2.2, iteration 5 | Edit the shell-tool descriptor to explain the publish-state, scratch-layout, and literal-output rules | No editable tool-description field | Not expressible | The tool call surface is fixed in the adapter; strategy notes can approximate instruction text but cannot change the tool descriptor. |
| Appendix C.2.2, iteration 5 | Shell-tool guard that tracks/blocks invalid publish-state transitions | `/tool_policy/forbidden_patterns` (coarse approximation) | Not expressible | A static substring denylist does not represent task state or validate allowed state transitions. |
| Appendix C.2.3, iteration 6 | Protect framework entrypoints from edits | `/tool_policy/forbidden_patterns` (coarse approximation) | Not expressible | The denylist checks command substrings; it does not provide path-aware write protection or protected-file enforcement. |
| Appendix C.2.3, iteration 6 | Execution-risk hints/middleware before risky actions | `/notes/act`, `/tool_policy/forbidden_patterns` | Not expressible | Text can advise caution and static patterns can refuse known strings, but no risk classifier or pre-execution middleware scores actions. |
| Appendix C.2.4, iteration 8 | FRAMEWORK reminders as behavioral advice | `/notes/act`, `/notes/verify` | Prompt-text-only | Notes can carry the reminder content as advice. The controller does not inject it conditionally into a later turn; that delivery behavior is covered in the next row. |
| Appendix C.2.4, iteration 8 | Middleware that increases reminder salience after detected violations | No strategy-controlled cross-step middleware | Not expressible | The controller does not infer those cross-step patterns or inject a conditional reminder into a later turn. |
| Appendix C.2.4, iteration 8 | Hard blocks for destructive deletion/reset operations | `/tool_policy/forbidden_patterns` (coarse approximation) | Not expressible | The current substring filter can block listed strings but does not implement semantic/path-aware protection for destructive operations. It is not equivalent to AHE's hard guard. |

## MemoHarness: six published control dimensions

MemoHarness presents six control dimensions and examples of per-case adaptation. The rows below expand dimensions where needed to separate atomic operations; they do not relabel the dimensions as retained edits.

| Published operation family | Nearest schema path | Class | Reason and limitation |
|---|---|---|---|
| Context assembly: instruct the model to structure task/context material | `/memory/context_mode`, `/memory/window_or_summary_k` | Prompt-text-only | Context policy is rendered as advice; the controller does not apply a sliding window or summarize based on these values. |
| Context assembly: retrieve and rank demonstrations for the current case | No retrieval/top-k/reranking mechanism | Not expressible | The controller has no demonstration store or case-conditioned retrieval path. |
| Tool interaction: adapt tool exposure/selection per case | No editable tool-description or tool-set field | Not expressible | Harbor always sends its fixed tool definitions to the model. `tools_allowed` authorizes shell execution at runtime, but does not hide/select tools at model-call time. |
| Tool interaction: enforce shell authorization, timeout, and observation limits | `/tool_policy/tools_allowed`, `/tool_policy/command_timeout_s`, `/tool_policy/max_observation_chars` | Code-enforced | Harbor gates terminal execution on shell authorization, applies the timeout, and clips returned output. This is an analogue for tool control, not MemoHarness's per-case tool selection/retrieval. |
| Generation control: adapt model sampling/generation parameters | No editable strategy field | Not expressible | Sampling and server generation controls are experiment configuration, not strategy edits in this schema. `/budget/max_tokens` is a fixed episode cap, not adaptive generation control. |
| Orchestration: advise planning and order of operations | `/planning/*`, `/notes/plan` | Prompt-text-only | Plan and replan behavior is stated in rendered instructions; the Harbor controller does not maintain a plan state machine or force replanning at the configured triggers. |
| Memory management: advise state tracking and lesson use | `/memory/state_notes`, `/memory/lessons_k`, `/memory/lesson_store_version` | Prompt-text-only | The prompt can request running state notes and lessons, but these fields do not themselves provide persistence or retrieval. |
| Memory management: persist state, summarize traces, and retrieve cross-call experience | No memory service or summarization controller | Not expressible | There is no experience-bank storage/retrieval or trace summarization service driven by these fields. |
| Output processing: extract/validate generated output and choose a fallback format | No output parser/repair/fallback policy | Not expressible | The adapter accepts the model's submit answer; it does not implement MemoHarness-style extraction, validation, or fallback formatting. |

The project does have a **separate executable verification analogue**: Harbor runs configured experimenter-provided checks and can return control after failure within the cycle cap (`/verification/*`; `environments/harbor_agent.py`, `_run_own_checks`; `tests/test_baselines.py`, `test_verification_sends_the_agent_back_to_fix`). This verifies task state; it does not transform the model's output and is therefore not classified as MemoHarness output processing.

## Evidence in this repository

- `strategy_schema/model.py`: schema types and `Strategy.render()`; notably planning, memory, recovery, and notes render as instructions.
- `environments/harbor_agent.py`: Harbor enforces tool availability, forbidden-pattern checks, command timeout, observation truncation, probes, verification checks, and verification-cycle limits.
- `baselines/agent_loop.py`: the non-Harbor baseline has its own enforcement of probes, verification, and episode budgets; do not generalize Harbor-specific paths to every adapter without checking that adapter.
- Existing tests exercising relevant behavior include `tests/test_baselines.py` (probe/check/retry-cycle behavior) and `tests/test_harbor_adapter.py` (adapter execution and budgets). This audit did not run tests.
- `docs/RISK_REGISTER.md`, RK-17, already records the broad distinction between controller behavior and prompt-only schema fields. This file refines that statement against the published operation families for E-N4.

## Implications for paper tables

For Table 1, use this audit only to characterize the closest-work mechanism; do not claim the audit is a performance comparison. For Table 2, classify fields individually using observed controller branches and tests, rather than carrying over a whole-dimension label. For Appendix A10, retain the source locator and mapping limitation in every row. The primary conclusion is that the schema's descriptive coverage exceeds its current executable coverage: retry, planning, context/memory strategy, and many safety ideas remain advice or unavailable runtime mechanisms.

## Sources

- Zhang et al., [Self-Harness: Harnesses That Improve Themselves](https://arxiv.org/abs/2606.09498), especially the four retained Qwen edits described in the paper's analysis and Figure 6.
- Lin et al., [Agentic Harness Engineering (AHE)](https://arxiv.org/html/2604.25850v4), Appendix C.2.1 to C.2.4.
- Huang et al., [MemoHarness: Agent Harnesses That Learn from Experience](https://arxiv.org/html/2607.14159), section 2.3 and Table 1.
