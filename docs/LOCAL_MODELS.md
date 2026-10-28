# Running with a local model

How to point the agent loop at a model served on your own machine (or any machine you control), and how cost is counted for it. Which small models to try, and their published scores, are in [SMALL_MODELS.md](SMALL_MODELS.md).

**Status (2026-10-29).** The client passed one direct request and one task through the toy runner against llama.cpp on the A2I2 L40S. It reported provider token counts and the runner wrote a completed result record. This does not test Harbor or a real benchmark task; the offline unit tests remain the only automated tests of client error handling. See the portable [report, scripts and raw result](cluster/l40s-client-smoke/). The development machine has no GPU.

## The client

`llm.OpenAICompatibleModel` sends each conversation to `{base_url}/chat/completions`, the OpenAI chat-completions API, as one non-streaming request. It uses only the Python standard library.

It needs:

- **`base_url`**: the API root including `/v1`;
- **`model`**: the id the server knows the model by;
- **`api_key`** (optional): sent as `Authorization: Bearer <key>`.

Optional settings are `name` (the name used in result records and to look up the price table; defaults to `model`), `timeout_s` (default 120), `temperature` (default 0; `None` leaves it out), `max_tokens` (default: not sent) and `headers` (extra HTTP headers).

Each reply carries the token counts the server reports in `usage.prompt_tokens` and `usage.completion_tokens`, and the wall-clock seconds of the call. If the server's reply has no `usage`, the call raises `MissingUsageError`. Tokens are never estimated for a real model. `model.usage` keeps the running total of calls, tokens and seconds.

