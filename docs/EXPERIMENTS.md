# Experiments for paper 1

Sagandeep Kaur, draft for discussion with Prof. Mohamed Abdelrazek (Deakin A2I2), 2026-10-20.

**Status (updated 2026-10-30).** No planned benchmark experiment has run. A one-task real-Qwen Harbor smoke on Rohan passed with reward 1.0, confirming native model tool calls and Harbor's synthetic task lifecycle only; it is not a benchmark result. P-M2 source/resource preflight has started, but the Alibaba base-image registry is unreachable from Rohan, so no task image build or Oracle trial has run. Every episode count and GPU-day figure below is an estimate. This file lists each planned experiment as a card, with its design, cost and decision rules. Where this file and [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md) sections 7 and 9 disagree, this file holds the later decisions (2026-10-20).

Some choices below depend on Prof. Abdelrazek's answers to open questions. Those choices are marked **to confirm with Prof. Abdelrazek**. Each has a stated default, which applies only if there is no answer by the Stage-1 freeze, and is then logged in the decision log, [DECISIONS.md](DECISIONS.md#3-decision-log) section 3. The questions are in [DECISIONS.md](DECISIONS.md#1-open-decisions) section 1, under the ids used in the [Open questions](#open-questions-for-prof-abdelrazek) table below.

---

## How to read this file

### Terms and acronyms

