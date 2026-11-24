# Synthetic tool-schema and message-history diagnostic — 2026-11-20

## Status

The task-free diagnostic ran first on Rohan's RTX Pro 6000 (job `4870222`) and then as a paired cap sensitivity check on an L40S (job `4882620`). Both completed at Slurm level. These are engineering diagnostics, not benchmark results or full Harbor agent replays.

## Why this is the next step

The Aider feasibility pilot attempted four eligible tasks in five Harbor trials and received no verifier rewards. Three trials ended when the adapter rejected malformed JSON tool arguments; Hangman received an HTTP 400 associated with context length. The earlier 50-request gpt-oss diagnostic passed, but used a synthetic `record_sample` schema and did not model the project's real `terminal` and `submit` calls or Harbor's multi-turn message roles. Re-running the same Aider tasks would repeat the failed sample without resolving this interface question.

## Diagnostic question

Can the pinned local gpt-oss model, llama.cpp server, project OpenAI-compatible client, actual tool schemas, and Harbor-shaped assistant/tool history sustain synthetic turns with parseable, schema-valid arguments at controlled history lengths?

## Safety and scope

- No benchmark task, task instruction, workspace, verifier, reference solution, or Oracle is loaded.
- No tool executor is instantiated. Synthetic tool calls are treated as inert data; commands returned by the model are never run.
- The prompt and tool results are generated synthetic text only.
- Logs and result artifacts contain only aggregate counts, timing, token counts, error categories, and input/configuration hashes. They must not contain prompts, completions, tool names, command/answer strings, or tool arguments.
- Use the already pinned local model and localhost-only server. This remains serving-only work under the A2I2 egress advisory; it does not validate task-container isolation.
- Abort if the pinned model/server files do not match the prior report, the server cannot bind only to localhost, telemetry cannot enforce the 1 GiB VRAM headroom stop, or any output path could persist raw model text.

## Proposed protocol

Use the schemas from `environments/harbor_agent.py`, the same `AsyncOpenAICompatibleModel` client and assistant-message serializer, and the S0 strategy rendering with a synthetic diagnostic prompt. This is a narrow schema/history test: it does not reproduce Harbor setup, task instructions, probes, command execution, verification, or the complete agent loop. For a valid first tool call, append Harbor-shaped `assistant` and `tool` messages with a fixed synthetic result; never pass the call to Harbor or a shell. Stop on malformed JSON, invalid argument shape, provider error, or unexpected tool response.

The predeclared conditions are 1,024, 4,096, and 6,400 measured input tokens; eight independent conversations per length; and at most two requests per conversation (48 calls maximum). The server context is 8,192 tokens, output cap 192 tokens, and context margin 1,024 tokens. Record outcome classes (client error category, JSON validity, tool category, argument schema), prompt/output token counts, latency, and assigned-GPU VRAM peak/minimum-free memory. Aggregate before writing the artifact. The wrapper verifies model/server hashes and requires an externally supplied expected source commit. The Python monitor selects the Slurm-visible device, stops the model server on telemetry failure or free headroom below 1 GiB, and fails closed. Do not retry failures or change prompts/settings after seeing outcomes.

## Interpretation and decision rule

These diagnostics can establish only whether the model/client interface handles the tested synthetic protocol. They cannot establish coding ability, Aider benchmark performance, Harbor task success, egress isolation, or the root cause of every earlier failure. The paired run still produced many no-tool responses and no valid submit call, so the task-level pilot remains premature. Do not rerun the four frozen Aider tasks. Before any new benchmark episode, resolve the remaining synthetic protocol failures, then freeze and preregister a fresh, unattempted Aider sample and one-task lifecycle check.

## Results (2026-11-20)

The pinned model and server SIF hashes matched. The model server was localhost-only. No benchmark task, Oracle, reference solution, or tool executor was used. The assigned GPU monitor recorded 40 samples, a peak of 11,953 MiB used, and minimum free memory of 85,934 MiB; the 1 GiB headroom stop was not approached. The job completed in 1 minute 16 seconds. Slurm's CPU and memory cgroup limit files were empty, so hard CPU/RAM enforcement remains unverified.

| Synthetic input condition | Mean input tokens | Calls | Outcome |
|---|---:|---:|---|
| Short (target 1,024) | 1,004.9 | 10 | 4 schema-valid terminal calls; 6 no-tool responses |
| Medium (target 4,096) | 4,142 | 8 | 8 no-tool responses |
| Long (target 6,400) | 6,353 | 8 | 8 no-tool responses |
| **Total** | — | **26** | **4 valid terminal calls; 22 no-tool responses** |

There were no malformed-JSON outcomes because most responses contained no structured tool call to parse. Mean output length was exactly the 192-token cap in the medium and long conditions. This suggests the cap may be too low for this system prompt and model; it does not prove why the model omitted calls. The diagnostic therefore does **not** clear the Harbor tool protocol and does not explain the Aider pilot's invalid-JSON errors. A separate, preregistered output-cap sensitivity check would be needed before another task episode.