| Server | `base_url` in its own docs | Source |
|---|---|---|
| Ollama | `http://localhost:11434/v1` | [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility) |
| llama.cpp (`llama-server`) | `http://127.0.0.1:<port>/v1`; the README gives 9931 as the default port (checked 2026-10-20; its Docker examples set `--port 8080` explicitly) | [llama.cpp server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) |
| vLLM (`vllm serve`) | `http://localhost:8000/v1` in its client example | [vLLM OpenAI-compatible server](https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/) |
| LM Studio | `http://localhost:1234/v1` | [LM Studio OpenAI compatibility](https://lmstudio.ai/docs/app/api/endpoints/openai) |

The same client works for hosted APIs that implement this endpoint, such as OpenAI or Together, with their base URL and an API key.

The llama.cpp README documents a `usage` object in its replies. The Ollama page above does not say whether non-streaming replies include `usage`. Before a run, check that your server sends it:

```
curl -s http://localhost:11434/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model": "qwen3.6:35b-a3b-q4_K_M", "messages": [{"role": "user", "content": "Say hi"}]}'
```

The reply should contain `"usage": {"prompt_tokens": ..., "completion_tokens": ...}`.

## Configuration from the environment

`OpenAICompatibleModel.from_env()` reads:

| Variable | Required | Meaning |
|---|---|---|
| `LLM_BASE_URL` | yes | the server's API root, including `/v1` |
| `LLM_MODEL` | yes | the model id on that server |
| `LLM_API_KEY` | no | bearer token |
| `LLM_NAME` | no | name for records and the price table; defaults to `LLM_MODEL` |
| `LLM_TIMEOUT_S` | no | seconds per request; default 120 |
| `LLM_MAX_TOKENS` | no | cap on output tokens per reply |

Another prefix can be passed, for example `from_env("DIAGNOSER_")` for a second model.

## Example

There is no command-line runner yet, so the example calls `evaluation.runner.evaluate` from a short script. It runs B0 with the starting strategy S0 on the toy environment's A split, which only checks that the model server, the client and the runner work together. The toy environment says nothing about agent performance.

The example has been exercised against a real Qwen llama.cpp server on the A2I2 L40S using one toy task. The reproducible job, settings and output are recorded in [the cluster smoke report](cluster/l40s-client-smoke/REPORT.md). The example still uses a toy environment, so it says nothing about benchmark performance.

```
# 1. Start a model server, for example with Ollama:
#      ollama pull qwen3.6:35b-a3b-q4_K_M
#    (any model id the server knows will do)
# 2. Run the toy split against it:
LLM_BASE_URL=http://localhost:11434/v1 LLM_MODEL=qwen3.6:35b-a3b-q4_K_M LLM_TIMEOUT_S=600 \
uv run python - <<'EOF'
from pathlib import Path

from baselines import FixedStrategy
from environments import ToyTextEnvironment, make_toy_tasks
from evaluation.runner import evaluate, summarise
from evaluation.splits import TaskInfo, make_split
from llm import OpenAICompatibleModel
from strategy_schema import s0

model = OpenAICompatibleModel.from_env()
tasks = make_toy_tasks(12, seed=0)
infos = [TaskInfo(task_id=t.task_id, category=t.category, difficulty=t.difficulty) for t in tasks]
split = make_split(infos, {"A": 4, "V": 4, "H": 4}, seed=0, benchmark="toy-text")
_, records = evaluate(
    run_id="local-smoke",
    baseline=FixedStrategy(),
    strategy=s0(),
    model=model,
    env=ToyTextEnvironment(),
    tasks={t.task_id: t for t in tasks},
    split=split,
    split_name="A",
    out_path=Path("runs/local-smoke.jsonl"),
)
print(summarise(records))
print(model.usage)
EOF
```

Each line of `runs/local-smoke.jsonl` holds the task's calls, tokens, `model_s` (seconds inside model calls) and `wall_s` (the whole episode). `dollars` is empty because no price entry is given; see below.

**If the runner is in a Docker container** and the model server is on the host, `localhost` inside the container is the container itself. Run the container with `--add-host=host.docker.internal:host-gateway` and use `http://host.docker.internal:11434/v1` ([Docker `--add-host`](https://docs.docker.com/reference/cli/docker/container/run/#add-host)), and make sure the server listens on an address the container can reach. `make test` runs with `--network none` and never reaches a model server.

## The benchmark containers are separate from the model server

Harbor runs the benchmark's task containers (TECHNICAL_PLAN.md, section 2). It does not serve the model. The model server is a separate process, on this machine, a GPU machine or a hosted API, and the agent loop reaches it only through `base_url`. Whatever process runs the agent loop must be able to reach that URL: a `localhost` server on a laptop is not reachable from a cloud sandbox. Harbor is not set up in this repository yet.

## Cost of a local model

A price entry in `evaluation/price_table.json` may have, besides its token prices:

- `compute_usd_per_hour`: the cost of an hour of the hardware serving the model (GPU rental, or hardware and electricity);
- `hardware`: what that rate is for, since local timings depend on it (TECHNICAL_PLAN.md, section 4.3);
- `placeholder`: `true` while the rates are not filled in.

Dollars are computed by `baselines.cost.PriceTable.dollars` as:

```
input_tokens * input_usd_per_m / 1e6 + output_tokens * output_usd_per_m / 1e6 + model_s / 3600 * compute_usd_per_hour
```

A local model has zero token prices, so its dollars are its model-call hours times the compute rate. `model_s` is the time spent inside model calls, not the episode's `wall_s`, which also covers time in the environment. If a GPU is rented for a whole run, the rental for idle time is not in these per-task figures. Entries without `compute_usd_per_hour` are priced on tokens only. The price table has two such API entries: `gpt-5-mini` (0.25 and 2.00 dollars per million input and output tokens, from OpenAI's pricing page) and `gpt-oss-120b` (0.15 and 0.60 dollars per million, from Together's model page), both seen on 2026-10-02.

The local entries in the price table (`qwen3.6:35b-a3b-q4_K_M`, `hf.co/mradermacher/Nemotron-Terminal-32B-GGUF:Q4_K_M`, `qwen3.5:35b-a3b-q4_K_M`) are placeholders: zero token price, no compute rate, `placeholder: true`. They are the three candidates of [SMALL_MODELS.md](SMALL_MODELS.md), section 4.2. They are to be replaced with the models and rates chosen there. Until then, pricing with them raises `PriceNotSetError`, and so does `RunBudget(prices=...)`, so no run records a dollar figure of zero by mistake. The entry is looked up by the client's `name`, so set `LLM_NAME` if the server's model id differs from the price-table name.

The names are the ones Ollama uses:

- The two Qwen names are Ollama library tags (`ollama pull qwen3.6:35b-a3b-q4_K_M`).
- Nemotron-Terminal-32B is not in the Ollama library (checked 2026-10-20). Ollama pulls the community GGUF from Hugging Face by that name, for example `ollama run hf.co/mradermacher/Nemotron-Terminal-32B-GGUF:Q4_K_M` ([Hugging Face, Use Ollama with any GGUF Model](https://huggingface.co/docs/hub/en/ollama)). With llama.cpp, download `Nemotron-Terminal-32B.Q4_K_M.gguf` from that repository and set `LLM_NAME=hf.co/mradermacher/Nemotron-Terminal-32B-GGUF:Q4_K_M`.
