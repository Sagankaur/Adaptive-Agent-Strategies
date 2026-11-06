# TB2 sibling groups recovered — 2026-11-05

## Finding

The missing nine pair IDs were present in design-review red-team notes (2026-10, not in the repository), lines 30–42, SHA-256 `fa249936dd967cac736e40d8ec6c78fb70abcc0966ab56d3cee044a7d9de4bfd`. Their table explicitly identifies the held-out task, sibling, and sibling pool for each pair.

| Group | Held-out task | Sibling task | Existing pool |
|---|---|---|---|
| 1 | `filter-js-from-html` | `break-filter-js-from-html` | A |
| 2 | `path-tracing` | `path-tracing-reverse` | A |
| 3 | `polyglot-c-py` | `polyglot-rust-c` | A |
| 4 | `qemu-startup` | `qemu-alpine-ssh` | A |
| 5 | `regex-chess` | `regex-log` | A |
| 6 | `feal-differential-cryptanalysis` | `feal-linear-cryptanalysis` | M |
| 7 | `torch-tensor-parallelism` | `torch-pipeline-parallelism` | M |
| 8 | `dna-insert` | `dna-assembly` | M |
| 9 | `pytorch-model-recovery` | `pytorch-model-cli` | V |

The IDs and current-pool assignments were checked against the pinned task inventory and `splits/terminal-bench-2.0.json` (SHA-256 `ad74c41b98d55111eda914d3048810a6035d0663316ff6d54933d0e41f0720f9`). The result is exactly five H–A pairs, three H–M pairs, and one H–V pair, matching the original report.

## Machine-readable manifest

[`evaluation/data/tb2_sibling_groups.json`](../../evaluation/data/tb2_sibling_groups.json) records the nine initial groups, pinned benchmark commit, source path, and source-file hash. The scoped review later merged two additional links into existing groups; the current nine-group manifest has seven pairs and two triplets. This does not change the historical split assignment or freeze the proposed E-RESPLIT split.

## Embedding check and limits

As a secondary check, the pinned TB2 instruction files were embedded locally with `BAAI/bge-base-en-v1.5` at revision `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`. At that initial discovery stage, no instruction text was printed or sent to a generative model; the later scoped review is recorded separately in the [review amendment](E-RESPLIT-candidate-review-amendment-2026-11-05.md). The model ranked seven of these nine pairs among its 30 highest-scoring pairs; it did not recover all nine from similarity ranking alone. The original red-team table, not the embedding scores, is the authority for the initial group labels. Similarity scores are only candidate-finding evidence and should not be used to add more sibling groups without review.

## Split candidate

The group manifest feeds a separate exact-size H52 split candidate. V1 was superseded after review found its eight-groups-in-H allocation too concentrated. V2 balanced the initial nine groups as A2 / V1 / V2-1 / H5; after review of 13 high-similarity candidates, V3 retains those quotas and includes the two accepted transitive links. See the [candidate report](E-RESPLIT-split-candidate-2026-11-05.md), [review amendment](E-RESPLIT-candidate-review-amendment-2026-11-05.md), and [V3 JSON](../../splits/tb2-resplit-h52-seed20261015-v3.json).

V3 is not frozen. Route-specific pre-screen/G-INFRA accounting remains open, and the research owner must approve the candidate and freeze its hash before any task build, Oracle check, reference-solution run, or agent episode. No split assignment has been used for these purposes. The historical `splits/terminal-bench-2.0.json` remains unchanged.
