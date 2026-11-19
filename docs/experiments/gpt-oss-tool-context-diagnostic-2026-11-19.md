# gpt-oss tool-call/context diagnostic — protocol

**Status:** completed as a synthetic serving diagnostic; no benchmark task or agent episode was run.

## Question and claim boundary

Does the pinned gpt-oss-20b model produce parseable, schema-valid native tool calls in a multi-turn synthetic conversation at the 8K server context used in the Aider pilot, and does behavior change at 32K? This measures model/server interface behavior only. It is not an agent task, benchmark score, or evidence of coding ability.

The Aider pilot used an 8,192-token llama.cpp context with S0's full-history mode. Three trials ended with invalid JSON tool arguments and Hangman returned a context-related HTTP 400. A context limit is a plausible cause, not an established one. This diagnostic isolates that possibility without task files or command execution.

## Frozen design

- **Model and server:** the already pinned local gpt-oss-20b MXFP4 GGUF and llama.cpp CUDA 12 SIF on Rohan's RTX Pro 6000; one slot, eight CPU threads, same chat template and sampling settings as the Aider run.
- **Contexts:** 8,192 and 32,768 tokens, one server at a time. The 8K server runs first. Proceed to the 32K server only if startup succeeds and at least 1 GiB of GPU memory remains free.
- **Sampling:** temperature 0.6, top-p 0.95, top-k 20, non-streaming, 256-token output limit, 180-second request timeout. Ten paired repetition seeds are identical across the two context sizes.
- **Tool schema:** one harmless `record_sample` function with a small enum and bounded integer schema. It has no executor. The client validates returned JSON in memory and discards every argument value.
- **Conversation:** each repetition requests a tool call at two full-history prompt sizes shared by both contexts (targets 4,096 and 6,656 input tokens). A third request targets 24,576 tokens at 32K only. Prior turns are fixed synthetic assistant/tool exchanges; live tool-call responses are added to that repetition's history. The 32K long-history condition is an extension check and is not paired against 8K.
- **Preflight:** count each exact rendered chat request with llama.cpp's token-count endpoint before generation. Require at least 768 tokens of margin after the 256-token output cap. If exact token counting is unavailable, abort before any generation. The official server docs describe the [chat-completion token-count endpoint](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md#openai-compatible-api-endpoints) and [tokenization endpoint](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md#post-tokenize-tokenize-a-given-text).
- **Privacy:** server logs are disabled; the client writes no prompt, completion, tool name, or argument value. It retains aggregate counters only. The executable contains no tool runner; executor invocation count must remain zero.
- **Resources:** one RTX Pro 6000, 8 CPUs requested, 64 GiB RAM requested, short QoS, one-hour maximum. Record GPU peak and visible Slurm cgroup values; do not claim hard CPU/memory enforcement if the cgroup values remain unavailable.

## Outcomes

For each context and prompt-size cell, report planned and attempted calls, HTTP 200 responses, exactly-one-tool-call rate, parseable JSON rate among single-tool responses (independent of tool-name/schema validity), schema-valid rate, request-match rate, no-call/multiple-call counts, HTTP status counts, context-error candidates, mean prompt/completion tokens, mean latency and token rates, model-load time, and peak VRAM. Rates use HTTP 200 responses as their denominator except JSON parse rate, which uses exactly-one-tool HTTP 200 responses; rates are null when their denominator is zero. Planned and attempted counts remain explicit, including cells with no attempts. Report the 32K long-history extension separately. Use counts and proportions only; n=10 is descriptive and does not justify significance tests or broad quality claims.

## Stop rules

