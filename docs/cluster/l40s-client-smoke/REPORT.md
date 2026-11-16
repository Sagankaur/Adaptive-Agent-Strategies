# L40S project client and toy-runner smoke

## Result

Slurm job `4316173` completed on `l40s-f-01` in 19 seconds with exit code `0:0`. The current project client made a direct request to llama.cpp, parsed non-empty text and provider-reported token counts, then the project evaluation runner completed one `reverse_words` toy task and wrote one JSONL record.

| Check | Result |
|---|---|
| Direct client request | `PASS`; 29 prompt tokens, 100 completion tokens; 0.875 s |
| Toy episode | `toy-000` (`reverse_words`); success; stop reason `submitted`; 2 model calls |
| Toy episode usage | 765 prompt tokens, 323 completion tokens; 3.496 model seconds in aggregate client usage |
| Total client usage, including direct request | 3 calls; 794 prompt tokens; 423 completion tokens |
| Model | `unsloth/Qwen3.6-35B-A3B-GGUF`, revision `a483e9e6cbd595906af30beda3187c2663a1118c`; Q4_K_M; 22,134,528,992 bytes; SHA-256 `ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61` |
| Server | llama.cpp build `b11515`, image `ghcr.io/ggml-org/llama.cpp:server-cuda12-b11515`, run through Apptainer |
| GPU | NVIDIA L40S, 46,068 MiB; driver 565.57.01 |
| Project source | Git commit `fde71fcf44922a0d26d41f76fdc664c8eb9f75cc` |
| Runtime | Python 3.11.7; Pydantic 2.13.5 in `/scratch/$USER/venvs/aas-client-smoke` |

This is an integration smoke, not a Harbor or Terminal-Bench result. It exercises the project's text-action contract (`ACTION:` / `SUBMIT:`); it does not validate native OpenAI `tool_calls`, reasoning parsing, Harbor rewards, task containers, or benchmark performance.

## Slurm and server settings

The job requested partition `gpu`, QoS `short`, one `l40s` GPU, 4 CPUs, 24 GiB host memory, and 20 minutes. The server bound to `127.0.0.1` on a job-specific port, with one slot, 16,384 context tokens, `-ngl 999`, and `--jinja`. The model file was mounted read-only. The smoke driver used temperature `0.0`, maximum generation 512 tokens, and a 180-second request timeout. The toy split used seed `20261028`.

## Artifacts

- [`client_smoke_summary.json`](client_smoke_summary.json)
- [`toy_run.jsonl`](toy_run.jsonl)
- [`project_client_toy_smoke.py`](project_client_toy_smoke.py)
- [`03_project_toy_smoke.sh`](03_project_toy_smoke.sh)
- Reproduction steps: [`README.md`](README.md)

## Reproduction

See the adjacent README for staging the code at the pinned commit and submitting the same Slurm job. The model and Apptainer image are large and remain on cluster scratch; their hashes and source pins are recorded above.