| Term | Meaning |
|---|---|
| TB2 | Terminal-Bench 2.0, 89 tasks, pinned at task commit `2fd12b8` |
| TB2-89 | All 89 TB2 tasks, held out for the final pre-registered run only |
| TB-Pro | terminal-bench-pro, 200 tasks ([GitHub](https://github.com/alibaba/terminal-bench-pro); [Hugging Face](https://huggingface.co/datasets/alibabagroup/terminal-bench-pro)), introduced in Let It Flow: Agentic Crafting on Rock and Roll, Building the ROME Model within an Open Agentic Learning Ecosystem ([Wang et al., arXiv 2512.24873, Dec 2025](https://arxiv.org/abs/2512.24873)). Used for all adaptation and calibration |
| A_pro, V_pro, V2_pro, dev slice | TB-Pro pools: adaptation, screening, end-of-loop choice, and a 15-task slice for bring-up and debugging only |
| Harbor | The official Terminal-Bench evaluation harness. One trial runs one agent on one task in its own Docker container, then runs the task's tests and records a reward. It does not serve the model |
| little-coder | A public third-party agent. Its 445 TB2 trials of Qwen3.6-35B-A3B (89 tasks × 5, run on an 8 GB-VRAM laptop) are in the Hugging Face dataset [`harborframework/terminal-bench-2-leaderboard`](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard). This file uses that run only as public reference data |
| RQ1 to RQ4 | The research questions ([TECHNICAL_PLAN.md](TECHNICAL_PLAN.md#research-questions-amended-2026-10-20), section 1). RQ1: does adaptation beat the fixed strategy, reflection-retry and best-of-N at the same budget? RQ2: do gains hold on unseen tasks (in paper 1, cross-source, TB-Pro to TB2)? RQ3: does revising the adaptation mechanism help (paper 2 by default)? RQ4: which strategy dimensions account for the gains? |
| Internship objectives 1 to 6 | (1) strong baselines; (2) the strategy as an explicit object; (3) an adaptation mechanism; (4) a second-order loop; (5) held-out generalisation; (6) transfer to a second benchmark family. Listed in [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md#the-six-internship-objectives-and-where-each-is-handled-here-amended-2026-10-20) |
| Q1 to Q6, Q8; plan items 1, 6, 11 | Open questions for Prof. Abdelrazek, numbered as in [DECISIONS.md](DECISIONS.md#1-open-decisions) section 1 |
| T-ids (T1 to T16) | Candidate research threads weighed in the design review ([DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md#m14-other-threads), M13 and M14). Each one used here is glossed where it appears |
| S0 | The fixed hand-written strategy (baseline B0) |
| S\*1, S\*2 | The strategies chosen by two independent adaptation loops (seed 1 and seed 2) |
| S\* | The per-task average of S\*1 ×5 and S\*2 ×5 runs (10 runs per task). In the single-seed branch, S\*1 ×10 |
| B1 | In-episode reflection-retry |
| B2, BoN | Best-of-N: pick one of N runs of S0 by a selector |
| B4 | Random strategy edits in the same edit space with the same loop and budget |
| B5 | Free-form edits of our controller code (optional, Tier C) |
| Episode | One Harbor trial of one strategy on one task. A B1 run counts as one episode-equivalent per attempt |
| k | Runs per task |
| MCU | Model Compute Units: a × prompt tokens + b × generated tokens, from llama.cpp per-call `timings`. a and b are fitted in E-P0 and frozen. MCU is the cost-matching unit |
| pp | Percentage points |
| MDE | Minimum detectable effect at 80% power, alpha 0.05 (planning estimate) |
| CI | 95% confidence interval from a one-stage task bootstrap (10,000 resamples) unless stated otherwise |
| Contested task | A task solved in some but not all of its runs |
| C3, C5 | Counts of contested TB-Pro tasks after S0 ×3, and after a top-up to ×5. Not the paper's claims C1 to C4 in [PAPER_PLAN.md](PAPER_PLAN.md) |
| C (pool sizing) | The contested count that sizes the pools in P-M2: C3, or C5 after a top-up |
| Cap | Episode capacity at gate G0: Cap = 0.9 × r × D_rem (called C in [DECISIONS.md](DECISIONS.md#q5-compute-meeting-point-6) Q5) |
| VBS, SBS | Virtual best solver (best version per task) and single best solver (best version overall) |
| CRN | Common random numbers: the same seed for a (task, run) pair across candidates |
| GPU-day | 24 hours of one dedicated GPU |
| Tier C | Optional add-ons funded only from headroom under the absolute cap |

### Hypotheses

**H1 to H4** name only the four confirmatory hypotheses of E3, the same chain as in [PAPER_PLAN.md](PAPER_PLAN.md) and [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md) section 7.2. Each has the null "difference = 0", and all are tested two-sided. Exploratory cards write **Ha** for their alternative and **H0** for their null.

### Planning simulation model

Every MDE and selection-rule figure marked "simulated" comes from one model, built before any run from public third-party data. E0-SIM refits it on TB-Pro E0 data before Stage 1.

- **Base rates.** Each TB2 task's S0 pass rate is drawn from the posterior of a beta-binomial fitted to little-coder's per-task counts (89 tasks × 5): Beta(0.170, 0.569), mean 0.230. Its intra-task correlation (ICC) is 1 / (a + b + 1) = 0.575, so tasks differ far more from each other than runs of one task do.
- **Effects.** A strategy change shifts each task's pass rate on the logit scale: a common shift plus task-level noise with SD 0.5 (the task heterogeneity). The shift applies to tasks that were contested in that run; tasks it never or always solved keep their rate.
- **Test.** Paired t on the 89 per-task mean differences, two-sided, alpha 0.05, 6,000 replicates per grid point. The MDE is the true mean difference at which power crosses 80%.
- **Edit effects in E2.** Each candidate edit's effect is drawn independently from N(0, 0.3²) on the logit scale, and effects add. This is an assumption, not a measurement.
- **From logits to pp.** One logit shift moves tasks by different amounts. +0.82 logit moves a task at 50% to 69% (+19 pp) and a task at 2% to 4.4% (+2.4 pp). Averaged over TB2's per-task rates, most of which are near 0, it is about +6.6 pp.
- **tau².** tau² = 0.008, the between-task variance of the effect, belongs to a closed-form cross-check: MDE ≈ 2.8 × sqrt((tau² + 2 × 0.062 / k) / n), where 0.062 is a mean within-task variance p(1 − p). Both inputs come from an earlier methodology review of the plan and were not fitted to data. The closed form gives 5.4 pp for 89 tasks × 5, against 5.8 pp simulated. The simulated figures are the ones used. E0-SIM replaces both inputs with values fitted on TB-Pro.
- **Figures marked "rough"** were not simulated. Each says how it was scaled from a simulated case.

### Pre-registration stages

- **Stage 1** is a signed git tag before the first E2 adaptation episode. It freezes the pool lists, thresholds, analysis code, budget caps and `pins.lock` (model file hash, llama.cpp commit and flags, Harbor version, image digests, sampling, MCU coefficients).
- **Stage 2** is a second signed tag before the first TB2 agent episode.
- Each tag is archived on Zenodo with a DOI (digital object identifier). An OSF (Open Science Framework) registration quotes the tag SHA and DOI. OSF text is drawn only from this public repository.

### Throughput used for every GPU-day figure

**213.5 TB2 episodes per GPU-day**, at concurrency 1. This is 86,400 s / 404.7 s, the mean trial time over all 445 trials of little-coder's public Qwen3.6-35B-A3B run on TB2 (trial records in the Hugging Face dataset [`harborframework/terminal-bench-2-leaderboard`](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard)). Those trials never overlapped, and their durations sum to 50.03 h.

- It was measured on a laptop with 8 GB of VRAM and 32 GB of RAM, using MoE (mixture-of-experts) offload to the CPU. It is used as a conservative planning proxy.
- It is a proxy with a ±30% band: 149 to 278 episodes per GPU-day.
- It is applied to TB-Pro episodes too, although TB-Pro tasks have 3600 s agent timeouts. The rate r is measured on TB-Pro at gate G0 (E0) and the plan is re-costed then.
- GPU-days in this file are episodes / 213.5, rounded to two decimals.

### Fixed run settings (all arms)

| Setting | Value |
|---|---|
| Primary model | Qwen3.6-35B-A3B, Q4_K_M, served by llama.cpp on the run host |
| Sampling | temperature 0.6, top_p 0.95, top_k 20, logged per-request seed (the model card's setting for precise coding in thinking mode) |
| Step budget | max_steps = 60 (a logged change from S0's committed 40) |
| Token budget | at most 64k generated tokens per episode, reasoning included (per attempt for B1) |
| Wall-clock | backstop only: Harbor agent timeout multiplier 2 for every arm |
| Concurrency | pinned from the E-P0 sweep |
| Network | TB-Pro: pinned allowlist fork. TB2: upstream setting (`allow_internet = true`), with per-trial audit (E3-AUDIT) |

---

## Index

Episodes are main-GPU episodes counted in the core total unless marked. "Points" are the six meeting points of 2026-10-14 ([MEETING_2026-10-14.md](MEETING_2026-10-14.md)): 1 "baseline cost : task", 2 "benchmark : task", 3 "strategy adapt", 4 "intelligence index", 5 "strategy switching", 6 "small models on terminal bench, coz everyone can run small models on local machine".

| ID | Title | Pool | Episodes | GPU-days | Status | Points | Paper slot |
|---|---|---|---|---|---|---|---|
| [P-M2](#p-m2-tb-pro-route-pilot) | TB-Pro route pilot (build, dedup, Oracle check, licence, disk) | TB-Pro | 0 (CPU only) | 0 | planned | 2 | Table 7, A1, A3, A7 |
| [E-P0](#e-p0-bring-up-and-throughput-sweep) | Bring-up, throughput sweep, A/A run | TB-Pro dev | 150 | 0.70 | planned | 6, 1 | Table 7, A2, A3, A4 |
| [E1](#e1-b1-smoke-test) | B1 smoke test | TB-Pro dev | 60 | 0.28 | planned | 1 | A4, A6 |
| [E0](#e0-calibration-on-tb-pro) | S0 calibration, gate G0 | TB-Pro | 600 | 2.81 | planned | 6, 2 | Table 7, A2, A7, Figure A1 |
| [E2](#e2-adaptation-loops) | Three adaptation loops: S\*1, S\*2, B4 | TB-Pro | 4,095 | 19.18 | planned | 3 | Figure 2, A5, A12 |
| [E3](#e3-confirmatory-run-on-tb2-89) | Confirmatory run: S0, S\*, B4, B1, BoN | TB2-89 | 3,249 | 15.22 | planned | 1, 2, 3 | Table 3, Table 4, Figure 3, Figure 4, A1 |
| [E-ATTR](#e-attr-leave-one-out-attribution) | Leave-one-out attribution, lessons/notes-off arm | TB2, 40 tasks | 480 | 2.25 | planned | 3 | Figure 6, Table 5 |
| [E-T2](#e-t2-enforced-versus-advised) | Enforced vs advised: advised cell | TB2-89 | 445 | 2.08 | planned | 3 | Figure 5, Table 5 |
| [E4-SW](#e4-sw-offline-strategy-switching) | Offline switching: library, selectors, regret | TB2-89 logs | 0 | 0 | planned | 5, 1 | Figure 8, A8 |
| [E4b](#e4b-mid-task-switching-reserve) | Mid-task switching | TB-Pro pilot + TB2-89 | 307 (reserve) | 1.44 | optional, default paper 2 | 5 | Table 3 row |
| [E-PORT](#e-port-portability-check) | Portability check on consumer-class hardware | TB2-89 | 267 | 1.25 | planned | 6 | Table 6 |
| [E11](#e11-adaptation-efficiency-index) | Adaptation efficiency index | logs | 0 | 0 | planned (reading to confirm) | 4 | Figure 7, A9, Figure A5 |
| [E-N1, E-N2, E-N3, E-N4, E-T12](#zero-episode-analyses) | Zero-episode analyses | logs | 0 | 0 | planned | 1, 3 | Table 1, Table 2, Table 4, A5, A10, A11, Figures A3 and A4 |
| [E-T2 enforce-only](#e-t2-enforced-versus-advised) | Enforce-only cell | TB2-89 | 445 | 2.08 | optional (Tier C rank 2) | 3 | Figure 5, Table 5 |
| [E-T1lite](#e-t1lite-second-model-row) | Second small model: TMax-9B | TB-Pro pilot + TB2-89 | 554 | 2.59 | optional (Tier C rank 3) | 6 | Table 6 |
| [E-B5](#e-b5-free-form-code-baseline) | Free-form code-edit baseline | TB-Pro + TB2-89 | 1,810 | 8.48 | optional (Tier C rank 4) | 3 | Table 5 row, Figure 3 point, A15 |
| [E5-DEMO](#e5-demo-descriptive-second-order-loop) | Descriptive second-order demonstration | TB-Pro only | ≤ 1,365 | 6.39 | optional (Tier C rank 1, only if asked) | none | Figure 2 overlay |
| [E-RESPLIT](#e-resplit-fallback-tb2-re-split) | Sibling-grouped TB2 re-split | TB2 | replaces the TB-Pro route | n/a | optional (fallback only) | 2 | Table 3 |
| [E0-FB](#e0-calibration-on-tb-pro) | E0 repeated for a fallback model | TB-Pro | ≤ 1,150 each, outside the total | ≤ 5.39 each | optional (fallback only) | 6 | A2 |
| [E8 re-entry](#moved-to-paper-2-or-dropped-and-why) | AppWorld S0 vs S\* at k=1 | AppWorld | costed from the adapter | n/a | optional, default paper 2 | 4 | A16 (only if run) |
| **Core total** | | | **9,653** | **45.21** | | | |

Experiment ids E6 and E7 are not used: the final held-out run is E3 and attribution is E-ATTR.

Table and figure ids follow [PAPER_PLAN.md](PAPER_PLAN.md#6-figures-and-tables) section 6 (Table 1 closest-work matrix; Table 2 mechanism table; Table 4 cost per task). Appendix ids A1 to A16 follow its section 7.

---

## Gates and zero-episode protocol items

These are not experiments, but experiments depend on them. None uses a GPU episode.

| ID | What it is | Closes when |
|---|---|---|
| G-INFRA | Async Harbor agent adapter. Reward read from the Harbor trial result. Async client per trial that parses `reasoning_content`, tool calls, timings and cached tokens. Native tool calling through the chat template. Per-step JSONL logs. Harbor job configs with `n_concurrent_trials` equal to the llama.cpp slot count | All items pass, the baseline unit tests pass, and a 5-task TB-Pro smoke run has 0 harness errors. Blocks every budgeted episode |
| G1 | `compile(strategy)` returns a controller configuration and prompt text with independent switches. Per-field tests decide which fields are "compiled" | The minimum compiled set (exploration, tool_policy, verification, and recovery.retry_on / max_retries / on_repeated_failure with values continue, replan, restart_task) passes CI tests. Edit-space tests show that rollback values and `switch_to` are excluded. Every other field is labelled text-only. Table 2 passes code review. Must close before Stage 1 |
| CODE-FIX | Selection thresholds compared as integer task counts in `adaptation_engine/first_order.py`, with exact-tie unit tests | Before Stage 1 |
| LEDGER | The boolean held-out guard keyed on the split name (`evaluation/runner.py`) is replaced by a guard keyed on the TB2-89 task ids. Every access appends a record to an append-only ledger, whose hash goes into each signed tag | Before the first TB2 image pull |
| LINT-PILOT | Lint on every note, lesson and proposer-written text: rejects task ids, URLs, commands over 40 characters and paths from any task. Piloted on proposer outputs from TB-Pro E0 failure logs, with its false-positive rate reported | Before Stage 1 |
| E-INTERP | Pre-registered table of how each B5 outcome will be read | Before Stage 1 |
| PREREG-1, PREREG-2 | Stage-1 and Stage-2 tags, Zenodo DOI, OSF entry | Before E2 and before the first TB2 agent episode |

**G1 fallback.** If recovery.\* cannot be compiled by the planned Stage-1 date, the typed-strategy claim is narrowed in the pre-registration and logged. It is never kept silently.

### Thresholds and where they come from

Each decision threshold has one of three sources: a **simulation** or arithmetic shown here, a **convention**, or **owner judgement** (a round value chosen in the design review, not derived). All are frozen in the Stage-1 tag.

| Threshold | Where used | Source and reason |
|---|---|---|
| Pass-rate CI bounds 12% and 45% | E0 fitness | Owner judgement. The recorded 20 to 40% band is in TB2 terms, and TB-Pro's difficulty is unknown, so the TB-Pro band is wider and uses CI bounds. It fails only a model that is clearly too weak or too strong. A point threshold would not do: E0's pass rate on about 200 tasks × 3 has a standard error of about 2.6 pp (estimate), so a 12% point cut cannot separate 10% from 14% |
| Infrastructure errors ≤ 5% (E0), ≤ 2 of 40 (E4b pilot) | E0, E4b | Owner judgement |
| C3 ≥ 40 | E0 supply | Arithmetic: 40 contested tasks about fill V_pro (cap 25) and V2_pro (cap 15) |
| C5 ≥ 30; 20 ≤ C5 < 30; C5 < 20 | E0 supply | Owner judgement. In the middle band V_pro is screened at k=2, within the E2 cap formula. Below 20, V_pro would hold at most 11 tasks, a thin screen with low selection power |
| ≥ 120 TB-Pro survivors | P-M2 | Simulation: 120 − 15 dev = 105 E0 tasks gives an expected C5 of about 32 and P(C5 < 20) below 0.01, if TB-Pro difficulty resembles TB2's (unverified) |
| V_pro = round(0.6 × C), caps 25 and 15 | P-M2 | Owner judgement: about 60% of contested tasks screen edits and 40% choose the final version. At C = 40 it gives 24 and 15, with one task to A_pro |
| 15-task dev slice; 50-task diagnosis set | P-M2, E-P0, E1, E2 | Owner judgement. 15 tasks × 2 runs gives the 30 trials per configuration that the timeout rule uses. The 50-task diagnosis set costs 50 episodes per round, 300 per loop |
| 20% disk headroom; 5 engineer-day adapter cap | P-M2 | Convention (disk); owner judgement (schedule) |
| ≤ 1 AgentTimeoutError in 30 trials | E-P0 | Owner judgement |
| Judge AUROC ≥ 0.6 | E0-JUDGE | Owner judgement (0.5 is chance) |
| r ≥ 150 episodes per GPU-day; median episode ≤ 600 s | G0 throughput | Arithmetic: 150 is the low edge of the ±30% throughput band (149). 600 s per episode is 144 episodes per day at concurrency 1, about the same edge |
| t-test size > 6% at nominal 5% | E0-SIM | Owner judgement |
| P(chosen worse than S0) ≤ 10% | E2 | Owner judgement. The simulated value is 3.5% (4.1% of loops below 0 in the between-loop simulation) |
| MCU residual ±3%, CI ±5%, ≥ 40 episodes | MCU gate | Owner judgement |
| Fire rate ≥ 6 of 40 | E4b pilot | Owner judgement: below 15%, the arm would differ from S\*1 on too few trials to measure |
| ≥ 3 of 20 solved, ≤ 10% format errors | E-T1lite pilot | Owner judgement |
| B1 mean attempt cap 2.3; at most 3 attempts | E3-B1 | Owner judgement. 2.3 is a planning estimate of attempts per B1 run, carried from an earlier methodology review; it was not simulated. The 3-attempt maximum comes from the design review's repair of B1 |
| Caps 10,500 and 12,500 episodes | Cost section | Owner judgement, round values. 10,500 leaves 847 episodes (about 9% of the core) for the named contingency uses. 12,500 leaves 2,847 above the core, which fits enforce-only, T1-lite and B5 together (2,809) only if little contingency is spent |
| 0.9 in Cap = 0.9 × r × D_rem; 1.2 in the B5 gate | G0 rule, E-B5 | Owner judgement: safety margins of 10% and 20% against reruns, idle time and cost overruns. Neither was derived |

---

## Phase 0 (TB-Pro only; no model touches TB2)

### P-M2 TB-Pro route pilot

- **Research question.** Supports RQ1 and RQ2 by fixing where adaptation happens and what is held out.
- **Question.** Can TB-Pro supply enough clean, deduplicated, runnable tasks to adapt on, so that all 89 TB2 tasks can be held out?
- **Why.** In little-coder's public TB2 run, 54 of 89 tasks were never solved, 28 were contested and 7 were always solved. The committed held-out split H37 has only 11 contested tasks, and all 9 known sibling pairs straddle it. Holding out all 89 tasks about triples the informative held-out tasks and removes the sibling leak.
- **Hypothesis.** Not a hypothesis test. It is a route check with a go/no-go rule.
- **Design.** CPU only, in Docker under a CPU and RAM limit. Four steps:
  1. **Build census.** Build every TB-Pro image once and record the sha256 digests in `pins.lock`. TB-Pro ships no prebuilt images, so all are built locally. Provisional resource filter: drop tasks asking for more than 4 CPUs or more than 8192 MB. The final filter, applied after the slot count is pinned and before E0, is per-task CPU and RAM ≤ host budget / pinned concurrency. Measure the disk footprint of the TB2-89 images (pulled by digest) plus the survivors.
  2. **Dedup.** Embed every TB-Pro and TB2 instruction with one pinned open embedding model. The owner reviews the 3 nearest TB2 tasks for every TB-Pro task, and removes any TB-Pro task that asks for the same artefact, algorithm or tool chain, with a one-line reason. TB-Pro near-siblings share a group, so no group straddles two pools.
  3. **Harbor and network check (E-NET).** Run Harbor's Oracle agent (no model) on TB-Pro survivors only, under the pinned Harbor version. The agent phase runs in allowlist mode, starting from package hosts (PyPI, Debian and Ubuntu mirrors, npm, crates.io, CRAN). Each failing oracle gets the minimum extra hosts it needs. This yields a pinned, hashed fork of the TB-Pro task directories that changes only the network lines, with the diff and per-task host lists published. Tasks whose oracle still scores 0 are dropped. Adapter work for TB-Pro's older task schema is capped at 5 engineer-days. There is no TB2 Oracle run.
  4. **Licence.** A LICENSE file in the GitHub repository, or written confirmation from the authors that Apache-2.0 covers the tasks. Today the licence appears only in the Hugging Face metadata.
- **Then.** Set aside a 15-task dev slice. E0 runs on every other survivor.
- **Pools (sized after E0).** C is the contested count from E0: C3, or C5 after a top-up. V_pro = round(0.6 × C) capped at 25. V2_pro = C − V_pro, capped at 15. Excess contested tasks and all other survivors go to A_pro. The per-round diagnosis set is a fixed stratified 50-task sample of A_pro, seed 20261015.
- **Pre-registered primary analysis.** None. Outputs: the per-task routing table (task id, source, pool, group, image digest, drop or dedup reason).
- **Secondary.** Dedup removal list, resource and disk census, host lists per task.
- **Cost.** 0 GPU episodes. About 200 CPU-only Oracle trials. Engineering 1 to 1.5 weeks (unverified estimate), plus 2 to 3 days for the allowlist fork (unverified estimate).
- **Dependencies.** None. Runs in parallel with G-INFRA.
- **Go/no-go.** GO for the TB-Pro route if all hold: (i) licence confirmed; (ii) at least 120 TB-Pro tasks survive the build census, resource filter, dedup and Oracle check (before removing the dev slice); (iii) Harbor runs the version-1.0 tasks within the 5-day adapter cap; (iv) the measured disk footprint fits the granted disk with at least 20% headroom, or else build-run-prune pinned by digest is adopted and logged. A failure on (i) to (iii) is a route failure and triggers [E-RESPLIT](#e-resplit-fallback-tb2-re-split).
- **Survivor floor (estimate).** With 120 survivors, 105 tasks enter E0. If TB-Pro difficulty resembles TB2's (unverified), a task is contested at k=5 with probability 0.308. Then the expected C5 is about 32, P(C5 ≥ 30) is about 0.7 and P(C5 < 20) is below 0.01.
- **Risks.** TB-Pro is a different source, so RQ2 becomes "cross-source (TB-Pro to TB2)". Some TB-Pro tasks may be related to TB2 tasks without being copies; dedup is by owner review. TB-Pro's difficulty is unknown. TB-Pro and the Qwen models share a provider, which could inflate calibration scores; the memorisation probe in E0 reports this.
- **Paper slot.** A1 (TB-Pro routing table); Table 7 (pools); A3 (allowlist fork diff and per-task host lists); A7 (dedup removal list).
- **Status.** Preflight underway as of 2026-10-30; the custom Alibaba base-image registry is unreachable from Rohan, so builds and Oracle checks have not run. See [`P-M2-preflight-2026-10-30.md`](experiments/P-M2-preflight-2026-10-30.md). Replacing the committed split is **to confirm with Prof. Abdelrazek** (Q3; see [Open questions](#open-questions-for-prof-abdelrazek)).
- **Meeting points.** 2.

### E-P0 Bring-up and throughput sweep

- **Research question.** Infrastructure for all RQs.
- **Question.** Which serving configuration gives the most episodes per GPU-day without memory errors or extra timeouts, and what are the cost coefficients?
- **Hypothesis.** Not a hypothesis test.
- **Design.**
  - On the granted GPU, inside Docker. Pull TB2 images by digest (ledgered; no TB2 trial).
  - **Fit-gated sweep.** List the configurations that fit measured free VRAM with at least 1 GiB headroom: slot count in {1, 2, 4}, per-slot context at least the pinned context, KV cache f16 or q8_0, MoE layers offloaded 0 to k. Sweep at most 3 of them on the 15-task dev slice × 2 runs (30 trials each).
  - Pin the highest-throughput configuration that fits and has at most 1 AgentTimeoutError in 30 trials (or an upper 95% bound ≤ 10%). If none qualifies, pin one slot and escalate before E0.
  - **A/A determinism run (E0-AA).** 60 episodes of S0 on the dev slice, to measure the correlation rho between paired runs that share a seed. No variance reduction from shared seeds is claimed unless rho is measured.
  - **Memory facts used (estimates, GiB throughout).** The Q4_K_M weights are 20.61 GiB. f16 KV needs about 20 KiB per token, about 1.25 GiB per 64k slot. Estimated GPU memory is about 23.4 GiB for one 64k slot and 24.7 GiB for two, in f16. On a 24 GiB card, one f16 slot leaves about 0.6 GiB and fails the 1 GiB headroom rule. So on 24 GiB even one slot needs q8_0 KV (about half the KV memory, so about 22.8 GiB in all) or a partial MoE offload, at a throughput cost that the sweep measures. f16 KV, or two or more slots, need 32 GiB or more unless part of the model is offloaded.
- **Outputs.** Rate r, MCU coefficients a and b (least squares of per-call time on token counts), k_occ (model-busy seconds per GPU wall-second, used to turn MCU into dollars), reasoning budget per call (p95), per-slot context (p99 of TB-Pro context at 60 steps, rounded up to a multiple of 16k, ceiling 96k), KV type. All go into `pins.lock`.
- **Pre-registered primary analysis.** None.
- **Secondary.** Episode time by outcome; within-task outcome variance against p(1 − p), as an independence check.
- **Cost.** Sweep ≤ 3 × 15 × 2 = 90, plus A/A 60, = 150 episodes. 150 / 213.5 = 0.70 GPU-days.
- **Dependencies.** G-INFRA, P-M2 (dev slice).
- **Go/no-go.** As in the sweep rule above.
- **Risks.** Continuous batching at more than one slot makes per-call times overlap; k_occ corrects dollars, and matching is unaffected because all arms use the same coefficients. A non-dedicated host would make throughput and wall-clock unreliable; they are then re-measured and flagged.
- **Paper slot.** A2 (throughput by configuration, rho); A3 (`pins.lock`, KV and context pins, timeout rates); A4 (MCU coefficients a, b and k_occ); Table 7 (run settings).
- **Status.** planned.
- **Meeting points.** 6 (local serving on one GPU), 1 (dollars per task need MCU and k_occ).

### E1 B1 smoke test

- **Research question.** RQ1 (baseline validity).
- **Question.** Does the repaired reflection-retry baseline run end to end, and does its MCU estimate validate?
- **Hypothesis.** Not a hypothesis test.
- **Design.** B1 on the 15-task dev slice × 2 runs with an attempt cap of 2. The B2 smoke test reuses E-P0 S0 trajectories at 0 episodes. The earlier 90-episode sampling choice is dropped, because sampling is pinned in advance.
- **Pre-registered primary analysis.** None.
- **Secondary.** B1 contributes at least 40 episodes to the MCU residual check (see E3). With fewer, B1's MCU is reported as "unvalidated".
- **Cost.** 15 × 2 × cap 2 = hard cap 60 episode-equivalents. 60 / 213.5 = 0.28 GPU-days.
- **Dependencies.** G-INFRA, baseline unit tests: B1 retries when the judge says fail; B2 can select an attempt other than 0; the request carries temperature, top_p, top_k and seed; judge calls are charged to the right arm; the judge cannot read a `tests/` path; S0 makes no in-run judge call.
- **Go/no-go.** None beyond the smoke run completing.
- **Risks.** At the expected first-attempt failure rate the 40-episode floor is usually reached, but not guaranteed.
- **Paper slot.** A4 (B1 MCU residual); A6 (baseline details).
- **Status.** planned.
- **Meeting points.** 1.

### E0 Calibration on TB-Pro

- **Research question.** Supports all RQs: model fitness and pool sizes.
- **Question.** Is the primary model in a usable difficulty range on TB-Pro, and does TB-Pro give enough contested tasks to select edits on?
- **Hypothesis.** Not a hypothesis test. It is a gate (G0) with four separate checks.
- **Design.** S0 ×3 on every surviving TB-Pro task outside the dev slice, with Qwen3.6-35B-A3B Q4_K_M. If C3 < 40, two more S0 runs on every non-contested task (top-up, from contingency).
- **Gate G0.**

  | Check | Rule |
  |---|---|
  | Fitness | TB-Pro pass rate over E0 trials, with a task-bootstrap CI. Fails if the upper bound is below 12%, the lower bound above 45%, or infrastructure errors (not agent failures) exceed 5% of trials |
  | Supply | C3 ≥ 40: size pools as in P-M2. Else top up and count C5 (1 to 4 successes over all runs). C5 ≥ 30: pools as in P-M2. 20 ≤ C5 < 30: pools as in P-M2 with V_pro screened at k=2. C5 < 20: fitness failure. Supply never triggers a TB2 re-split |
  | Throughput | If r < 150 episodes per GPU-day or the median episode exceeds 600 s, apply the cut order in the [cost section](#cost-table). Never switch the model for speed |
  | Memorisation (E0-MEM) | Ask the model to complete the instruction from the task name on 20 TB-Pro tasks, and report |

- **Starting-score rule.** The recorded rule (a 20 to 40% starting score on TB2, fallback if none reaches about 20%) is kept and checked on public TB2 figures only. Qwen3.6-35B-A3B solved 106 of 445 trials (23.8%) in little-coder's run, so it passes. The TB-Pro gate is a supplement to the recorded rule, and he is told so. The two bands differ on purpose: the recorded band is in TB2 terms and cannot be mapped to TB-Pro without running TB2, which would break the hold-out, so the TB-Pro band is wider and CI-based (see [Thresholds](#thresholds-and-where-they-come-from)). A model must pass both: the recorded rule on public TB2 figures, then G0 on TB-Pro. Where the public figures are ambiguous, as for fallback 1 (40.5% and 18.0%), G0 decides and the ambiguity is logged.
- **Fallback models (E0-FB).** On a fitness failure the next local model runs E-P0 and E0 again, within ≤ 1,150 episodes each (bring-up ≤ 150 + E0 ≤ 600 + top-up ≤ 400). Fallback episodes are deducted from the available GPU-days before the G0 rule is applied. At most 2 fallbacks on a 24 GiB GPU and 3 on 32 GiB or more. Default order, **to confirm with Prof. Abdelrazek** (Q6):

  | Order | Model | Public TB2 figure | Note |
  |---|---|---|---|
  | 1 | Qwen3.5-35B-A3B Q4_K_M | 40.5% (vendor card); 18.0% with Self-Harness's initial harness on a 64-task subset | Ambiguous, logged |
  | 2 | TMax-9B Q4_K_M ([allenai/tmax-9b](https://huggingface.co/allenai/tmax-9b), Apache-2.0, 5.63 GB file) | 27.2 ± 1.5 (vendor, own harness) | Not in the original candidate list |
  | 3 | Nemotron-Terminal-32B Q4_K_M | n/a here | Only on 32 GiB or more: about 27.9 GiB with one 32k slot in f16 KV |
  | Last | GPT-5-mini (API) | n/a here | Only by Prof. Abdelrazek's decision |

- **Zero-episode analyses on E0 data.**
  - **E0-JUDGE.** The same-model judge scores each of the about 600 E0 trajectories. AUROC (area under the ROC curve) ≥ 0.6 makes the judge the primary BoN selector. Below 0.6, the primary selector is "agent-written tests passed, ties random", the judge becomes a sensitivity analysis, and the paper says a realistic selector is weak for this model.
  - **E0-SIM.** Fit a beta-binomial to E0 rates with the unbiased within-task variance k/(k − 1) p(1 − p), and re-state the MDE for the abstract. Simulate the size of the paired t-test twice: on E0-fitted rates and on little-coder's public per-task TB2 rates (third-party data; no TB2 contact by us). If size exceeds 6% at nominal 5% in either, the sign-flip test becomes primary in E3.
  - **E0-SIM2.** Re-simulate the E2 selection rule on the actual V_pro and V2_pro tasks (see E2 go/no-go), test the cost-aware tie-break, and test per-test partial credit (E-N2).
  - **Model-choice table.** Phase-0 table in [SMALL_MODELS.md](SMALL_MODELS.md), with an AA-style composite column (in the style of the Artificial Analysis Intelligence Index) from published scores plus the dev slice. It never uses TB2 runs. It is a named result only under reading (b) of point 4.
- **Pre-registered primary analysis.** The G0 rules above.
- **Cost.** S0 ×3 on every survivor outside the dev slice, capped at 600 episodes: 600 / 213.5 = 2.81 GPU-days. Top-up ≤ 400 (1.87 GPU-days) from contingency, not in the core total. Each fallback ≤ 1,150 (5.39 GPU-days), deducted from the available days, not in the total.
- **Dependencies.** P-M2, E-P0.
- **Go/no-go.** GO with the primary model if fitness passes and C5 ≥ 20 (C3 ≥ 40 needs no top-up). Otherwise the next fallback. If no local model passes, the default is to keep the best local model with a smaller contested pool (**to confirm with Prof. Abdelrazek**, Q6).
- **Risks.** A thin contested pool (12 to 18 tasks at k=2) gives low selection power and an S\* close to S0. This is accepted as the expected band, not a reason to switch model. The 12% and 45% thresholds cannot separate nearby rates precisely.
- **Paper slot.** A2 (pass rate with CI, C3 and C5, infrastructure error rate, throughput by configuration, rho, model-choice table); Table 7 (pools); Figure A1 (TB-Pro difficulty and contested histogram); A7 (memorisation probe); A6 (judge AUROC); A5 (E0-SIM, E0-SIM2).
- **Status.** planned (E0-FB optional, only on a fitness failure).
- **Meeting points.** 6, 2.

---

## Adaptation (TB-Pro only)

### E2 Adaptation loops

- **Research question.** RQ1 (produces S\*1, S\*2 and B4).
- **Question.** What strategy does diagnosis-driven adaptation reach on TB-Pro, and what do random edits reach under the same rule and budget?
- **Hypothesis.** E2 chooses strategies; it does not test them. RQ1 is tested in E3 on untouched tasks, so noise in selection does not bias the held-out comparison. Planning simulation (estimate; see [Planning simulation model](#planning-simulation-model)): under N(0, 0.3²) edit effects on the logit scale, the chosen version gains about 0.82 logit (about 6.6 pp on TB2), and about 3.5% of loops end worse than S0. A second simulation of the same rule, summarised in pp per loop, gives a between-loop mean gain of 6.7 pp (SD 4.7 pp), with 4.1% of loops below 0. The two are different summaries, not a conflict. Under a pure null the rule accepts about 4.4 edits per loop; that is a count of edits, not a harm rate.
- **Design.** Three loops: S\*1 (seed 1), S\*2 (seed 2) and B4 (random edits). B5, if admitted, uses the same rule. All use the same hybrid rule with R = 6 fixed rounds, no early stop.
  1. Run S_r once on the fixed 50-task A_pro diagnosis set.
  2. The proposer emits K = 4 candidates of at most 2 edit operations each. Each must pass the lint. The paper-1 edit space excludes rollback values, rollback fields and `switch_to`.
  3. Run the parent S_r fresh and the 4 candidates once each on V_pro (≤ 25 contested tasks), with shared per-(task, run) seeds. rho = 0 is assumed in every calibration.
  4. Statistic: the integer net count of tasks solved by the candidate minus the parent. Accept the best candidate if it is at least +1 task. Ties go to the lower mean MCU, then the earlier version.
  5. After round 6, run all 7 versions (S0 to S6) ×3 on V2_pro (≤ 15 contested tasks, disjoint by group from A_pro and V_pro). S\* is the version with the most net V2 successes; ties go to the earlier version.
  - A cost-aware variant (lowest mean V2 MCU within 1 net task of the best) replaces this choice only if the pre-Stage-1 simulation shows it loses less than 10% of expected gain.
  - The diagnoser and proposer use the same local model as the agent.
- **Seeds.** Loop seeds 1 and 2 for S\*1 and S\*2. The diagnosis sample uses seed 20261015.
- **Pre-registered primary analysis.** None in E2. Pre-registered valid outcomes include "few or no accepted edits" and "S\* = S0".
- **Secondary.** Adaptation trajectory (V2 score per version, with CIs), edit log with strategy hash, edits, V_pro outcomes and MCU. V_pro deltas are screening data. They are never used as effect sizes for attribution, and the chosen version's V2 score is not a gain estimate (winner's curse). Between-seed difference.
- **Cost.** Per loop: 6 × (50 + 5 × 25 × 1) + 7 × 15 × 3 = 1,050 + 315 = 1,365 episodes = 6.39 GPU-days. Three loops: 4,095 episodes = 19.18 GPU-days. Cap per loop by formula: 6 × (|A_diag| + 5 × |V_pro| × k_screen) + 7 × |V2_pro| × k_V2 ≤ 1,575. If the k=2 screen and a V2 k=5 escalation would both apply, V_pro shrinks until the formula holds. Diagnosis and proposal calls are charged to each arm's one-time adaptation cost, outside the episode count.
- **Dependencies.** E0 (pools), G1, CODE-FIX, LINT-PILOT, PREREG-1.
- **Go/no-go.** Before Stage 1 (0 episodes): proceed if the E0-fitted simulation gives P(chosen worse than S0) ≤ 10% under N(0, 0.3²) at the actual pool sizes. Otherwise raise V2_pro to k=5 within the cap formula and re-check. If it still exceeds 10%, proceed with V2 at k=5 and flag the harm rate in the pre-registration.
- **Risks.** The rule is lenient: under a pure null it accepts about 4.4 edits per loop. The edit log will look like progress while being mostly noise, and neutral edits can raise S\*'s per-task MCU. The stricter alternatives tested in simulation stalled after about 2 rounds with little gain, so they were not adopted. One loop is a high-variance draw; this is why two seeds are core. R = 8 rounds was not adopted (no simulated gain, +440 episodes per loop). Variance-focused validation pools follow Task-CoEvolve: Efficient Harness Optimization via Adaptive Validation Task Selection ([Miyai et al., arXiv 2608.20169, Aug 2026](https://arxiv.org/abs/2608.20169)).
- **Paper slot.** Figure 2 (adaptation trajectory for S\*1, S\*2, B4); A12 (edit log); A5 (selection-rule simulation and rho).
- **Status.** planned.
- **Meeting points.** 3.

---

## Final pre-registered run (TB2-89)

Everything in this section runs once, after the Stage-2 tag. Before Stage 2 the only TB2 contact is image pulls by digest, recorded in the ledger.

### E3 Confirmatory run on TB2-89

- **Research question.** RQ1, and RQ2 scoped as cross-source held-out generalisation from TB-Pro to TB2.
- **Question.** On 89 tasks it never saw, does the adapted strategy beat the fixed strategy, random edits, reflection-retry and best-of-N, with the last two at matched per-task compute?
- **Hypotheses.** Estimand: the equal-weight mean over the 89 tasks of p(S\*) − p(B), in pp. Fixed-sequence gatekeeping at alpha 0.05: a later hypothesis is tested only if all earlier ones are rejected **in favour of S\*** (estimate > 0). A rejection with S\* behind stops the sequence.

  | Hypothesis | Alternative | Null (H0) |
  |---|---|---|
  | H1 | S\* ≠ S0 | S\* − S0 = 0 |
  | H2 | S\* ≠ B4 (worded about the realised strategies) | S\* − B4 = 0 |
  | H3 | S\* ≠ B1 at matched per-task MCU | S\* − B1 = 0 |
  | H4 | S\* ≠ pooled BoN at matched per-task MCU | S\* − BoN = 0 |

  "Beats" is claimed only for a rejected hypothesis whose estimate is positive and whose CI excludes 0. Every estimate and CI is reported wherever the sequence stops.
- **Design.**

  | Arm | Runs per task | Episodes | Note |
  |---|---|---|---|
  | S0 | 10 | 890 | Also the pool for BoN |
  | S\*1 | 5 | 445 | |
  | S\*2 | 5 | 445 | S\* = per-task average of S\*1 and S\*2 |
  | B4 | 5 | 445 | |
  | B1 | 5 | ≤ 1,024 | Attempt caps randomised, see below |
  | BoN | 0 new | 0 | Computed from the S0 pool |
  | **Total** | | **≤ 3,249** | |

  - **B1 (E3-B1).** Reflection-retry inside one Harbor trial. It retries when the in-run judge says fail or an agent-written test fails, never on hidden tests. At most 3 attempts, with no environment reset between them. Step and token budgets apply per attempt. The attempt cap is drawn per (task, run) from {1, 2, 3}, with the mixture fixed at Stage 2 to match S\*'s TB-Pro per-task MCU and a mean cap ≤ 2.3. The seeded draw makes the sum of caps ≤ 1,024 exactly (89 × 5 × 2.3 = 1,023.5, rounded up). After cut 3 it is 614 (89 × 3 × 2.3 = 614.1). Sources of 2.3 and of the 3-attempt maximum are in [Thresholds](#thresholds-and-where-they-come-from). If matching needs a mean cap above 2.3, B1 is flagged under-matched. B1's timeout rate is reported separately.
  - **BoN (E3-BoN).** Computed exactly from the S0 pool of P = 10 runs over all subsets, for N = 1 to 5 and N = P. The judge scores each S0 trajectory after the trial, from the instruction, the trajectory and agent-test outputs. It never sees `tests/`. Its calls are charged to BoN rows only. Ties are broken uniformly at random, analytically. BoN@N is charged N episodes plus N judge calls per task. Matching: N\* = S\* mean MCU per task / (S0 mean MCU per episode + judge MCU per trajectory), with q fixed at Stage 2 from TB-Pro V2_pro runs. A non-integer N\* = n + q is matched as (1 − q) × BoN@n + q × BoN@(n + 1). If N\* > P, BoN@P is reported and flagged under-matched. Oracle pass@N (unbiased estimator) is plotted dashed, as a ceiling only.
  - **Seeds.** Logged per-request seeds; E4b reuses S\*1's seeds for runs 1 to 3.
  - **Leaderboard comparison (E3-LB).** No separate leaderboard-protocol run. S0 trials are censored at 1× the task timeout using the logged agent-execution time, and reported as approximately leaderboard-comparable, a slight lower bound. If Phase-0 trial code shows censoring is invalid, a 1× S0 run of 89 × 2 = 178 episodes is charged to contingency.
  - **Reference comparison (E3-REF).** One fixed figure: little-coder's 100 of 410 trials (24.39%, errored trials counted as failures) on the 82 TB2 tasks unchanged between its task commit `69671fb` and our pin `2fd12b8`. It is compared with our S0 arm descriptively. Confounds listed in the Table 3 footnote: 7 tasks changed, mixed agent versions after a resume, laptop MoE offload, wall-clock 1× timeouts against our step and token budgets, a different harness and sampling.
  - **Leak audit (E3-AUDIT).** TB2 runs under its upstream network setting, with per-trial SNI (TLS server name) and DNS logging and a grep of commands and observations for the canary GUID and for benchmark and solution strings. Flagged trials count as failures in the primary analysis and are excluded in a sensitivity analysis. Flag rates are reported per arm.
- **Pre-registered primary analysis.** Paired t-test on the 89 per-task mean differences, two-sided, alpha 0.05, in the fixed sequence above. The unit of analysis is the task. McNemar's test is dropped; on majority votes it has an MDE of about 9.7 pp on TB2-89 ×5, against 5.8 pp for the task-level t.
- **Sensitivity.** Paired sign-flip permutation (100,000 flips). GLMM (generalised linear mixed model) pass ~ arm + (1 + arm | task). Matched compute from the realised TB2 MCU ratio. Flagged trials excluded.
- **Planning MDEs (estimates, re-stated after E0-SIM).**

  | Contrast | MDE |
  |---|---|
  | S\* (10 runs) vs S0 ×10 | about 4.5 pp |
  | S\* (10 runs) vs a ×5 arm (H2 against B4 ×5, H3 against B1 ×5) | about 5.2 pp (interpolated between the rows above and below, not simulated) |
  | k=5 arms (for example S\*1 vs B4) | 5.8 to 5.9 pp |
  | S\* (10 runs) vs B1 ×3 (after cut 3) | about 6.1 pp |
  | Committed split H37 ×5, for comparison | about 9.5 pp |

  Except for the interpolated row, these are simulated with the [planning simulation model](#planning-simulation-model) (logit-shift effects, task heterogeneity SD 0.5, base rates from little-coder's public counts). The tau² = 0.008 cross-check and its source are described there.
- **Chance of success (planning estimates).**

  | Outcome | Estimate | Basis |
  |---|---|---|
  | H1 rejected with S\* ahead | about 0.8 (rough) | The E2 simulation's gain per loop (mean 6.7 pp, SD 4.7 pp between loops, so about 3.3 pp for the two-seed average) combined with the simulated power curve for 10 vs 10 runs. Not simulated end to end |
  | A single loop's true gain below the 4.5 pp MDE | about 35% | E2 simulation |
  | A single loop's true gain below 0 | 4.1% | E2 between-loop simulation |
  | H1 and H2 both rejected | not estimated | The model draws diagnosed and random edits from the same N(0, 0.3²), so it predicts no S\* − B4 gap. A rate needs an assumed advantage of diagnosis over random edits, which E0-SIM2 sets before Stage 1 |
  | H1 to H3, H1 to H4 | not estimated; expected low | No planning model of B1's or BoN's gain exists. See Risks |
  | S\* = S0 | not estimated | The simulation reports P(chosen version worse than S0), 3.5%, not P(chosen version is S0). E0-SIM2 adds it |

  All rest on the assumed N(0, 0.3²) edit effects. E0-SIM and E0-SIM2 re-state them before Stage 1, and the pre-registration quotes the re-stated values.
- **Secondary metrics.** Point-1 cost table (E3-COST, below). Per-category results. Between-seed SD. Pass rate against MCU per task (frontier figure, with BoN and B1 curves). Per-task difference distribution. The 89-row per-task pass/fail table. All exploratory, with no p-values in the abstract.
- **Point-1 cost table (E3-COST, Table 4).** One cost function, `episode_cost()` in `baselines/cost.py`, used everywhere.
  - Rows: S0, B1 (each cap), BoN (N = 1 to 5 and P), B4, S\* (seed average and each seed), library + selector (E4-SW), B5 if run, the E-T2 cells.
  - Columns: mean, median, IQR (interquartile range) and CI of dollars per task at two frozen named rates (electricity; cloud-GPU-equivalent), as (MCU-hours / k_occ) × rate. Wall-clock labelled with GPU model, slot count and concurrency. Generated tokens including reasoning, prompt tokens, cached tokens, MCU, and pass rate per dollar.
  - Every column is split by outcome (solved or failed) and by S0 task class (never, contested, always). MCU never appears without dollars next to it.
- **MCU validation gate (before Stage 2, TB-Pro data only).** An arm passes if its mean episode residual is within ±3% and the CI of that mean is within ±5%, with at least 40 TB-Pro episodes. If a validated arm fails, add a context-length term and refit. If it still fails, match on processed tokens, with MCU kept as a sensitivity analysis. Logged either way.
- **Cost.** ≤ 3,249 episodes. 3,249 / 213.5 = 15.22 GPU-days. Judge calls (about 890 on TB2 plus about 600 on E0) are model calls, not episodes, and come from the contingency line.
- **Dependencies.** E2, E0-JUDGE, E0-SIM, MCU gate, LEDGER, PREREG-2.
- **Go/no-go.** None after Stage 2; the run is pre-registered. Before Stage 2, any failed gate is resolved or the pre-registration is amended.
- **Risks.** The true gaps between S\* and B1 or BoN may be at or below the MDE, so H3 and H4 may rarely reject. Non-rejection is reported as an estimate with its CI, never as "no difference". Per-task matching treats the one-time adaptation cost as free; the payback T\* in E11 reports that cost, and this choice is open to the reading of point 1 as total project cost. A same-model judge may be near chance; the AUROC gate and the dashed oracle make that visible. The TB2 internet setting leaves a leak channel that grep audits cannot fully close.
- **Paper slot.** Table 3 (H1 to H4 estimates and CIs, MDE in the abstract, between-seed row, E3-REF footnote); Table 4 (cost per task); Figure 3 (pass rate against compute, with BoN and B1 curves); Figure 4 (per-task differences and per-seed estimates); A1 (89-row per-task table plus routing table); A6 (B1 cap mixture and timeout rate); Figure A2 (BoN judge against oracle); A7 (TB2 flag rates).
- **Status.** planned.
- **Meeting points.** 1 (Table 4), 2 (Appendix A1, per-task results), 3 (S\* against all baselines).

### E-ATTR Leave-one-out attribution

- **Research question.** RQ4, amended to "which strategy dimensions account for the gains". Rollback is no longer part of RQ4.
- **Question.** Which changed dimension groups of S\*1 carry its gain, and how much comes from lessons and notes?
- **Hypothesis.** Ha: reverting a changed group changes the pass rate. H0: no change. Exploratory, outside the gatekeeping chain.
- **Design.**
  - **Task set (40 TB2 tasks), fixed at Stage 1 from public third-party data only:** the 35 tasks with at least one success in little-coder's run, plus 5 of its 54 never-solved tasks drawn with seed 20261015, stratified by category. This avoids selecting on our own TB2 outcomes.
  - **Arms.** S\*1 with one changed dimension group reverted to S0, for up to 3 groups: all groups if there are 3 or fewer, otherwise the 3 with the most accepted edits in S\*1's lineage (ties to the earliest acceptance). Plus one arm with lessons_k = 0 and notes off.
  - Each arm 40 tasks × 3 runs, paired with S\*1 ×5 on the same tasks.
  - If S\*1 = S0, E-ATTR does not run and its episodes return to contingency.
- **Pre-registered primary analysis.** Paired per-task differences with task-bootstrap CIs; no confirmatory test.
- **Secondary.** Mechanism examples linked to provenance tags (for example, a probe that found a missing package).
- **Cost.** ≤ 4 arms × 40 × 3 = 480 episodes, 480 / 213.5 = 2.25 GPU-days. After cut 1: 2 arms (top group plus lessons/notes-off) = 240 episodes, 1.12 GPU-days.
- **Dependencies.** E2 (S\*1), E3 (S\*1 runs), G1.
- **Go/no-go.** Runs only if S\*1 ≠ S0. The lessons/notes-off arm is never cut.
- **Why core despite its power.** It is paper 1's only evidence for RQ4, and its lessons/notes-off arm bounds the memorisation channel, so that arm is never cut. The two group arms beyond the top group are the first cut in the cut order (cut 1).
- **Risks.** MDE about 12 pp (rough: the simulated 37 tasks × 3 vs 3 runs case, 12.0 pp; with 40 tasks and 3 vs 5 runs it should be a little smaller), so per-group effects of a few pp cannot be confirmed. Groups interact.
- **Paper slot.** Figure 6 (attribution by dimension group); Table 5 rows (each arm, lessons/notes-off); lessons/notes-off row in A7.
- **Status.** planned.
- **Meeting points.** 3.

### E-T2 Enforced versus advised

- **Research question.** RQ4 (mechanism).
- **Question.** Does it matter that strategy fields are enforced in code, or would the same content as prompt advice do as well?
- **Hypothesis.** Three estimands, paired by task, exploratory, in one Holm family with the S\* − B5 contrast:
  - Δ1 = compiled S\*1 minus advised S\*1 (enforcement on top of advice). Ha: Δ1 ≠ 0; H0: Δ1 = 0.
  - Δ2 = advised minus S0 (advice alone). Ha: Δ2 ≠ 0; H0: Δ2 = 0.
  - Δ3 = main effect of enforcement, and the interaction, only with the enforce-only cell.
- **Design.** Cells are (controller, prompt text), built by G1's independent switches:

  | Cell | Controller | Text | Source | Runs per task | Episodes |
  |---|---|---|---|---|---|
  | S0 | S0 | S0 | E3 | 10 | 0 new |
  | S\*1 | S\*1 | S\*1 | E3 | 5 | 0 new |
  | Advised (core) | S0 | S\*1, same render template | new | 5 | 445 |
  | Enforce-only (Tier C rank 2) | S\*1 | S0 | new | 5 | 445 |

  Main model only. All cells use S\*1, paired with S\*1's 5 runs (10 runs in the single-seed branch).
- **Pre-registered primary analysis.** Paired per-task differences with task-bootstrap CIs and Holm adjustment within the family. No p-values in the abstract.
- **Planning MDEs (estimates).** Δ1 about 5.8 pp at 5 vs 5 runs (simulated). After cut 2, about 6.6 pp (rough: between the simulated 89 × 3 and 89 × 5 cases, 7.4 and 5.8 pp). Δ3 main effect about 3.8 pp (rough: a 2×2 main effect averages two contrasts, so it uses about twice the runs of Δ1), which needs the enforce-only cell. Interaction about 8 pp (rough), descriptive.
- **Secondary.** Per-field adherence, pilot first: each enforced field gets an event tag, and text-only fields are scored from transcript actions by a rule fixed before Stage 1. Validated on TB-Pro E0 logs before Stage 2; dropped if validation fails.
- **Cost.** Advised cell 89 × 5 = 445 episodes = 2.08 GPU-days (core). After cut 2: 89 × 3 = 267 = 1.25 GPU-days. Enforce-only 445 = 2.08 GPU-days (Tier C, not in the core total).
- **Dependencies.** G1, E2, E3.
- **Go/no-go.** The advised cell runs only if at least one field that S\*1 changed is compiled with a passing controller test. Otherwise T2 is "not applicable" and its 445 episodes return to contingency. Enforce-only runs only if admitted by the Tier C rule.
- **Risks.** Without the enforce-only cell, Δ1 measures enforcement given advice, and is named so. If few fields compile, the cells differ little. Only fields compiled with a test enter enforcement claims.
- **Paper slot.** Figure 5 (3-cell or 2×2 pass rates with paired CIs, adherence panel if validated); Table 5 rows (Δ1, Δ2, Δ3 if run); the "why typed" section.
- **Status.** Advised cell planned; enforce-only optional (Tier C rank 2).
- **Meeting points.** 3.

### E4-SW Offline strategy switching

- **Research question.** Reading (a) of point 5 (per-task choice of a strategy version).
- **Question.** Is there per-task complementarity among our strategy versions, and can a cheap selector frozen on TB-Pro capture it?
- **Hypothesis.** Ha: cross-fitted VBS − SBS > 0 (headroom exists). H0: headroom = 0. Exploratory.
- **Design.** 0 new episodes; uses the E3 runs.
  - **Library.** {S0, S\*1, S\*2, B4-final}, plus B5-final if run: up to 5 versions. This is a logged change from the plan's estimate of 4 (section 5.4). Single-seed branch: {S0, S\*1, B4-final (, B5)}.
  - **Cross-fitted VBS.** Per task, split each version's runs by run-index parity. Choose the version with the best mean on odd runs, score it on even runs, swap, and average. Ties go to lower mean MCU on the choosing half, then the fixed order S\*1, S\*2, S0, B4, B5. Cross-fitted SBS is computed the same way across tasks. This replaces the plan's hidden-test oracle selector, which is biased upward: with S\* = S0, the naive headroom is about +4.5 pp at k=5 and +3.4 pp at k=10, and cross-fitting removes it. See Bias in Algorithm Portfolio Performance Evaluation (Cameron, Hoos and Leyton-Brown, IJCAI 2016).
  - **Two selectors**, designed only on TB-Pro logs (E0 and the V2_pro runs of each version) and frozen by commit hash at the Stage-2 tag: (1) a rule table from TB-Pro category × difficulty to a version, with back-off to the TB-Pro SBS and a TB2-to-TB-Pro category map fixed before the freeze; (2) one local-model call per TB2 task over the instruction text (fixed prompt, pinned sampling, fixed seed).
  - Each selector is scored by the mean of all runs of its chosen version. Per-task cost = chosen version's mean MCU + selector MCU. Library construction cost includes the B4 loop (and B5's) on top of the adaptation cost.
- **Pre-registered primary analysis.** Headroom = CF-VBS − CF-SBS with a CI. Regret = CF-VBS − selector. Fraction of the gap closed, only if the headroom CI excludes 0; otherwise "no detectable headroom". Negative regret and gap closed above 100% are reported as observed.
- **Secondary.** Library + selector against S\* at matched per-task MCU. If their MCU differs by more than 5%, report the paired difference with the MCU difference, and log the unmatched comparison as a deviation from plan section 5.4. Naive same-run VBS shown, labelled "biased; for illustration".
- **Cost.** 0 episodes, 0 GPU-days. About 89 selector calls on TB2 plus design calls on TB-Pro, in the non-episode line. About 0.5 analysis-day.
- **Dependencies.** E2, E3, PREREG-2 (selector freeze).
- **Go/no-go.** None.
- **Risks.** The library is two seeds of one procedure plus random edits, so headroom may be near 0 because the versions are similar. With about 28 contested tasks the selector is barely estimable. Per-input routing over evolved harnesses on TB2 is published, so this is framed as a measurement. Prior work: Mixture of Self-Improving Branches For Agent Harness Optimization ([Dong et al., arXiv 2609.37834, Sep 2026](https://arxiv.org/abs/2609.37834)) and MemoHarness: Agent Harnesses That Learn from Experience ([Huang et al., arXiv 2607.14159, Jul 2026](https://arxiv.org/abs/2607.14159)).
- **Paper slot.** Figure 8 "Strategy switching: cross-fitted VBS/SBS, selector regret and cost"; A8 (cross-fitted and naive oracle quantities); a routing column in A1.
- **Status.** planned. The reading of point 5 is **to confirm with Prof. Abdelrazek** (Q2). E4-SW is in paper 1 under every answer. The probe-then-choose selector needs new episodes and moves to paper 2 unless he asks for it.
- **Meeting points.** 5, 1 (selector cost per task).

### E4b Mid-task switching reserve

- **Research question.** Reading (b) of point 5 (changing strategy mid-task when stuck).
- **Question.** Does switching to another library version when recovery is exhausted change the pass rate and cost?
- **Hypothesis.** Ha: S\*1 + switch ≠ S\*1. H0: no difference. Exploratory estimate only.
- **Design.** A new value `switch_to:<version>` of `recovery.on_repeated_failure`, behind a flag the proposer cannot emit. The trigger is the compiled recovery event: `recovery.max_retries` exhausted under `recovery.retry_on`, with both frozen in the Stage-1 tag. The switch target is the non-S\*1 library version with the highest TB-Pro V2_pro pass rate.
  - TB-Pro pilot: 20 E0-contested tasks, outside V2_pro where supply allows, × 2 runs = 40 episodes.
  - TB2 arm: S\*1 + switch on TB2-89 × 3 (same seeds as S\*1 runs 1 to 3) = 267 episodes.
- **Pre-registered primary analysis.** S\*1 + switch ×3 against S\*1 ×5, paired by task, with a task-bootstrap CI.
- **Secondary.** Fire rate, pass rate on trials where the switch fired, cost per task.
- **Planning MDE (estimate).** About 6.6 pp (rough: 3 vs 5 runs, between the simulated 89 × 3 and 89 × 5 cases); about 6 pp in the single-seed branch against S\*1 ×10 (rough).
- **Cost.** 40 + 267 = 307 episodes = 1.44 GPU-days. Plus 1 to 2 engineering days, shared with G1.
- **Dependencies.** All three gates: (1) point 5 answered (b) or (c) before the Stage-1 freeze, with the arm and its gate written into the Stage-1 pre-registration; (2) G1 passes with the flag-gated `switch_to` and a unit test; (3) the pilot passes.
- **Go/no-go.** Pilot GO if the switch fires on at least 6 of 40 trials (15%, Wilson 95% CI reported) and infrastructure errors are at most 2 of 40. NO-GO: the TB2 arm is not run, the fire rate goes to the appendix, mid-task switching moves to paper 2 (logged), and the 267 episodes return to contingency. The pilot never touches TB2.
- **Release rule.** If point 5 is answered (a) or not answered by the Stage-1 freeze, the 307 episodes return to contingency and mid-task switching moves to paper 2. The reserve sits outside the cut order until then.
- **Risks.** The contrast is diluted by trials where the switch never fires, so fire rate and conditional pass rate are reported. The code sits on the `compile()` critical path.
- **Paper slot.** Table 3 row (exploratory); fire rate in the appendix.
- **Status.** optional; default paper 2. **To confirm with Prof. Abdelrazek** (Q2).
- **Meeting points.** 5.

### E-PORT Portability check

- **Research question.** Supports the "small models anyone can run" framing (point 6). Not an RQ test.
- **Question.** Does the method run end to end on consumer-class hardware, and what does S0 score there?
- **Hypothesis.** Not a hypothesis test. Descriptive, with no precision or replication claim.
- **Design.** S0 on TB2-89 × 3 on a consumer-class x86-64 machine (at least 8 GB VRAM, 32 GB RAM, Docker). Default if no machine is provided by the Stage-1 freeze: the same runs on the main GPU in an emulated configuration (MoE offload with `--n-cpu-moe`, VRAM capped at 8 GB), stated as emulated in the paper. Optional S\*1 × 2 (178 episodes) on the consumer machine only, never on the main GPU. Its TB2 runs belong to the final pre-registered run. Apple Silicon is out of scope (the task images are amd64 only).
- **Pre-registered primary analysis.** Pass rate with CI, seconds per step and cost per task, reported beside the main S0 arm.
- **Secondary.** Demonstrated minimum spec: the paper states the machine E-PORT actually ran on.
- **Cost.** 89 × 3 = 267 episodes = 1.25 GPU-days on the main GPU (default). If a consumer machine is provided, these leave the main GPU, and the core becomes 9,386 episodes = 43.96 GPU-days.
- **Dependencies.** E-P0 pins; PREREG-2.
- **Go/no-go.** None. Never cut.
- **Risks.** An emulated configuration shows that the configuration works, not that a specific consumer box does, and is labelled so. For context: little-coder's reference run used an 8 GB-VRAM laptop, and Self-Harness served the same model class on four NVIDIA H200 GPUs.
- **Paper slot.** Table 6 portability row.
- **Status.** planned. The machine and GPU-days are **to confirm with Prof. Abdelrazek** (Q5).
- **Meeting points.** 6.

---

## Analyses at zero episodes

### E11 Adaptation efficiency index

- **Research question.** Point 4; RQ1 framing.
- **Question.** How much is adaptation worth per unit of compute?
- **Hypothesis.** Not a test. Estimates with censored CIs.
- **Reading of point 4: to confirm with Prof. Abdelrazek (Q1).** Reading (a): one number for how efficiently the agent improves, after Chollet's skill-acquisition efficiency in On the Measure of Intelligence ([Chollet, arXiv 1911.01547, Nov 2019](https://arxiv.org/abs/1911.01547)). Reading (b): a composite over several benchmarks, like the Artificial Analysis Intelligence Index, for choosing models.
- **Design.** Every variant is computed after the final run, from logs already budgeted. None feeds back into adaptation or selection. Cost unit = the E3 matching unit (MCU if its gate passes, else processed tokens).
  - T = number of held-out tasks (89; 52 under E-RESPLIT). p\* = S\*'s mean pass rate. c_test\* = S\*'s mean MCU per task. A\* = E2 adaptation MCU of the S\* loop (mean of the two loops), including diagnosis and proposal calls; E0 and Phase 0 excluded, with a sensitivity that includes them.
  - g(c) = the S0 pooled BoN frontier over N = 1 to P, pass rate against mean MCU per task, where c(N) includes the judge's MCU. c_eq = the smallest c with g(c) ≥ p\*.
  - **(a1) CER_test** (compute-equivalence ratio) = c_eq / c_test\*: how many S0 best-of-N samples S\* is worth per task. Censored as "> c(P) / c_test\*" when g(P) < p\*, never extrapolated.
  - **(a2) Payback T\*** = A\* / (c_eq − c_test\*), in tasks; "never" if c_eq ≤ c_test\*.
  - **(a3) Amortised CER(T)** = c_eq / (c_test\* + A\*/T), as a curve over T. At T = 89 it is bounded at about 0.6 by construction, because adaptation costs about 15 episodes per held-out task, so it is never a headline.
  - **(a4)** The plan's Δp / C(T), only where C > 0. Here C(T) is cost: the one-time adaptation cost plus T × the extra cost per task over S0 ([TECHNICAL_PLAN.md](TECHNICAL_PLAN.md) section 7.6). **(a5)** Pass per MCU.
  - The same for B1, B4 and B5, with Kendall's tau between method rankings by pass rate, pass per MCU, CER_test and Δp / C.
  - The composite (reading b) never uses TB2 held-out runs; it lives in the Phase-0 model-choice table. A Chollet-weighted variant is computed only if its weights are written into the Stage-1 pre-registration.
- **Pre-registered primary analysis.** Default if no answer by the Stage-1 freeze: reading (a), headline CER_test with T\* as companion; amortised CER(T) and Δp / C in the appendix; composite in the model-choice table. The headline label is frozen at Stage 1.
- **Secondary.** Δp and C are always shown next to any index.
- **Cost.** 0 episodes, 0 GPU-days, about 1 analysis-day.
- **Dependencies.** E2, E3 (S0 ×10 pool, S\*, B1, B4), MCU gate, E0-JUDGE.
- **Go/no-go.** None.
- **Risks.** Any single ratio invites the "bespoke metric" criticism. CER depends on the BoN selector's quality, is censored when the frontier never reaches p\*, and may have a CI spanning an order of magnitude with 11 to 28 contested tasks. This is why Δp and C are always shown and the oracle frontier is drawn as a bound.
- **Paper slot.** Figure 7 "Adaptation efficiency" (CER_test with censored CIs per method, plus the T\* curve); A9 and Figure A5 (variants). Under reading (b), the model-choice table in A2 instead.
- **Status.** planned (reading to confirm).
- **Meeting points.** 4.

### Zero-episode analyses

All use logs already budgeted. All are exploratory.

| ID | What | Data | Paper slot | Points |
|---|---|---|---|---|
| E-N1 | Net pass@k difference S\* − S0, k = 1 to 5 per seed (1 to 10 in the single-seed branch). Never reported as a count of "newly solved tasks": with S\* = S0, the gross count of "unlocked" tasks is about 11 to 12 pp by chance, while the net difference is unbiased | E3 | Figure A4 | 3 |
| E-N2 | Per-test partial credit as a screening statistic. Replaces binary outcomes on V_pro only if, at no higher null acceptance, it raises the simulated chance of choosing the best version. Never on V2_pro or TB2. Runs only if TB-Pro tests write per-test results | TB-Pro E0 and A/A logs | A5 | 3 |
| E-N3 | Cost-of-failure columns: cost per task split by outcome and S0 task class, for every arm | E3 | Table 4 columns | 1 |
| E-N4 | Expressiveness audit: each published edit of Self-Harness (4 retained edits), AHE and MemoHarness mapped onto our schema as compiled, text-only or not expressible | Papers and schema | Table 1, A10, Table 2 column | 3 |
| E-T12 | Failure-taxonomy shift across rounds, plus diagnoser accuracy (Cohen's kappa) on 40 to 60 hand-labelled failed trajectories | TB-Pro E0 and E2 logs, never TB2 | Figure A3 (failure mix), A11 (diagnoser agreement) | 3 |

E-N4 sources: Self-Harness: Harnesses That Improve Themselves ([Zhang et al., arXiv 2606.09498, Jun 2026](https://arxiv.org/abs/2606.09498)); Agentic Harness Engineering: Observability-Driven Automatic Evolution of Coding-Agent Harnesses ([Lin et al., arXiv 2604.25850, Apr 2026](https://arxiv.org/abs/2604.25850)); MemoHarness (above).

---

## Optional add-ons (Tier C)

Tier C items run only from headroom under the absolute cap of 12,500 episodes, in rank order, and only if their own gate passes (see the [cost section](#cost-table)). None is in the core total.

### E-T2 enforce-only cell

See [E-T2](#e-t2-enforced-versus-advised). Rank 2. 445 episodes = 2.08 GPU-days.

### E-T1lite Second-model row

- **Research question.** Secondary transfer: does S\*1, adapted on the main model, help another small model?
- **Question.** On TMax-9B, does S\*1 change the pass rate against S0, with no new adaptation?
- **Hypothesis.** Ha: S\*1 ≠ S0 on TMax-9B. H0: no difference. Exploratory, labelled "secondary transfer".
- **Design.** S0 and S\*1 (from the main model) on TMax-9B Q4_K_M, TB2-89 × 3 each. A 20-episode TB-Pro pilot first (S0, 20 tasks × 1). Framed as "which small models anyone can run". TMax-9B sits outside the 20 to 40% starting band rule, which applies to the main model.
- **Pre-registered primary analysis.** Paired per-task difference with a task-bootstrap CI.
- **Secondary.** Format and tool-call error rates.
- **Cost.** 2 × 89 × 3 = 534 + 20 pilot = 554 episodes = 2.59 GPU-days.
- **Dependencies.** E2, E3, Tier C admission.
- **Go/no-go.** Proceed if the pilot solves at least 3 of 20, the format and tool-call error rate is at most 10%, a check of TMax's released training data finds no TB2 or TB-Pro task overlap, and the 554 episodes fit the Tier C rule. Otherwise paper 2.
- **Risks.** TMax is tuned on its own harness, so the contrast mixes model, strategy fit and harness or format mismatch. Its vendor TB2 scores come from its own harness.
- **Paper slot.** One row in Table 6.
- **Status.** optional (Tier C rank 3).
- **Meeting points.** 6.

### E-B5 Free-form code baseline

- **Research question.** RQ1 framing: does restricting edits to a typed schema cost pass rate against free-form code edits?
- **Question.** With the same proposer, diagnoses, pools and selection rule, how does editing our controller code compare with typed edits?
- **Hypothesis.** Ha: S\* − B5 ≠ 0. H0: S\* − B5 = 0. Estimation only, outside the gatekeeping chain, with a Holm-adjusted CI in the family {S\* − B5, E-T2 Δ1, Δ2, Δ3 if run}.
- **Design.** Free-form edits of our controller code by the same proposer, from the same diagnoses, on the same TB-Pro pools (A15 / V12 / V2 10 under E-RESPLIT), with the E2 rule. Final evaluation on TB2-89 at k=5 (H52 under E-RESPLIT). Comparator: S\* (seed average). Runs only in a per-trial sandbox container whose only network route is the llama.cpp endpoint, killed on timeout, never in the host Harbor process. The outcome-interpretation table E-INTERP is committed before Stage 1; for example, if B5 ≥ S\*, the typed claim retreats to auditability, attribution and seed stability.
- **Pre-registered primary analysis.** S\* − B5 with a Holm-adjusted CI.
- **Secondary.** B5 point on the frontier figure; B5 in the E4-SW library.
- **Cost.** 1,365 adaptation + 445 evaluation = 1,810 episodes = 8.48 GPU-days, plus at most 5 engineering days.
- **Dependencies.** G-INFRA, E0, E2 rule, sandbox.
- **Go/no-go.** Runs only if all hold before the Stage-1 tag: (1) the sandbox is built and passes an escape test within 5 engineering days after G-INFRA; (2) of 10 B5 proposals generated from TB-Pro E0 failure logs, at least 5 apply cleanly and pass the controller unit tests; (3) projected main-GPU use (core + every higher-ranked admitted Tier C item + B5) × 1.2 fits the G0 capacity Cap and the 12,500 cap (1.2 is a safety margin; see [Thresholds](#thresholds-and-where-they-come-from)). Any failure moves B5 to paper 2, and the paper states that it makes no comparison with code-harness evolution.
- **Risks.** B5 against S\* mixes representation with search-space size and the proposer's code-writing skill, so it cannot test "typed beats code". One B5 loop is a single high-variance draw. Ranked last, it may well be cut, and a reviewer who knows the code-harness work will then ask for it. Closest work searches code: Self-Harness edits a Python harness, and Meta-Harness: End-to-End Optimization of Model Harnesses ([Lee et al., arXiv 2603.28052, Mar 2026](https://arxiv.org/abs/2603.28052)) searches harness code.
- **Paper slot.** Table 5 row (S\* − B5, Holm-adjusted); Table 3 extra row; Figure 3 point; A15 (E-INTERP table and sandbox design).
- **Status.** optional (Tier C rank 4). Whether Prof. Abdelrazek wants B5 specifically is an open question (Q8; default: rank 4).
- **Meeting points.** 3.

### E5-DEMO Descriptive second-order loop

- **Research question.** RQ3, descriptive only.
- **Question.** What does one first-order loop look like under a meta-edited adaptation mechanism?
- **Hypothesis.** None. No inferential claim.
- **Design.** M\* = the adaptation mechanism edited by one meta-proposal over the E2 logs of S\*1, S\*2 and B4 (0 episodes). Then one E2-style loop from S0 under M\* on the same TB-Pro pools. Reported as its V2_pro trajectory beside the S\*1 and S\*2 loops (mechanism M0). TB-Pro only, never TB2.
- **Pre-registered primary analysis.** None.
- **Cost.** ≤ 1,365 episodes = 6.39 GPU-days.
- **Dependencies.** E2.
- **Go/no-go.** Runs only if Prof. Abdelrazek says the second-order loop is essential for the internship and chooses this option over more GPU-days. Then it takes Tier C rank 1.
- **Risks.** One loop cannot separate mechanism from loop-seed luck.
- **Paper slot.** Overlay on Figure 2.
- **Status.** optional (only if asked).
- **Meeting points.** None of the six. It serves internship objective 4 (the second-order loop).

### E-RESPLIT Fallback TB2 re-split

- **Research question.** RQ1 and RQ2, only if the TB-Pro route fails.
- **Design.** Re-split TB2 into H52 held out plus A15 / V12 / V2 10, with sibling groups (the 9 known pairs plus review finds), seed 20261015, stratified by category and difficulty. Logged as a deviation from the committed split. S0 ×3 pre-screen on the 37 non-held-out tasks only.
- **Cost.** Replaces the TB-Pro pools; E3-style arms on 52 tasks instead of 89.
- **Go/no-go.** Triggered only by a P-M2 route failure, never by a contested-supply shortfall.
- **Risks.** MDE about 7.6 pp at k=5 (5.8 × sqrt(89/52)), stated in the abstract. Only about 12 contested adaptation tasks among the 37 non-held-out tasks.
- **Status.** optional (fallback only).
- **Meeting points.** 2.

---

## Open questions for Prof. Abdelrazek

These are his decisions. Each default applies only if there is no answer by the Stage-1 freeze, and is logged in the decision log, [DECISIONS.md](DECISIONS.md#3-decision-log) section 3, with the default marked as applied. This is the same list as [DECISIONS.md](DECISIONS.md#1-open-decisions) section 1 (Q1 to Q6, Q8 and plan items 1, 6 and 11), which has the full option texts and holds where they differ.

| Q | Topic | Options | Default | Cards affected |
|---|---|---|---|---|
| [Q1](DECISIONS.md#q1-intelligence-index-meeting-point-4) | Point 4 "intelligence index" | (a) one number, CER_test; (a) two numbers, CER_test + T\*; (b) a composite for model choice, plus AppWorld re-entry if he wants our method scored across benchmarks; (c) something else | (a), CER_test headline with T\* companion | E11, E0 model-choice table, E8 |
| [Q2](DECISIONS.md#q2-strategy-switching-meeting-point-5) | Point 5 "strategy switching" | (a) per-task selector only; (b) mid-task switching; (c) both; (a) plus the probe-based selector | (a) only; mid-task switching to paper 2 | E4-SW, E4b |
| [Q3](DECISIONS.md#q3-task-pools-meeting-point-2) | Replacing the committed split | (i) approve holding out all 89 TB2 tasks and adapting on TB-Pro; (ii) keep the committed split (MDE about 9.5 pp at k=5, sibling leak remains); (iii) use the TB2 re-split directly | (i) | P-M2, E0, E3, E-RESPLIT |
| [Q4](DECISIONS.md#q4-scope-of-paper-1) | Scope | (i) second-order loop (internship objective 4), AppWorld transfer (objective 6) and the rollback sub-question (formerly part of RQ4; no objective of its own) to paper 2; (ii) essential: E5-DEMO; (iii) essential: more GPU-days for a powered design | (i) | E5-DEMO, E8, E9 |
| [Q5](DECISIONS.md#q5-compute-meeting-point-6) | Compute | Dedicated GPU-days D, which GPU (at least 24 GiB, where one slot needs q8_0 KV; 32 GiB or more for f16 KV or concurrency), and whether a consumer-class machine can be provided | E-PORT emulated on the main GPU; plan the full core and halt at G0 if below the floor | All, E-PORT |
| [Q6](DECISIONS.md#q6-fallback-models-meeting-point-6) | Fallback models | Accept or change the order in E0; if no local model passes: API model, best local model, or re-scope | Stated order; best local model if no answer within one week | E0, E0-FB |
| [Q8](DECISIONS.md#q8-a-free-form-code-edit-baseline-informational) | B5 | Promote to the first Tier C slot after any E5-DEMO, or no preference | Tier C rank 4 | E-B5 |
| [Plan item 1](DECISIONS.md#plan-item-1-duration-start-date-hours-per-week-and-supervision-rhythm) | Duration, start, hours, supervision | About 24 weeks part-time, or another length and rhythm | 24-week target; schedule at 20 hours per week | Dates only, no card changes |
| [Plan item 6](DECISIONS.md#plan-item-6-model-for-the-diagnoser-and-proposer) | Model for the diagnoser and proposer | (a) same model only; (b) plus a stronger-model variant | (a) | E2 |
| [Plan item 11](DECISIONS.md#plan-item-11-publication-target-and-authorship) | Venue and authorship | See [PAPER_PLAN.md, section 9](PAPER_PLAN.md#9-candidate-venues) | None | None |

---

## Moved to paper 2 or dropped, and why

### Moved to paper 2

| Item | Why | Re-entry in paper 1 |
|---|---|---|
| E5 second-order loop (RQ3) | The loop is the unit of replication. Detecting a 50% relative change between mechanisms needs about 27 to 32 independent loops per arm: 73,710 to 87,360 episodes, 345 to 409 GPU-days. RQ3 also had no clean task split. Paper 2 redesigns it with loop-level replication and an independent meta-training pool | E5-DEMO, only on request |
| E8 AppWorld transfer | Planned at about 2,500 episodes (about 11.7 GPU-days at the TB2 rate, a proxy). Not needed for paper 1's cross-source RQ2 | Only if point 4 is read as (b) and he wants our method scored across benchmarks: S0 vs S\* on AppWorld test-normal at k=1, costed from the adapter and admitted as Tier C within the 12,500 cap. Paper slot: Appendix A16, descriptive, absent otherwise |
| E9 rollback vs restart (thread T10) | Harbor offers no snapshot or restore, so rollback is files-only through git, which would confuse "rollback" with incomplete state restoration. Rollback values and fields are removed from the paper-1 edit space, with a unit test | None |
| E10 full model ladder (thread T1) | One full rung with its own adaptation run costs about 2,255 episodes (10.56 GPU-days). Paper 2 uses the TMax family (4B, 9B, 27B). Nemotron-Terminal is dropped from the ladder | E-T1lite (one row, no new adaptation) |
| E4b mid-task switching | Default if point 5 is read as (a) or not answered | The E4b reserve, behind its gates |
| Probe-then-choose selector | Needs new episodes | Only if he asks for it |
| T3 cross-model transfer (does S\* help other models?), T14 model × dimension sensitivity map | Need per-model adaptation runs | None |
| T6 diagnosis-noise injection | A causal noise arm needs a full adaptation run per noise level and loop-level replication. Paper 1 makes no causal claim about diagnosis quality; the paper states that S\* vs B4 gives no causal evidence on it | None. T6 is the first paper-2 experiment if the S\* − B4 CI includes 0 |
| N3 part 2 (a "give up" field) | New schema field | None |
| B5, if not run | See E-B5 gate | E-B5 |
| T7 capability assessment | A possible follow-up on capability assessment of strategy versions (paper 2) | None |

### Dropped

| Item | Why |
|---|---|
| B3 prose or playbook adaptation | Leaves paper 1. The question it was meant to answer, whether structure matters, is answered with content held fixed by E-T2, and expressiveness by E-N4. Saves about 1,810 episodes |
| T15 seed variance (a second loop seed) as an add-on | Not dropped as a question: the second seed is now core (S\*2 in E2 and E3) |
| T9 strategy compression, T11 human vs agent edits | Ranked low in the thread review; no budget assigned |
| T16 edit-effect calibration (predicting each edit's effect) as a thread | Folded into the E2 edit log |
| RHAE / ARC-AGI-3 index variant | Dropped from E11 |
| Sampling-choice experiment (90 episodes) | Sampling is pinned in advance from the model card |
| McNemar's test | Low power on per-task majority votes (see E3) |
| R = 8 rounds and the plan's "two empty rounds" stop | No simulated gain from rounds 7 and 8 (+440 episodes per loop); the stop rule ended loops after about 2 rounds in simulation |
| Separate leaderboard-protocol B0 run | Replaced by 1× censoring of S0 at 0 episodes (E3-LB) |
| TB2 Oracle census before Stage 2 | Would touch held-out tasks; the Oracle check runs on TB-Pro only |
| Earlier consumer-machine replication proposal (356 episodes) | It had no named hardware and an unverified precision claim. Replaced by E-PORT |

---

## Cost table

Rate: 213.5 episodes per GPU-day (see [Throughput](#throughput-used-for-every-gpu-day-figure)). GPU-days = episodes / 213.5.

| ID | Arithmetic | Episodes | GPU-days |
|---|---|---|---|
| E-P0 | sweep ≤ 3 × 15 × 2 = 90, plus A/A 60 | 150 | 0.70 |
| E1 | 15 tasks × 2 runs × cap 2 | 60 | 0.28 |
| E0 | S0 × 3 on TB-Pro survivors outside the dev slice (cap) | 600 | 2.81 |
| E2 | 3 loops × [6 × (50 + 5 × 25) + 7 × 15 × 3] = 3 × 1,365 | 4,095 | 19.18 |
| E3 | 890 + 445 + 445 + 445 + ≤ 1,024 | 3,249 | 15.22 |
| E-ATTR | ≤ 4 arms × 40 tasks × 3 | 480 | 2.25 |
| E-T2 advised | 89 × 5 | 445 | 2.08 |
| E4b reserve | 20 × 2 + 89 × 3 | 307 | 1.44 |
| E-PORT | 89 × 3 (main GPU, emulated by default) | 267 | 1.25 |
| **Core total** | | **9,653** | **45.21** |

The total equals the frozen plan total of 9,653 episodes and 45.21 GPU-days. Across the ±30% throughput band the core takes 34.8 to 64.6 GPU-days. If a consumer machine runs E-PORT, the main-GPU core is 9,386 episodes (43.96 GPU-days). If the E4b reserve is released, 307 episodes return to contingency.

### Not in the total

| Item | Size | Funded from |
|---|---|---|
| E0 top-up | ≤ 400 episodes, only if C3 < 40 | Contingency |
| 1× leaderboard fallback | 178 episodes, only if censoring is invalid | Contingency |
| Non-episode model calls | Judge about 1,490 calls (about 600 on E0, 890 on TB2), selector 89, diagnosis and proposal calls of 3 loops × 6 rounds. Measured in MCU and converted to episode-equivalents at G0 | Contingency |
| Infrastructure-error reruns | As needed | Contingency |
| Fallback models (E0-FB) | ≤ 1,150 each | Deducted from the available GPU-days |
| Tier C | E5-DEMO ≤ 1,365 (only on request), T2 enforce-only 445, T1-lite 554, B5 1,810 | Headroom under the 12,500 absolute cap |
| Optional S\*1 × 2 | 178 episodes on a consumer machine only | Off the main GPU |
| AppWorld re-entry | Costed from the adapter, only on point-4 reading (b) with cross-benchmark scoring | Tier C headroom |

### Caps

| Cap | Episodes | GPU-days |
|---|---|---|
| Core | 9,653 | 45.21 |
| Core plus contingency | 10,500 | 49.18 |
| Absolute cap, including Tier C | 12,500 | 58.55 |
| Floor | 6,224 | 29.15 |

Contingency (10,500 − core = 847 episodes) funds only the named uses above, never new arms. The two caps are round values set in the design review; see [Thresholds](#thresholds-and-where-they-come-from). API spend for paper-1 arms is $0; any API use needs a logged amendment with its own cap.

### Rule at gate G0

After E-P0, E1, E0, any top-up and any fallbacks:

1. Measure r (episodes per GPU-day at the pinned configuration, on TB-Pro) and D_rem (dedicated GPU-days left before the analysis deadline).
2. Cap = 0.9 × r × D_rem. The 0.9 is a 10% safety margin (owner judgement).
3. Remaining core = 9,653 − 810 Phase-0 episodes (E-P0 150 + E1 60 + E0 600) = 8,843, re-costed with the measured per-loop cost.
4. If Cap ≥ remaining core, run the full core, and admit Tier C items in rank order while remaining core + admitted Tier C ≤ min(Cap, 12,500 − spent).
5. If Cap < remaining core, apply the cuts below in order, each costed on the plan left by the earlier ones, until the plan fits Cap. Cuts 4 and 5 must be decided before the Stage-1 tag.
6. If Cap is below the remaining floor (6,224 − 810 = 5,414), halt before Stage 1 and escalate: more GPU-days, a faster GPU, or a narrower paper 1.

A measured rate below 150 per day, or a median episode above 600 s, triggers this re-plan, never a model switch.

### Cut order

| Step | Cut | Change | Plan after (episodes) | GPU-days |
|---|---|---|---|---|
| 0 | Tier C is not admitted when Cap < core + item. If headroom shrinks, drop B5, then T1-lite, then enforce-only, then E5-DEMO | n/a | 9,653 | 45.21 |
| 1 | E-ATTR to 2 arms (top changed group + lessons/notes-off) | −240 | 9,413 | 44.09 |
| 2 | E-T2 advised cell k 5 → 3 | −178 | 9,235 | 43.26 |
| 3 | B1 ×5 → ×3 (hard cap 614) | −410 | 8,825 | 41.33 |
| 4 | R 6 → 4 rounds in all three loops (1,365 → 925 each) | −1,320 | 7,505 | 35.15 |
| 5 | Drop the S\*2 loop (925 after cut 4); S\* = S\*1 ×10, TB2 episodes unchanged; claims about the realised strategy; only before the Stage-1 tag | −925 | 6,580 | 30.82 |
| 6 | S0 pool ×10 → ×6; BoN rows N = 1 to 5 and 6 | −356 | 6,224 | 29.15 |

The floor is 6,224 episodes (29.15 GPU-days). It is 5,957 if E-PORT runs off the main GPU, 5,917 if the E4b reserve is released, and 5,650 with both. After the Stage-1 tag only cuts 1 to 3 and 6 may be applied.

**Never cut:** G-INFRA, G1, E-P0, E0, all 89 TB2 tasks held out, S0 ≥ 6 and S\* ≥ 10 runs per task, B4 ×5, B1, BoN, the point-1 cost table, the point-2 per-task table, the index variants and the selector (0 episodes), E-PORT, the lessons/notes-off arm, the E4b reserve until the point-5 answer or the Stage-1 freeze, pre-registration and the held-out ledger.

Planned against realised episodes and GPU-days will be published as an appendix table.
