# E-RESPLIT split candidate — 2026-11-05

## Status

V3 is a deterministic candidate, not a frozen experimental split. It supersedes V2 for consideration because the scoped instruction review accepted two additional leakage links. V1 and V2 remain preserved. The existing A25/V12/M15/H37 split was not modified. No task was built, Oracle-checked, reference solution run, or evaluated by an agent. H52 remains unexecuted.

The review used only public `instruction.md` files for the 13 unconfirmed high-similarity pairs, as authorized and recorded in [`E-RESPLIT-candidate-review-amendment-2026-11-05.md`](E-RESPLIT-candidate-review-amendment-2026-11-05.md). Eleven pairs were kept separate; two were added to existing groups. The amendment records each decision and its rationale, as well as the protocol deviation.

## Inputs and hashes

| Artifact | SHA-256 |
|---|---|
| Pinned task metadata, `evaluation/data/tb2_tasks.jsonl` | `ed7d652ea977eb0a609daa551ba5bfc61f96631e32fbd6f48d77f6adb04ffe1e` |
| Reviewed sibling-group manifest, `evaluation/data/tb2_sibling_groups.json` | `d36bcd4ba1256e33af811f3ae8a2920c0030ea74a7eb7f9cb6618b6bc71c3335` |
| Existing split, `splits/terminal-bench-2.0.json` | `ad74c41b98d55111eda914d3048810a6035d0663316ff6d54933d0e41f0720f9` |
| V1 candidate, superseded | `7f16e19e8d93d27bb4608b782ba217389255c9c943069f7fc5c2df44f932a8be` |
| V2 candidate, superseded | `c7c803165947eecee3d4b5d4c7d21bf1cf080473eeafe2eee06fc887740081bc` |
| V3 candidate, `splits/tb2-resplit-h52-seed20261015-v3.json` | `057901a360bfcc378fceec1708ea4c87cab1f233b1244f45e3d90212a69824a7` |
| Generator, `evaluation/build_resplit.py` | `eb68f1d29d71e0e235622784397e949943d764f1ea6409681acae2eb2cfc19b5` |

Task metadata is pinned to `laude-institute/terminal-bench-2@2fd12b88aafdd04a52c298e3940bcb189f9766d6`. The split records task-ID fingerprint `5c7ed05c61e6768b71bebb5ffd05d9ce07e185b3cf519b06ca2ae5d476f99638`.

## Allocation method

- Seed: `20261015`; 50,000 deterministic starts. SHA-256 keys derived from seed, trial, unit, and pool set order and tie breaks.
- Units: nine indivisible groups (seven pairs and two triplets) and 69 singleton tasks. The triplets are regex/log/date-range and polyglot/Fibonacci.
- Exact pool sizes: A15 / V12 / V2 10 / H52. Indivisible-group quotas: A2 / V1 / V2 1 / H5, proportional to pool sizes by largest remainder.
- Objective: minimize normalized squared deviation across category × difficulty strata, `sum((observed - expected)^2 / max(expected, 1))`, with `expected = stratum_total × pool_size / 89`.
- For each start, groups are placed within their quotas using incremental stratum-balance cost; remaining singletons fill remaining capacity, prioritizing the largest deficit. The saved assignment has the lowest objective; ties use lexicographically ordered task IDs.
- The V3 objective is `18.08986836`. It is the best of these 50,000 deterministic greedy starts, not a proven global optimum.

Running `py -3.14 -m evaluation.build_resplit` regenerated the LF-serialized V3 byte-for-byte (SHA-256 above). Canonical LF output keeps the recorded hash stable across Windows and Linux. The generator validates the pinned metadata, group manifest, exact task coverage, no duplicate assignment, exact pool sizes, intact groups, and group quotas.

## Group distribution

| Pool | Tasks | Groups | Grouped tasks |
|---|---:|---:|---:|
| A | 15 | 2 | 5 |
| V | 12 | 1 | 2 |
| V2 | 10 | 1 | 2 |
| H | 52 | 5 | 11 |

## Achieved category × difficulty counts

| Category | Difficulty | A | V | V2 | H | Total |
|---|---|---:|---:|---:|---:|---:|
| data-processing | medium | 1 | 1 | 0 | 2 | 4 |
| data-querying | hard | 0 | 0 | 0 | 1 | 1 |
| data-science | hard | 1 | 0 | 0 | 1 | 2 |
| data-science | medium | 1 | 1 | 1 | 3 | 6 |
| debugging | easy | 0 | 0 | 0 | 1 | 1 |
| debugging | medium | 1 | 1 | 0 | 2 | 4 |
| file-operations | hard | 0 | 0 | 0 | 1 | 1 |
| file-operations | medium | 1 | 1 | 0 | 2 | 4 |
| games | medium | 0 | 0 | 0 | 1 | 1 |
| machine-learning | hard | 0 | 0 | 0 | 1 | 1 |
| machine-learning | medium | 1 | 0 | 0 | 1 | 2 |
| mathematics | hard | 1 | 0 | 0 | 2 | 3 |
| mathematics | medium | 0 | 0 | 0 | 1 | 1 |
| model-training | hard | 0 | 0 | 0 | 1 | 1 |
| model-training | medium | 0 | 2 | 0 | 1 | 3 |
| optimization | medium | 0 | 0 | 0 | 1 | 1 |
| personal-assistant | medium | 0 | 0 | 0 | 1 | 1 |
| scientific-computing | hard | 0 | 0 | 1 | 2 | 3 |
| scientific-computing | medium | 1 | 1 | 1 | 2 | 5 |
| security | hard | 1 | 0 | 0 | 1 | 2 |
| security | medium | 1 | 1 | 1 | 3 | 6 |
| software-engineering | easy | 0 | 1 | 0 | 2 | 3 |
| software-engineering | hard | 2 | 2 | 1 | 8 | 13 |
| software-engineering | medium | 1 | 1 | 1 | 7 | 10 |
| system-administration | hard | 0 | 0 | 1 | 1 | 2 |
| system-administration | medium | 2 | 0 | 2 | 3 | 7 |
| video-processing | hard | 0 | 0 | 1 | 0 | 1 |

## Remaining decision before freeze

The original static candidate search used `BAAI/bge-base-en-v1.5` at revision `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`. It ranked seven known groups among the top 30 and missed two; similarity scores are ranking signals, not probabilities or evidence of task equivalence. The 13 high-similarity candidates were reviewed under the limited protocol amendment. Before any task build, Oracle access, reference-solution run, or agent episode, the research owner must accept or revise this candidate, resolve route-specific pre-screen/G-INFRA accounting, and freeze the selected split hash in the preregistration.