Two earlier submissions failed before inference and are excluded: job `4870215` hit an A2I2 profile startup error (`LC_BYOBU` under nounset), and job `4870220` had a stale runner filename in its preflight. Neither started the model server or sent a model request.

The sanitized result artifact is [`aider_tool_schema_history_diagnostic_2026-11-20.json`](artifacts/aider_tool_schema_history_diagnostic_2026-11-20.json). It records source commit `be772b82563a0a13e3c5167784c4fad6b9f05367` and contains aggregate outcomes only.

## Prior evidence

- [Aider Polyglot pilot](aider-six-task-pilot-2026-11-19.md): 4 eligible IDs attempted, 5 Harbor trials, no valid verifier reward.
- [Synthetic context diagnostic](gpt-oss-tool-context-diagnostic-2026-11-19.md): 50/50 requests passed its `record_sample` schema; this did not exercise the real agent schema/history protocol.

## Files

- Runner: [`03_tool_schema_history_diagnostic.py`](../cluster/aider-pilot/03_tool_schema_history_diagnostic.py)
- Slurm wrapper: [`03_tool_schema_history_diagnostic.sbatch`](../cluster/aider-pilot/03_tool_schema_history_diagnostic.sbatch)
- Results artifact: [`aider_tool_schema_history_diagnostic_2026-11-20.json`](artifacts/aider_tool_schema_history_diagnostic_2026-11-20.json)

## Pre-registered cap sensitivity follow-up (2026-11-23)

The first run's medium and long mean output lengths equaled the 192-token cap, but the client does not retain the server's `finish_reason`; saturation is a hypothesis, not a confirmed truncation event. To test that hypothesis with a controlled comparison, run paired 192- and 512-token output-cap arms using the same fresh synthetic prompt and seed for each pair. Keep the pinned model/server, system text, schemas, context targets, sampler settings, eight repetitions per length, and maximum two-turn trajectory fixed. The only treatment difference is output cap. Use seed root `20261123`, with separate client instances per arm so each paired conversation uses the same request-seed sequence. Report the arms descriptively; do not claim a task-level effect or statistical significance.

The maximum is 96 model calls (3 history lengths × 8 repetitions × 2 caps × 2 turns). The initial prompt target is checked against each arm's output cap plus the 1,024-token margin. At the long target, the first call fits under the 8,192-token context; if a second-turn history no longer fits, the runner records a context-headroom stop and does not send it. The artifact also counts responses whose reported output tokens reach the configured cap; this is only a saturation proxy because the client does not capture `finish_reason`. No benchmark task or task text is involved. This is a separate engineering follow-up, not a rerun of the Aider task pilot.

## Paired cap sensitivity results (2026-11-24)

Slurm job `4882620` ran on an Rohan L40S and completed `COMPLETED 0:0` in 2 minutes 56 seconds. It used the pinned model and server hashes and sent no benchmark task or task text. The 192- and 512-token arms used the same synthetic prompts and paired request seeds, with eight repetitions at each history length. The L40S monitor recorded 188 samples, peak use of 11,771 MiB, and minimum free memory of 34,297 MiB. The 1 GiB headroom stop was not approached. Slurm's CPU and RAM cgroup limit files were empty, so hard enforcement of those limits remains unverified.

| History target | Output cap | Model calls | Terminal-schema responses (any turn) | No-tool responses (any turn) | Mean output tokens |
|---:|---:|---:|---:|---:|---:|
| 1,024 | 192 | 8 | 0 | 8 | 192 |
| 1,024 | 512 | 11 | 6 | 5 | 401.5 |
| 4,096 | 192 | 8 | 0 | 8 | 192 |
| 4,096 | 512 | 9 | 2 | 7 | 434.4 |
| 6,400 | 192 | 8 | 0 | 8 | 192 |
| 6,400 | 512 | 8 | 2 | 6 | 498.1 |

The long 512-token arm also recorded two context-headroom stops before a second request; these were not model calls. Across the 512-token arm, 10 of 28 model calls returned schema-valid terminal calls, while 18 returned no tool call. Neither arm produced a valid `submit` call or an invalid-JSON outcome. All 24 calls in the 192-token arm used all 192 output tokens; the 512-token arm also frequently reached its cap. The client does not record `finish_reason`, so output counts at the cap do not prove truncation.

The 192-token arm had 24 first-turn requests and no conditional second turns. The 512-token arm had 24 first-turn requests plus four conditional second-turn requests. Because outcomes were aggregated across turns, the result does **not** isolate the cap's first-turn effect: it reports 10 terminal-schema responses among 28 calls at cap 512 versus none among 24 calls at cap 192, but four of the 512 calls were extra opportunities after a valid terminal response. This is descriptive evidence only, not a clean paired cap-effect estimate. It does not explain the earlier malformed-JSON responses, and the no-tool and submit failures mean it does not clear a benchmark task run. The GPU differed from the first diagnostic (L40S here, RTX Pro 6000 previously); this is not a speed comparison across hardware.

