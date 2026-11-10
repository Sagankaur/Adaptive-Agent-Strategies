# E-RESPLIT sibling-candidate review amendment — 2026-11-05

## Decision and authorization

The researcher explicitly asked the assistant to review the remaining high-similarity TB2 task pairs. This authorizes a limited language-model review of their public task instructions before the Stage 2 freeze, amending the earlier rule that no generative model would read TB2 task text before Stage 2.

The amendment is recorded before opening instruction text for the candidate review. It does not authorize task builds, Oracle access, reference-solution access, agent runs, hidden-test access, or H52 benchmark episodes.

## Review scope and method

- Benchmark source: `laude-institute/terminal-bench-2@2fd12b88aafdd04a52c298e3940bcb189f9766d6`.
- Review only public `instruction.md` files for the 13 unconfirmed pairs in the V2 candidate report's top-20 cross-H similarity list.
- Do not inspect `tests/`, `solution/`, `environment/`, task images, Oracle outputs, or model/agent trajectories.
- Classify a pair as a sibling only when the instructions request substantially the same target artifact or task-specific procedure. Shared broad topic, language, framework, or tool alone is insufficient.
- Record each pair ID, classification, and a short paraphrased rationale. Do not reproduce task instructions.
- Re-run the deterministic split generator only if this review adds groups. Preserve the old split and keep all H52 tasks free of benchmark execution.

## Research-integrity impact

This is a protocol deviation because a generative assistant will read public task instructions before Stage 2. It creates a risk of researcher/model familiarity with held-out task wording. Record the deviation in the final preregistration and limitations. The review is limited to leakage control and split construction; no task outcomes are observed.

## Results

All 13 candidate pairs were reviewed under the stated criterion. Two additions were accepted; the other eleven were rejected as non-siblings.

| Candidate pair | Decision | Paraphrased rationale |
|---|---|---|
| `code-from-image` / `gcode-to-text` | Separate | One evaluates pseudocode read from an image; the other extracts text from printer G-code. |
| `dna-assembly` / `protein-assembly` | Separate | They concern different molecular design procedures and target artifacts. |
| `crack-7z-hash` / `vulnerable-secret` | Separate | One recovers an archive password; the other extracts a secret by analyzing an executable. |
| `git-leak-recovery` / `vulnerable-secret` | Separate | One recovers and removes leaked repository history; the other analyzes an executable for a secret. |
| `gpt2-codegolf` / `pytorch-model-cli` | Separate | They implement inference for different models, formats, and interfaces. |
| `log-summary-date-ranges` / `regex-log` | Same group | Both parse logs and handle date-range or regex-based selection; the former joins the existing regex/log group transitively. |
| `feal-linear-cryptanalysis` / `vulnerable-secret` | Separate | FEAL cryptanalysis and executable secret extraction use different procedures and targets. |
| `path-tracing` / `write-compressor` | Separate | One reconstructs an image by rendering; the other implements data compression. |
| `code-from-image` / `polyglot-rust-c` | Separate | Image transcription and a cross-language Fibonacci program do not share a task-specific procedure. |
| `circuit-fibsqrt` / `write-compressor` | Separate | Gate-level computation and decompression have different targets and methods. |
| `circuit-fibsqrt` / `polyglot-rust-c` | Same group | Both require computing Fibonacci values; the core algorithm transfers directly despite different implementation constraints. |
| `chess-best-move` / `regex-chess` | Separate | Choosing a move from a board differs from implementing a legal-move generator. |
| `extract-moves-from-video` / `regex-chess` | Separate | Transcribing commands from video differs from implementing chess move generation. |

The two accepted links extend existing groups transitively. They produce nine indivisible groups: seven pairs and two three-task groups (regex/log/date-range, and the polyglot/Fibonacci group). The revised split is a new V3 candidate; V1 and V2 remain preserved as historical artifacts. No task build, Oracle check, reference-solution execution, agent run, or H52 benchmark episode was performed.
