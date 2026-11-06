# Per-cell synthetic serving results - 2026-11

This companion table summarizes every measured prompt/output cell. The raw per-call JSONL, server timing fields, GPU samples, metadata, and retained server logs are in the matching `docs/experiments/artifacts/serving_sweep_<job-id>/` directory.

Prompt and generation speed are medians of per-call llama.cpp timing fields across all calls for that cell (3 calls for the one-slot run, 12 for four slots). Aggregate total throughput is the median of the three synchronized batches, computed as realized prompt plus generated tokens divided by batch wall time; bracketed values are the minimum and maximum batch throughputs. Call wall is the median client wall time across calls. Output values are requested caps, while the right column gives actual generated-token median and range. Early EOS can make generation-speed and total-throughput comparisons noisy, especially when actual output is short.

| Run | Prompt target / output cap | Prompt tok/s, per-call median | Generation tok/s, per-call median | Aggregate prompt + generated tok/s, median [range] | Call wall median | Actual output tokens, median [range] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4504968 L40S 1 slot q8_0 | 8,192 / 512 | 7,092 (n=3) | 143.6 | 6,284 [6,239-6,819] | 1.3 s | 21 [6-23] |
| 4504968 L40S 1 slot q8_0 | 8,192 / 2,048 | 6,856 (n=3) | 142.6 | 979 [657-6,153] | 9.5 s | 1,132 [20-2,048] |
| 4504968 L40S 1 slot q8_0 | 32,768 / 512 | 6,535 (n=3) | 127.6 | 3,682 [3,668-3,685] | 9.0 s | 512 [512-512] |
| 4504968 L40S 1 slot q8_0 | 32,768 / 2,048 | 6,374 (n=3) | 128.2 | 5,621 [1,638-5,639] | 5.8 s | 87 [86-2,048] |
| 4504968 L40S 1 slot q8_0 | 63,360 / 512 | 5,729 (n=3) | 113.1 | 4,089 [4,067-4,115] | 15.6 s | 512 [512-512] |
| 4504968 L40S 1 slot q8_0 | 63,360 / 2,048 | 5,665 (n=3) | 113.0 | 2,232 [2,231-3,012] | 29.3 s | 2,048 [1,154-2,048] |
| 4504968 L40S 1 slot q8_0 | 64,896 / 512 | 5,629 (n=3) | 113.0 | 5,210 [5,209-5,225] | 12.5 s | 104 [102-104] |
| 4504971 L40S 4 slots q8_0 | 8,192 / 512 | 4,163 (n=12) | 52.4 | 2,946 [2,888-3,593] | 8.6 s | 270 [21-512] |
| 4504971 L40S 4 slots q8_0 | 8,192 / 2,048 | 4,082 (n=12) | 44.0 | 1,099 [954-1,354] | 18.8 s | 642 [21-2,048] |
| 4504971 L40S 4 slots q8_0 | 32,768 / 512 | 5,198 (n=12) | 19.4 | 4,019 [3,934-4,287] | 30.4 s | 484 [63-512] |
| 4504971 L40S 4 slots q8_0 | 32,768 / 2,048 | 5,167 (n=12) | 35.8 | 2,451 [2,032-3,271] | 41.1 s | 1,437 [15-2,048] |
| 4504971 L40S 4 slots q8_0 | 63,360 / 512 | 4,869 (n=12) | 19.7 | 4,359 [4,336-4,423] | 57.7 s | 512 [170-512] |
| 4504971 L40S 4 slots q8_0 | 63,360 / 2,048 | 4,871 (n=12) | 34.0 | 3,143 [2,846-3,516] | 77.5 s | 2,048 [192-2,048] |
| 4504971 L40S 4 slots q8_0 | 64,896 / 512 | 4,888 (n=12) | 20.4 | 4,504 [4,450-4,525] | 57.4 s | 512 [78-512] |
| 4505001 L40S 4 slots f16 | 8,192 / 512 | 4,213 (n=12) | 59.9 | 3,258 [3,077-3,600] | 6.7 s | 67 [8-512] |
| 4505001 L40S 4 slots f16 | 8,192 / 2,048 | 4,121 (n=12) | 29.4 | 1,549 [1,471-1,744] | 8.2 s | 22 [8-2,048] |
| 4505001 L40S 4 slots f16 | 32,768 / 512 | 5,276 (n=12) | 7.6 | 4,937 [4,918-5,168] | 22.9 s | 60 [15-512] |
| 4505001 L40S 4 slots f16 | 32,768 / 2,048 | 5,239 (n=12) | 32.4 | 2,159 [2,120-3,205] | 34.1 s | 552 [48-2,048] |
| 4505001 L40S 4 slots f16 | 63,360 / 512 | 4,983 (n=12) | 16.8 | 4,423 [4,368-4,670] | 55.5 s | 512 [20-512] |
| 4505001 L40S 4 slots f16 | 63,360 / 2,048 | 4,964 (n=12) | 30.6 | 2,883 [2,801-3,666] | 79.7 s | 2,048 [138-2,048] |
| 4505001 L40S 4 slots f16 | 64,896 / 512 | 4,989 (n=12) | 20.2 | 4,353 [4,346-4,625] | 59.2 s | 512 [180-512] |
| 4505019 RTX Pro 6000 4 slots q8_0 | 8,192 / 512 | 5,208 (n=12) | 58.6 | 3,112 [3,108-4,240] | 8.0 s | 512 [6-512] |
| 4505019 RTX Pro 6000 4 slots q8_0 | 8,192 / 2,048 | 5,263 (n=12) | 71.0 | 1,227 [1,200-2,090] | 16.5 s | 1,436 [6-2,048] |
| 4505019 RTX Pro 6000 4 slots q8_0 | 32,768 / 512 | 6,854 (n=12) | 24.9 | 6,193 [5,457-6,541] | 19.4 s | 220 [17-512] |
| 4505019 RTX Pro 6000 4 slots q8_0 | 32,768 / 2,048 | 6,864 (n=12) | 77.7 | 4,490 [4,131-4,597] | 18.7 s | 175 [15-2,048] |
| 4505019 RTX Pro 6000 4 slots q8_0 | 63,360 / 512 | 6,807 (n=12) | 27.1 | 6,068 [5,862-6,485] | 41.3 s | 512 [77-512] |
| 4505019 RTX Pro 6000 4 slots q8_0 | 63,360 / 2,048 | 6,813 (n=12) | 40.7 | 4,238 [3,869-4,506] | 50.3 s | 884 [74-2,048] |
| 4505019 RTX Pro 6000 4 slots q8_0 | 64,896 / 512 | 6,803 (n=12) | 27.6 | 6,062 [6,045-6,072] | 42.8 s | 512 [376-512] |

No row represents a benchmark task or episode. These cells are engineering measurements for the pinned model/server on the named GPU only.
