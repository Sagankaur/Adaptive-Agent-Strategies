# Synthetic tool-schema and message-history diagnostic — 2026-11-20

## Status

The task-free diagnostic script and Slurm wrapper are prepared; no diagnostic inference or benchmark task has run under this record yet. This is an engineering diagnostic, not a benchmark result or a full Harbor agent replay.

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

## Prior evidence

- [Aider Polyglot pilot](aider-six-task-pilot-2026-11-19.md): 4 eligible IDs attempted, 5 Harbor trials, no valid verifier reward.
- [Synthetic context diagnostic](gpt-oss-tool-context-diagnostic-2026-11-19.md): 50/50 requests passed its `record_sample` schema; this did not exercise the real agent schema/history protocol.

## Files

- Runner: [`03_tool_schema_history_diagnostic.py`](../cluster/aider-pilot/03_tool_schema_history_diagnostic.py)
- Slurm wrapper: [`03_tool_schema_history_diagnostic.sbatch`](../cluster/aider-pilot/03_tool_schema_history_diagnostic.sbatch)
- Results: not run yet.
