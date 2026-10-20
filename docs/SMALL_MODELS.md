# Small models for Terminal-Bench 2.0

Checked on 2026-10-15 with web search and fetch, as input to the model choice in [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 2. The supervisor wants a model that anyone can run on a local machine, so that the experiments can be reproduced without an API budget. The target is a model that solves roughly 20–40% of Terminal-Bench 2.0 tasks at the start, so there is room to improve.

**How to read this document.**

- Every number has a URL that was opened on 2026-10-15. Section 5 lists all of them.
- Some pages were read through a fetch tool that returns a summary rather than the raw page. Those items are marked "(summary)". The leaderboard, the paper, the Hugging Face cards and the Ollama pages were downloaded and read directly.
- "Not found" means a search was made and nothing was found. It does not mean no result exists.
- "Derived" means I calculated the number from sourced inputs. The inputs are shown.
- Nothing here has been run by us. All scores are other people's results.

---

## 0. Summary

- **The official Terminal-Bench 2.0 leaderboard is no longer online.** Since about 1 September 2026, https://www.tbench.ai/leaderboard/terminal-bench/2.0 redirects to the Terminal-Bench 4.0 board. The last archived copy (Wayback Machine, 26 August 2026) still has all 140 entries, and the tables below use that copy.
- **I found only two independent TB2 results for models that fit on a consumer machine:**
  - Qwen3.6-35B-A3B: 24.6%.
  - Qwen3.5-9B: 9.2%.

  Both were run by one person (little-coder) on a laptop with 8 GB of VRAM and 32 GB of RAM, with the model served by llama.cpp at Q4_K_M and the task containers in local Docker.
- **Base models at 32B or below are at the floor** with the neutral Terminus 2 agent:
  - gpt-oss-20b: 3.1%.
  - Qwen3-8B: 2.5%.
  - Qwen3-14B: 4.0%.
  - Qwen3-32B: 3.4%.
- **Fine-tuned terminal models do much better.** NVIDIA's Nemotron-Terminal models, fine-tuned from Qwen3, reach 13.0% (8B), 20.2% (14B) and 27.4% (32B) on Terminus 2, as reported by NVIDIA.
- **Vendor-reported numbers for new Qwen models are much higher, but are not comparable.** Qwen reports 51.5% for Qwen3.6-35B-A3B. It used a 3-hour timeout and 32 CPUs / 48 GB RAM per task, while the independent laptop run of the same model scored 24.6%.
- **Small API models that sit in the 20–40% band:**
  - GPT-5-mini: 22–32%, depending on the agent.
  - Claude Haiku 4.5: 27.5–29.8% on the leaderboard.

  GPT-5-nano (7–11.5%) and Gemini 2.5 Flash (15–17%) are below the band.

---

## 1. Terminal-Bench 2.0 results for small models

### 1.1 Sources and what they measure

| Source | What it is | Notes |
|---|---|---|
| **TB2 paper**: Merrill et al., arXiv 2601.11868, Table 2 | Run by the benchmark authors | "we run the benchmark at least five times" for each model and agent pair. Open-weight models were "queried through the Together.AI API". Containers ran on Daytona. Results are given with 95% confidence intervals. |
| **TB2 leaderboard**: Wayback copy of tbench.ai, 2026-08-26 | Mixed | "Verified" entries are the paper's runs. Other entries were submitted by third parties. The page shows accuracy ± standard error, but not the number of trials or the cost. |
| **Leaderboard submissions**: Hugging Face dataset `harborframework/terminal-bench-2-leaderboard` | Raw job files behind the leaderboard entries | Used to read the trial count, the run settings and the wall-clock time for the little-coder runs. |
| **Model cards and papers** | Vendor-reported | Settings vary, so they are noted per row. |

For most of the small-model rows used here, the leaderboard accuracy is the same as the paper's Table 2 figure. The OpenHands rows differ by 0.4–1.5 points, and both values are shown in section 1.3. Some rows for larger models also differ; for example, Grok 4 with Mini-SWE-Agent is 25.4% on the leaderboard and 29.0% in the paper. The ± values differ because the leaderboard shows the standard error and the paper shows the 95% confidence interval.

**Benchmark version.** Terminal-Bench 2.1 fixes 28 of the 89 tasks: "We're releasing Terminal-Bench 2.1 to fix issues in 28 of the 89 tasks in Terminal-Bench 2.0" (tbench.ai/news/terminal-bench-2-1, summary). The archived 2.1 leaderboard (2026-08-26) has 17 entries, all frontier models. It has **no small models**. The current site shows Terminal-Bench 4.0, which has 66 tasks and an 8-hour timeout.

### 1.2 Open-weight models (about 35B total parameters or fewer), Terminal-Bench 2.0

"LB" is the archived leaderboard (2026-08-26). "Paper" is arXiv 2601.11868, Table 2. On the leaderboard, ± is the standard error; in the paper it is the 95% CI. "Date" is the date field on the leaderboard entry, or the date of the report.

| Model | Size (total / active) | Agent harness | TB2 accuracy | Trials | Cost reported | Date | Who ran it | Source |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-20b | 21B / 3.6B | Terminus 2 | **3.1%** (LB ±0.8; paper ±1.5 CI) | ≥5 per task (paper) | No. Paper gives tokens: 75.5M in, 1.2M out | 2025-11-01 | TB authors, via Together AI | LB; paper |
| gpt-oss-20b | 21B / 3.6B | Mini-SWE-Agent | **3.4%** (±0.7) | ≥5 | No. Tokens: 11.5M in, 0.8M out | 2025-11-03 | TB authors | LB; paper |
| gpt-oss-20b, "high" reasoning | 20B | Terminus 2 | 3.10% ± 1.5 | not stated | No | 2026-02-24 (arXiv) | NVIDIA, reproducing the TB number | Nemotron-Terminal paper, Table 3 |
| AfterQuery-GPT-OSS-20B (`gpt-oss-20b-rl`, an RL fine-tune) | 20B (inferred from the name) | Terminus 2 | **17.0%** (±1.3) | not stated | No | 2026-03-31 | AfterQuery (unverified submission) | LB. Public weights not found on Hugging Face. |
| Qwen3.6-35B-A3B, Q4_K_M via llama.cpp | 35B / 3B | little-coder v0.1.14 | **24.6%** (±1.6) | 445 (89 × 5); `n_attempts: 5` in the job config | No API cost. Wall-clock in section 3 | 2026-05-14 (LB); run 2026-04-24 to 04-26 | Itay Inbar, on a consumer laptop (unverified submission) | LB; HF job files; github.com/itayinbarr/little-coder |
| Qwen3.6-35B-A3B | 35B / 3B | little-coder v0.1.13 | 23.0% (no ± given) | not stated | No | 2026-05-14 | same | LB |
| Qwen3.5-9B, Q4_K_M via llama.cpp | 9B | little-coder v0.1.24 | **9.2%** (±1.2) | 445 (89 × 5) | No API cost | 2026-05-14 (LB); run 2026-04-26 to 04-27 | same | LB; HF job files; little-coder README |
| Qwen3-8B | 8B | Terminus 2 | 2.47% ± 0.5 | not stated | No | 2026-02-24 | NVIDIA | Nemotron-Terminal paper, Table 3; HF card |
| Qwen3-8B | 8B | Terminus-2 | 0.0% | not stated | No | not stated (card) | OpenThoughts | OpenThinker-Agent-v1 card |
| Qwen3-14B | 14B | Terminus 2 | 4.04% ± 1.3 | not stated | No | 2026-02-24 | NVIDIA | Nemotron-Terminal paper |
| Qwen3-32B | 32B | Terminus 2 | 3.37% ± 1.6 | not stated | No | 2026-02-24 | NVIDIA | Nemotron-Terminal paper |
| Qwen3-32B | 32B | Terminus-2 | 1.9% | not stated | No | not stated | OpenThoughts | OpenThinker-Agent-v1 card |
| Qwen3-Coder-30B-A3B-Instruct | 30B / 3B | OpenHands | 10.1% | not stated | No | not stated | OpenThoughts | OpenThinker-Agent-v1 card |
| Nemotron-Terminal-8B (Qwen3-8B fine-tune) | 8B | Terminus 2 | **13.0%** ± 2.2 | not stated | No | 2026-02-24 | NVIDIA (vendor) | arXiv 2602.21193; HF card |
| Nemotron-Terminal-14B | 14B | Terminus 2 | **20.2%** ± 2.7 | not stated | No | 2026-02-24 | NVIDIA (vendor) | same |
| Nemotron-Terminal-32B | 32B | Terminus 2 | **27.4%** ± 2.4 | not stated | No | 2026-02-24 | NVIDIA (vendor) | same |
| OpenThinker-Agent-v1 (Qwen3-8B fine-tune) | 8B | Terminus-2 | 4.9% | not stated | No | not stated | OpenThoughts (vendor) | HF card |
| TermiGen-32B (Qwen2.5-Coder-32B fine-tune) | 32B | "Bash Agent" | 19.3% (±1.0) | not stated | No | 2026-05-14 | UCSB-SURFI (unverified submission) | LB; HF card |
| Qwen3.5-35B-A3B | 35B / 3B | not stated on the card | 40.5% | not stated | No | Feb 2026 card | Qwen (vendor) | HF card |
| Qwen3.5-27B | 27B dense | not stated on the Qwen3.5 card | 41.6% | not stated | No | Feb 2026 card | Qwen (vendor) | HF card |
| Qwen3.6-35B-A3B | 35B / 3B | Harbor / Terminus-2, **3h timeout, 32 CPU / 48 GB RAM**, 256K context | 51.5% | "avg of 5 runs" | No | Apr 2026 card | Qwen (vendor) | HF card |
| Qwen3.6-27B | 27B dense | same settings as above | 59.3% | "avg of 5 runs" | No | Apr 2026 card | Qwen (vendor) | HF card |
| Gemma 4 31B | 30.7B dense | same Qwen settings | 42.9% | as above | No | Apr 2026 | Qwen, not Google | Qwen3.6-35B-A3B card |
| Gemma 4 26B-A4B | 25.2B / 3.8B | same Qwen settings | 34.2% | as above | No | Apr 2026 | Qwen, not Google | same |

**Notes on the rows.**

- **Little-coder runs.**
  - The leaderboard gives 24.6% for the Qwen3.6-35B-A3B run. The `result.json` in that job directory gives a mean of 23.8%, with "n_errors": 15. I did not resolve the difference.
  - The little-coder README attributes the 24.6% run to v0.1.13 and gives "24.6 % ± 3.2". The leaderboard attributes 24.6% to v0.1.14 and 23.0% to v0.1.13.
- **The Qwen vendor numbers are not comparable to the leaderboard.**
  - The Qwen3.6 card footnote reads: "Terminal-Bench 2.0: Harbor/Terminus-2 harness; 3h timeout, 32 CPU/48 GB RAM; temp=1.0, top_p=0.95, top_k=20, max_tokens=80K, 256K ctx; avg of 5 runs."
  - The leaderboard does not allow changed timeouts: "entrants must solve the same tasks under the time constraints we specify" (tbench.ai/news/leaderboard-integrity-and-timeouts, summary).
  - The same model scored 51.5% on Qwen's setup and 24.6% on a laptop setup. That gap is the clearest sign that the evaluation setup matters as much as the model.
- **Qwen3.5 card columns for other models.** The same table lists GPT-5-mini at 31.9 and GPT-OSS-120B at 18.7. These are the same as the leaderboard figures for GPT-5-mini with Codex CLI and gpt-oss-120b with Terminus 2.

**Searched, with no published TB2 result found:**

| Model | Where I looked |
|---|---|
| Qwen3-4B | No TB2 figure found in any source opened. Not searched separately. |
| Qwen3-30B-A3B (base, Instruct or Thinking-2507) | Nemotron 3 Nano card (it gives only a "Terminal Bench (hard subset)" figure, which is a different benchmark) |
| Qwen3.5-9B (vendor) | HF card has no TB2 row. The only result is little-coder's 9.2%. |
| gpt-oss-20b (vendor) | HF card has no Terminal-Bench row |
| Gemma 3 (any size) | Not found |
| Gemma 4 (vendor) | gemma-4-31B-it and gemma-4-26B-A4B-it cards have no Terminal-Bench row |
| Llama 3.x / 4 small models | Not found. Llama 4 Maverick is in the paper's model list but is far above 35B. |
| DeepSeek small variants (R1 distills, V2-Lite) | Not found. DeepSeek-V3.2 (685B) has a result: 39.6% on LB and 38.2% in the Nemotron paper. |
| Devstral Small 1.x / 2 | Mistral's Devstral 2 launch post has no TB score. Aggregator snippets claim 29.6–32%, but I could not open them, so not confirmed. |
| GLM-4.7-Flash (30B-A3B, MIT licence) | HF card has no TB row. It only says to "turn on Preserved Thinking mode" for "Terminal Bench 2". |
| GLM-4.5-Air | 106B total / 12B active per the subagent's reading of the HF card (not re-checked). No TB row; above 35B in any case. |
| GLM-5.3-Flash | Only a **Terminal-Bench 4.0** result was found (section 1.4). Parameter count and open weights not confirmed. |
| Nemotron 3 Nano 30B-A3B | Card gives only "Terminal Bench (hard subset)": 8.5. Not TB2. |

### 1.3 Small proprietary models, Terminal-Bench 2.0

All rows are from the paper's Table 2 and the leaderboard, except where marked. Parameter counts are not published for any of these models.

| Model | Agent harness | TB2 accuracy (paper, 95% CI) | Trials | Tokens per run, from paper Table 2 | Date (LB) |
|---|---|---|---|---|---|
| GPT-5-mini | Codex CLI | 31.9% ± 3.0 | ≥5 | 3.4M in / 0.7M out | 2025-11-04 |
| GPT-5-mini | OpenHands | 27.7% ± 2.6 (LB: 29.2%) | ≥5 | 6.0M / 3.1M | 2025-11-02 |
| GPT-5-mini | Terminus 2 | 24.0% ± 2.5 | ≥5 | 5.9M / 1.9M | 2025-10-31 |
| GPT-5-mini | Mini-SWE-Agent | 22.2% ± 2.6 | ≥5 | 2.9M / 1.9M | 2025-11-03 |
| GPT-5-mini | spoox-o-m (third party, unverified) | LB 34.8% (±1.4 SE) | not stated | not stated | 2025-12-24 |
| GPT-5-nano | Codex CLI | 11.5% ± 2.3 | ≥5 | 2.1M / 0.8M | 2025-11-04 |
| GPT-5-nano | OpenHands | 9.5% ± 2.0 (LB 9.9%) | ≥5 | 16.7M / 10.7M | 2025-11-02 |
| GPT-5-nano | Terminus 2 | 7.9% ± 1.9 | ≥5 | 13.7M / 5.3M | 2025-10-31 |
| GPT-5-nano | Mini-SWE-Agent | 7.0% ± 1.9 | ≥5 | 1.3M / 2.2M | 2025-11-03 |
| GPT-5-nano | spoox-o-m (unverified) | LB 21.8% (±1.4 SE) | 445 trial directories in the HF submission | not stated | 2026-05-15 |
| Claude Haiku 4.5 | Mini-SWE-Agent | 29.8% ± 2.5 | ≥5 | 3.6M / 1.4M | 2025-11-03 |
| Claude Haiku 4.5 | Terminus 2 | 28.3% ± 2.9 | ≥5 | 3.9M / 1.3M | 2025-10-31 |
| Claude Haiku 4.5 | Claude Code | 27.5% ± 2.8 | ≥5 | 0.2M / 0.3M | 2025-11-04 |
| Claude Haiku 4.5 | OpenHands | 13.3% ± 2.6 (LB 13.9%) | ≥5 | 663.1M / 3.3M | 2025-11-02 |
| Claude Haiku 4.5 | Goose (unverified) | LB 35.5% | not stated | not stated | 2025-12-11 |
| Gemini 2.5 Flash | Mini-SWE-Agent | 17.1% ± 2.5 | ≥5 | 18.4M / 6.0M | 2025-11-03 |
| Gemini 2.5 Flash | Terminus 2 | 16.9% ± 2.4 | ≥5 | 10.5M / 3.1M | 2025-10-31 |
| Gemini 2.5 Flash | OpenHands | 15.5% ± 2.3 (LB 16.4%) | ≥5 | 14.8M / 2.8M | 2025-11-02 |
| Gemini 2.5 Flash | Gemini CLI | 15.4% ± 2.3 | ≥5 | 6.8M / 1.5M | 2025-11-04 |
| Gemini 3 Flash | Terminus 2 | 51.7% ± 3.1 | ≥5 | 52.1M / 2.6M | 2026-01-07 |
| Gemini 3 Flash | Gemini CLI (unverified) | LB 47.4% | not stated | not stated | 2026-03-06 |
| GPT-5.1-Codex-Mini | Crux (verified) | LB 43.1% | not stated | not stated | 2025-11-17 |

**Other reports.**

- **Claude Haiku 4.5, Anthropic announcement (15 Oct 2025).** It reports "Terminus 2, with XML parser, averaging 11 runs (6 without thinking (40.21% score), 5 with 32K thinking budget (41.75% score))". The post does not say which Terminal-Bench version was used, so this is **not confirmed as TB2**. It is higher than the leaderboard's 28.3% for the same harness.
- **GPT-5.4 mini, GPT-5.4 nano and GPT-5 mini: 60.0%, 46.3% and 38.2%.** These come from secondary press coverage (the-decoder.com, summary). OpenAI's own page returned HTTP 403, so the primary source was **not opened**. They are not confirmed.

**Token counts in Table 2.** The caption says: "Token counts are for running all 74 tasks in Terminal-Bench 2.0". I read this as one pass over the tasks, but the paper does not make that explicit, and the "74" does not match the 89 tasks. Treat the derived costs in section 3 with that caveat.

### 1.4 Terminal-Bench 4.0 (current leaderboard), small or "Flash"-class entries, for context only

This is not the pinned benchmark. It has 66 tasks, 5 trials each (330 trials), and an 8-hour timeout. Cost is the total for 330 trials, read from https://www.tbench.ai/leaderboard on 2026-10-15.

| Model | Agent | Accuracy | Trials | Total cost (USD) | Date |
|---|---|---|---|---|---|
| GLM-5.3-Flash | Claude Code | 35.76% | 330 | 2,883.11 | 2026-08-26 |
| Gemini 3.8 Flash | mini-SWE-agent | 19.09% | 330 | 1,828.77 | 2026-09-02 |
| Gemini 3.7 Flash | mini-SWE-agent | 11.21% | 330 | 1,261.87 | 2026-08-13 |

There are no open-weight models of 35B or fewer on the TB4 board.

---

## 2. Running the open-weight candidates locally

**Rule of thumb.** Unsloth's guides say "Available memory should match or exceed the model file size" for usable speed (the gpt-oss guide; the Qwen3 guide says the same). On top of the file, the KV cache grows with context length. Hugging Face's docs say it "can occupy a significant portion of memory". I found no single source with a formula, so treat **file size + a few GB for context** as a working estimate, not a sourced figure.

Long agent trajectories need long contexts. Qwen's own TB2 runs used a 256K context, and little-coder's example server uses 16K "for 8 GB VRAM". The context used in little-coder's TB2 runs is not stated.

### 2.1 Q4 file sizes

Ollama sizes were read from https://ollama.com/library/<model>/tags. Hugging Face sizes come from the repository file listing.

| Model | Q4 file (approx. memory floor) | Source |
|---|---|---|
| gpt-oss-20b | 14 GB (`gpt-oss:20b`, native MXFP4). OpenAI: runs "within 16GB of memory" | Ollama gpt-oss tags; HF openai/gpt-oss-20b |
| gpt-oss-120b | 65 GB. OpenAI: fits "a single 80GB GPU" | same |
| Qwen3-4B | 2.6 GB (`qwen3:4b-q4_K_M`) | Ollama qwen3 tags |
| Qwen3-8B | 5.2 GB | same |
| Qwen3-14B | 9.3 GB | same |
| Qwen3-32B | 20 GB | same |
| Qwen3-30B-A3B | 19 GB | same |
| Qwen3-Coder-30B-A3B | 19 GB | Ollama qwen3-coder tags |
| Qwen3.5-9B | 6.6 GB | Ollama qwen3.5 tags |
| Qwen3.5-27B | 17 GB | same |
| Qwen3.5-35B-A3B | 22 GB | same |
| Qwen3.6-35B-A3B | 24 GB (`qwen3.6:35b-a3b-q4_K_M`). Little-coder ran it with 8 GB VRAM + 32 GB RAM, by offloading MoE layers to the CPU (`--n-cpu-moe`) | Ollama qwen3.6 tags; little-coder README (summary) |
| Qwen3.6-27B | 17 GB | Ollama qwen3.6 tags |
| Nemotron-Terminal-8B / 14B / 32B | 5.03 / 9.0 / 19.76 GB (Q4_K_M, community GGUF by mradermacher). Not in the Ollama library (checked 2026-10-20); Ollama pulls the GGUF from Hugging Face as `hf.co/mradermacher/Nemotron-Terminal-32B-GGUF:Q4_K_M` | HF file listings; [Hugging Face, Use Ollama with any GGUF Model](https://huggingface.co/docs/hub/en/ollama) |
| Gemma 3 12B / 27B | 8.2 / 17 GB | Ollama gemma3 tags |
| Gemma 4 26B-A4B / 31B | 18 / 20 GB | Ollama gemma4 tags (subagent reading, not re-checked) |
| Devstral Small 2 (24B) | 15 GB | Ollama devstral-small-2 tags |
| GLM-4.7-Flash (30B-A3B) | 19 GB. Unsloth: "around 18GB RAM/unified memory" | Ollama glm-4.7-flash tags; Unsloth docs (summary) |
| Nemotron 3 Nano 30B-A3B | 24 GB | Ollama nemotron-3-nano tags |
| Llama 3.1 8B | 4.9 GB | Ollama llama3.1 tags (subagent reading, not re-checked) |
| DeepSeek-R1-Distill-Qwen-14B / 32B | 9.0 / 20 GB | Ollama deepseek-r1 tags (subagent reading, not re-checked) |

### 2.2 Generation speed (tokens per second) on consumer hardware

| Model | Hardware | tok/s (generation) | Source |
|---|---|---|---|
| gpt-oss-20b, MXFP4, llama.cpp `tg128` | RTX 3090 24 GB | 161.77 | llama.cpp discussion #15396 (summary) |
| gpt-oss-20b | RTX 4090 24 GB | 221.95 | same |
| gpt-oss-20b | RTX 5090 32 GB | 282.51 | same |
| gpt-oss-20b | M4 Max 36 GB | 92.36 | same |
| gpt-oss-20b | M1 Pro 32 GB | 45.68 | same |
| gpt-oss-120b, MXFP4 | M2 Ultra 192 GB | 79.68 | same |
| Qwen3.6-35B-A3B, Q4_K_M, llama.cpp with MoE CPU offload | RTX 5070 Laptop 8 GB VRAM, i9-14900HX, 32 GB RAM | "~44 tok/s" | little-coder README (summary) |
| Qwen3.8-27B, UD-Q4_K_XL, partial offload | same laptop | 6.72 tok/s (16K ctx) | same |
| Qwen3-30B-A3B, Q4_K_M | RTX 4090 / RTX 3090 | "120–196" / "~73". Community figures without links, so **unverified** | runaihome.com (summary) |
| Qwen3-4B/8B/14B/32B, Qwen3-Coder-30B-A3B, Qwen3.5 models, Nemotron-Terminal, Gemma, Devstral, GLM-4.7-Flash | any | **No measured figure found** | (none) |

There is a reference point for dense models of about 8B on Apple Silicon. Llama 2 7B at Q4_0 generates 24.11 tok/s on an M4, 50.74 on an M4 Pro (20-core GPU) and 83.06 on an M4 Max (40-core) (llama.cpp discussion #4167, summary). This is a proxy only, not a measurement of any candidate.

---

## 3. Cost per task

### 3.1 API models

Standard-tier list prices, read on 2026-10-15, in USD per million tokens.

| Model | Input | Cached input | Output | Source |
|---|---|---|---|---|
| GPT-5-mini | 0.25 | 0.025 | 2.00 | developers.openai.com/api/docs/pricing |
| GPT-5-nano | 0.05 | 0.005 | 0.40 | same |
| GPT-5.4-mini | 0.75 | 0.075 | 4.50 | same |
| GPT-5.4-nano | 0.20 | 0.02 | 1.25 | same |
| Claude Haiku 4.5 | 1.00 | 0.10 | 5.00 | platform.claude.com/docs/en/about-claude/pricing |
| Claude Haiku 5.5 (prompts ≤100K tokens) | 0.10 | 0.01 | 0.50 | same. **No TB2 result found** |
| Gemini 2.5 Flash | 0.30 | 0.03 | 2.50 | ai.google.dev/gemini-api/docs/pricing (page "Last updated 2026-10-14", summary) |
| Gemini 2.5 Flash-Lite | 0.10 | 0.01 | 0.40 | same |
| Gemini 3 Flash (preview) | 0.50 | 0.05 | 3.00 | same |
| gpt-oss-120b (Together AI) | 0.15 | n/a | 0.60 | together.ai/pricing (summary); same on OpenRouter's Together endpoint |
| gpt-oss-20b (OpenRouter, cheapest to dearest provider) | 0.018–0.075 | n/a | 0.09–0.30 | openrouter.ai API endpoints listing |
| Qwen3.6-35B-A3B (OpenRouter; DeepInfra) | 0.10 | n/a | 0.95 | same |
| Qwen3-Coder-30B-A3B (OpenRouter; SiliconFlow) | 0.07 | n/a | 0.28 | same |

**Derived cost of one pass, from paper Table 2 tokens × list price, with all input priced as uncached.** This is an upper bound on input cost, and it assumes the Table 2 counts are for one pass (see section 1.3).

| Model and agent | Tokens (in / out) | Derived cost per pass | Per task (÷ 89) |
|---|---|---|---|
| GPT-5-mini, Terminus 2 | 5.9M / 1.9M | 5.9 × 0.25 + 1.9 × 2.00 = **$5.28** | ≈ $0.06 |
| GPT-5-mini, Codex CLI | 3.4M / 0.7M | **$2.25** | ≈ $0.03 |
| GPT-5-nano, Terminus 2 | 13.7M / 5.3M | **$2.81** | ≈ $0.03 |
| Claude Haiku 4.5, Terminus 2 | 3.9M / 1.3M | **$10.40** | ≈ $0.12 |
| gpt-oss-120b, Terminus 2, Together AI | 13.4M / 0.8M | **$2.49** | ≈ $0.03 |

These sit at the cheap end of the paper's statement that a run "costs anywhere from one to a hundred dollars". They are consistent with the $0.05–$0.40 per episode assumed in TECHNICAL_PLAN.md, section 9. Agent traces in our own loop may be longer.

### 3.2 Local models: what to report

A local model has no per-token price, so cost is compute time. For every run, report:

1. **Wall-clock seconds per trial**: agent start to verifier end, as Harbor records it. Also report the mean and median per task.
2. **Tokens**: prompt tokens processed and tokens generated per trial. llama.cpp and Ollama both return these per request.
3. **Hardware and settings**: GPU or SoC, VRAM and RAM, quantisation, context length, number of concurrent trials, and the CPU/RAM given to each task container.
4. **Optional dollar equivalent**: wall-clock hours × a stated rate. Use one of the two rates below.
   - **Electricity.** Board power × hours × tariff. For example, an RTX 4090 at its 450 W total graphics power (NVIDIA spec page) for one hour at Melbourne flat-rate prices of 25.96–28.22 c/kWh is about 12–13 c. That figure is derived and covers the GPU only. The tariff is the Victorian Default Offer 2026-27 for the CitiPower, Jemena, United Energy and Powercor zones, from the Essential Services Commission (summary). The US average residential price is 18.31 c/kWh for July 2026 (EIA Electric Power Monthly table 5.6.A, summary).
   - **Cloud-GPU equivalent.** The hourly price of a comparable rented GPU. Examples:
     - RunPod RTX 4090: $0.34/h Community Cloud, $0.74/h Secure Cloud. The page also showed a second table with $0.89/h, so **re-check before quoting**.
     - RunPod RTX 3090: $0.22 or $0.50/h.
     - Lambda 1× A10 24 GB: $1.29/h.
     - Modal L4: $0.000222/s, about $0.80/h.

     All of these were read through the fetch tool (summary).

**One measured data point.** It comes from the little-coder Harbor job files for Qwen3.6-35B-A3B, with 445 trials and `n_concurrent_trials: 1`, run on one laptop with 8 GB VRAM:

- It started at 2026-04-24T18:16 and finished at 2026-04-26T03:38. That is **33.4 hours**, or about **270 s per trial** on average (derived).
- The Qwen3.5-9B run took **26.4 hours**, about 214 s per trial (derived).
- These figures include the time for local Docker task containers on the same machine.

On a rented RTX 4090 at $0.74/h, 33.4 hours would be about $25 per full 5-trial pass. That is illustrative only, because a 4090 would run faster than an 8 GB laptop GPU.

---

## 4. Recommendation

### 4.1 Where "local" applies

**"Local" means the model, not necessarily the benchmark.**

- Harbor runs every Terminal-Bench task in its own Docker container and calls the model through an API endpoint. The model can be served by llama.cpp, Ollama or vLLM on any machine, and the containers can run in local Docker or a cloud sandbox (Daytona, Modal, and others).
- The little-coder runs show that both can share one laptop. Its job config has `"type": "docker"` and one trial at a time.
- Some tasks need more CPU and RAM than a laptop gives them:
  - Qwen ran its TB2 runs with 32 CPU / 48 GB RAM per task.
  - Terminal-Bench 2.1 lists "insufficient resource budgets" as one cause of broken tasks.
  - PRIOR_WORK.md notes that some tasks need a GPU sandbox.
- Reproducibility therefore depends on pinning three things: the model file, the serving settings, and the container resource limits.

### 4.2 Candidates in the 20–40% starting band

1. **Qwen3.6-35B-A3B at Q4_K_M** (24 GB file; 35B total / 3B active). This is the first choice.
   - It is the only model of 35B or fewer with an **independent** TB2 result in the band: 24.6%, with 445 trials, on a consumer laptop with 8 GB VRAM and 32 GB RAM.
   - The vendor reports 51.5% under a more generous setup (3h timeout, 32 CPU / 48 GB per task). That suggests the headroom comes from strategy and settings, not only the model, which suits this project.
   - Because it is a mixture of experts with 3B active parameters, it is fast for its size. Little-coder reports "~44 tok/s" with CPU offload.
2. **Nemotron-Terminal-32B** (Qwen3-32B fine-tune; Q4_K_M about 19.8 GB; NVIDIA open model licence).
   - NVIDIA reports 27.4% ± 2.4 with Terminus 2. The 14B version reports 20.2% ± 2.7 at a 9.0 GB file.
   - The trial count is not stated, and no independent rerun was found.
   - It was trained on the Terminus 2 JSON format. A custom agent loop that uses a different action format may lose some of that gain. This is an inference, not tested.
   - It is a dense 32B model, so it will be slower than option 1 on the same hardware. No tok/s figure was found.
3. **Qwen3.5-35B-A3B** (22 GB) is a fallback.
   - Vendor-reported 40.5%, with the harness and settings not stated on the card.
   - No independent result was found. Given that Qwen3.6's vendor figure was about twice the independent one, I would expect a lower independent score. This is an inference to be checked in Phase 0.

As a matched API reference, **GPT-5-mini** (22–32% in the paper, depending on the agent) or **Claude Haiku 4.5** (27.5–29.8%) could serve as a cost-matched comparison. Neither is needed for the main experiments.

### 4.3 The smallest model that is plausibly not at the floor

- **Nemotron-Terminal-8B** (5.0 GB Q4_K_M file): 13.0% ± 2.2, vendor-reported.
- **Qwen3.5-9B** (6.6 GB): 9.2% ± 1.2, independent, 445 trials on a laptop.

Both should run on a 16 GB laptop or a base Apple Silicon machine. That is an inference from the file sizes; no speed figure was found. Both are well below 20%, and at 9–13% per trial most tasks would give no successful trajectories to learn from.

**Models at the floor, not recommended as the base model:** base Qwen3-8B, 14B and 32B (0–4%), and gpt-oss-20b (3.1–3.4%). gpt-oss-120b (18.7%) is just below the band and needs about 65 GB, so it is not "small".

### 4.4 To check in Phase 0

- Run S0 with Qwen3.6-35B-A3B on 20 tasks from A∪V, on the target hardware, with the default TB2 timeouts. Confirm that the score is near 24.6%, not near 51.5%.
- Record per-trial wall-clock and tokens as set out in section 3.2.
- Fix the context length and container CPU/RAM limits, and record them in a separate frozen run-settings file, proposed as `evaluation/run_settings.json`, to be created in Phase 0. *(Updated 2026-10-20.)* They cannot go in the split file: the `Split` model in `evaluation/splits.py` forbids extra fields, and `save_split` refuses to overwrite a committed split with a different one.

---

## 5. Sources (all opened 2026-10-15)

**Leaderboards and benchmark**

- https://www.tbench.ai/leaderboard (current page, Terminal-Bench 4.0; data read from the page payload)
- https://www.tbench.ai/leaderboard/terminal-bench/2.0 (now redirects to the site root)
- http://web.archive.org/web/20260826113700/https://www.tbench.ai/leaderboard/terminal-bench/2.0 (last archived TB2 leaderboard, 140 entries)
- http://web.archive.org/cdx/search/cdx?url=www.tbench.ai/leaderboard/terminal-bench/2.0 (snapshot index showing the 308 redirect from 2026-09-01)
- http://web.archive.org/web/20260826020311/https://www.tbench.ai/leaderboard/terminal-bench/2.1 (archived TB2.1 leaderboard)
- https://www.tbench.ai/news/terminal-bench-2-1 (summary)
- https://www.tbench.ai/news/continuous-benchmarks (summary)
- https://www.tbench.ai/news/leaderboard-integrity-and-timeouts (summary)
- https://arxiv.org/abs/2601.11868 and https://arxiv.org/pdf/2601.11868 (TB2 paper, v1, 17 Jan 2026; Table 2 and sections 3–4)
- https://huggingface.co/api/datasets/harborframework/terminal-bench-2-leaderboard/tree/main/submissions/terminal-bench/2.0 (submission list)
- https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/resolve/main/submissions/terminal-bench/2.0/little-coder__qwen3.6-35b-a3b/tb2-leaderboard-k5-2026-04-24__00-34-46/result.json and `.../config.json`
- https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard/resolve/main/submissions/terminal-bench/2.0/little-coder__qwen3.5-9b/tb2-leaderboard-k5-v0.1.24-9b-2026-04-26__20-32-42/result.json and `.../config.json`
- `metadata.yaml` for the little-coder, BashAgent__TermiGen-32B, terminus-2__AfterQuery-GPT-OSS-20B and spoox-o-m__GPT-5-Nano submissions (same dataset)

**Model cards, papers and repositories**

- https://github.com/itayinbarr/little-coder (summary)
- https://huggingface.co/Qwen/Qwen3.6-35B-A3B (raw README)
- https://huggingface.co/Qwen/Qwen3.6-27B (raw README)
- https://huggingface.co/Qwen/Qwen3.5-35B-A3B (raw README)
- https://huggingface.co/Qwen/Qwen3.5-27B (subagent)
- https://huggingface.co/Qwen/Qwen3.5-9B (raw README)
- https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct (subagent)
- https://arxiv.org/abs/2602.21193 and https://arxiv.org/html/2602.21193 (Nemotron-Terminal, 24 Feb 2026; Table 3)
- https://huggingface.co/nvidia/Nemotron-Terminal-32B (raw README)
- https://huggingface.co/api/models/mradermacher/Nemotron-Terminal-8B-GGUF/tree/main, and the same for the 14B and 32B repositories
- https://huggingface.co/open-thoughts/OpenThinker-Agent-v1 (raw README)
- https://huggingface.co/UCSB-SURFI/TermiGen-32B (raw README)
- https://huggingface.co/openai/gpt-oss-20b (raw README)
- https://huggingface.co/zai-org/GLM-4.7-Flash (raw README)
- https://huggingface.co/zai-org/GLM-4.5-Air (subagent)
- https://huggingface.co/google/gemma-4-31B-it and https://huggingface.co/google/gemma-4-26B-A4B-it (subagent)
- https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16 (subagent)
- https://mistral.ai/news/devstral-2-vibe-cli/ (subagent)
- https://www.anthropic.com/news/claude-haiku-4-5 (raw page)
- https://the-decoder.com/openai-ships-gpt-5-4-mini-and-nano-faster-and-more-capable-but-up-to-4x-pricier/ (subagent, summary)
- https://openai.com/index/introducing-gpt-5-4-mini-and-nano/ (HTTP 403, **not read**)

**Local inference**

- https://ollama.com/library/gpt-oss/tags
- https://ollama.com/library/qwen3/tags
- https://ollama.com/library/qwen3-coder/tags
- https://ollama.com/library/qwen3.5/tags
- https://ollama.com/library/qwen3.6/tags
- https://ollama.com/library/glm-4.7-flash/tags
- https://ollama.com/library/gemma3/tags
- https://ollama.com/library/devstral-small-2/tags
- https://ollama.com/library/nemotron-3-nano/tags
- https://ollama.com/library/gemma4/tags, https://ollama.com/library/llama3.1/tags and https://ollama.com/library/deepseek-r1/tags (subagent)
- https://github.com/ggml-org/llama.cpp/discussions/15396 (summary)
- https://github.com/ggml-org/llama.cpp/discussions/4167 (subagent, summary)
- https://unsloth.ai/docs/models/gpt-oss-how-to-run-and-fine-tune and https://unsloth.ai/docs/models/glm-4.7-flash (subagent, summary)
- https://huggingface.co/docs/transformers/main/en/kv_cache (subagent, summary)
- https://runaihome.com/blog/qwen3-30b-a3b-local-ai-guide-2026/ (subagent; unverified community figures)

**Prices and power**

- https://developers.openai.com/api/docs/pricing
- https://platform.claude.com/docs/en/about-claude/pricing
- https://ai.google.dev/gemini-api/docs/pricing (summary)
- https://www.together.ai/pricing (summary)
- https://openrouter.ai/api/v1/models/openai/gpt-oss-20b/endpoints
- https://openrouter.ai/api/v1/models/openai/gpt-oss-120b/endpoints
- https://openrouter.ai/api/v1/models/qwen/qwen3.6-35b-a3b/endpoints
- https://openrouter.ai/api/v1/models/qwen/qwen3-coder-30b-a3b-instruct/endpoints
- https://www.runpod.io/pricing (summary; two conflicting tables)
- https://lambda.ai/pricing (summary)
- https://modal.com/pricing (summary)
- https://www.esc.vic.gov.au/electricity-and-gas/prices-tariffs-and-benchmarks/victorian-default-offer/victorian-default-offer-price-review-2026-27 (summary)
- https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=epmt_5_6_a (summary)
- https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/ (summary)

Items marked "(subagent)" were opened by a research subagent in this same session on 2026-10-15 and were not re-opened by me. All Ollama sizes in section 2.1 that are not marked "not re-checked" were re-read directly.