The aggregate artifact is [`aider_tool_schema_history_cap_sensitivity_2026-11-24.json`](artifacts/aider_tool_schema_history_cap_sensitivity_2026-11-24.json). It records runner commit, seeds, hashes, per-arm outcomes, and GPU metrics; it contains no prompts, completions, or argument values.

## Turn-separated cap follow-up (2026-11-24)

Slurm job `4889039` ran on Rohan's L40S and completed `COMPLETED 0:0` in 2 minutes 50 seconds. It ran the committed source at `cf5eec5d4d92c7c13691153627454136b7dad8a6`, using `gpt-oss-20b-MXFP4.gguf` and the same pinned server image hash as the prior diagnostic. It sent 48 first-turn model requests (24 paired prompts × two caps), seven conditional second-turn requests, and recorded one context-headroom stop before a second request. No task, task text, oracle, reference solution, or command executor was used. The artifact contains no prompts, completions, or tool arguments. GPU monitoring sampled 178 times, with peak use of 11,781 MiB and minimum free memory of 34,287 MiB. The Slurm CPU and memory cgroup limit files were empty, so hard enforcement of those limits remains unverified.

| History target | Cap | First-turn calls | First-turn valid terminal calls | First-turn no-tool responses | Invalid JSON | Conditional second calls |
|---:|---:|---:|---:|---:|---:|---:|
| 1,024 | 192 | 8 | 0 | 8 | 0 | 0 |
| 1,024 | 512 | 8 | 3 | 4 | 1 | 3 |
| 4,096 | 192 | 8 | 1 | 7 | 0 | 1 |
| 4,096 | 512 | 8 | 3 | 5 | 0 | 3 |
| 6,400 | 192 | 8 | 0 | 8 | 0 | 0 |
| 6,400 | 512 | 8 | 1 | 7 | 0 | 0 |

Across the 24 matched first-turn prompts, cap 192 produced one schema-valid `terminal` call and cap 512 produced seven. The paired cross-tab had six prompts valid only at 512, none valid only at 192, one valid in both arms, and 17 valid in neither. One 512-cap first turn returned invalid JSON. This is a small, synthetic, descriptive signal that the larger output cap may help the first-turn tool contract for these prompts; it is not an estimate of benchmark success or a general model capability. No first turn produced a valid `submit` call. Conditional second-turn requests are reported separately: one at cap 192 and six at cap 512; all seven returned schema-valid `terminal` calls. The long-history 512 arm stopped before a second request once because of the context headroom guard. These conditional results do not change the paired first-turn denominator.

The run still does not justify an Aider/Harbor episode: 17/24 paired prompts had no valid first-turn call under either cap, no `submit` call was observed, and the test never executes a tool. It does not authorize TB2/TB-Pro work. Full per-turn counters and hashes are in [`aider_tool_schema_history_turn_separated_2026-11-24.json`](artifacts/aider_tool_schema_history_turn_separated_2026-11-24.json).

## Planned cap and sequence follow-up (2026-11-24)

**Question.** Does increasing the synthetic request cap from 512 to 1,024 tokens improve completion of the two-call tool protocol: one schema-valid `terminal` call followed by one schema-valid `submit` call?

**Design.** Use the pinned `gpt-oss-20b-MXFP4.gguf`, server image, project sampler settings, system instruction, tool schemas, and 8,192-token context. Compare 512 and 1,024 output-token caps in eight matched prompt/seed pairs at history targets 1,024, 4,096, and 5,500 tokens. Use fresh seed root `20261126`. The long target is reduced from 6,400 so the larger cap still fits with the 1,024-token context margin. Balance cap order within each target; use the same generated prompt and seed sequence within each pair. Limit each arm to two model calls. The second call is conditional on a valid first-turn `terminal` call and receives only the canned inert tool result. Neither tool is executed.

**Primary measure.** Count exact `terminal`-then-`submit` sequences per cap and the paired outcome table. Also report first-turn tool validity, second-turn outcomes and denominators, preflight/context stops separately from model calls, output-token cap-hit counts, latency, and GPU headroom. Do not calculate significance tests at this sample size or infer task success. Do not store raw prompts, completions, or arguments.

**Stop and interpretation rules.** Stop on any source/model/image hash mismatch, inability to classify requests without recording content, server failure, output leakage, OOM, or less than 1 GiB free GPU memory. A context-margin stop is recorded as a preflight event, never as a model call. Even if the synthetic sequence completes, it is not permission to run a benchmark task; task execution still requires verified egress isolation. If neither cap produces the full sequence, keep the agent pilot paused and investigate prompt/protocol handling offline.
