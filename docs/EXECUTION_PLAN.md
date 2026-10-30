# Execution plan for paper 1

Sagandeep Kaur, draft for discussion with Prof. Mohamed Abdelrazek (Deakin A2I2), 2026-10-20.

**Status (2026-10-20).** No experiment has been run and no model has been called. This file turns the experiment cards in [EXPERIMENTS.md](EXPERIMENTS.md) into a dated plan. Every effort figure, date and GPU-day figure below is an estimate. Where this file and EXPERIMENTS.md disagree on a design choice, EXPERIMENTS.md and the design review ([DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md)) hold. This file only adds the order of work, the effort estimates and the dates.

Choices that depend on Prof. Abdelrazek's answers are marked **to confirm with Prof. Abdelrazek**. Each has a default that applies only if there is no answer by the Stage-1 freeze, and is then logged in [DECISIONS.md](DECISIONS.md).

---

## How to read this file

### Terms and acronyms

The full list is in [EXPERIMENTS.md](EXPERIMENTS.md#terms-and-acronyms). The terms used most here:

| Term | Meaning |
|---|---|
| TB2, TB2-89 | Terminal-Bench 2.0 (89 tasks, task commit `2fd12b8`); all 89 tasks, held out for the final pre-registered run |
| TB-Pro | terminal-bench-pro (200 tasks), used for all calibration and adaptation |
| GPU, VRAM | Graphics processing unit; its on-board memory |
| GPU-day | 24 hours of one dedicated GPU |
| Episode | One Harbor trial of one strategy on one task |
| S0, S\*1, S\*2, B1, B4, B5 | Fixed strategy; strategies chosen by adaptation seeds 1 and 2; reflection-retry; random edits; free-form code edits (optional) |
| MCU | Model Compute Units, the cost-matching unit (a × prompt tokens + b × generated tokens) |
| CI | 95% confidence interval (one-stage task bootstrap unless stated) |
| Stage 1, Stage 2 | Signed pre-registration tags: before the first adaptation episode, and before the first TB2 agent episode |
| SK, MA | Owners: Sagandeep Kaur; Prof. Mohamed Abdelrazek |
| W*n* | Week *n* of this plan. W1 starts Monday 2026-10-19 |
| BoN, CER_test, T\* | Best-of-N; compute-equivalence ratio at test time; payback in tasks (see E11 in EXPERIMENTS.md) |
| VBS, SBS | Virtual best solver (best version per task); single best solver (best version overall) |
| MDE, pp | Minimum detectable effect at 80% power, alpha 0.05; percentage points |
| MoE | Mixture of experts. MoE offload keeps expert layers in CPU RAM to save VRAM |
| KV cache | The key-value cache of the model server, one per slot |
| CPU, RAM, API | Central processing unit; main memory; a hosted model interface paid per token |
| DOI, OSF | Digital object identifier (Zenodo); Open Science Framework |
| TLS, SNI, DNS | Transport Layer Security; its server-name indication; the Domain Name System |

### Planning assumptions

| Assumption | Value | Status |
|---|---|---|
| Start | Monday 2026-10-19 (W1) | Fixed |
| Owner time | **20 hours per week**, one person (SK) | Assumption. Duration, start date and weekly hours are plan item 1 in [DECISIONS.md](DECISIONS.md#plan-item-1-duration-start-date-hours-per-week-and-supervision-rhythm). The plan rescales (table below) |
| Engineering effort | The hour ranges in the [backlog](#5-phase-0-engineering-backlog). The schedule uses the midpoints | Estimates, not measured |
| Run host | One x86-64 workstation with the GPU, Docker and enough disk, usable from W7 (2026-11-30). It is dedicated during budgeted runs | Assumption. The hardware is not granted yet (Q5, to confirm with Prof. Abdelrazek) |
| GPU use | The GPU runs unattended, 24 hours a day, during budgeted runs | Assumption behind every GPU-day figure |
| Planning throughput | 213.5 episodes per GPU-day (verified, laptop-measured proxy, ±30%) | See [section 6](#6-compute-schedule) |
| Optimistic throughput | 277.55 episodes per GPU-day (213.5 × 1.3, the top of the ±30% band) | Estimate. The real rate r is measured at gate G0 |
| Tier C add-ons and conditional arms | Not in the dated schedule | Each adds time if admitted; see [section 6](#tier-c-and-conditional-items) |

### How the plan rescales

Owner hours, not the GPU, set the critical path. Before the Stage-1 tag the plan needs about 400 owner-hours (midpoint estimates, including P0-25 and P0-26 in [section 5](#added-items-p0-25-to-p0-30)). After the final run it needs about 80 more, so 480 in total. The GPU blocks after Stage 1 take about 6.9 calendar weeks at the planning throughput, whatever the weekly hours:

- adaptation 19.18 GPU-days, the E4b pilot 0.19 and the final run 22.05: 41.42 GPU-days, which is 5.9 weeks of 7 GPU-days;
- plus 1 week for the Stage-2 freeze (W24), in which only the E4b pilot uses the GPU;
- 5.9 + 1 = 6.9 weeks.

Duration in weeks ≈ 480 / (hours per week) + 6.9 (estimate). Each milestone is the plan week in which it falls, so week counts are rounded up:

| Hours per week | Stage-1 tag | Final run ends | Draft paper | Total |
|---|---|---|---|---|
| 15 | about W27 | about W34 | about W39 | about 39 weeks |
| **20 (this plan)** | **W20** | **W27** | **W31 (2027-05-23)** | **31 weeks** |
| 30 | about W14 | about W21 | about W23 | about 23 weeks |
| 40 | about W10 | about W17 | about W19 | about 19 weeks |

**Owner work inside the GPU weeks.** The 480 hours leave out the owner work that runs while the GPU is busy (W21 to W27). It is listed here with midpoint estimates:

| Week | Owner work | Hours (estimate) |
|---|---|---|
| W21 | P0-20 network audit (10); P0-21 E-PORT configuration (3); monitoring and the T2 applicability check (3) | 16 |
| W22 | P0-29 selector design (10); P0-30 E-T12 failure labels, first part (8); monitoring (2) | 20 |
| W23 | P0-30 (finish, 4); E-N4 expressiveness audit (8); P0-28 adherence-rule validation (5); monitoring (2) | 19 |
| W24 | Stage-2 text (4); MCU gate, q, B1 cap mixture, selector freeze and tag (6); monitoring (2) | 12 |
| W25 to W27 | Monitoring and audit-flag review (2 per week); paper skeleton, methods, related work and Appendix A1 scaffolding (10 per week) | 36 |
| **Total** | | **103** |

That is about 15 hours per week over 7 weeks. So the formula holds at 15 hours per week or more. Below that, this work, not the GPU, sets the length of W21 to W27.

At the optimistic throughput the GPU blocks shrink from about 6.9 to about 5.5 weeks (31.85 GPU-days, which is 4.55 weeks, plus the freeze week). That saves about 1.4 weeks at any weekly hours. [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md#10-timeline-amended-2026-10-20) section 10 records the original suggestion of about 24 weeks part-time. [DECISIONS.md](DECISIONS.md#plan-item-1-duration-start-date-hours-per-week-and-supervision-rhythm) (plan item 1) keeps that as the default until the length and hours are agreed. At 20 hours per week this plan needs about 31 weeks. To finish in 24 weeks, these estimates need about 28 hours per week (480 / (24 − 6.9)). Otherwise the end date moves, or scope is cut with the [cut order](#cut-order-with-both-throughputs). This is for SK and MA to agree.

---

## 1. Summary

- **Duration.** 31 weeks at 20 hours per week, from 2026-10-19 to 2027-05-23 (estimate).
- **Critical path.** About 221 owner-hours of engineering before the first budgeted GPU episode (W1 to W11), then about 179 hours of build and analysis work before the Stage-1 tag (W12 to W20). That is about 400 hours, the whole of W1 to W20 at 20 hours per week, with no slack.
- **GPU.** The core plan is 9,653 episodes = 45.21 GPU-days at 213.5 per day (34.78 at 277.55). The GPU is busy in three blocks: Phase 0 calibration (W12 to W13), adaptation (W21 to W23) and the final run (W24 to W27).
- **First budgeted GPU episode.** W12 (week of 2027-01-04), after gate G-INFRA closes. Before that, a 5-task TB-Pro smoke run in W11 closes G-INFRA. Its 5 episodes are logged for infrastructure checks only, enter no analysis and are charged to contingency.
- **No TB2 agent episode before W24** (on the TB-Pro route). Before the Stage-2 tag the only TB2 contact is image pulls by digest, recorded in the held-out ledger. The first pull is for the disk census in W8. Reading TB2's public task files is not contact; see [What counts as TB2 contact](#what-counts-as-tb2-contact).
- **Decisions owed by Prof. Abdelrazek.** Seven questions (Q1 to Q6 and Q8), sent in W1. All are needed by the Stage-1 freeze (W20). Q5 (GPU-days and hardware) is needed much earlier in practice; see [section 7](#7-decisions-owed-by-prof-abdelrazek).

---

## 2. Phases

| Phase | Weeks (dates) | Tasks | Deliverables | Owner |
|---|---|---|---|---|
| 0a. Engineering and route pilot (no budgeted GPU episode) | W1 to W11 (2026-10-19 to 2027-01-03) | Backlog items P0-01 to P0-08, P0-10 to P0-13, P0-24, P0-25 and P0-26: client, Harbor adapter, budgets, baseline repair, cost function, held-out ledger, pool builder, `pins.lock`; P-M2 route pilot (build census, dedup, TB-Pro Oracle check, allowlist fork, licence, disk census); question sheet and [DECISIONS.md](DECISIONS.md) | Green baseline unit tests (G-BASE); routing table; TB-Pro allowlist fork with diff and host lists; G-ROUTE decision; 5-task TB-Pro smoke run with 0 harness errors (G-INFRA) | SK; host provider for the run host (Q5) |
| 0b. GPU calibration (TB-Pro only) | W12 to W13 (2027-01-04 to 2027-01-17) | E-P0 fit-gated sweep and A/A run; E1 B1 smoke; E0 S0 ×3 and any top-up; memorisation probe (E0-MEM); MCU fit and k_occ; G0 checks and the G0 budget rule; any fallback model | Filled `pins.lock`; Phase-0 calibration table; G0 decision record with r, D_rem and capacity C; pool lists | SK; MA for Q6 if no local model passes |
| 1. Pre-registration build | W12 to W20 (2027-01-04 to 2027-03-07) | `compile()` and per-field tests (G1); edit-space exclusions; hybrid selection rule; lint; LLM diagnoser and proposer; point-1 cost table code; analysis and simulation code; E0-JUDGE, E0-SIM, E0-SIM2, LINT-PILOT, E-INTERP (P0-27); Stage-1 tag | Mechanism table (Table 2) passing code review; simulation report; Stage-1 tag with Zenodo DOI and OSF entry | SK; MA answers Q1 to Q4 and Q8 by the freeze |
| 2. Adaptation (TB-Pro only) | W21 to W23 (2027-03-08 to 2027-03-28) | E2: three hybrid loops in sequence (S\*1 first, then B4 and S\*2); in parallel, network audit code, E-PORT configuration, selector design on TB-Pro logs (P0-29), failure labels for E-T12 (P0-30), adherence-rule validation (P0-28), E-N4 expressiveness audit | S\*1, S\*2, B4-final; edit logs; Figure 2 draft; frozen selectors (by commit) | SK |
| 3. Stage-2 freeze | W24 (2027-03-29 to 2027-04-04) | E4b pilot (only if admitted); MCU validation gate; fix q and the B1 cap mixture; freeze selectors; T2 applicability check; Stage-2 tag | Stage-2 tag with ledger hash | SK |
| 4. Final pre-registered run (TB2-89) | W24 to W27 (2027-04-01 to 2027-04-25) | E3 (S0 ×10, S\*1 ×5, S\*2 ×5, B4 ×5, B1 ×5); E-T2 advised cell; E-ATTR; E4b arm (only if admitted); E-PORT; network audit per trial | Complete, ledgered run logs; per-arm flag rates | SK; host provider for the consumer machine if any |
| 5. Analysis and write-up | W28 to W31 (2027-04-26 to 2027-05-23) | H1 to H4; point-1 cost table (Table 4); E11; E4-SW; E-ATTR; E-T2; E-N1, E-N3; Appendix A1; planned-against-realised budget table | Draft paper; released code and logs | SK; MA reviews |

---

## 3. Week-by-week calendar

Hours are midpoint estimates at 20 hours per week. "GPU" lists budgeted episodes on the main GPU.

| Week | Starts | Owner work (SK, about 20 h) | GPU | Gate or decision due |
|---|---|---|---|---|
| W1 | 2026-10-19 | Start the log in [DECISIONS.md](DECISIONS.md); send the question sheet (Q1 to Q6, Q8) to MA; P0-01 sampling; P0-04 budgets; P0-11 `pins.lock` skeleton | none | Question sheet sent |
| W2 | 2026-10-26 | P0-02 async client: reasoning, tool calls, timings, `tool` role | none | |
| W3 | 2026-11-02 | P0-07 `episode_cost()` and MCU; P0-08 held-out ledger | none | LEDGER code done |
| W4 | 2026-11-09 | P0-05 B1 repair; P0-06 judge and pooled BoN (part) | none | |
| W5 | 2026-11-16 | P0-06 (rest) and baseline unit tests; P0-03 Harbor adapter (start) | none | G-BASE tests green in CI |
| W6 | 2026-11-23 | P0-03 Harbor adapter | none | |
| W7 | 2026-11-30 | P0-03 Harbor adapter (finish, against a scripted fake model); P0-10 pool builder. Run host assumed available: start the TB-Pro build census (unattended) | none | Run host available (assumption) |
| W8 | 2026-12-07 | P0-12 P-M2: resource filter; disk census (TB-Pro survivors plus the TB2-89 images, pulled by digest through the ledger); dedup embeddings and owner review | none | First TB2 image pull (ledgered) |
| W9 | 2026-12-14 | P0-12 P-M2: TB-Pro version-1.0 schema adapter (capped at 5 engineer-days), Oracle check | none | |
| W10 | 2026-12-21 | P0-12 (finish); P0-13 allowlist fork and DNS sinkhole | none | |
| W11 | 2026-12-28 | P0-13 (finish); licence confirmation; route decision; set aside the 15-task dev slice; P0-25 adherence rule (draft); P0-26 E0-MEM probe script; 5-task TB-Pro smoke run | 5-task smoke run only (not budgeted; charged to contingency) | **G-ROUTE**, **G-INFRA** |
| W12 | 2027-01-04 | E-P0 and E1 analysis (pin configuration, fit MCU a and b, k_occ); P0-15 edit-space exclusions; P0-16 selection rule | E-P0 150, E1 60, E0 starts | **G-SWEEP** |
| W13 | 2027-01-11 | G0 checks (including the E0-MEM probe) and budget rule; E0-JUDGE; E0-SIM fit; P0-09 point-1 table code | E0 600; top-up ≤ 400 if C3 < 40 | **G0**, **G-JUDGE**; Q6 if a fallback is needed |
| W14 | 2027-01-18 | P0-14 `compile()` and per-field tests | idle, or a fallback model's E0 | |
| W15 | 2027-01-25 | P0-14 `compile()` | idle | |
| W16 | 2027-02-01 | P0-14 (finish); P0-17 lint | idle | |
| W17 | 2027-02-08 | P0-18 LLM diagnoser, proposer and B4 random proposer | idle | |
| W18 | 2027-02-15 | P0-18 (finish); P0-19 analysis code (start) | idle | Last week for E0 data to arrive without moving Stage 1 |
| W19 | 2027-02-22 | P0-19 analysis code | idle | |
| W20 | 2027-03-01 | P0-19 (finish); E0-SIM2 hybrid re-simulation; LINT-PILOT; E-INTERP (P0-27); G1 code review; Stage-1 text; tag | idle | **G-SEL**, **G1**, **PREREG-1**; deadline for Q1 to Q4, Q8 |
| W21 | 2027-03-08 | P0-20 network audit; P0-21 E-PORT configuration; monitor S\*1 loop; T2 applicability check once S\*1 is chosen | E2: S\*1 loop 1,365 | |
| W22 | 2027-03-15 | P0-29 selector design on TB-Pro logs; P0-30 E-T12 failure labels (start) | E2: B4 loop 1,365 | |
| W23 | 2027-03-22 | P0-30 (finish); E-N4 expressiveness audit; P0-28 adherence-rule validation on TB-Pro E0 logs | E2: S\*2 loop 1,365 (ends about 2027-03-27) | |
| W24 | 2027-03-29 | Stage-2 text; MCU gate; fix q and the B1 mixture ([recipes](#stage-2-recipes-q-and-the-b1-cap-mixture)); freeze selectors; Stage-2 tag; start the final run | E4b pilot 40 (if admitted); final run starts about 2027-04-01 | **G-MCU**, **G-E4b**, **G-T2**, **PREREG-2** |
| W25 | 2027-04-05 | Monitor; review audit flags; paper skeleton (Tables 1 and 2, methods) | E3 | |
| W26 | 2027-04-12 | Monitor; methods and related-work text | E3 (ends about 2027-04-16), E-T2 advised | |
| W27 | 2027-04-19 | Monitor; Appendix A1 scaffolding | E-ATTR, E4b arm (if admitted), E-PORT (ends about 2027-04-23) | Final run complete |
| W28 | 2027-04-26 | Run frozen analysis code: H1 to H4, Tables 3 and 4, E11, E4-SW, E-ATTR, E-T2, E-N1, E-N3 | none | **G-H2** read-out |
| W29 | 2027-05-03 | Draft paper: results | none | |
| W30 | 2027-05-10 | Draft paper: discussion, appendices, budget table | none | |
| W31 | 2027-05-17 | Release code and logs; [DECISIONS.md](DECISIONS.md) audit; send draft to MA | none | Draft paper |

**GPU idle weeks.** The main GPU has no budgeted work from W14 to W20 at 20 hours per week. If it is shared, it need not be reserved then, and those weeks do not count towards the dedicated GPU-days D.

**If the run host is late.** The host is needed from W7 for the TB-Pro builds and from W11 for the smoke run. If it arrives later, SK moves pre-Stage-1 work (P0-14 to P0-19) forward. The end date holds if the host is usable by about W13 (2027-01-11), so that E0 ends by W18. Each week beyond that moves every later week by one (estimate).

---

## 4. Gates

A gate is a measurable condition that must hold before the next step. Gate names follow [EXPERIMENTS.md](EXPERIMENTS.md#gates-and-zero-episode-protocol-items), so G0 is the calibration gate and G1 is the `compile()` gate. The other gates get descriptive names. Deadlines are the weeks of this schedule.

### A. Before any budgeted GPU episode

| Gate | Criterion (measurable) | Evidence | Deadline | Action on failure |
|---|---|---|---|---|
| **LEDGER** | Every runner call that names a TB2 task id goes through the task-id guard and appends a ledger record. Before Stage 2 the only accepted purpose is an image pull by digest. Static reads of public task files are not runner calls ([What counts as TB2 contact](#what-counts-as-tb2-contact)) | Unit tests; the ledger file and its hash | W3 (code); before the first TB2 image pull (disk census, W8) | No TB2 image is pulled |
| **G-BASE** (baseline repair) | All six baseline unit tests pass in CI on the toy environment: B1 retries when the judge returns fail; B2 can select an attempt other than 0; the request body carries temperature 0.6, top_p 0.95, top_k 20 and a seed; judge calls appear in the charged arm's cost; the judge cannot read a `tests/` path; S0 makes no in-run judge call | CI log; test ids | W5 (code); required to close G-INFRA in W11 | G-INFRA stays open, so no budgeted episode runs. Fix and re-run CI |
| **G-ROUTE** (P-M2 go/no-go) | All of: (i) licence confirmed (a LICENSE file or written confirmation from the authors); (ii) at least 120 TB-Pro tasks survive the build census, resource filter, dedup and Oracle check, before the dev slice is removed; (iii) Harbor runs the version-1.0 tasks within the 5-engineer-day adapter cap; (iv) the measured disk footprint fits the granted disk with at least 20% headroom | Routing table; census and disk report; licence record | W11 | (i) to (iii) failing is a route failure: re-split TB2 into H52 held out plus A15 / V12 / V2 10 with sibling groups (seed 20261015, stratified), logged as a deviation; S0 ×3 pre-screen on the 37 non-held-out tasks only; MDE about 7.6 pp at k=5, stated in the abstract (E-RESPLIT). (iv) failing: adopt build-run-prune pinned by digest, logged |
| **G-INFRA** (infrastructure) | All of: (a) async Harbor agent adapter; (b) reward read from the Harbor trial result, `env.grade` removed; (c) async client per trial with a long enough timeout, parsing `reasoning_content`, tool calls, timings and cached tokens, allowing null content; (d) `tool` role and native tool calling through the chat template; (e) per-step JSONL logs (JSON Lines) with strategy hash, provenance tag, seed, timings and Harbor trial id; (f) Harbor job configs with `n_concurrent_trials` equal to the llama.cpp slot count. Plus G-BASE, and a 5-task TB-Pro smoke run with 0 harness errors | Smoke-run logs; CI log | W11 | No budgeted episode runs. Every week of delay moves every later week by one |

#### What counts as TB2 contact

This plan reads the held-out rule as follows, and logs that reading in [DECISIONS.md](DECISIONS.md) in W1.

- **Allowed and ledgered before Stage 2:** pulling a TB2 image by digest. The first pull is for the P-M2 disk census in W8.
- **Allowed and not ledgered:** reading TB2's public task files at the pinned task commit `2fd12b8` (instruction text, `task.toml` metadata and categories). This is needed for the dedup (W8), the 40-task E-ATTR set (fixed from public data) and the selector's TB2-to-TB-Pro category map (W22). No agent, Oracle or model acts in a TB2 environment, and no generative model reads TB2 text before Stage 2. The dedup embedding model only turns text into vectors. These reads do not go through the runner's task-id guard. The dedup script records the TB2 commit and the files it read in the P-M2 routing report, so the reads can be audited.
- **Not allowed before Stage 2:** any agent, Oracle or model run in a TB2 environment.

### B. Phase 0 on the GPU (TB-Pro only)

| Gate | Criterion (measurable) | Evidence | Deadline | Action on failure |
|---|---|---|---|---|
| **G-SWEEP** (serving configuration) | Among at most 3 configurations that fit free VRAM with at least 1 GiB headroom, the one with the most episodes per GPU-day that has at most 1 AgentTimeoutError in 30 trials and no out-of-memory error. The "or an upper 95% bound ≤ 10%" wording in EXPERIMENTS.md (E-P0) adds nothing at 30 trials: a one-sided Clopper-Pearson 95% upper bound is at most 10% only with 0 timeouts in 30. It applies only to a configuration run for more trials, for example at most 1 timeout in 46 | E-P0 sweep table; `pins.lock` | W12 | If none qualifies at timeout multiplier 2, pin one slot (`-np 1`) and escalate before E0 |
| **G0 fitness** | TB-Pro pass rate over E0 trials, with a task-bootstrap CI, has upper bound ≥ 12% and lower bound ≤ 45%; infrastructure errors (not agent failures) ≤ 5% of trials | Phase-0 calibration table | W13 | **Model-fallback rule.** Move to the next local model, which repeats bring-up and E0 within ≤ 1,150 episodes (bring-up ≤ 150, E0 ≤ 600, top-up ≤ 400), deducted from the available GPU-days before the G0 budget rule. Order (to confirm with Prof. Abdelrazek, Q6): Qwen3.5-35B-A3B Q4_K_M, then TMax-9B Q4_K_M, then Nemotron-Terminal-32B Q4_K_M only on a GPU with 32 GB or more. At most 2 fallbacks on a 24 GB GPU and 3 on 32 GB or more. GPT-5-mini (API) only by Prof. Abdelrazek's decision. If no local model passes, the default is to keep the best local model with a smaller contested pool, if there is no answer within one week. Each fallback costs up to 5.39 GPU-days (4.14 at the optimistic rate) and about one calendar week |
| **G0 supply** | C3 ≥ 40 contested tasks after S0 ×3. Otherwise top up non-contested tasks to ×5 (≤ 400 episodes, from contingency) and count C5: C5 ≥ 30 sizes pools normally; 20 ≤ C5 < 30 sizes pools with V_pro screened at k=2 | C3 and C5 counts; pool lists | W13 | C5 < 20 counts as a fitness failure (model-fallback rule above). Supply never triggers a TB2 re-split |
| **G0 throughput** | Measured r ≥ 150 episodes per GPU-day and median episode ≤ 600 s at the pinned configuration | E0 timing records | W13 | Apply the M16 cut order through the G0 budget rule. Never switch the model for speed |
| **G0 memorisation** | Probe of 20 TB-Pro tasks done and reported | Probe log | W13 | No threshold. The result is reported |
| **G0 budget rule** | C = 0.9 × r × D_rem, where D_rem is the dedicated GPU-days left before the analysis deadline. In this plan the analysis deadline is the end of the final run: the end of W27 (2027-04-25) at 20 hours per week. It moves with the hours agreed under plan item 1. C ≥ remaining core (8,843 episodes, re-costed with the measured per-loop cost) runs the full core and admits Tier C in rank order while remaining core + admitted Tier C ≤ min(C, 12,500 − spent) | G0 decision record in [DECISIONS.md](DECISIONS.md) | W13 | 5,414 ≤ C < remaining core: apply cuts in order until the plan fits; cuts 4 and 5 are decided before the Stage-1 tag. C < 5,414 (remaining floor): halt before Stage 1 and escalate to Prof. Abdelrazek (more GPU-days, a faster GPU, or a narrower paper 1). If D is not known, the default is to plan the full core and halt here if C is below the floor |
| **G-JUDGE** (BoN selector) | Same-model judge AUROC (area under the ROC curve) ≥ 0.6 on the about 600 E0 trajectories | AUROC with CI | W13 | The primary BoN selector becomes "agent-written tests passed, ties random". The judge becomes a sensitivity analysis, and the paper says a realistic selector is weak for this model |

### C. Before the Stage-1 tag (no adaptation episode before it)

| Gate | Criterion (measurable) | Evidence | Deadline | Action on failure |
|---|---|---|---|---|
| **G-SEL** (selection-noise calibration) | The CODE-FIX exact-tie tests (P0-16) pass. Re-simulation of the hybrid rule with the E0 beta-binomial fit at the actual V_pro and V2_pro sizes gives P(chosen version worse than S0) ≤ 10% under N(0, 0.3²) edit effects. Also: the paired-t size check (on E0 rates and on public little-coder TB2 rates) is ≤ 6% at nominal 5%; rho is measured from the A/A run | Simulation report (E0-SIM, E0-SIM2) | W20 | Selection: raise V2_pro to k=5 within the per-loop cap formula (≤ 1,575) and re-check; if still above 10%, proceed with k=5 and flag the harm rate in the pre-registration. Size above 6% in either simulation: the sign-flip test becomes primary in E3. Without a measured rho, no variance reduction from shared seeds is claimed. The cost-aware tie-break replaces the argmax only if it loses less than 10% of expected gain |
| **LINT-PILOT** | Lint run on proposer outputs generated from TB-Pro E0 failure logs, with its false-positive rate on generic content reported | Lint report | W20 | No threshold. The rate is reported in the pre-registration |
| **G1** (`compile()`) | The minimum compiled set (exploration, tool_policy, verification, and recovery.retry_on / max_retries / on_repeated_failure with values continue, replan, restart_task) has passing CI tests showing a non-default value changes the controller's actions; edit-space tests show rollback values, rollback fields and `switch_to` are excluded; every other field is labelled text-only; Table 2 passes code review | CI log; Table 2; review record | W20 | If recovery.\* cannot be compiled by W20, the typed-strategy claim is narrowed in the pre-registration and logged, never kept silently |
| **G-B5** (Tier C rank 4, only if attempted) | Sandbox built and passing an escape test within 5 engineering days after G-INFRA; at least 5 of 10 B5 proposals from TB-Pro E0 failure logs apply cleanly and pass the controller unit tests; (core + higher-ranked admitted Tier C + B5) × 1.2 ≤ C and within 12,500 | Sandbox test log; smoke-test record | W20 | B5 moves to paper 2. The paper states that it makes no comparison with code-harness evolution |
| **G-T1lite** (Tier C rank 3, only if admitted) | TMax-9B S0 on 20 TB-Pro tasks ×1 solves ≥ 3 of 20; format and tool-call error rate ≤ 10%; no TB2 or TB-Pro task overlap found in its released training data; the 554 episodes fit the Tier C rule | Pilot log; overlap check | W20 | T1-lite moves to paper 2 |
| **PREREG-1** (Stage 1) | A signed git tag freezes `pins.lock`, analysis code, thresholds, pool lists, budget caps, the seed branch (two seeds by default), the 40-task attribution set, E-INTERP, the adherence rule and its validation criterion (P0-25), sampling and judge prompt, the index headline label (Q1), the E4b arm and its gate if Q2 is (b) or (c), and the decisions on cuts 4 and 5. Archived on Zenodo with a DOI; an OSF registration quotes the tag SHA and DOI | Tag, DOI, OSF entry | W20 | **No E2 episode runs before this tag.** Unanswered questions take their defaults, logged as "defer to professor, default applied" and told to him |

### D. Before the Stage-2 tag (no TB2 agent episode before it)

| Gate | Criterion (measurable) | Evidence | Deadline | Action on failure |
|---|---|---|---|---|
| **G-T2** (advised cell applicability) | At least one field that S\*1 changed from S0 is compiled with a passing controller test. The adherence rule validates on TB-Pro E0 logs | Diff of S\*1 against S0; Table 2 | W21 (once S\*1 is chosen); W23 for adherence | T2 is "not applicable" and its 445 episodes return to contingency. A failed adherence validation drops the adherence readout |
| **G-E4b** (only if Q2 is (b) or (c)) | Q2 answered (b) or (c) before the Stage-1 freeze and the arm written into Stage 1; G1 passes with the flag-gated `switch_to` and its unit test; the TB-Pro pilot (20 E0-contested tasks × 2 = 40 episodes) fires the switch on ≥ 6 of 40 trials (Wilson 95% CI reported) with ≤ 2 of 40 infrastructure errors | Pilot log | W24 | The TB2 arm is not run; the fire rate goes to the appendix; mid-task switching moves to paper 2 (logged); the 267 TB2 episodes return to contingency. With Q2 = (a) or no answer, all 307 reserve episodes return to contingency at the Stage-1 freeze |
| **G-MCU** (cost-unit validation) | Every arm with at least 40 TB-Pro episodes has a mean episode residual within ±3% and the 95% CI of that mean within ±5% | MCU fit table (a, b, k_occ, residuals with CIs) | W24 | Add a context-length term and refit. If it still fails, match on processed tokens, with MCU kept as a sensitivity analysis. Arms below 40 episodes are reported as "unvalidated". Logged either way |
| **PREREG-2** (Stage 2) | A second signed tag freezes q (from TB-Pro V2_pro runs), the B1 cap mixture (sum of caps ≤ 1,024 at ×5, or ≤ 614 after cut 3), both selectors by commit hash, the audit configuration and the held-out ledger hash. Zenodo DOI and OSF entry as in Stage 1 | Tag, DOI, OSF entry | W24 | **No TB2 agent episode runs before this tag.** Any failed gate above is resolved, or the pre-registration is amended, before the tag |

#### Stage-2 recipes: q and the B1 cap mixture

Both are fixed in W24 from TB-Pro data only. The numbers in the examples are illustrative, not estimates.

- **q (BoN matching).** Data: the chosen version's V2_pro runs (3 per task; with two seeds, the average of S\*1 and S\*2), S0's V2_pro runs (version 0 of the same loops, 3 per task) and the judge's MCU per trajectory from the E0-JUDGE calls. N\* = S\* mean MCU per episode / (S0 mean MCU per episode + judge MCU per trajectory). n is the integer part of N\* and q the fractional part. Example: S\* 1,800 MCU, S0 900 MCU and judge 150 MCU give N\* = 1,800 / 1,050 = 1.71. So n = 1, q = 0.71, and the matched BoN is 0.29 × BoN@1 + 0.71 × BoN@2.
- **B1 cap mixture.** Data: S\*'s mean MCU per episode on V2_pro (as above) and E1's 60 B1 episodes. From E1's attempt logs, cost(c) is the mean MCU of a run cut off after attempt c, for c = 1, 2, 3, including judge and reflection calls. Take the two adjacent caps whose costs bracket S\*'s cost and solve for the weight. Example: cost(1) = 1,000, cost(2) = 1,600 and cost(3) = 2,100 MCU, and S\* = 1,700 MCU. Then w3 × 2,100 + (1 − w3) × 1,600 = 1,700 gives w3 = 0.2 and w2 = 0.8, a mean cap of 2.2 (≤ 2.3). Over 445 runs the seeded draw gives 89 runs with cap 3 and 356 with cap 2, 979 caps in total, within the 1,024 hard cap. If S\*'s cost is above cost(3), or the mean cap would exceed 2.3, B1 is flagged under-matched. E1 runs on dev-slice tasks, so this match is approximate. The E3 sensitivity analysis re-matches on the realised TB2 MCU ratio.

### E. After the final run

| Gate | Criterion (measurable) | Evidence | Deadline | Action on failure |
|---|---|---|---|---|
| **G-H2** (first-order adaptation against random edits) | In the fixed sequence, H1 (S\* against S0) is rejected, and then H2 (S\* against B4, two-sided, alpha 0.05, on the 89 per-task differences with the primary test: paired t, or sign-flip if G-SEL switched it) is rejected with a CI that excludes 0 | Table 3 | W28 | The run is pre-registered and is not stopped or repeated. The estimate and CI are reported. H3 and H4 are not tested, but their estimates and CIs are reported. "Diagnosis beats random search" is never claimed in paper 1 in any case (B4 has one loop). If the S\* − B4 CI includes 0, the diagnosis-noise injection (T6) becomes the first paper-2 experiment |

The plan's older checkpoint ("stop if first-order adaptation does not beat cost-matched best-of-N on V", [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md) section 10) guarded the build of the second-order loop. That loop is now paper-2 work by default (Q4). In paper 1 there is no early stop on adaptation results. The chosen version's V2_pro score is not a gain estimate, and "few or no accepted edits" and "S\* = S0" are pre-registered valid outcomes.

---

## 5. Phase 0 engineering backlog

Each item is a code change needed before a run. "Blocks" names the first gate or run that cannot start without it. Effort is in owner-hours and is an estimate. Ranges marked "design review" restate the design review's own estimates, which are unverified. All tests run offline in Docker (`make test`) within the shared machine's CPU and RAM limits. No model episode runs on the shared development machine.

### Needed before the first GPU episode (G-INFRA, LEDGER, G-ROUTE)

| ID | File | Change | Why | Acceptance test | Effort (h) | Blocks |
|---|---|---|---|---|---|---|
| P0-01 | `llm/openai_compatible.py` | Remove the `temperature = 0.0` default (line 63). Send temperature, top_p, top_k and a logged per-request seed, plus `tools` and `chat_template_kwargs`. Pin 0.6 / 0.95 / 20 for all arms | Without a temperature above 0, S0 runs are not independent draws and BoN is degenerate. The request body today carries only model, messages, stream, temperature and max_tokens (lines 103 to 113). llama.cpp accepts a per-request seed | Request body contains the four sampling keys with pinned values; seeds differ per request and are logged; no code path sends temperature 0 by default | 4 to 6 | G-BASE |
| P0-02 | `llm/openai_compatible.py`, `llm/base.py` | Async client, one per trial. Timeout at least the task's agent timeout × multiplier (or streaming). Parse `reasoning_content`, `tool_calls`, the `timings` object (`prompt_n`, `cache_n`, `predicted_n`, `prompt_ms`, `predicted_ms`) and cached-token usage. Allow null content. Add the `tool` role | The client is synchronous with a 120 s timeout (line 62), which caps a call at about 5,280 generated tokens at the reference 44 tokens per second. It reads only `message.content`, so reasoning is discarded. `Message.role` has no `tool` value | Recorded llama.cpp reply fixtures: a null-content reply with tool calls parses; reasoning text is stored in the step log; timings fields reach the cost record; a `tool` message round-trips; the timeout is derived from the task timeout | 16 to 24 | G-INFRA (c), (d) |
| P0-03 | New Harbor agent module (for example `environments/harbor_agent.py`) | Async `HarborStrategyAgent` with async `setup` and `run`; tools, probes and own checks through `environment.exec`; `AgentContext` filled every step; reward read from the Harbor trial result instead of `env.grade`; per-step JSONL logs; Harbor job configs with `n_concurrent_trials` = slot count, replacing the sequential `evaluate()` loop; agent timeout multiplier 2 for all arms; loaded by `import_path` in the harness process | Harbor v0.23.0 agents are async and run inside `asyncio.wait_for`; job configs default to 4 concurrent trials. Our `Environment` is synchronous and calls `env.grade` at the end of `run_episode` (`baselines/agent_loop.py:171`). `evaluate()` runs tasks one by one (`evaluation/runner.py:133`) | CPU test: Harbor in Docker runs a toy task with a scripted fake model and produces a complete step log and reward. Gate test: the 5-task TB-Pro smoke run with 0 harness errors | 40 to 60 (design review: 2 to 3 weeks for the infrastructure work, overlapping G1) | G-INFRA (a), (b), (e), (f) |
| P0-04 | `strategy_schema/defaults.py`, `baselines/agent_loop.py` | S0 budget: max_steps 40 → 60 (logged in [DECISIONS.md](DECISIONS.md)); at most 64k generated tokens per episode including reasoning, counted from model-reported output tokens. B1 shares the episode cap across attempts, judge calls, and reflection calls; wall-clock is only the Harbor backstop | Before this change, S0's cumulative 200,000-token default (`defaults.py:75`) differed from the planned 64k cap and could bind at about step 15. Its 1,200 s wall-clock limit is longer than the TB2 agent timeout on 50 of 89 tasks | Toy-env checks: an episode stops at 60 steps; it stops at 64k generated tokens regardless of prompt length; an edit to `/budget` is rejected | 3 to 5 | G-INFRA |
| P0-05 | `baselines/baselines.py` | B1 as in-episode reflection-retry inside one trial: retry when the in-run judge says fail or an agent-written test fails, never on hidden tests; no environment reset between attempts; 60-step cap per attempt; one 64k generated-token cap across the B1 run, including judge and reflection; requested attempt cap drawn per (task, run) from {1, 2, 3} by a seeded draw whose caps sum to <= 1,024 (x5) or <= 614 (x3); reflection and judge calls charged to B1 | B1 initially retried only when `own_check_passed is False`, so it could not retry when no own check applied; the blind judge now provides the other allowed retry trigger | B1 retries on public judge failure; no reset between attempts; drawn caps stay below the hard limit; actual attempts may be lower if the token cap binds; B1 cost includes judge and reflection calls | 8 to 12 | G-BASE |
| P0-06 | New judge module in `baselines/` | Post-trial judge: scores each S0 trajectory once from the instruction, the trajectory and agent-test outputs saved during `run()`; never reads `tests/`. Pooled BoN computed exactly over all subsets of the S0 pool, ties broken at random analytically. Fallback selector "agent-written tests passed, ties random" for G-JUDGE | B2 picks the first attempt whose own checks passed, else attempt 0 (line 154), so it collapses to attempt 0 when checks return None. No judge exists ("not implemented", lines 137 to 138) | BoN can select an index above 0; the judge cannot open a path under `tests/`; S0 makes no in-run judge call; analytic BoN@N equals brute-force enumeration on a small pool; judge cost lands only on BoN rows | 10 to 16 | G-BASE |
| P0-07 | `baselines/cost.py`, `evaluation/price_table.json` | One `episode_cost()`. MCU = a × `prompt_n` + b × `predicted_n` (`prompt_n` excludes `cache_n`; `predicted_n` includes reasoning). Least-squares fit of a and b on E-P0 per-call times; k_occ = (sum over calls of (`prompt_ms` + `predicted_ms`) / 1000) / (GPU busy wall-seconds), where busy wall-seconds is the length of the union of the calls' server-side intervals, each [end − (`prompt_ms` + `predicted_ms`) / 1000, end] from the logged end time and the llama.cpp timings, over the E-P0 window (`nvidia-smi` utilisation, sampled once per second, is a cross-check only); dollars = (MCU-hours / k_occ) × rate at two frozen named rates (electricity; cloud-GPU-equivalent), with source and date. Per-arm residual gate with the context-term and processed-token fallbacks. Every call charged to the arm that makes it | Three local-cost definitions conflict (TECHNICAL_PLAN 4.3, SMALL_MODELS 3.2 and `cost.py` itself). `cost.py:64` prices `model_s`, which under concurrency also counts waiting for a free server slot | Known timings give the expected MCU; the fit recovers a and b on synthetic data; the gate passes and fails correctly at its ±3% and ±5% boundaries; placeholder prices still refuse; no code path prices `model_s`; k_occ is 1.0 for non-overlapping synthetic calls and above 1.0 for overlapping ones | 10 to 16 | E-P0 (logging), G-MCU |
| P0-08 | `evaluation/runner.py` | Replace the boolean guard keyed on the split name (line 112) with a guard keyed on the held-out task-id set (TB2-89, or H52 under E-RESPLIT). Every access appends a JSONL record (UTC time, git SHA, `pins.lock` hash, arm, task ids, runs, purpose) to an append-only ledger whose hash goes into each signed tag. Before Stage 2 the only accepted purpose is an image pull by digest | The guard checks `split_name == HELD_OUT` with a `final_evaluation` flag, so a held-out task under another split name passes | A TB2 task id under any split name raises before Stage 2 unless the purpose is an image pull; earlier ledger bytes are unchanged after a write; an edited earlier line is detected through the hash | 6 to 10 | First TB2 image pull (disk census, W8) |
| P0-10 | `evaluation/splits.py`, `evaluation/data/` | Sibling-group handling: TB2 group labels for the 9 known sibling pairs plus review finds (for E-RESPLIT); a TB-Pro pool builder for the dev slice (15), A_pro, V_pro = min(25, round(0.6 C)), V2_pro = min(15, C − V_pro) and the fixed stratified 50-task diagnosis set (seed 20261015), with no group straddling two pools; a routing-table export (task id, source, pool, group, image digest, drop or dedup reason) | `make_split` already keeps a `group` together, but it takes fixed sizes, and `tb2_tasks.jsonl` has no group values today. Pools must be sized from the contested count after E0 | No group appears in two pools; pool sizes follow the formulas at their caps; the builder is deterministic for a seed; the routing table has one row per task with a reason for every drop | 8 to 12 | E-P0 (dev slice), E0 |
| P0-11 | New `pins.lock` writer and checker | Record GGUF sha256, llama.cpp commit and flags, GPU and driver, Harbor tag and commit, task commits, image digests, slot count, KV cache type, context, reasoning budget, sampling, MCU a and b, k_occ | Stage 1 freezes these; the runner must refuse a run whose environment differs | The checker fails on a changed digest or flag; the file round-trips | 4 to 6 | E-P0, PREREG-1 |
| P0-12 | New route-pilot scripts (for example `evaluation/tbpro/`) | P-M2: build every TB-Pro image once and record digests; provisional resource filter (> 4 CPUs or > 8,192 MB dropped), final filter after the slot count is pinned; disk census (TB2-89 by digest plus survivors); dedup with one pinned open embedding model and owner review of the 3 nearest TB2 tasks per TB-Pro task ([recipe below](#dedup-recipe-p0-12)); Harbor Oracle runs on TB-Pro only; version-1.0 schema adapter, capped at 5 engineer-days | TB-Pro ships no prebuilt images (no `docker_image` set), uses the older `version = "1.0"` schema and 3,600 s agent timeouts, and some tasks ask for 4 to 16 CPUs. The TB2 images alone are 48.98 GB compressed | Routing table complete for all 200 tasks; digests in `pins.lock`; G-ROUTE criteria (i) to (iv) evaluated | 40 to 60 (design review: 1 to 1.5 weeks) | G-ROUTE |
| P0-13 | Pinned fork of the TB-Pro task directories; network sidecar | Agent phase in Harbor allowlist mode starting from package hosts (PyPI and files.pythonhosted.org, Debian and Ubuntu mirrors, npm, crates.io, CRAN), adding the minimum hosts each failing oracle needs; the fork changes only the network lines; diff and per-task host lists published; DNS sinkhole for benchmark web domains | Harbor offers only public, no-network and allowlist modes, with no denylist. TB-Pro sets no `allow_internet` | Every surviving oracle passes under its host list; the diff touches only network lines; a sinkholed domain does not resolve inside a trial | 16 to 24 (design review: 2 to 3 days) | E-P0 (all TB-Pro runs). Without nftables on the host, TB-Pro runs on the public network with the full audit, logged as a deviation |
| P0-24 | [DECISIONS.md](DECISIONS.md) entries, tag script | Decision-log entries; a script that builds the signed tag and records the ledger hash and `pins.lock` hash; the [release checklist](#release-checklist-p0-24) for signing, Zenodo and OSF | Every deviation and every defaulted question is logged | Script produces a verifiable signed tag on a test repository; the checklist runs end to end on Zenodo Sandbox; log template has one row per open question | 4 to 6 | W1 (log); PREREG-1 (script) |

Subtotal: 169 to 257 hours (midpoint about 213), which is W1 to W11 at 20 hours per week. With P0-25 and P0-26 (about 8 hours, in W11) the W1 to W11 total is about 221 hours, at the limit of the 220 hours available.

#### Dedup recipe (P0-12)

- **Model.** `BAAI/bge-base-en-v1.5`, an open embedding model, pinned by its Hugging Face commit hash in `pins.lock` and run on CPU in Docker. Input: the full instruction text of each TB-Pro task and each TB2-89 task at the pinned commits. Similarity: cosine.
- **Review.** For every TB-Pro task, the owner reads its 3 nearest TB2 tasks. There is no similarity threshold: all 600 pairs (200 × 3) are read, about 3 to 4 hours inside P0-12.
- **Rule.** Remove the TB-Pro task if, for any of the 3, it asks for the same artefact (the same program, file or service as the end product), the same algorithm, or the same tool chain for the same goal. A shared topic alone does not remove it. If unsure, remove it: the cost is one TB-Pro task, while the risk is a leak. Each removal gets a one-line reason in the routing table.
- **Worked example (made-up tasks).** A TB-Pro task asks the agent to build library X from source and install it under a given prefix. Its nearest TB2 task asks to build the same library X from source. Same artefact: removed, reason "same artefact: library X built from source". Another TB-Pro task asks to count HTTP status codes in a web-server log with `awk`. Its nearest TB2 task asks to train a small classifier on log lines. Shared topic (logs), but a different artefact, algorithm and tool chain: kept.

### Needed before the Stage-1 tag

| ID | File | Change | Why | Acceptance test | Effort (h) | Blocks |
|---|---|---|---|---|---|---|
| P0-14 | `strategy_schema/` (new `compile()`), `baselines/agent_loop.py` | `compile(strategy)` returns (controller configuration, prompt text) with independent switches, so the T2 cells can be built. Every field is either compiled, with a CI test showing a non-default value changes the controller's actions in a specified way, or labelled text-only. Minimum compiled set as in G1, recovery first. Provenance tag and an executed or overridden flag on every strategy-triggered stage. Table 2 generated from the tests | The controller reads only probes, tool policy, verification and budget (`agent_loop.py:1-14`). `recovery.*` reaches the agent only as prompt text | One test per compiled field on the toy environment with a scripted fake model; switching controller and text independently gives the four T2 cells; every field has a label; Table 2 regenerates from the test ids | 40 to 60 | G1 |
| P0-15 | `strategy_schema/model.py`, `strategy_schema/edits.py` | Remove from the paper-1 edit space: `on_repeated_failure = rollback`, `rollback_target`, `max_rollbacks` and every checkpoint field. Add `switch_to:<version>` behind a flag the proposer cannot emit; `compile()` rejects it unless the E4b gates admit the arm | Rollback is files-only under Harbor (no snapshot or restore) and moves to paper 2. Mid-task switching is decided by Q2 | The default edit space contains neither rollback values nor `switch_to`; the proposer cannot produce them; `compile()` rejects `switch_to` without the flag | 4 to 8 | G1 |
| P0-16 | `adaptation_engine/first_order.py` | Hybrid rule: R = 6 fixed rounds, no early stop; K = 4 candidates of at most 2 edit operations; the parent re-run fresh each round; shared per-(task, run) seeds; statistic = integer net count of tasks solved by candidate minus parent, accept the best if at least +1, ties to lower mean MCU then the earlier version; after round 6 all 7 versions ×3 on V2_pro, S\* = most net V2 successes, ties to the earlier version; the per-loop cap formula with the V_pro shrink rule; every candidate logged | Line 157 computes deltas as float rate differences and line 163 tests `c.delta >= min_delta`. With one-task thresholds the float comparison is False for some counts, which rejects about a third of one-task gains | Exact-tie unit tests for every parent count 0 to \|V_pro\|; the cap formula gives 1,365 at 50 / 25 ×1 / 15 ×3; no early stop; the round log holds every candidate's hash, edits, outcomes and MCU | 12 to 18 | G-SEL, PREREG-1 |
| P0-17 | New lint module in `adaptation_engine/` | Reject any note, lesson or proposer-written text that contains a task id from the TB2-89 or TB-Pro lists, any URL, any command string over 40 characters, or any path from any task's files or instructions. Rejected candidates are logged and count against K | Leak channel through free text | Unit tests for each rejection class; a clean generic note passes; the false-positive rate is computed on the LINT-PILOT set | 6 to 10 | LINT-PILOT |
| P0-18 | `adaptation_engine/first_order.py` (or new modules) | LLM diagnoser and proposer on the same local model, replacing the rule-based stand-ins; B4 random proposer over the same edit space, with the same loop and budget; diagnosis and proposal calls charged to each arm's one-time adaptation cost | The current diagnoser and proposer are trivial rules (lines 12 to 16 of the module docstring) | A fake-model test produces valid diagnoses and edits; every edit passes schema validation and the lint; B4 draws only from the paper-1 edit space | 24 to 36 | E2 (PREREG-1) |
| P0-09 | `evaluation/runner.py` `summarise()` | Point-1 cost table: mean, median, IQR (interquartile range) and task-bootstrap CI of dollars per task at both rates; wall-clock labelled with GPU model, slot count and concurrency; generated tokens including reasoning; `prompt_n`; `cache_n`; MCU; pass rate per dollar; every column split by outcome and S0 task class; MCU never shown without dollars | `summarise()` reports only means of calls, tokens and dollars (meeting point 1) | Golden-file test on synthetic records; no table row prints MCU without dollars | 10 to 14 | PREREG-1 (analysis code frozen) |
| P0-19 | New `analysis/` package | Paired t on per-task differences, sign-flip permutation, GLMM (generalised linear mixed model) sensitivity with lme4 `glmer`, one-stage task bootstrap; fixed-sequence H1 to H4; analytic BoN with randomised N matching; B1 cap mixture; cross-fitted VBS and SBS; CER_test and payback T\*; net pass@k; the E0-SIM and E0-SIM2 simulations | Stage 1 freezes the analysis code before any adaptation episode | Each estimator matches a brute-force or textbook result on small synthetic data; simulations reproduce the target figures in the [analysis spec](#analysis-and-simulation-spec-for-p0-19) within simulation error | 30 to 45 | G-SEL, PREREG-1 |

Subtotal: 126 to 191 hours. With about 20 hours of gate work (G0 analysis, E0-JUDGE, LINT-PILOT, E-INTERP, Stage-1 text), this is W12 to W20 at 20 hours per week.

#### Analysis and simulation spec (for P0-19)

The targets are the design review's planning figures. Settings the design review does not state are defaults of this plan, frozen in the Stage-1 tag.

- **Software.** Python for the estimators and simulations. The GLMM runs in R with lme4 `glmer`, in a pinned Docker image (R and lme4 versions in `pins.lock`): binomial family with logit link, `pass ~ arm + (1 + arm | task)`, Laplace approximation (`nAGQ = 1`), optimiser `bobyqa` with `maxfun = 2e5`. On a singular fit or a convergence warning, refit with `(1 + arm || task)`, then `(1 | task)`, and report which model was used.
- **Bootstrap and permutation.** One-stage task bootstrap with 10,000 resamples and percentile CIs. Sign-flip test with 100,000 flips.
- **E0-SIM (size and MDE).** True per-task rates are drawn from the beta-binomial fitted to E0 by moments, with the unbiased within-task variance k/(k − 1) p(1 − p). Under the null both arms share each task's rate. Runs are independent binomial draws (rho = 0). Size is the share of 10,000 simulated datasets in which the paired t rejects at 5%. The same is repeated with little-coder's public per-task TB2 rates (successes out of 5) as the true rates. MDE is the smallest mean shift with 80% power, with per-task effects drawn with between-task variance tau² = 0.008 on the pass-rate scale and rates clipped to [0, 1]. The Monte Carlo SE of a 5% size at 10,000 replicates is about 0.2 pp.
- **E0-SIM2 (selection rule).** Base per-task logits come from the E0 fit for the actual V_pro, V2_pro and diagnosis-set tasks. Each candidate gets one edit effect on the logit scale, added to every task's logit. Effects add up along the accepted lineage. Three scenarios: full null (all effects 0), N(0, 0.3²) and N(−0.1, 0.3²). The full P0-16 rule is applied (R = 6, K = 4, at least +1 net task, the tie rules, the V2_pro ×3 choice) with rho = 0. Outputs per scenario, over 10,000 simulated loops: expected gain of the chosen version, P(chosen version worse than S0) and null edits accepted. The same code tests the cost-aware tie-break and, if TB-Pro tests write per-test results, per-test partial credit (E-N2).
- **rho.** From the A/A run: the correlation of per-task outcomes between paired runs with shared seeds. Reported only; no calibration uses it.
- **Target figures (acceptance test).** Run with the little-coder per-task rates that the design review used: paired-t size 4.3 to 5.8% at nominal 5%; power 0.54 to 0.675 for the t against 0.50 to 0.59 for sign-flip; MDE about 5.8 pp at TB2-89 × 5 and 4.3 to 4.5 pp at × 10; the hybrid rule ending at a gain of about 0.82 logit (about +6.6 pp), worse than S0 in about 3.5% of loops under N(0, 0.3²) and about 8.6% under N(−0.1, 0.3²), with about 4.4 edits accepted per loop when no edit helps. Sources: [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md#4-main-errors-found-and-corrected) section 4 (row 6) and motions [M3](DESIGN_REVIEW_2026-10.md#m3-statistics) and [M9](DESIGN_REVIEW_2026-10.md#m9-selection-noise-fix). A gap larger than two Monte Carlo SEs is explained and logged in [DECISIONS.md](DECISIONS.md) before Stage 1.

### Needed before the Stage-2 tag

| ID | File | Change | Why | Acceptance test | Effort (h) | Blocks |
|---|---|---|---|---|---|---|
| P0-20 | Run scripts for the final run | E3-AUDIT: per-trial SNI (TLS server name) and DNS logging; grep of commands and observations for the canary GUID, "terminal-bench", "tbench", "harborframework", "laude-institute", "terminal-bench-pro" and "solution/"; flags written to the trial record | TB2 runs under its upstream setting (`allow_internet = true`) to stay comparable with public results, so the leak channel is measured, not blocked | A scripted trial that echoes a flagged string is flagged; SNI and DNS lines appear per trial | 8 to 12 | PREREG-2 |
| P0-21 | Serving configuration | E-PORT emulated consumer configuration, used if no consumer machine is provided by the Stage-1 freeze: MoE offload with `--n-cpu-moe`, one slot, at the pinned context. llama.cpp has no hard VRAM cap, so the cap is set by measurement: the smallest `--n-cpu-moe` value whose peak VRAM use (`nvidia-smi`, sampled every second) stays at or below 8 GB (8,192 MiB) over a 5-task dev-slice smoke run. That value goes into `pins.lock` | Meeting point 6; Q5 default | The TB-Pro dev-slice smoke run at the chosen value completes, with logged peak VRAM ≤ 8,192 MiB | 2 to 4 | PREREG-2 |

### Added items (P0-25 to P0-30)

Work that the schedule and the experiment cards need but that had no backlog row. P0-25 and P0-26 are in the 400 pre-Stage-1 hours. P0-27's hours are already inside the 20 hours of gate work. P0-28 to P0-30 run inside the GPU weeks (see [How the plan rescales](#how-the-plan-rescales)).

| ID | File | Change | Acceptance test | Effort (h) | Week | Blocks |
|---|---|---|---|---|---|---|
| P0-25 | New `analysis/adherence.py` and a rule file | Per-field adherence rule. Each enforced field gets an event tag from P0-14's provenance and executed-or-overridden flags. Each text-only field gets a rule that maps its value to observable transcript actions (for example, verification "run tests before finishing" is followed if a test command runs after the last file edit), scored per trial as followed, not followed or not applicable. Drafted for every field in W11; rows for fields that P0-14 compiles are dropped. The validation criterion is fixed with it (default: rule and owner agree on at least 80% of 30 hand-checked trial-field pairs) | One unit test per field on synthetic transcripts; the rule file's hash is in the Stage-1 tag | 4 to 6 | W11 (draft); frozen W20 | PREREG-1 |
| P0-26 | New `evaluation/probes/memorisation.py` | E0-MEM probe: 20 TB-Pro tasks drawn with seed 20261015; prompt gives the task name only and asks for the instruction; pinned sampling, fixed seed, one call per task (non-episode model calls). Score: ROUGE-L F1 between the completion and the real instruction, plus the count of shared 8-word sequences. Reported, no threshold | Script runs on a fake model and writes one row per task with both scores | 2 to 4 | W11 (code); W13 (run) | G0 memorisation |
| P0-27 | [DECISIONS.md](DECISIONS.md) and the Stage-1 text | E-INTERP table: each possible B5 outcome (S\* − B5 CI above 0, including 0, below 0; B5 not run) and the sentence the paper will use for it | Table covers every outcome; frozen in the Stage-1 tag | 2 to 4 (inside gate work) | W20 | PREREG-1 |
| P0-28 | `analysis/adherence.py` | Validate P0-25 on TB-Pro E0 logs: the owner hand-checks 30 trial-field pairs, stratified across fields, against the rule's score | Agreement computed by script against the frozen criterion; a failed validation drops the adherence readout (G-T2) | 4 to 6 | W23 | PREREG-2 |
| P0-29 | New `selectors/` module | E4-SW selectors on TB-Pro logs only (E0 and the V2_pro runs): (1) rule table from TB-Pro category × difficulty to a version, with back-off to the TB-Pro SBS; (2) TB2-to-TB-Pro category map from TB2's public metadata; (3) LLM selector prompt (fixed prompt, pinned sampling, fixed seed), tried on TB-Pro tasks only | Rule table covers every TB-Pro category; the map covers every TB2 category; the LLM selector gives the same choice twice for the same seed; both selectors frozen by commit at Stage 2 | 8 to 12 | W22 | PREREG-2 |
| P0-30 | Label file and `analysis/` script | E-T12: a failure taxonomy fixed before labelling (the diagnoser's categories plus "other"); the owner labels 40 to 60 failed TB-Pro trajectories from E0 and E2 before seeing the diagnoser's output; Cohen's kappa between owner and diagnoser with a task-bootstrap CI | Label file with 40 to 60 rows and no TB2 trajectory; kappa script passes a unit test on a known table | 10 to 14 | W22 to W23 | Appendix (no gate) |

#### Release checklist (P0-24)

1. **Signing.** Create an SSH or GPG signing key for SK. Set `gpg.format` and `user.signingkey` in git. Publish the public key in the repository. Tag with `git tag -s` and check with `git tag -v`.
2. **Zenodo.** Switch on the GitHub repository in Zenodo's GitHub settings. Publish a GitHub release from the signed tag; Zenodo archives it and mints a DOI. Do a dry run first on Zenodo Sandbox (sandbox.zenodo.org) with a test repository.
3. **OSF.** Create a registration with the "OSF Preregistration" template. Quote the tag name and SHA, the Zenodo DOI, the ledger hash and the `pins.lock` hash.
4. **Log.** Record the tag, DOI and OSF link in [DECISIONS.md](DECISIONS.md).

### Conditional items (not in the dated schedule)

| ID | File | Change | Condition | Effort (h) |
|---|---|---|---|---|
| P0-22 | New sandbox container for B5 | Per-trial container whose only network route is the llama.cpp endpoint, killed on timeout, never in the host Harbor process; escape test; 10-proposal smoke test | B5 attempted (Tier C rank 4, or promoted by Q8). Within 5 engineering days after G-INFRA | ≤ 40 (about 2 weeks at 20 h; moves every later week by about 2) |
| P0-23 | Controller (`compile()` path) | Execute `switch_to:<version>` when `recovery.max_retries` is exhausted under `recovery.retry_on`, behind the flag; unit test | Q2 answered (b) or (c) | 8 to 16 (design review: 1 to 2 days, shared with G1) |

**Backlog total** (P0-01 to P0-21 and P0-24 to P0-30, with P0-27 counted in gate work): 333 to 506 hours, midpoint about 420, before gate work, analysis of results and writing. These are estimates.

---

## 6. Compute schedule

### Throughputs

- **Planning (verified): 213.5 episodes per GPU-day** at concurrency 1. This is 86,400 s divided by the 404.7 s mean trial time over all 445 trials of little-coder's public Qwen3.6-35B-A3B run on TB2 (trial records in the [TB2 leaderboard dataset](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard)). It was measured on an 8 GB-VRAM laptop with MoE (mixture-of-experts) offload to the CPU, so it is a conservative proxy with a ±30% band (149 to 278 per GPU-day). The older 270 s per trial and 320 to 340 per day figures are wrong and are not used.
- **Optimistic: 277.55 episodes per GPU-day**, the top of that band. A figure of about 500 per day at concurrency 4 on a 32 GB-class GPU was also proposed, but it is not measured (unverified) and is not used.
- The real rate r is measured on TB-Pro in E-P0 and E0, and the plan is re-costed at G0.

### GPU-days per phase (core plan, main GPU)

| Phase | Weeks | Items | Episodes | GPU-days at 213.5 | GPU-days at 277.55 |
|---|---|---|---|---|---|
| 0b. Calibration | W12 to W13 | E-P0 150, E1 60, E0 600 | 810 | 3.79 | 2.92 |
| 2. Adaptation | W21 to W23 | E2: S\*1, B4, S\*2 loops, 1,365 each | 4,095 | 19.18 | 14.75 |
| 3. Stage-2 freeze | W24 | E4b pilot (reserve) | 40 | 0.19 | 0.14 |
| 4. Final run | W24 to W27 | E3 3,249; E-ATTR 480; E-T2 advised 445; E4b arm 267 (reserve); E-PORT 267 | 4,708 | 22.05 | 16.96 |
| **Core total** | | | **9,653** | **45.21** | **34.78** |

Notes:

- Within the final run: E3 15.22 GPU-days (11.71 optimistic), E-ATTR 2.25 (1.73), E-T2 2.08 (1.60), E4b arm 1.25 (0.96), E-PORT 1.25 (0.96).
- At the pessimistic end of the band (149.5 per day) the core takes 64.59 GPU-days.
- If a consumer machine runs E-PORT, the main-GPU core is 9,386 episodes (43.96 GPU-days).
- If Q2 is answered (a) or not answered by the Stage-1 freeze, the 307-episode E4b reserve returns to contingency.

### Outside the core total

| Item | Episodes | GPU-days at 213.5 | GPU-days at 277.55 | Funded from |
|---|---|---|---|---|
| G-INFRA smoke run (W11) | 5 | 0.02 | 0.02 | Contingency |
| E0 top-up (only if C3 < 40) | ≤ 400 | ≤ 1.87 | ≤ 1.44 | Contingency |
| Each fallback model | ≤ 1,150 | ≤ 5.39 | ≤ 4.14 | Deducted from the available GPU-days |
| 1× leaderboard fallback (only if censoring is invalid) | 178 | 0.83 | 0.64 | Contingency |
| Non-episode model calls (judge about 1,490 calls, selector 89, diagnosis and proposal calls) | measured in MCU, converted at G0 | n/a | n/a | Contingency |
| Contingency in total (10,500 − 9,653) | 847 | 3.97 | 3.05 | Named uses only, never new arms |

### Tier C and conditional items

Admitted only by the G0 budget rule, in rank order, each only if its own gate passes, within the 12,500 absolute cap. Each one lengthens the GPU blocks by its GPU-days.

| Rank | Item | Episodes | GPU-days at 213.5 | GPU-days at 277.55 | Where it lands |
|---|---|---|---|---|---|
| 1 | E5-DEMO (only if Q4 says the second-order loop is essential and option (ii) is chosen) | ≤ 1,365 | 6.39 | 4.92 | Phase 2, one more loop |
| 2 | E-T2 enforce-only cell | 445 | 2.08 | 1.60 | Phase 4 |
| 3 | E-T1lite (TMax-9B, including a 20-episode pilot) | 554 | 2.59 | 2.00 | Pilot in W13 to W20; TB2 rows in Phase 4 |
| 4 | E-B5 (1,365 adaptation + 445 evaluation) | 1,810 | 8.48 | 6.52 | Phase 2 and Phase 4, plus P0-22 owner time |

Headroom from the core to the absolute cap is 2,847 episodes before any contingency use. Ranks 2 to 4 together need 2,809, so they fit only if little contingency is spent. If E5-DEMO is triggered, B5 does not fit.

### Caps

| Cap | Episodes | GPU-days at 213.5 | GPU-days at 277.55 |
|---|---|---|---|
| Core | 9,653 | 45.21 | 34.78 |
| Core plus contingency | 10,500 | 49.18 | 37.83 |
| Absolute, including Tier C | 12,500 | 58.55 | 45.04 |
| Floor | 6,224 | 29.15 | 22.42 |

API spend for paper-1 arms is $0. Any API use needs a logged amendment with its own cap.

### Cut order with both throughputs

Applied at G0 by the budget rule, each cut costed on the plan left by the earlier ones, until the plan fits C. Cuts 4 and 5 must be decided before the Stage-1 tag. After the Stage-1 tag only cuts 1 to 3 and 6 may be applied.

| Step | Cut | Change | Plan after (episodes) | GPU-days at 213.5 | GPU-days at 277.55 |
|---|---|---|---|---|---|
| 0 | Tier C is not admitted when C < core + item. If headroom shrinks, drop B5, then T1-lite, then enforce-only, then E5-DEMO | n/a | 9,653 | 45.21 | 34.78 |
| 1 | E-ATTR to 2 arms (top changed group + lessons/notes-off) | −240 | 9,413 | 44.09 | 33.91 |
| 2 | E-T2 advised cell k 5 → 3 | −178 | 9,235 | 43.26 | 33.27 |
| 3 | B1 ×5 → ×3 (hard cap 614) | −410 | 8,825 | 41.33 | 31.80 |
| 4 | R 6 → 4 rounds in all three loops (1,365 → 925 each) | −1,320 | 7,505 | 35.15 | 27.04 |
| 5 | Drop the S\*2 loop; S\* = S\*1 ×10; TB2 episodes unchanged; claims about the realised strategy; only before the Stage-1 tag | −925 | 6,580 | 30.82 | 23.71 |
| 6 | S0 pool ×10 → ×6; BoN rows N = 1 to 5 and 6 | −356 | 6,224 | 29.15 | 22.42 |

The floor is 6,224 episodes. It is 5,957 if E-PORT runs off the main GPU, 5,917 if the E4b reserve is released, and 5,650 with both. Below the floor, halt before Stage 1 and escalate to Prof. Abdelrazek.

**Never cut:** G-INFRA, G1, E-P0, E0, all 89 TB2 tasks held out, S0 ≥ 6 and S\* ≥ 10 runs per task, B4 ×5, B1, BoN, the point-1 cost table, the point-2 per-task table, the index variants and the selector (0 episodes), E-PORT, the lessons/notes-off arm, the E4b reserve until the point-5 answer or the Stage-1 freeze, pre-registration and the held-out ledger.

### What each cut does to the calendar

At 213.5 per day, cuts 1 to 3 shorten the final run by 3.88 GPU-days in total (about half a week). Cut 4 shortens adaptation by 6.18 GPU-days (about one week). Cut 5 removes a further 4.33 GPU-days of adaptation. Cut 6 shortens the final run by 1.67 GPU-days. None of them shortens the owner-hours on the critical path.

---

## 7. Decisions owed by Prof. Abdelrazek

All are sent in W1. Each default applies only if there is no answer by the stated week, and is logged in [DECISIONS.md](DECISIONS.md) as "defer to professor, default applied" and told to him. The question sheet, with full wording, options and defaults, is [DECISIONS.md section 1](DECISIONS.md#1-open-decisions). [DESIGN_REVIEW_2026-10.md section 6](DESIGN_REVIEW_2026-10.md#6-questions-for-prof-abdelrazek) has a one-table summary.

| Q | Topic (meeting point) | Needed by | Why then | Default |
|---|---|---|---|---|
| Q5 | GPU-days D, which GPU, consumer machine (6) | W7 in practice (host for P-M2); formally W13 (G0 rule) | The run host is on the critical path from W7. D sets capacity C at G0 | Plan the full core and halt at G0 if C is below the floor; E-PORT emulated on the main GPU |
| Q6 | Fallback model order; what to do if no local model passes (6) | W13, only if a fallback is needed | G0 fitness | Stated order; keep the best local model if no answer within one week |
| Q3 | Replace the committed split with all 89 TB2 tasks held out and adaptation on TB-Pro (2) | W20 (Stage-1 freeze); W11 preferred | P-M2 work in W7 to W11 assumes the TB-Pro route | (i) approve, logged as superseding the 2026-10-15 action |
| Q1 | Reading of "intelligence index" (4) | W20 | The index headline label is frozen in Stage 1 | Reading (a): CER_test headline with T\* companion |
| Q2 | Reading of "strategy switching" (5) | W20 | The E4b arm must be written into Stage 1 | (a) only; mid-task switching to paper 2 |
| Q4 | Scope: second-order loop, AppWorld and rollback to paper 2 | W20 | E5-DEMO would need a Tier C slot | (i) defer all three to paper 2 |
| Q8 | A free-form code-edit baseline (B5) | W11 preferred; W20 at the latest | P0-22 would start right after G-INFRA | B5 stays Tier C rank 4 |
| Plan item 1 | Duration, start, hours per week, supervision | W13 (before G0) | Every date in this plan assumes 20 hours per week | 24-week target; schedule at 20 hours per week, rescaled once hours are agreed |
| Plan item 6 | Same or stronger model for the diagnoser and proposer | W20 | Model pins freeze in Stage 1 | (a) same model |
| Plan item 11 | Venue and authorship | W28 (write-up start); earlier if NeurIPS 2027 is wanted | Page budget and write-up start | None |

A short weekly update to Prof. Abdelrazek is suggested, as in [DECISIONS.md](DECISIONS.md#plan-item-1-duration-start-date-hours-per-week-and-supervision-rhythm) plan item 1.

---

## 8. Schedule risks

This table covers the schedule only. The full risk register, with likelihood, impact, triggers and the gates each risk is tied to, is [RISK_REGISTER.md](RISK_REGISTER.md).

| Risk | Effect on the plan | Response |
|---|---|---|
| Engineering takes the top of each range (506 h instead of about 420) | About 4 more weeks at 20 hours per week | Re-plan at G-INFRA (W11) and at G1 (W20); report the slip to Prof. Abdelrazek |
| The run host arrives after about W13 | Every later week moves by the delay | Move pre-Stage-1 work forward (section 3) |
| r measured below 150 per GPU-day, or a median episode above 600 s | The G0 rule applies cuts | Cut order above; never a model switch |
| A fallback model is needed | Up to 5.39 GPU-days and about one week per fallback | Model-fallback rule in G0 |
| TB-Pro route fails at G-ROUTE | E-RESPLIT replaces the TB-Pro pools; held-out set H52 | Logged deviation; MDE about 7.6 pp stated in the abstract |
| Professor answers arrive after W20 | Defaults are frozen in Stage 1 | Logged; later changes are amendments |
| Tier C items admitted | GPU blocks lengthen by their GPU-days; B5 also adds about 2 owner-weeks | Admitted only by the G0 rule and their own gates |

Planned against realised episodes, GPU-days and weeks will be published as an appendix table.
