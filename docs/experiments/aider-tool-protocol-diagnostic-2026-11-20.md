# Synthetic tool-schema and message-history diagnostic — 2026-11-20

## Status

The task-free diagnostic ran once on Rohan RTX Pro 6000 (Slurm job `4870222`, `COMPLETED 0:0`). This is an engineering diagnostic, not a benchmark result or a full Harbor agent replay.

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

This diagnostic can establish only whether the model/client interface handles the tested synthetic protocol. It cannot establish coding ability, Aider benchmark performance, Harbor task success, egress isolation, or the root cause of every earlier failure. If failures reproduce, inspect only sanitized error categories and minimal source-level protocol evidence; do not rerun the four frozen Aider tasks. If all conditions pass, freeze a fresh, unattempted Aider task sample and preregister a one-task lifecycle check before any new benchmark episode.

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
