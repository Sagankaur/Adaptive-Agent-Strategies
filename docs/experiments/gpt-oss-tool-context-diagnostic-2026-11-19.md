# gpt-oss tool-call/context diagnostic — protocol

**Status:** preregistered engineering diagnostic; implementation review pending; no requests have been sent yet.

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