- Do not send inference requests if model or SIF hashes differ from the pinned values, server logs cannot be suppressed, exact prompt token counting fails, or the endpoint binds beyond localhost.
- Do not send a prompt unless the measured prompt plus 256 output tokens leaves at least 768 tokens of context margin.
- Stop immediately on less than 1 GiB of VRAM headroom, OOM, server instability, or any executor invocation. The client polls headroom during inference and terminates the server if the threshold is crossed; the in-flight response is discarded. On an HTTP 400, stop that context condition. Continue from 8K to 32K only when the response is classified in memory as a context-error candidate, `/health` remains healthy, and at least 1 GiB GPU headroom remains. Any transport error, non-400 HTTP error, unhealthy server, or other 400 stops the whole job. HTTP error text is inspected only in memory (bounded to 2 KiB) to set a boolean context-error-candidate field; the text itself is never saved. No retries beyond the preregistered repetitions; report incomplete cells as incomplete.
- Do not launch another benchmark task based on this result. First review the model/agent interface and the unconfirmed Slurm process limits.

## Result record

After the run, update this document with the Slurm job ID, commit and artifact hashes, aggregate counts, observed resource limits, deviations, and limitations. Store only sanitized aggregate JSON under `docs/experiments/artifacts/`; raw server logs remain on scratch and are not copied into the repository.

### Execution record (2026-11-19)

- Slurm job `4869012` was submitted to Rohan's `gpu` partition under the `short` QoS. `sbatch --test-only` accepted the request and selected an RTX Pro 6000 node.
- The pinned model and server SIF SHA-256 values were verified on Rohan and match the values above. The runner, batch script, and preregistration file were staged with hashes matching the committed files.
- GitHub Actions passed on Python 3.11 and 3.12 for the PR branch before submission.
- At 22:39 AEDT the job was initially `PENDING (Priority)`, then started at 22:47 and completed at 22:48. `sacct` reports `COMPLETED`, exit code `0:0`, elapsed `00:01:06`.

### Results

All 50 planned synthetic requests returned HTTP 200, exactly one tool call, parseable JSON arguments, schema-valid arguments, and the requested values. No context-error candidate occurred. This indicates that the pinned model/server combination handled these synthetic prompts at the tested lengths; it does not establish task-solving ability or explain every failure in the earlier Aider pilot.

| Context | History target | Calls matching schema/request | Mean request latency | Mean generation speed |
|---:|---:|---:|---:|---:|
| 8,192 | 4,096 | 10/10 | 0.33 s | 282.07 tok/s |
| 8,192 | 6,656 | 10/10 | 0.36 s | 273.14 tok/s |
| 32,768 | 4,096 | 10/10 | 0.58 s | 282.68 tok/s |
| 32,768 | 6,656 | 10/10 | 0.35 s | 275.90 tok/s |
| 32,768 | 24,576 | 10/10 | 1.27 s | 255.29 tok/s |

The 8K server reached healthy status in 9.02 s; the 32K server in 8.01 s. GPU memory peaked at 11,953 MiB and 12,553 MiB respectively, leaving at least 85,334 MiB free on the 97,887 MiB device. The 1 GiB headroom stop was never approached. Slurm allocated 8 CPUs and requested 64 GiB RAM, but `cpu.max` and `memory.max` were unavailable and the visible CPU set was `0-95`; hard CPU and memory enforcement is therefore unverified.

Prompt-throughput figures are not interpreted: some reported values were implausibly high, consistent with prompt-cache reuse in this repeated-prefix synthetic design. A separate cache-controlled serving test is needed before using prefill speed for cost estimates. The measured generation rates and latencies are descriptive for this run only.

The sanitized artifact is [`artifacts/gpt-oss-tool-context-diagnostic-2026-11-19.json`](artifacts/gpt-oss-tool-context-diagnostic-2026-11-19.json). It retains aggregate and per-call counters/timings only; no prompts, completions, tool names, or argument values. Its SHA-256 is `80a203092ffa07fe066b1f03804d46fb1ea98b499f11f9ebaccf585ef3fceb1d`. The result records protocol hash `fa311de4816faa966f87aa9633662ba9aea9e5c4a8ddcf206571280d911f23f2` and experiment commit `f9ba4e9`.
