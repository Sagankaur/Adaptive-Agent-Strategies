# Decisions

Sagandeep Kaur, for discussion with Prof. Mohamed Abdelrazek (Deakin A2I2). Created 2026-10-20.

**Status.** This is the decision record of the project. It has three parts:

1. open decisions, most of them for you;
2. the outcomes of the design review of 2026-10-20 ([DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md)), proposed by Sagandeep Kaur. You may overrule any of them;
3. a log of deviations from earlier plans and of defaults applied.

No experiment has been run and no model has been called. Every episode count, GPU-day and dollar figure here is an estimate. GPU-days use the planning rate of 213.5 episodes per GPU-day. That rate was measured on a laptop and is used as a proxy with a ±30% band ([DESIGN_REVIEW_2026-10.md, section 4](DESIGN_REVIEW_2026-10.md#4-main-errors-found-and-corrected)).

**Who does what.** You decide the questions marked Q and the three plan items. Sagandeep Kaur sends them, records each answer here, and applies the default if no answer arrives by the deadline gate. The one exception is the change to internship objectives O4 and O6 in Q4: it has no default and needs your explicit answer. Every applied default is logged in section 3 as "defer to professor, default applied", and you are told in one line.

### Terms used

| Term | Meaning |
|---|---|
| TB2 | Terminal-Bench 2.0: 89 tasks, pinned at task commit `2fd12b8` |
| TB2-89 | All 89 TB2 tasks, held out for the final pre-registered run |
| TB2.1 | A later revision of TB2 that fixes 28 of its 89 tasks. Several related papers report on it. Its scores are not directly comparable with scores at our pin |
| Terminal-Bench 4.0 | The current Terminal-Bench, now a continuous benchmark with semantic versions. It removed 8 tasks, fixed 19 and sets an 8-hour agent timeout. The Artificial Analysis index uses it. Not used here |
| TB-Pro | terminal-bench-pro: 200 public terminal tasks ([GitHub](https://github.com/alibaba/terminal-bench-pro)) |
| A, V, V2, M, H | Task pools; the number after the letter is the task count (A25 = 25 tasks). A adaptation, V selection (screen), V2 final choice, M meta-training for the second-order loop, H held out |
| Contested task | A task solved in some but not all runs of the same strategy |
| Sibling pair | Two near-duplicate TB2 tasks. If they sit in different pools, what is learnt on one leaks to the other |
| Episode | One agent attempt at one task, that is, one Harbor trial |
| GPU-day | 24 hours of one GPU |
| k | Runs per task |
| S0 | The hand-written starting strategy (baseline B0) |
| S\*1, S\*2, S\* | The strategies chosen by adaptation loops with seed 1 and seed 2. S\* is their per-task average |
| B1, BoN, B4, B5 | Reflection-retry; best-of-N (baseline B2); random strategy search; free-form code-edit adaptation (optional) |
| MCU | Model compute units: a × prompt tokens + b × generated tokens, from the per-call timings of llama.cpp (the model server) |
| CER_test | Compute-equivalence ratio at test time: how many S0 best-of-N samples S\* is worth per task |
| T\* | Payback: the number of tasks after which the one-time adaptation cost is recovered |
| VBS, SBS | Virtual best solver (the best strategy version for each task) and single best solver (the best version overall) |
| pp | Percentage points |
| MDE | Minimum detectable effect: the smallest true difference found with 80% power at two-sided alpha 0.05 |
| CI | Confidence interval (95% unless stated) |
| Stage 1, Stage 2 | The two pre-registration tags: before the first adaptation episode, and before the first TB2 episode |
| Stage-1 freeze | The date the Stage-1 tag is signed. Most defaults apply then. [EXECUTION_PLAN.md](EXECUTION_PLAN.md) plans it for week 20, the week of 2027-03-01 (estimate) |
| G0 | The gate after Phase 0 calibration, where the measured throughput sets what can run. Planned for week 13, the week of 2027-01-11 (estimate) |
| W1, W2, ... | Weeks of [EXECUTION_PLAN.md](EXECUTION_PLAN.md). W1 starts on 2026-10-19 |
| Tier C | Optional work, admitted only within the absolute cap of 12,500 episodes, in a fixed order |
| O1 to O6 | The six internship objectives (below). They are not the six meeting points of 2026-10-14 |

Experiment ids (E0, E3, E-PORT and so on) refer to the cards in [EXPERIMENTS.md](EXPERIMENTS.md). Motion ids (M1 to M16) refer to the blocks in [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md).

### Internship objectives (O1 to O6)

From [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 1. None is dropped.

| Objective | Status |
|---|---|
| O1. Strong baselines: a fixed strategy, reflection-retry and best-of-N at matched cost | Paper 1 |
| O2. The strategy as an explicit, versioned object that can be searched | Paper 1 |
| O3. An adaptation mechanism that proposes, selects or combines strategy changes from past outcomes | Paper 1 |
| O4. A second-order loop that revises and evaluates the adaptation mechanism itself | Proposed for paper 2. Moves only with your answer to Q4 |
| O5. Generalisation to held-out tasks, with strict separation of adaptation and test tasks | Paper 1 (adapt on TB-Pro, test on TB2) |
| O6. Transfer of learned strategies to a second benchmark family | Proposed for paper 2. Moves only with your answer to Q4. Paper 1 covers only transfer from TB-Pro to TB2, within terminal tasks |

---

## 1. Open decisions

This is the one list of questions for you. [OVERVIEW.md](OVERVIEW.md) and [EXPERIMENTS.md](EXPERIMENTS.md) summarise it and link here. Where they differ, this list holds.

There are ten in all: seven questions (Q1 to Q6 and Q8) and three items left from the 2026-10-15 plan (plan items 1, 6 and 11).

| Q | Topic (meeting point) | Urgent | Answer by (estimate) | Default if no answer | Why it matters |
|---|---|---|---|---|---|
| [Q1](#q1-intelligence-index-meeting-point-4) | Meaning of "intelligence index" (4) | Yes | W20, 2027-03-01 (Stage-1 freeze) | (a), CER_test with T\* | The headline index is frozen in the Stage-1 tag |
| [Q2](#q2-strategy-switching-meeting-point-5) | Meaning of "strategy switching" (5) | Yes | W20, 2027-03-01 | (a) only | Reading (b) needs controller work and a pilot before Stage 2 |
| [Q3](#q3-task-pools-meeting-point-2) | Task pools: replace the committed split (2) | Yes | W11, 2026-12-28 preferred; W20, 2027-03-01 at the latest | (i) approve | Every pool, power figure and budget line assumes (i) |
| [Q4](#q4-scope-of-paper-1) | Scope of paper 1: second-order loop, AppWorld, rollback | Yes | W20, 2027-03-01 | Plan: (i). Objectives O4 and O6: no default | It changes what the internship delivers (O4 and O6) |
| [Q5](#q5-compute-meeting-point-6) | Compute: GPU, GPU-days, who provides them, consumer machine (6) | Yes, first | Run host from W7, 2026-11-30; GPU-days by G0, W13, 2027-01-11; consumer machine by W20 | E-PORT emulated; plan the full core; halt at G0 below the floor | No episode can run without a GPU |
| [Q6](#q6-fallback-models-meeting-point-6) | Fallback models (6) | No | Only if the primary model fails at G0 (W13); then within one week | Stated order; (b) if no local model passes | Model choice at G0 |
| [Q8](#q8-a-free-form-code-edit-baseline-informational) | Free-form code-edit baseline B5 | No | W11, 2026-12-28 preferred; W20 at the latest | B5 stays Tier C rank 4 | Order of optional work |
| [Plan item 1](#plan-item-1-duration-start-date-hours-per-week-and-supervision-rhythm) | Duration, start, hours, supervision | No | Before G0, W13, 2027-01-11 | 24-week target; schedule at 20 hours per week | Sets every date and the venue |
| [Plan item 6](#plan-item-6-model-for-the-diagnoser-and-proposer) | Same or stronger model for diagnoser and proposer | No | W20, 2027-03-01 | (a) same model | Model pins freeze at Stage 1 |
| [Plan item 11](#plan-item-11-publication-target-and-authorship) | Venue and authorship | No | W28, 2027-04-26; earlier if NeurIPS 2027 is wanted | None | Page budget and write-up start |

### 1.1 The five most urgent

Q1 to Q5, in number order. Q5 is needed first.

#### Q1. Intelligence index (meeting point 4)

**Question.** Did you mean (a) one number for how efficiently our agent improves, that is, held-out gain per unit of adaptation compute, after Chollet's "skill-acquisition efficiency"; (b) a composite score over several benchmarks, like the Artificial Analysis Intelligence Index, used to compare and choose models; or (c) something else? If (a), one number or two? May we call it "adaptation efficiency (after Chollet)"?

The source for reading (a) is [On the Measure of Intelligence (Chollet, arXiv 1911.01547, Nov 2019)](https://arxiv.org/abs/1911.01547). For reading (b), the [Artificial Analysis methodology page](https://artificialanalysis.ai/methodology/intelligence-benchmarking) describes version 4.3.2 as a weighted average of 10 evaluations, with Terminal-Bench 4.0 (not 2.0; see Terms) at 10% weight.

**Why the amortised ratio is not a headline.** A ratio that spreads the adaptation cost over our 89 test tasks is at most about 0.6 by construction. Its numerator c_eq is at most about 10 episodes per task, because best-of-N uses at most P = 10 samples of S0. Its denominator is about 1 episode per task for S\*, plus one loop's 1,365 adaptation episodes spread over 89 tasks, about 15.3. So the ratio is at most about 10 / 16.3, about 0.6. It is therefore shown only as a curve over the number of tasks.

**Options and what each changes.**

| Option | What changes |
|---|---|
| (a) One number | CER_test is the headline. 0 extra GPU-days |
| (a) Two numbers | CER_test is the headline and T\* its companion. 0 extra GPU-days |
| (b) Composite for model choice | The composite becomes a named paper-1 model-choice table, from published scores plus the TB-Pro dev slice, never from TB2 held-out runs. CER_test stays as a secondary efficiency analysis. 0 extra GPU-days. If you also want our method scored across benchmarks, AppWorld re-enters as S0 against S\* on test-normal at k = 1, admitted as Tier C within the 12,500 cap. It is costed from the adapter before any commitment. For scale only: if test-normal has 168 tasks (not re-checked), that is about 336 episodes, about 1.6 GPU-days at the TB2 rate (a proxy), plus adapter work |
| (c) Something else | Computed from logs already budgeted. No episodes are reserved |

Under every option, all candidates are computed after the final run from logs already budgeted, at 0 extra episodes, and none feeds back into adaptation. Δp (gain in pass rate) and C (cost) are always shown next to any index. A Chollet-weighted variant is computed only if its weights are pre-registered at Stage 1.

**Recommendation.** (a) with two numbers. T\* shows the one-time adaptation cost, which CER_test alone leaves out.

**Default if no answer.** (a), with CER_test as headline and T\* as companion. The amortised ratio and Δp/C go to the appendix, and the composite appears only in the model-choice table. Logged against meeting item 4 (log entry 14).

**Deadline gate.** The Stage-1 freeze.

**Owner.** You decide.

**Source.** [M5](DESIGN_REVIEW_2026-10.md#m5-the-intelligence-index-deferred-to-the-professor), [M14](DESIGN_REVIEW_2026-10.md#m14-other-threads).

#### Q2. Strategy switching (meeting point 5)

**Question.** Did you mean (a) choosing one strategy version per task, from task features before starting; (b) changing strategy in the middle of a task when it gets stuck; (c) both; or (d) as (a), but choosing after a few probe steps on the task?

Paper 1 carries reading (a) whatever the answer, at no extra runs.

**Options and what each changes.**

| Option | What changes |
|---|---|
| (a) One version per task | Offline switching (E4-SW): a library of up to 5 versions {S0, S\*1, S\*2, B4-final, and B5-final if run}, cross-fitted VBS-SBS headroom with a CI, two selectors frozen on TB-Pro data before any TB2 episode, regret and cost per task. 0 extra episodes. The 307-episode reserve (1.44 GPU-days) returns to contingency and mid-task switching moves to paper 2 |
| (b) Mid-task switching | Adds E4b, exploratory: S\*1 with a mid-task `switch_to` on TB2-89 at k = 3 (267 episodes) against S\*1 × 5, MDE about 6.6 pp. It needs three gates: the answer before the Stage-1 freeze; a flag-gated `switch_to` in `compile()` with unit tests; and a 40-episode TB-Pro pilot in which the switch fires on at least 6 of 40 trials with at most 2 infrastructure errors. About 307 episodes in all (about 1.44 GPU-days). These are already reserved inside the core, so no extra GPU-days are requested |
| (c) Both | (a) and (b). Same GPU-days as (b) |
| (d) (a) plus the probe-based selector | A selector that runs a few probe steps before choosing needs new episodes. Not yet costed. They would come from contingency or Tier C headroom, not from the core |

**Recommendation.** The meaning is yours to state. If you have no strong view, (a) costs no extra runs.

**Default if no answer.** (a) only. Mid-task switching moves to paper 2, and the reserve returns to contingency. Logged against meeting item 5 (log entry 15).

**Deadline gate.** The Stage-1 freeze. The E4b arm and its gate must be written into the Stage-1 pre-registration.

**Owner.** You decide.

**Source.** [M6](DESIGN_REVIEW_2026-10.md#m6-strategy-switching-deferred-to-the-professor), [M7](DESIGN_REVIEW_2026-10.md#m7-scope-of-paper-1), [M12](DESIGN_REVIEW_2026-10.md#m12-compile-as-a-gate).

#### Q3. Task pools (meeting point 2)

**Question.** May we replace the committed split (A25 / V12 / M15 / H37, recorded on 2026-10-15 as done for meeting item 2) with all 89 TB2 tasks held out and adaptation on deduplicated TB-Pro?

**Why it is asked.** In the committed split, A is adaptation (25 tasks), V selection (12), M meta-training for the second-order loop (15) and H held out (37). In the public reference run (little-coder with Qwen3.6-35B-A3B, 5 attempts per task), H37 has only 11 contested tasks, solved in some but not all of the 5 attempts: 22 were never solved and 4 always solved. A sibling pair straddles H when one task is in H and its near-duplicate is in a pool used before the final run, so what is learnt on one leaks to the other. All 9 known sibling pairs straddle H (the other task is in A for 5 pairs, in M for 3 and in V for 1).

**Options and what each changes.**

| Option | What changes |
|---|---|
| (i) Approve | TB2-89 is used only in the final pre-registered run. Adaptation, selection and calibration move to deduplicated TB-Pro, after a CPU-only route pilot (image builds, dedup, a check with Harbor's Oracle agent, which needs no model, licence, disk). Planning MDE about 5.8 pp at k = 5. Research question 2 (RQ2, generalisation; [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 1) is labelled "cross-source (TB-Pro to TB2)". If the pilot fails, the fallback is a sibling-grouped TB2 re-split with 52 held-out tasks (H52), MDE about 7.6 pp, logged as a deviation. Already in the core |
| (ii) Keep the committed split | H37 stays, with an MDE of about 9.5 pp at k = 5 and the sibling leak. The review's pool sizes and budget assume (i) and would have to be re-derived (not done) |
| (iii) Use the TB2 re-split directly | H52 plus A15 / V12 / V2 10, with sibling groups, seed 20261015, stratified by category and difficulty. MDE about 7.6 pp. No TB-Pro images to build, and adaptation and test come from one distribution. Fewer tasks are held out |

**Recommendation.** (i).

**Default if no answer.** (i), logged as superseding the 2026-10-15 split action for meeting item 2.

**Deadline gate.** The Stage-1 freeze; W11 (2026-12-28) preferred, because the route pilot in W7 to W11 assumes the TB-Pro route. The CPU-only route pilot can start before the answer.

**Owner.** You decide. Sagandeep Kaur runs the pilot and records the GO or NO-GO.

**Source.** [M2](DESIGN_REVIEW_2026-10.md#m2-task-pools), [M10](DESIGN_REVIEW_2026-10.md#m10-leak-fixes).

#### Q4. Scope of paper 1

**Question.** The second-order loop, AppWorld transfer and rollback cannot be powered on one GPU. We propose to move them to a second paper, and with them internship objectives O4 (second-order loop) and O6 (transfer to a second benchmark family). Is that acceptable, or is the second-order loop essential for the internship?

**Options and what each changes.**

| Option | What changes |
|---|---|
| (i) Defer all three to paper 2 | Paper 1 = RQ1 + RQ2 (cross-source) + a lean RQ4. No episodes go to the second-order loop, AppWorld or rollback. O4 and O6 become paper-2 objectives. 0 extra GPU-days |
| (ii) Essential: a descriptive demonstration | One edit of the adaptation mechanism, made from the logs of the three adaptation loops, then one adaptation loop under the edited mechanism, on TB-Pro only (E5-DEMO). At most 1,365 episodes (about 6.4 GPU-days; 9.1 at the slow end of the band), no inferential claim, never on TB2. Tier C rank 1, so it needs the Tier C GPU-days in Q5 |
| (iii) Essential: more GPU-days for a powered design | A powered comparison of two mechanisms needs 27 to 32 independent loops per arm: 73,710 to 87,360 episodes, about 345 to 409 GPU-days. This is not feasible on one GPU |

AppWorld re-enters paper 1 only through Q1: if you choose reading (b) and want our method scored across benchmarks.

**Recommendation.** (i).

**Default if no answer.** For the paper-1 experiment plan, (i): no episodes go to the three items. For the internship objectives, there is no default. O4 and O6 move to paper 2 only with your explicit answer. If none has arrived by the Stage-1 freeze, we ask again before the tag is signed, and O4 and O6 stay marked open (log entry 17).

**Deadline gate.** The Stage-1 freeze.

**Owner.** You decide.

**Source.** [M7](DESIGN_REVIEW_2026-10.md#m7-scope-of-paper-1).

#### Q5. Compute (meeting point 6)

**Question.** How many dedicated GPU-days (D) can we count on before the analysis deadline, and on which GPU? Who provides them: a university GPU cluster, grant-funded cloud rental, or a lab machine? Can you or we provide a consumer-class x86-64 machine for the portability check?

**What is requested.** This replaces the earlier compute request and open decision 2 of the 2026-10-15 plan ("who pays for compute, and the cap").

| Item | Request |
|---|---|
| Research machine | 1 NVIDIA GPU with at least 24 GB (32 GB or more recommended for 2 or more parallel slots), 16 cores, 64 GB RAM, 500 GB NVMe disk (1 TB recommended), nftables available, dedicated during budgeted runs |
| Portability machine | A consumer-class x86-64 machine with at least 8 GB of GPU memory (VRAM), 32 GB RAM and Docker |
| GPU-days | At least 49 (core plus contingency); about 59 if any optional item is wanted. Tiers below |
| API budget | None for paper-1 arms. Any API use needs a logged amendment with its own cap |

Why 24 GB is the minimum (estimate): the primary model fully on the GPU needs about 23.4 GiB for one slot at 64k context with an f16 key-value (KV) cache. More slots need a q8_0 KV cache or offloading part of the model to the CPU. Apple Silicon is out of scope, because the task images are amd64 only.

**GPU-days, in tiers.** At the planning rate. The band column applies the ±30% rate band, from a faster to a slower GPU.

| Tier | Episodes | GPU-days | Band (±30%) | What it pays for |
|---|---|---|---|---|
| Floor | 6,224 | 29.15 | 22.4 to 41.6 | The smallest paper 1, after all six cuts |
| Core | 9,653 | 45.21 | 34.8 to 64.6 | Every core experiment |
| Core plus contingency | 10,500 | 49.18 | 37.8 to 70.3 | Also the E0 top-up, the judge (about 1,490 calls), the selector, the diagnosis and proposal calls, and reruns after infrastructure errors |
| Absolute cap, with Tier C | 12,500 | 58.55 | 45.0 to 83.6 | Also optional items in a fixed order |

The judge, selector, diagnosis and proposal calls run in every adaptation loop, but they are paid from contingency. So the core figure alone does not cover a complete paper 1.

**What each option elsewhere adds.**

| Option | Extra episodes | Extra GPU-days | Paid from |
|---|---|---|---|
| Q1 (b) with AppWorld scoring | Not yet costed (about 336 at k = 1, for scale) | About 1.6 (proxy) | Tier C headroom |
| Q2 (b) or (c) | 307 | 1.44 | Already reserved in the core |
| Q2 (d) probe-based selector | Not yet costed | Not yet costed | Contingency or Tier C headroom |
| Q4 (ii) E5-DEMO | At most 1,365 | 6.39 | Tier C headroom |
| Q6, each fallback model | At most 1,150 | 5.39 | Deducted from D |
| Q8 "Yes" (B5) | 1,810 | 8.48 | Tier C headroom |

Tier C items share the 2,847 episodes (13.3 GPU-days) between the core and the 12,500 cap, less any contingency used. E5-DEMO and B5 together need 3,175 episodes (14.9 GPU-days), so both do not fit.

**Rough cost in dollars (estimate).** RunPod listed an RTX 4090 (24 GB, the minimum spec) at $0.34 per hour (Community Cloud) and $0.89 per hour (Secure Cloud) when read on 2026-10-20. A GPU with 32 GB or more costs more per hour; no rate was checked. One GPU-day is 24 GPU-hours.

| Tier | GPU-hours | At $0.34 per hour | At $0.89 per hour |
|---|---|---|---|
| Floor | 700 | about $240 | about $620 |
| Core | 1,085 | about $370 | about $970 |
| Core plus contingency | 1,180 | about $400 | about $1,050 |
| With Tier C | 1,405 | about $480 | about $1,250 |
| Core at the slow end of the band (64.6 GPU-days) | 1,550 | about $530 | about $1,380 |

The planning rate comes from a laptop with 8 GB of VRAM. A desktop GPU is likely faster, so real costs may be lower. On a university or lab GPU the same need is dedicated time: 45 to 59 GPU-days is about 6.5 to 8.5 weeks of one GPU running around the clock, within the GPU phases from W12 to W27 (2027-01-04 to 2027-04-25). Electricity alone for an RTX 4090 is about 12 to 13 Australian cents per hour ([GLOSSARY.md](GLOSSARY.md)), about AUD 130 to 140 for the core.

**Options and what each changes.**

| Option | What changes |
|---|---|
| (a) Consumer machine provided; D stated | The portability check (E-PORT: S0 on TB2-89 × 3, 267 episodes) runs off the main GPU. The core falls to 9,386 episodes (43.96 GPU-days). An optional S\*1 × 2 run (178 episodes) can be added on that machine. The paper states the real minimum spec |
| (b) No consumer machine; D stated | E-PORT runs on the main GPU in an emulated configuration: VRAM capped at 8 GB, with part of the model offloaded to the CPU. The core stays at 9,653 episodes (45.21 GPU-days). The paper says the spec is emulated |
| (c) D below about 29 GPU-days | This is below the floor. Work halts before Stage 1, and we choose between more GPU-days, a faster GPU, or a narrower paper 1 |

If D lies between the floor and the core, the cut order in [TECHNICAL_PLAN.md, section 9](TECHNICAL_PLAN.md#9-budget-amended-2026-10-20) applies at G0. Capacity there is C = 0.9 × r × D_rem, where r is the measured episodes per GPU-day and D_rem the dedicated GPU-days left.

**Recommendation.** At least 49 dedicated GPU-days (core plus contingency) on a GPU with 32 GB or more, plus a consumer machine. That covers the core and the model calls that contingency pays for, at the planning rate. About 59 if you want any optional item (Q1 (b) with AppWorld, Q4 (ii) or Q8 "Yes"). The consumer machine makes the point-6 portability result direct rather than emulated.

**Default if no answer.** Option (b). Plan the full core, and halt at G0 if capacity is below the floor. The emulated E-PORT is logged as "defer to professor" against meeting item 6 (log entry 16).

**Deadline gate.** The run host (GPU, Docker and disk) is needed from W7 (2026-11-30) for the TB-Pro image builds of the route pilot, and from W11 (2026-12-28) for the smoke run. The end date holds if it arrives by about W13 (2027-01-11). The first GPU episode, Phase 0 bring-up (E-P0), is planned for W12 (week of 2027-01-04). D is needed at G0 (W13). The consumer machine is needed by the Stage-1 freeze (W20, 2027-03-01).

**Owner.** You decide. Sagandeep Kaur sends the revised request.

**Source.** [M11](DESIGN_REVIEW_2026-10.md#m11-infrastructure), [M16](DESIGN_REVIEW_2026-10.md#m16-total-compute-and-the-cut-order).

### 1.2 Other open decisions

#### Q6. Fallback models (meeting point 6)

**Question.** If the primary model fails the TB-Pro calibration, may we use this local fallback order? And if no local model passes, which way should we go?

The primary model is Qwen3.6-35B-A3B (Q4_K_M), served locally. The recorded 20 to 40% starting band is checked on public TB2 scores only. The little-coder reference run scores 106/445 = 23.8% overall and 100/410 = 24.4% on the 82 TB2 tasks that did not change between its task commit (`69671fb`) and our pin, so the primary model passes.

| Order | Model | Note |
|---|---|---|
| 1 | Qwen3.5-35B-A3B, Q4_K_M | Public TB2 figures disagree: 40.5% on the vendor card, 18.0% for the initial harness on a 64-task subset in Self-Harness. Logged as ambiguous |
| 2 | TMax-9B, Q4_K_M | Apache-2.0. Vendor TB2 score 27.2%, from its own harness. Not in the original candidate list |
| 3 | Nemotron-Terminal-32B, Q4_K_M | Only on a GPU with 32 GB or more. Estimate: one 32k slot needs about 27.9 GiB, so it does not fit 24 GB without offload |
| n/a | GPT-5-mini (API) | Only by your decision |

**Options and what each changes.**

| Option | What changes |
|---|---|
| Accept the order | Each fallback costs at most 1,150 episodes (5.39 GPU-days), deducted from the GPU-day budget. At most 2 fallbacks on a 24 GB GPU and 3 on 32 GB |
| Change the order | The new order is logged and used at G0 |
| If no local model passes: (a) GPT-5-mini via API | The main result is no longer locally reproducible. Needs a logged amendment with an API cap |
| (b) The best local model, with smaller pools | Lower selection power. The main result stays local |
| (c) Re-scope to a smaller-model study | Paper 1 is redesigned |

**Recommendation.** Accept the order, and (b) if no local model passes. That keeps the main result reproducible on a local machine.

**Default if no answer.** The stated order, and (b) if no local model passes and there is no answer within one week. Logged against meeting item 6.

**Deadline gate.** G0, after the first calibration run (E0). The fallback question is answered within one week of the case arising.

**Owner.** You decide.

**Source.** [M15](DESIGN_REVIEW_2026-10.md#m15-phase-0-calibration-and-the-fallback-model).

#### Q8. A free-form code-edit baseline (informational)

**Question.** [Self-Harness: Harnesses That Improve Themselves (Zhang et al., arXiv 2606.09498, Jun 2026)](https://arxiv.org/abs/2606.09498) already shows self-improvement of a frozen Qwen3.5-35B-A3B harness on TB2. [MetaRSI (Tan et al., arXiv 2609.06396, Sep 2026)](https://arxiv.org/abs/2609.06396) adapts a typed scaffold of the same model on TB2.1, with weights frozen in its harness-only condition. An evaluation study, [Rethinking the Evaluation of Harness Evolution for Agents (Wang et al., arXiv 2607.12227, Jul 2026)](https://arxiv.org/abs/2607.12227), already compares harness evolution with matched-budget sampling on TB2.1, using frontier models. Paper 1 is therefore framed as a compute-matched test of a typed, compiled strategy for a small local model on held-out tasks, with cost per task. Do you specifically want a free-form code-edit baseline (B5)?

**Options and what each changes.**

| Option | What changes |
|---|---|
| Yes | B5 moves to the first Tier C slot, after the descriptive demonstration if Q4 asks for it. 1,810 episodes (8.48 GPU-days) from Tier C headroom |
| No preference | B5 stays Tier C rank 4 |

Either way, B5 runs only if its gates pass before Stage 1: a sandbox escape test, at least 5 of 10 trial proposals that apply cleanly and pass the controller tests, and a fit within the episode caps. It costs 1,810 episodes (8.48 GPU-days). With E5-DEMO (Q4 (ii)) it does not fit under the 12,500 cap (Q5).

**Recommendation.** None needed; the default is sound.

**Default if no answer.** B5 stays Tier C rank 4.

**Deadline gate.** Non-blocking. W11 (2026-12-28) preferred. The B5 go or no-go is decided before the Stage-1 tag.

**Owner.** You, if you have a view.

**Source.** [M1](DESIGN_REVIEW_2026-10.md#m1-novelty-reframe-and-a-code-edit-baseline-b5).

#### Plan item 1. Duration, start date, hours per week and supervision rhythm

From the 2026-10-15 list in [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 11, item 1.

- **Question.** How long is the internship, when does it start, how many hours per week, and how often do we meet?
- **Options.** About 24 weeks part-time with a short weekly update (the original suggestion), or another length and rhythm.
- **What it changes.** The schedule in [EXECUTION_PLAN.md](EXECUTION_PLAN.md), the analysis deadline that sets D in Q5, and which venues are reachable (plan item 11). That schedule assumes 20 hours per week, which gives about 31 weeks to a draft paper (estimate). Finishing in 24 weeks would need about 28 hours per week, a later end date, or cuts.
- **Recommendation.** Agree the weekly hours first; the length follows from them. A short weekly update either way.
- **Default if no answer.** The 24-week part-time suggestion stays the target. The schedule assumes 20 hours per week and is rescaled once the hours are agreed.
- **Deadline gate.** Before the Q5 answer is used at G0 (W13, 2027-01-11).
- **Owner.** You and Sagandeep Kaur, together.

#### Plan item 11. Publication target and authorship

- **Question.** Which venue, and what authorship?
- **Options.** From [PAPER_PLAN.md, section 9](PAPER_PLAN.md#9-candidate-venues). Dates not posted by the venue are unverified.
  - NeurIPS 2027. Paper deadline not posted; mid-May 2027 is expected. At 20 hours per week the draft reaches you in the week of 2027-05-17, at or after that deadline. It is reachable only with about 28 hours per week (plan item 1) or cuts.
  - TMLR. Rolling submission, so no deadline risk. It suits a pre-registered result in either direction.
  - ICLR 2028 main track. Deadline likely late September 2027 (an inference from ICLR 2027).
  - Authorship: not yet proposed.
- **What it changes.** The page budget and the date the write-up must start.
- **Recommendation.** Decide together with plan item 1. At 20 hours per week, TMLR or ICLR 2028; NeurIPS 2027 only if the hours rise to about 28 per week. Authorship to agree with you.
- **Default if no answer.** None. The plan does not depend on it before the write-up, unless NeurIPS 2027 is wanted, which moves the schedule.
- **Deadline gate.** Before the write-up starts (W28, 2027-04-26), or with plan item 1 if NeurIPS 2027 is wanted.
- **Owner.** You.

#### Plan item 6. Model for the diagnoser and proposer

- **Question.** Should the diagnoser and proposer use the same model as the agent, or should a stronger model also be run as a labelled variant?
- **Options.** (a) Same model only. (b) Same model for the main claims, plus a stronger-model variant.
- **What it changes.** (b) needs either an API model or a second local model. Paper-1 API spend is $0 and the core has no line for this variant, so (b) needs a logged amendment with its own cap.
- **Recommendation.** (a) in paper 1; the stronger-model variant goes to paper 2.
- **Default if no answer.** (a).
- **Deadline gate.** The Stage-1 freeze, when the model pins are frozen.
- **Owner.** You and Sagandeep Kaur, together.

### 1.3 Where the 14 items of the 2026-10-15 list went

| Item (TECHNICAL_PLAN section 11, 2026-10-15) | Now |
|---|---|
| 1. Duration, start date, hours, supervision | Open: plan item 1 above |
| 2. Who pays for compute, and the cap | Q5: who provides the GPU, GPU-days in tiers with caps, and a rough dollar cost |
| 3. Which benchmark pair and version | TB2 pinned at `2fd12b8`, held out; TB-Pro for adaptation (Q3); AppWorld to paper 2 by default (Q4). The continuous Terminal-Bench and τ²-bench are not used in paper 1 |
| 4. Enlarge the task pool | Q3 |
| 5. Which model | Primary Qwen3.6-35B-A3B (M15); fallback order in Q6. gpt-oss-120b is not in paper 1, because paper-1 API spend is $0 |
| 6. Same or stronger model for diagnoser and proposer | Open: plan item 6 above |
| 7. How much free text | Proposed by M10 and M12: typed fields plus fenced notes; every proposer-written text passes a lint; text-only fields are labelled |
| 8. Agent framework and tracking | Proposed for the agent by M11: a custom agent loaded into the Harbor harness process, with per-step JSONL logs. MLflow stays optional |
| 9. Include the free-text baseline B3 | Proposed by M1: B3 leaves paper 1 |
| 10. Rollback sub-question in scope | Q4 (plan default: paper 2). Rollback values are excluded from the paper-1 edit space (M12) |
| 11. Publication target and authorship | Open: plan item 11 above |
| 12. Naming | Unchanged: the plan says "strategy adaptation". No question raised |
| 13. What "intelligence index" means | Q1 |
| 14. What "strategy switching" means | Q2 |

---

## 2. Proposed after the design review of 2026-10-20

**Who did the review, and how.** Sagandeep Kaur ran the review on 2026-10-20 with AI assistance. Language-model agents in fixed roles argued the 16 motions in two rounds. A verifier agent checked each factual claim against its source, and adjudicator agents decided each motion against fixed criteria. The method is in [DESIGN_REVIEW_2026-10.md, section 2](DESIGN_REVIEW_2026-10.md#2-method). You were not part of it, and no line below is your view.

**What this section is.** Sagandeep Kaur proposes the outcomes for 14 of the 16 motions and is responsible for them. M5 and M6 are left to you (Q1 and Q2 above). The plan uses these outcomes until you say otherwise. You may overrule any line; an overrule is logged in section 3 and the plan is re-costed. Each line gives the review outcome and the proposal in brief. The full text, the evidence and the strongest dissent are in the linked block of [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md). Where a proposal contains a question, the question is in section 1, and its default applies until you answer.

| Motion | Review outcome | Proposal | Details |
|---|---|---|---|
| M1 Contribution and code-edit baseline | Adopt amended | Paper 1 is a pre-registered, compute-matched test of typed, compiled strategy adaptation for a small local model, with cost per task for every arm. No "first" claim. B3 leaves paper 1. A zero-episode expressiveness audit maps published harness edits onto the schema. B5 is an optional, sandboxed estimation arm (Tier C rank 4, at most 1,810 episodes) | [M1](DESIGN_REVIEW_2026-10.md#m1-novelty-reframe-and-a-code-edit-baseline-b5) |
| M2 Task pools | Pilot first | Hold out TB2-89 and adapt on deduplicated TB-Pro, after a CPU-only route pilot. GO needs a confirmed licence, at least 120 surviving tasks, adapter work within 5 engineer-days and disk with 20% headroom. NO-GO gives the sibling-grouped TB2 re-split (H52). Approval is Q3 | [M2](DESIGN_REVIEW_2026-10.md#m2-task-pools) |
| M3 Statistics | Adopt amended | Paired t on the 89 per-task differences, two-sided. Fixed sequence: S\* against S0, then B4, then B1 and pooled BoN at matched compute. One-stage task bootstrap; McNemar dropped. S0 × 10, S\* 10 runs over two seeds, B4 × 5, B1 × 5. Two pre-registration stages (signed git tag, Zenodo digital object identifier, Open Science Framework entry) | [M3](DESIGN_REVIEW_2026-10.md#m3-statistics) |
| M4 Cost unit and matching | Adopt amended | One cost function. MCU is the matching unit, with a per-arm residual gate and processed tokens as fallback. Every call is charged to the arm that makes it. Per-task matching is primary; payback T\* is secondary. Dollars at two frozen rates. An extended point-1 cost table | [M4](DESIGN_REVIEW_2026-10.md#m4-cost-unit-and-matching) |
| M7 Scope of paper 1 | Adopt amended | Paper 1 = RQ1 + RQ2 (cross-source, TB-Pro to TB2) + a lean RQ4 (leave-one-out attribution and the enforced-versus-advised contrast; rollback removed). Second-order loop, AppWorld and rollback go to paper 2 in the plan (Q4). O4 and O6 move only with your answer | [M7](DESIGN_REVIEW_2026-10.md#m7-scope-of-paper-1) |
| M8 Baseline repair | Adopt amended | The client sends sampling fields and a seed. Temperature 0.6, `top_p` 0.95, `top_k` 20 for every arm. A same-model judge that never sees `tests/`, run after the trial for the S0 pool. Pooled BoN from the S0 pool, with a judge-quality gate on calibration data. B1 retries inside one episode, at most 3 attempts, no reset | [M8](DESIGN_REVIEW_2026-10.md#m8-baseline-repair) |
| M9 Selection rule | Adopt amended | One hybrid rule for every adapted arm: 6 fixed rounds, 4 candidates of at most 2 edit operations, a screen on at most 25 contested TB-Pro tasks (accept at +1 net task), and a final choice on at most 15 more × 3. At most 1,575 episodes per loop. Integer thresholds in code. 8 rounds not adopted | [M9](DESIGN_REVIEW_2026-10.md#m9-selection-noise-fix) |
| M10 Leak fixes | Adopt amended | Dedup; a lint on all proposer text; an egress allowlist fork for TB-Pro; TB2 under its upstream network with a per-trial audit (flagged trials count as failures); an append-only held-out ledger keyed on task ids; a lessons-off and notes-off arm that is never cut | [M10](DESIGN_REVIEW_2026-10.md#m10-leak-fixes) |
| M11 Infrastructure | Adopt amended | One x86-64 workstation, llama.cpp on the host, Harbor with local Docker. An infrastructure gate before any budgeted episode. 60 steps and 64k generated tokens per episode; wall-clock multiplier 2 as a backstop; S0 censored at 1× for leaderboard comparison. Revised hardware request (Q5). No model episodes on the shared development machine | [M11](DESIGN_REVIEW_2026-10.md#m11-infrastructure) |
| M12 `compile()` gate | Adopt amended | Gate G1 before Stage 1. A field counts as compiled only with a passing unit test in continuous integration; everything else is labelled text-only. Minimum compiled set includes `recovery.*`. Rollback values and `switch_to` are outside the paper-1 edit space | [M12](DESIGN_REVIEW_2026-10.md#m12-compile-as-a-gate) |
| M13 Model ladder and enforced versus advised | Adopt amended | The enforced-versus-advised contrast is in paper 1: an "advised" cell in the core (445 episodes) and an "enforce-only" cell as Tier C rank 2. The full model ladder goes to paper 2 on the TMax family. A one-row second model (TMax-9B) is Tier C rank 3 | [M13](DESIGN_REVIEW_2026-10.md#m13-model-ladder-t1-and-compiled-vs-advised-t2) |
| M14 Other threads | Adopt amended | Zero-episode analyses in paper 1: index variants, cost-of-failure columns, failure-taxonomy shift with diagnoser agreement, net pass@k, per-test partial-credit screening. The second seed is core. Portability check E-PORT. Diagnosis-noise injection and others go to paper 2. A possible follow-up on capability assessment of strategy versions (paper 2) | [M14](DESIGN_REVIEW_2026-10.md#m14-other-threads) |
| M15 Phase 0 calibration | Adopt amended | Phase 0 runs on TB-Pro only (bring-up 150 episodes, calibration 600). Gate G0 has four checks: fitness, contested supply, throughput and memorisation. A slow GPU triggers cuts, never a model switch. Fallback order in Q6 | [M15](DESIGN_REVIEW_2026-10.md#m15-phase-0-calibration-and-the-fallback-model) |
| M16 Total compute | Adopt amended | Planning rate 213.5 episodes per GPU-day (±30%). Core 9,653 episodes, about 45.2 GPU-days. Caps of 10,500 (with contingency) and 12,500 (with Tier C). API spend $0. A fixed Tier C order, a G0 capacity rule, six ordered cuts and a floor of 6,224 episodes | [M16](DESIGN_REVIEW_2026-10.md#m16-total-compute-and-the-cut-order) |

---

## 3. Decision log

Entries are added, never edited. A correction is a new entry. "Decided" means proposed after the design review and used by the plan; you may overrule it (section 2).

| # | Date | Entry | Status | Source |
|---|---|---|---|---|
| 1 | 2026-10-20 | The committed split A25 / V12 / M15 / H37 (2026-10-15, meeting item 2) is to be superseded by TB2-89 held out and adaptation on TB-Pro. The split file stays in the repository as history | Pending Q3; default (i) at the Stage-1 freeze | [M2](DESIGN_REVIEW_2026-10.md#m2-task-pools) |
| 2 | 2026-10-20 | `max_steps` raised from S0's committed 40 to 60 for every arm, as a deliberate change. 64k generated tokens per episode. Wall-clock is a backstop at multiplier 2 | Decided | [M11](DESIGN_REVIEW_2026-10.md#m11-infrastructure) |
| 3 | 2026-10-20 | The figure of about 270 s per reference trial (about 340 episodes per GPU-day) is retired. The planning rate is 213.5 episodes per GPU-day | Decided | [M16](DESIGN_REVIEW_2026-10.md#m16-total-compute-and-the-cut-order) |
| 4 | 2026-10-20 | The client's default temperature 0.0 is removed. Sampling is pinned at 0.6 / 0.95 / 20 for every arm, from the model card's setting for precise coding in thinking mode | Decided | [M8](DESIGN_REVIEW_2026-10.md#m8-baseline-repair) |
| 5 | 2026-10-20 | The free-text baseline B3 is removed from paper 1 | Decided | [M1](DESIGN_REVIEW_2026-10.md#m1-novelty-reframe-and-a-code-edit-baseline-b5) |
| 6 | 2026-10-20 | The plan's selection rule (8 rounds, stop after two empty rounds, staged screen on V) is replaced by the hybrid rule | Decided | [M9](DESIGN_REVIEW_2026-10.md#m9-selection-noise-fix) |
| 7 | 2026-10-20 | McNemar's test with Holm correction across all pairs is replaced by a paired t with fixed-sequence gatekeeping. Holm is kept only for the exploratory B5 and enforced-versus-advised contrasts | Decided | [M3](DESIGN_REVIEW_2026-10.md#m3-statistics) |
| 8 | 2026-10-20 | The switching library holds up to 5 versions, a deviation from TECHNICAL_PLAN 5.4's estimate of at most 4. The same-run oracle is replaced by a cross-fitted VBS | Decided | [M6](DESIGN_REVIEW_2026-10.md#m6-strategy-switching-deferred-to-the-professor) |
| 9 | 2026-10-20 | The efficiency index Δp/C at T = 37 is retired as the headline | Decided; the new headline is pending Q1 | [M5](DESIGN_REVIEW_2026-10.md#m5-the-intelligence-index-deferred-to-the-professor) |
| 10 | 2026-10-20 | Internship objectives 4 and 6 to become paper-2 objectives | Defer to professor; pending Q4, default "paper 2" | [M7](DESIGN_REVIEW_2026-10.md#m7-scope-of-paper-1) |
| 11 | 2026-10-20 | Fallback order changed: TMax-9B added; Nemotron-Terminal-32B only on 32 GB or more | Defer to professor against meeting item 6; pending Q6 | [M15](DESIGN_REVIEW_2026-10.md#m15-phase-0-calibration-and-the-fallback-model) |
| 12 | 2026-10-20 | The TB-Pro calibration gate G0 is added as a supplement to the recorded 20 to 40% starting rule. The recorded rule is checked on public TB2 scores only | Decided; to be told to Prof. Abdelrazek | [M15](DESIGN_REVIEW_2026-10.md#m15-phase-0-calibration-and-the-fallback-model) |
| 13 | 2026-10-20 | The compute request is revised and replaces open decision 2 | Pending Q5 | [M11](DESIGN_REVIEW_2026-10.md#m11-infrastructure), [M16](DESIGN_REVIEW_2026-10.md#m16-total-compute-and-the-cut-order) |
| 14 | 2026-10-20 | The reading of meeting point 4 ("intelligence index") is not decided by the review. The plan uses reading (a), CER_test with T\*, until you answer | Defer to professor; pending Q1 | [M5](DESIGN_REVIEW_2026-10.md#m5-the-intelligence-index-deferred-to-the-professor) |
| 15 | 2026-10-20 | The reading of meeting point 5 ("strategy switching") is not decided by the review. The plan uses reading (a) and keeps the E4b reserve until you answer | Defer to professor; pending Q2 | [M6](DESIGN_REVIEW_2026-10.md#m6-strategy-switching-deferred-to-the-professor) |
| 16 | 2026-10-20 | E-PORT runs on the main GPU in an emulated consumer configuration (VRAM capped at 8 GB) unless a consumer machine is provided | Defer to professor against meeting item 6; pending Q5 | [M11](DESIGN_REVIEW_2026-10.md#m11-infrastructure), [M16](DESIGN_REVIEW_2026-10.md#m16-total-compute-and-the-cut-order) |
| 17 | 2026-10-20 | Correction to entry 10. Internship objectives O4 and O6 move to paper 2 only with your explicit answer to Q4; there is no default for them. Meanwhile the paper-1 experiment plan follows Q4 (i) | Pending Q4; explicit answer needed | [M7](DESIGN_REVIEW_2026-10.md#m7-scope-of-paper-1) |
| 18 | 2026-10-20 | Correction to entry 13. The compute request is stated in tiers (floor, core, core plus contingency, with Tier C) with a rough dollar cost, and asks who provides the GPU. The recommendation is at least 49 GPU-days, not 45, because contingency pays for the judge, selector, diagnosis and proposal calls | Pending Q5 | [M16](DESIGN_REVIEW_2026-10.md#m16-total-compute-and-the-cut-order) |
| 19 | 2026-10-20 | M1 amended after review: 2607.12227 found during drafting narrows the novelty claim. [Rethinking the Evaluation of Harness Evolution for Agents (Wang et al., arXiv 2607.12227, Jul 2026)](https://arxiv.org/abs/2607.12227) compares harness evolution with matched-budget best-of-N sampling and sequential refinement on TB2.1, with frontier API models. The M1 wording "none of the closest works we checked reports a cost-matched BoN comparison" is replaced by: among the harness-evolution methods we checked, none reports one; the evaluation study 2607.12227 does, with frontier API models. Paper 1's distinct part is that test on a small, locally served model with a typed, compiled strategy, with cost per task for every arm and the enforced-versus-advised contrast. 2607.12227 joins Table 1 | Decided | [M1](DESIGN_REVIEW_2026-10.md#m1-novelty-reframe-and-a-code-edit-baseline-b5) |
| 20 | 2026-10-20 | The attribution part of the M1 contribution sentence now reads "leave-one-out attribution over changed strategy-dimension groups". E-ATTR reverts changed dimension groups of S\*1, not single fields | Decided | [M1](DESIGN_REVIEW_2026-10.md#m1-novelty-reframe-and-a-code-edit-baseline-b5), [M16](DESIGN_REVIEW_2026-10.md#m16-total-compute-and-the-cut-order) |

**To be logged when they happen.**

- The route pilot's GO or NO-GO, and any TB2 re-split (M2).
- The MCU gate result, and any switch to processed tokens as the matching unit (M4).
- The judge-quality result (AUROC, the area under the receiver operating characteristic curve) on calibration trajectories, and which BoN selector is primary (M8).
- The pre-Stage-1 re-simulation of the selection rule: whether the final-choice pool is raised to k = 5, and whether the cost-aware tie-break is adopted (M9).
- TB-Pro runs on the public network, if the run host lacks nftables (M10).
- Any narrowing of the compiled set, if `recovery.*` cannot be compiled by the planned Stage-1 date (M12).
- The advised cell marked "not applicable", and the outcome of the second-model pilot (M13).
- At G0: the measured rate r, D_rem, capacity C, the cuts applied, the Tier C items admitted, and any fallback model used (M15, M16).
- The B5 go or no-go (M1) and the mid-task switching pilot result (M6).
- A library-plus-selector comparison whose mean cost per task differs from S\*'s by more than 5% (M6).
- Use of the 178-episode leaderboard-protocol fallback run (M11).
- Each default applied for Q1 to Q6 and Q8, marked "defer to professor, default applied". For Q4 this covers only the experiment plan, not O4 and O6.
- Any line of section 2 that you overrule, and the re-costed plan.
