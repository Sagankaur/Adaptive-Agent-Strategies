# Design review, October 2026

Sagandeep Kaur, for discussion with Prof. Mohamed Abdelrazek (Deakin A2I2). The review ran on 2026-10-20 and its verdicts were frozen the same day.

**Status.** This is the record of a design review of [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md). No experiment has been run and no model has been called. Every episode count and GPU-day figure below is an estimate. Each comes from public data, a simulation or arithmetic, and is labelled as such. Two motions (M5 and M6) and several sub-decisions are questions for Prof. Abdelrazek. They are not decided; section 6 lists them with the defaults that apply if there is no answer.

### Terms used

| Term | Meaning |
|---|---|
| TB2 | Terminal-Bench 2.0: 89 tasks, pinned at task commit `2fd12b8` |
| TB-Pro | terminal-bench-pro: a separate set of 200 terminal tasks ([GitHub](https://github.com/alibaba/terminal-bench-pro), [Hugging Face](https://huggingface.co/datasets/alibabagroup/terminal-bench-pro)) |
| Episode | One agent attempt at one task, that is, one Harbor trial |
| GPU-day | 24 hours of one GPU |
| k | Runs per task |
| A, V, M, H | The committed TB2 split (`splits/terminal-bench-2.0.json`, seed 20261015): adaptation 25, selection 12, meta-training 15, held-out 37 tasks |
| S0 | The hand-written starting strategy (baseline B0) |
| S\*1, S\*2 | The strategy chosen by adaptation loop seed 1 or seed 2. S\* alone means their per-task average, unless stated |
| B1, B2 | Reflection-retry and best-of-N (BoN) baselines |
| B3, B4, B5 | Prose-playbook adaptation; random strategy search (same budget and edit space, random edits); free-form code-edit adaptation (proposed here) |
| pp | Percentage points |
| MDE | Minimum detectable effect: the smallest true difference found with 80% power at two-sided alpha 0.05 |
| CI | Confidence interval (95% unless stated) |
| MCU | Model compute units: a × prompt tokens + b × generated tokens, from llama.cpp's per-call `timings` (M4) |
| VBS, SBS | Virtual best solver (the best version for each task) and single best solver (the best version overall) |
| Stage 1, Stage 2 | The two pre-registration tags: before the first adaptation episode, and before the first TB2 episode |

---

## 1. Why the review was done

The plan was written before any run. Three design-phase reports then raised problems that would be expensive to find later:

- a digest of the repository, which listed 16 inconsistencies between documents and code;
- a hostile methodology review (the "red-team" report), which argued that the held-out set is mostly floor, that the baselines are weaker than written, and that the selection rule accepts noise;
- a literature scout, which found a cluster of 2026 papers on self-improving agent harnesses, several of them on TB2 and one with a small open model served locally.

The meeting of 2026-10-14 ([MEETING_2026-10-14.md](MEETING_2026-10-14.md)) also added six points to carry. The compute request (a GPU of at least 24 GB, a Docker-capable Linux machine, an API budget) has not been granted yet. The plan therefore had to be fixed before the request is final and before anything is pre-registered. The review put 16 motions (M1 to M16) to a structured argument, checked the factual claims behind them, and decided each one.

## 2. Method

**What it was.** An AI-assisted review, run for the owner. Large language model (LLM) agents played fixed roles from a common frozen brief. They are model instances, not people, and they can share blind spots. The owner set the brief and the motions and is responsible for what is adopted. Nothing here is the supervisor's view, except where the meeting record is quoted.

**Roles.** Six argued positions:

| Function | Mandate |
|---|---|
| Proponent | Defends the current plan and amends it to survive objections |
| Skeptical reviewer | Novelty and construct validity; "would I reject this paper?" |
| Statistician | Unit of analysis, power, multiplicity, selection bias |
| Systems engineer | GPU, Harbor with local Docker, timeouts, disk, reproducibility pins |
| Supervisor-requirements check | Represents the six meeting points. Could quote only the meeting record and could not invent preferences |
| Novelty scout | Turns the literature scout's threads into costed candidate experiments |

**Rounds.**

1. Openings, written blind and in parallel: a stance on each motion (support, oppose, amend, abstain), objections, proposals and sourced claims.
2. Cross-examination: each role saw all openings and answered every objection aimed at it (concede, defend or amend).

A third round was not run. In the process design's judgement, further LLM debate rounds mostly repeat arguments and drift toward agreement; that is a judgement, not a cited result. The effort went into verification instead.

**Verification.** Every claim went into one ledger. A verifier agent re-opened the source (URL, repository path and line, or a derivation) and recorded what it opened, a verbatim quote or recomputed value, and a status. Numbers were recomputed independently, and simulations were re-run in Python rather than taken from the role that asserted them. Claims cited in support of a stance ("decisive" claims) got a second, independent pass that was told to try to refute them. Disagreements between the two passes went to a tie-breaker. The 46 non-decisive inference claims were not checked.

**Adjudication.** Four adjudicators with no earlier position decided the motions in clusters (setup: M2, M3, M9, M10, M15; readings: M5, M6; scope: M1, M7, M13, M14; infrastructure: M4, M8, M11, M12, M16). They applied fixed criteria in this order:

1. Veto: a motion fails if it uses H outside the final run, breaks a budget cap, breaks the shared-machine limits, or drops one of the six meeting points without logging it as a question for the professor.
2. Evidence: only verified or partially verified claims can be decisive. A motion resting on an unverified claim can at most become a pilot.
3. Validity: does the design answer the research question?
4. Cost and feasibility.
5. Paper value.
6. Reversibility.

The possible decisions were adopt, adopt amended, reject, pilot first (with a go/no-go rule), and defer to the professor. A dissent checker then read each cluster's verdicts, steelmanned the losing side and flagged violated criteria (59 issues in all). One appeal round followed: a role could appeal once, and only by citing a verified claim the adjudicator had ignored. Of 34 appeals, 27 were upheld and 7 were not. A final pass merged the four clusters, removed contradictions between them and froze the verdicts.

**Limits of the method.** Simulated power and selection results are estimates under stated models; real task rates on TB-Pro are unknown until Phase 0. All verifiers were LLM agents, so a shared misreading is possible. The review saw only public data and this repository.

## 3. Ledger statistics

From the verification report (925 claims: 515 seeded from the existing docs, 410 asserted during the debate).

| Status | All claims | Decisive claims |
|---|---|---|
| Verified | 757 | 310 |
| Partially verified (used with the corrected detail) | 111 | 51 |
| Refuted | 5 | 4 |
| Unverifiable | 5 | 0 |
| Unverified | 47 | 1 |
| **Total** | **925** | **366** |

How each status was reached: 513 claims by one confirming pass, 361 by both passes, 5 by the tie-breaker, and 46 non-decisive inferences skipped. The one decisive claim left unverified (about 500 episodes per GPU-day at concurrency 4) is not used in any budget below.

The five refuted claims:

| Refuted claim | Correct value |
|---|---|
| The reference run took about 270 s per trial | About 405 s per trial at concurrency 1 (section 4) |
| The plan's selection rule accepts a null edit with probability 0.362, at +15.5 pp | About 0.52 per round, at about +13.4 pp |
| Under the same rule, edits of +1.0 and +0.5 logit are accepted 24.3% and 13.3% of the time | Withdrawn with the claim above; not used |
| Harbor's `extra_allowed_hosts` never changes the network mode | It is ignored (with a warning) under `public`, merged under `allowlist`, and turns `no-network` into `allowlist` ([`network_policy.py`, v0.23.0](https://github.com/harbor-framework/harbor/blob/v0.23.0/src/harbor/trial/network_policy.py)) |
| [LOCAL_MODELS.md](LOCAL_MODELS.md) and `evaluation/price_table.json` disagree on a model tag | They agree |

## 4. Main errors found and corrected

| # | What was believed | What was found | Source |
|---|---|---|---|
| 1 | **Throughput.** About 270 s per TB2 trial at concurrency 1, so about 340 episodes per GPU-day | Mean 404.7 s per trial (median 296.4 s) over all 445 trials, so **213.5 episodes per GPU-day** at concurrency 1. The 270 s figure divided a 33.4 h job window, which covers only the 287 trials run after a resume, by all 445 trials. Even 270 s gives 320 per day, not 340 | little-coder's Qwen3.6-35B-A3B submission in the [TB2 leaderboard dataset](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard) (445 trial records) |
| 2 | That rate is a GPU benchmark | It was measured on an 8 GB-VRAM laptop with 32 GB RAM and MoE CPU offload. It is used as a conservative planning proxy with a ±30% band (149 to 278 episodes per GPU-day) until Phase 0 measures the real rate | [little-coder](https://github.com/itayinbarr/little-coder) README |
| 3 | **Budgets.** Several debate budgets fit in about 27 to 45 GPU-days | Re-costed at 213.5 per day, for example 11,072 episodes is 51.9 GPU-days (not 34.6) and 14,755 is 69.1 (not 43.4) | Arithmetic |
| 4 | **Null acceptance of the selection rule** | The red-team value holds: under no true improvement, the plan's staged rule accepts an edit in about 52% of rounds, recording a fake gain of about +13.4 pp. The code's unstaged rule accepts about 67%. The lower 0.362 figure came from a float comparison: `adaptation_engine/first_order.py:163` checks `c.delta >= min_delta` on rate differences, which silently rejects about a third of one-task gains | Simulation with the little-coder per-task rates; `adaptation_engine/first_order.py:157,163` |
| 5 | **Floor effect** | Confirmed. In the reference run, 54 of 89 tasks were never solved in 5 attempts, 28 were contested and 7 always solved. Of the 37 tasks in H: 22 never, 11 contested, 4 always | TB2 leaderboard dataset, `splits/terminal-bench-2.0.json` |
| 6 | **MDE.** Red-team: about 10 pp for H37 × 3, 8 pp for H37 × 5, 5.4 pp for TB2-89 × 5 | The red-team used the plug-in within-task variance, which is biased low by a factor 4/5 at 5 runs. A simulated paired t-test gives about 12.0 pp (H37 × 3), 9.5 pp (H37 × 5), 5.8 pp (TB2-89 × 5) and 4.3 to 4.5 pp (TB2-89 × 10) | Simulation (estimate) |
| 7 | **Baselines as coded** | The client defaults to temperature 0.0 and cannot send `top_p`, `top_k` or a seed. Harbor uploads the tests only at verification, so the agent's own checks return None. B1 retries only on an explicit check failure, so when no check applies it never retries. B2 picks the first attempt whose checks passed, otherwise attempt 0 | `llm/openai_compatible.py:63,103-113`; `baselines/agent_loop.py:83-90`; `baselines/baselines.py:118,154`; [Harbor v0.23.0](https://github.com/harbor-framework/harbor) verifier |
| 8 | **Local cost** has one definition | Three conflict: compute hours × GPU rate (TECHNICAL_PLAN 4.3), wall-clock seconds per trial (SMALL_MODELS 3.2), and time inside model calls (`baselines/cost.py:64`), which also counts waiting for a free server slot | The three files |
| 9 | **Efficiency index** E = Δp/C is usable | It is undefined at C ≤ 0 and unbounded near 0. Section 7.6 also states it per GPU hour while section 4.3 converts to dollars | TECHNICAL_PLAN 4.3, 7.6 |
| 10 | Two-stage cluster bootstrap for CIs | It overstates the standard error of the task-averaged difference by about 22 to 28%. A one-stage task bootstrap is calibrated. McNemar on majority votes has an MDE above 16 pp on H37 | Simulation (estimate) |
| 11 | A per-task oracle over versions measures switching headroom | Choosing and scoring on the same runs is biased upward: +4.5 pp at k = 5 even when S\* = S0. Cross-fitting removes it | Simulation; [Bias in Algorithm Portfolio Performance Evaluation (Cameron et al., IJCAI 2016)](https://www.cs.ubc.ca/~cchris13/docs/ijcai16_bias.pdf) |
| 12 | Self-Harness held-out result 23.8% to 38.1% | The rates fit 10/42 to 16/42 (21 tasks × 2 attempts). The paper does not print the denominators, so they are labelled inferred and no significance test is quoted | [arXiv 2606.09498](https://arxiv.org/abs/2606.09498), Table 1 |
| 13 | S0's budget is loose | S0's cumulative 200,000-token cap binds at about step 15. Its 1,200 s wall-clock limit is longer than the TB2 agent timeout on 50 of 89 tasks | `baselines/agent_loop.py:131`; `strategy_schema/defaults.py:75`; TB2 `task.toml` files |
| 14 | A 24 GB GPU allows several slots | Qwen3.6-35B-A3B fully on the GPU needs about 23.4 GiB for 1 slot × 64k context and 24.7 GiB for 2 × 64k (f16 KV cache). A 24 GB card fits one slot at the planned context | Memory arithmetic (estimate) |
| 15 | TB-Pro holds near-copies of TB2 tasks | Partly: the example pair covers the same topic with different specifications. Dedup is still needed | Both task directories |
| 16 | The held-out guard protects H | It is a boolean flag keyed on the split name, not on task ids | `evaluation/runner.py:112` |

---

## 5. Decisions, motion by motion

Each block gives the question, the main positions by function, the key objections, the decision and its policy, the decisive evidence, and the strongest dissent. "Tier C" means optional work admitted only within the absolute episode cap, in the order set by M16.

### M1. Novelty reframe and a code-edit baseline (B5)

**Question.** After Self-Harness and the 2026 harness cluster, what exactly is the paper-1 contribution? Should a free-form harness-code baseline be added?

**Positions.** All six roles amended. The skeptical reviewer and the novelty scout held that B5 is required, should replace B3, and on appeal should rank above the six meeting-point items. The proponent wanted B5 moved to paper 2, with the enforced-vs-advised contrast (T2) as the answer to reviewers.

**Key objections.** One B5 loop is a single high-variance draw and serves none of the six points. B5 against S\* confounds representation with search-space size and the proposer's coding skill, so it cannot test "typed versus code". T2 holds content fixed and so cannot say whether the typed restriction costs pass rate.

**Decision: adopt amended.**

- Contribution: "A pre-registered, compute-matched test of whether adapting a typed, compiled strategy of a small, locally served model on Terminal-Bench beats a fixed strategy, random edits, reflection-retry and best-of-N, with cost per task reported for every arm and mechanism evidence (enforced-vs-advised contrast, leave-one-out attribution over changed strategy-dimension groups)."
- Claims follow the M3 fixed sequence: C1 = S\* beats S0; C2 = S\* beats B4 (worded about the realised strategies); C3 = S\* against B1 and against pooled BoN at matched per-task compute, two-sided, last in the chain. "Beats" only if the hypothesis is rejected and its CI excludes 0. C4 = exploratory mechanism evidence (T2, leave-one-out attribution).
- Not claimed: "first" self-improving harness on TB2 or for small models, second-order gains, cross-family transfer, "typed beats code", "diagnosis beats random search". After the post-review note below, also not claimed: the first compute-matched comparison of harness adaptation with test-time sampling or refinement on Terminal-Bench (2607.12227), the first typed or frozen-weight harness adaptation of a small self-hosted model on Terminal-Bench (MetaRSI), and the first adaptation on a task source disjoint from TB2 (ModularRSI). The full list is in [PAPER_PLAN.md, section 4.3](PAPER_PLAN.md#43-what-the-paper-does-not-claim). The typed space is stated as a deliberate restriction of code space, chosen for compiled enforcement, attribution and auditability.
- A closest-work table (paper Table 1). The paper says "none of the closest works we checked" reports a cost-matched BoN comparison, never "no paper". *This wording was replaced on 2026-10-20; see the post-review note below.*
- B3 leaves paper 1.
- N4 expressiveness audit, 0 episodes, always in paper 1: map each published edit of Self-Harness (4 retained edits), AHE and MemoHarness onto the schema as compiled, text-only or not expressible.
- B5 = free-form edits of our controller code by the same proposer, from the same diagnoses, on the same TB-Pro pools, under the M9 rule, scored on TB2-89 at k = 5. It is Tier C rank 4, capped at 1,810 episodes plus at most 5 engineering days. It is an estimation arm outside the gatekeeping chain, with a Holm-adjusted CI for S\* minus B5. It runs only in a per-trial sandbox whose only network route is the model server, killed on timeout, never in the host Harbor process. An outcome-interpretation table is committed before Stage 1 (for example, if B5 ≥ S\*, the typed claim retreats to auditability, attribution and seed stability). If B5 is not run, the paper says it makes no comparison with code-harness evolution.
- B5 gates, all before Stage 1: the sandbox passes an escape test within 5 engineering days after the infrastructure gate; at least 5 of 10 B5 proposals from TB-Pro failure logs apply cleanly and pass the controller tests; the projected total through B5 × 1.2 fits the M16 capacity rule and the 12,500 cap. Any failure moves B5 to paper 2.
- For the professor (Q8, informational): does he specifically want B5? Default: B5 stays Tier C rank 4.

**Decisive evidence.**

- [Self-Harness: Harnesses That Improve Themselves (Zhang et al., arXiv 2606.09498, Jun 2026)](https://arxiv.org/abs/2606.09498): a loop on TB2, SWE-bench Verified and AppWorld with Qwen3.5-35B-A3B among three models; held-out 23.8% to 38.1% on a 64-task TB2 subset; served on four H200 GPUs; compares only initial against final harness, reports no token or cost figures, merges four retained edits with no per-edit contribution, and edits Python code.
- [Agentic Harness Engineering: Observability-Driven Automatic Evolution of Coding-Agent Harnesses (Lin et al., arXiv 2604.25850, Apr 2026)](https://arxiv.org/abs/2604.25850): ablations attribute gains to tools, middleware and memory rather than the prompt; "factual harness structure transfers while prose-level strategy does not".
- [Meta-Harness: End-to-End Optimization of Model Harnesses (Lee et al., arXiv 2603.28052, Mar 2026)](https://arxiv.org/abs/2603.28052): searches harness code; its best-of-N is a search control in a text-classification setting, not on TB2.
- [ModularRSI: Modular and Generalizable Recursive Harness Self-Improvement (Wu et al., arXiv 2609.14857, Sep 2026)](https://arxiv.org/abs/2609.14857), [MetaRSI / RSI2: A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems Themselves (Tan et al., arXiv 2609.06396, Sep 2026)](https://arxiv.org/abs/2609.06396), [SEAGym: An Evaluation Environment for Self-Evolving LLM Agents (Zheng et al., arXiv 2606.17546, Jun 2026)](https://arxiv.org/abs/2606.17546), [Harness Updating Is Not Harness Benefit: Disentangling Evolution Capabilities in Self-Evolving LLM Agents (Lin et al., arXiv 2605.30621, May 2026)](https://arxiv.org/abs/2605.30621), [MemoHarness: Agent Harnesses That Learn from Experience (Huang et al., arXiv 2607.14159, Jul 2026)](https://arxiv.org/abs/2607.14159), [Mixture of Self-Improving Branches For Agent Harness Optimization (Dong et al., arXiv 2609.37834, Sep 2026)](https://arxiv.org/abs/2609.37834), [Task-CoEvolve: Efficient Harness Optimization via Adaptive Validation Task Selection (Miyai et al., arXiv 2608.20169, Aug 2026)](https://arxiv.org/abs/2608.20169) and [Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models (Zhang et al., arXiv 2510.04618, Oct 2025)](https://arxiv.org/abs/2510.04618) make up the rest of the closest-work table. AHE, Meta-Harness, ModularRSI, MetaRSI and MemoHarness already cover ablation, modular and typed harness edits; Mixture of Self-Improving Branches covers per-input routing. Neither TECHNICAL_PLAN nor PRIOR_WORK cites Self-Harness, AHE or SEAGym.
- Loop simulation: one adaptation loop is a high-variance draw (M3, M16).

**Strongest dissent** (skeptical reviewer, novelty scout). The closest prior work searches harness code on the same benchmark and model class, so a reviewer's first question is whether the typed restriction costs pass rate. Ranking B5 last in Tier C means it will probably be cut, and the paper then concedes the comparison that defines the field. A sandbox is about one week of work.

*Post-review note (2026-10-20).* [Rethinking the Evaluation of Harness Evolution for Agents (Wang et al., arXiv 2607.12227, Jul 2026)](https://arxiv.org/abs/2607.12227), found while drafting, compares harness evolution with matched-budget parallel sampling and sequential refinement on TB2.1 with frontier API models. The decision's wording above is therefore replaced by "among the harness-evolution methods we checked, none reports a test-time best-of-N comparison at matched compute; the evaluation study 2607.12227 does, with frontier API models on the searched tasks". Paper 1's distinct part is that test on a small, locally served model with a typed, compiled strategy, with cost per task for every arm and the enforced-versus-advised contrast. 2607.12227 joins Table 1. The change is logged as a deviation in [DECISIONS.md](DECISIONS.md), section 3, entry 19 ("M1 amended after review"). The attribution phrase of the contribution sentence was also corrected to match E-ATTR (entry 20).

### M2. Task pools

**Question.** Hold out all 89 TB2 tasks and adapt on deduplicated TB-Pro, or re-split TB2 by sibling groups?

**Positions.** The proponent and the statistician supported the TB-Pro route. The others amended it. Round-1 gates (at least 50 contested tasks at k = 3; at least 25% of survivors contested) were withdrawn when simulation showed a healthy model would usually fail them. In round 2, the proponent, the skeptical reviewer, the systems engineer and the novelty scout wanted a fallback TB2 re-split if fewer than 40 TB-Pro tasks are contested.

**Key objections.** TB-Pro has no prebuilt images, an older task schema, 3,600 s timeouts and a licence stated only in dataset metadata. A TB2 re-split leaves only about 12 contested tasks among its 37 non-held-out tasks, so it cannot cure a supply shortfall.

**Decision: pilot first.**

- Target: hold out all 89 TB2 tasks for the final pre-registered run only; adapt on deduplicated TB-Pro (200 tasks).
- CPU-only route pilot before any GPU episode, in Docker with resource limits: (1) build every TB-Pro image once and record digests in `pins.lock`; drop tasks above 4 CPUs or 8,192 MB for now, with the final rule tied to the pinned concurrency; measure disk for TB2-89 plus survivors. (2) Dedup: embed every TB-Pro and TB2 instruction with one pinned embedding model; the owner reviews the 3 nearest TB2 tasks for each TB-Pro task and removes any that ask for the same artefact, algorithm or tool chain, with a one-line reason; near-siblings share a group. (3) Run Harbor's Oracle agent (no model) on TB-Pro survivors only and drop tasks whose oracle scores 0; adapter work capped at 5 engineer-days. (4) Licence: a LICENSE file or written author confirmation.
- Before Stage 2, the only TB2 contact is image pulls by digest, logged in the held-out ledger (M10).
- A 15-task TB-Pro dev slice is set aside for bring-up and debugging. Pools come from the contested count C5 of M15: V_pro = round(0.6 × C5), capped at 25; V2_pro = C5 − V_pro, capped at 15; the rest go to A_pro. The per-round diagnosis set is a fixed stratified 50-task sample of A_pro (seed 20261015).
- GO if: licence confirmed; at least 120 TB-Pro tasks survive (before removing the dev slice); Harbor runs the tasks within the adapter cap; and the disk footprint fits with at least 20% headroom (else build, run and prune by digest). The expected-supply derivation (about 32 contested tasks from 105, so roughly 30% chance of M15's reduced-pool band) is pre-registered.
- NO-GO fallback: re-split TB2 into H52 + A15 / V12 / V2 10 with sibling groups, seed 20261015, stratified by category and difficulty, logged as a deviation; MDE about 7.6 pp at k = 5, stated in the abstract.
- RQ2 is labelled "cross-source (TB-Pro to TB2)". A per-task routing table and the 89-row per-task pass/fail table are fixed deliverables (meeting point 2). A contested-supply shortfall is never a reason to re-split TB2.
- For the professor (Q3, approval): replace the committed A25/V12/M15/H37 split, recorded as done for meeting item 2, with this design. Options: (i) approve; (ii) keep the committed split (MDE about 9.5 pp at k = 5, sibling leak remains); (iii) use the TB2 re-split directly. Default if no answer by the Stage-1 freeze: (i), logged as superseding the 2026-10-15 action.

**Decisive evidence.** Floor counts (section 4, row 5). All 9 sibling pairs found by the red-team straddle H (5 siblings in A, 3 in M, 1 in V). MDE about 9.5 pp for H37 × 5 against 5.8 pp for TB2-89 × 5. TB-Pro facts: 200 tasks, no `docker_image` set, `version = "1.0"` schema, 3,600 s agent timeouts, mostly 1 CPU and 2,048 MB ([repository](https://github.com/alibaba/terminal-bench-pro)). The 89 TB2 images total 48.98 GB compressed. `evaluation/splits.py` already supports a per-task `group`.

**Strongest dissent** (skeptical reviewer, systems engineer, novelty scout). If TB-Pro yields fewer than 40 contested tasks, adaptation optimises against a thin, foreign pool and edits may not transfer. A sibling-grouped TB2 re-split keeps adaptation and test in one distribution, so RQ1 measures adaptation rather than transfer, at a cost of only about 1.8 pp of MDE.

### M3. Statistics

**Question.** Runs per task, the primary test, the gatekeeping order and the pre-registration venue.

**Positions.** The red-team report proposed a paired sign-flip permutation test as primary and a two-stage cluster bootstrap; the proponent, the skeptical reviewer and the novelty scout backed sign-flip in round 1. The skeptical reviewer wanted the confirmatory test on seed 1 only. The statistician wanted S\* against BoN and B1 as Holm-adjusted estimates only. The novelty scout held that OSF is optional.

**Key objections.** Sign-flip has less power than the paired t while the t holds its size in the simulated nulls. Floor-heavy nulls were not simulated, hence a second size check. Two seeds at k = 5 cost the same TB2 episodes as one seed at k = 10.

**Decision: adopt amended.**

- Unit of analysis: the task. Estimand: equal-weight mean over the 89 TB2 tasks of the per-task pass-rate difference (pp).
- Primary test: paired t on the 89 per-task mean differences, alpha 0.05, all hypotheses two-sided. Sensitivity: paired sign-flip (100,000 flips) and a mixed-effects logistic model, pass ~ arm + (1 + arm | task). CIs: one-stage task bootstrap, 10,000 resamples. McNemar dropped.
- Arms on TB2-89: S0 × 10 (also the BoN pool), S\* = 10 runs, B4 × 5, B1 × 5. Two-seed branch (default): S\* = S\*1 × 5 + S\*2 × 5, averaged per task. Single-seed branch, only if M16 cut 5 is applied: S\*1 × 10. The branch is fixed in the Stage-1 tag.
- Fixed-sequence gatekeeping at alpha 0.05: H1 S\* vs S0; H2 S\* vs B4; H3 S\* vs B1 at matched compute; H4 S\* vs pooled BoN at matched compute. Estimates and CIs for all four are reported wherever the sequence stops.
- "Diagnosis beats random search" is never claimed with fewer than 2 loops per arm. Between-seed SD is reported.
- B1: at most 3 attempts per run, total capped at 1,024 episode-equivalents (614 after M16 cut 3).
- Exploratory, with no p-values in the abstract: attribution, T2, switching, per-category results, lessons-off ablation, net pass@k. Every per-task oracle or "newly solved" quantity is 2-fold cross-fitted (choose on odd runs, score on even, swap, average).
- Before Stage 1, at 0 episodes: fit a beta-binomial to the TB-Pro E0 rates with the unbiased within-task variance and re-state the MDE in the abstract (planning values: 4.5 pp for H1 at 10 vs 10 runs; 5.8 to 5.9 pp for k = 5 arms; about 6.1 pp for S\* × 10 vs B1 × 3). Simulate the t-test's size on the E0 rates and on the public little-coder TB2 rates; if size exceeds 6% at nominal 5% in either, sign-flip becomes primary.
- Pre-registration in two stages (before the first adaptation episode; before the first TB2 episode). Each stage is a signed git tag freezing `pins.lock`, analysis code, thresholds, pool lists and caps, archived on Zenodo with a DOI (digital object identifier), plus an OSF (Open Science Framework) entry quoting the tag and DOI.

**Decisive evidence.** Simulations (estimates): sign-flip power 0.50 to 0.59 against 0.54 to 0.675 for the t; the t held 4.3 to 5.8% size at nominal 5%; the two-stage bootstrap overstates the SE by 22 to 28%; McNemar MDE above 16 pp on H37 and about 9.7 pp on TB2-89 × 5; between-loop SD of the chosen strategy's gain about 4.7 pp.

**Strongest dissent** (statistician). True gaps between S\* and BoN or B1 are plausibly 0 to 5 pp, at or below the MDE, so H3 and H4 will rarely reject, and a non-rejection invites "no difference" readings. Holm-adjusted simultaneous CIs answer the real question without a binary verdict.

### M4. Cost unit and matching

**Question.** Which cost unit; how BoN and retry are matched; how to resolve the three local-cost definitions.

**Positions.** The proponent, with the statistician, the systems engineer and the novelty scout, wanted a confirmatory matched-compute test amortised over 89 tasks. The proponent proposed validating MCU by call-level R² ≥ 0.9. The supervisor-requirements check proposed occupancy GPU-hours as the definition. The systems engineer proposed two token units and no scalar.

**Key objections.** Amortised matching at T = 89 is not estimable: one adaptation loop (1,365 episodes) over 89 tasks is about 15.3 episodes per task, so BoN would need N of about 16 from a 10-run pool. R² can pass while one arm is biased. Occupancy includes idle time and other users' load. Without one pre-registered scalar, matching is a forking path.

**Decision: adopt amended.**

- One cost function, `episode_cost()` in `baselines/cost.py`, replacing model-time pricing (line 64). TECHNICAL_PLAN 4.3, 7.6 and SMALL_MODELS 3.2 point to it.
- Matching unit: MCU = a × prompt_n + b × predicted_n from llama.cpp `timings` (prompt_n excludes cached tokens; predicted_n includes reasoning). a and b are fitted on the Phase-0 TB-Pro sweep and frozen at Stage 1. MCU is not claimed to equal GPU-seconds.
- Validation gate before Stage 2, TB-Pro data only: an arm passes if its mean episode residual is within ±3% and the CI of that mean within ±5%, with at least 40 episodes. If a validated arm fails, add a context term; if it still fails, match on processed tokens with MCU as sensitivity.
- Every model call is charged to the arm that makes it (BoN judge calls to BoN rows only; B1's judge and reflection calls to B1; selector calls to the selector arm; diagnosis and proposal calls to adaptation cost).
- Pooled BoN is computed exactly from the S0 pool over all subsets; a non-integer N is matched as a mixture of the two neighbouring N. Primary matching is per task (deployment): N\* = S\*'s mean MCU per task / (S0 MCU per episode + judge MCU per trajectory). If N\* exceeds the pool, BoN at the pool size is reported and flagged under-matched. B1 gets a randomised attempt cap in {1, 2, 3} per task and run, with the mixture fixed at Stage 2 and mean cap at most 2.3. Amortised cost is shown as a payback curve, with no confirmatory amortised test.
- Dollars: measure an occupancy factor k_occ in Phase 0; dollars = (MCU-hours / k_occ) × rate, at two frozen named rates (electricity; cloud-GPU equivalent).
- Point-1 table (meeting item 1), for every arm: mean, median, IQR and CI of dollars per task at both rates; wall-clock labelled with GPU and concurrency; generated, prompt and cached tokens; MCU; pass rate per dollar; every column split by outcome and by S0 task class. MCU never appears without dollars next to it.

**Decisive evidence.** The three conflicting definitions (section 4, row 8). llama.cpp returns per-call `prompt_n`, `cache_n`, `predicted_n` and their times. Per-trial time is heavy-tailed (mean 1.37 × the median; the longest trial 11 × the mean) and depends on outcome (mean agent time 231 s on successes, 357 s on failures). A BoN arm at N still consumes N episodes per task. `evaluation/runner.py` `summarise()` reports only means.

**Strongest dissent** (proponent, statistician, systems engineer, novelty scout). RQ1's "equal cost" means total cost, so the one-time adaptation should be amortised over a pre-registered horizon. Per-task matching treats about 1,365 adaptation episodes as free and flatters S\*. This is strongest if the professor reads point 1 as total project cost per task.

### M5. The "intelligence index" (deferred to the professor)

**Question.** Which index to propose, and how to put the two readings of meeting point 4.

**Positions.** The proponent and the novelty scout first wanted the compute-equivalence ratio plus payback adopted outright, then conceded that this decides an unresolved point. The statistician wanted Δp and C as the primary result, with any index secondary. The literature scout's thread T5 proposed a human-baseline variant using TB2 reference solutions.

**Key objections.** The plan's Δp/C is undefined at C ≤ 0. An amortised ratio at T = 89 is bounded at about 0.6 by construction under the hybrid budget, so it can only read "not worth its compute". Reference solutions are scripts, not human traces.

**Decision: defer to the professor.** The reading of point 4 and the headline are his decision. Meanwhile, at 0 extra episodes, every candidate is computed after the final run from logs already budgeted, and none feeds back into adaptation:

- CER_test = c_eq / c_test\*: how many S0 best-of-N samples S\* is worth per task, at the M4 unit. It is censored, never extrapolated, when the BoN frontier does not reach S\*'s pass rate.
- Payback T\* = adaptation cost / (c_eq − c_test\*), in tasks; "never" if c_eq ≤ c_test\*.
- Amortised CER(T) as a curve (appendix); Δp/C only where C > 0 (appendix); pass per MCU; rank agreement across indices (Kendall tau).
- Δp and C are always shown next to any index. A composite score in the style of the Artificial Analysis index is used only in the model-choice table, never on TB2 held-out runs. A Chollet-weighted variant is computed only if its weights are pre-registered.

Q1, options: (a) one number, CER_test; (a) two numbers, CER_test and T\*; (b) a composite for model choice (with an AppWorld re-entry if he wants our method scored across benchmarks, M7); (c) something else. **Default if no answer by the Stage-1 freeze:** reading (a), CER_test as headline with T\* as companion, logged as "defer to professor, default applied".

**Decisive evidence.** Meeting record, item 4, readings (a) and (b) ([MEETING_2026-10-14.md](MEETING_2026-10-14.md)). TECHNICAL_PLAN 7.6. [On the Measure of Intelligence (Chollet, arXiv 1911.01547, Nov 2019)](https://arxiv.org/abs/1911.01547). The [Artificial Analysis methodology page](https://artificialanalysis.ai/methodology/intelligence-benchmarking) describes v4.3.2 as a weighted average of 10 evaluations, with Terminal-Bench 4.0 (not 2.0) at 10% weight.

**Strongest dissent** (statistician). Any single ratio invites the "bespoke metric" criticism. CER inherits the BoN selector's quality, is often censored, and with about 11 to 28 contested tasks its CI may span an order of magnitude. The honest primary result is the (Δp, C) pair. This is partly met: Δp and C are always shown.

### M6. Strategy switching (deferred to the professor)

**Question.** A per-task library and selector with VBS-SBS headroom and regret, or switching in the middle of a task? What goes into paper 1?

**Positions.** The skeptical reviewer and the statistician first wanted only S0-vs-S\* headroom in paper 1, then conceded. The statistician, the systems engineer and the novelty scout wanted mid-task switching moved to paper 2 unconditionally. The scout's thread hypothesised VBS-SBS ≥ 10 pp with a same-run oracle.

**Key objections.** Moving mid-task switching out removes reading (b) before the professor answers. The same-run oracle is biased upward (section 4, row 11). The controller does not read any `recovery.*` field today.

**Decision: defer to the professor.** Whatever the answer, paper 1 carries reading (a) at 0 extra episodes:

- Library L = {S0, S\*1, S\*2, B4-final} (plus B5 if run), up to 5 versions, a logged deviation from the plan's estimate of 4.
- Cross-fitted VBS and SBS (choose on odd runs, score on even, swap, average), headroom CI by task bootstrap. The same-run VBS is shown labelled "biased; for illustration".
- Two selectors designed on TB-Pro logs only and frozen by commit at Stage 2: a category-by-difficulty rule table, and one local-model call per task over the instruction. Each is scored on TB2 by the mean of all runs of its chosen version. Per-task cost includes the selector's MCU; library construction cost counts B4 (and B5).
- Report regret, fraction of gap closed (only if the headroom CI excludes 0), and library-plus-selector against S\* at matched per-task MCU. All exploratory.
- Reading (b), mid-task switching: a reserve of 307 episodes (40 TB-Pro pilot + 267 TB2). It runs only if (1) Q2 is answered (b) or (c) before the Stage-1 freeze; (2) the M12 gate passes with a `switch_to` value executed by the controller behind a flag the proposer cannot emit; (3) the pilot fires the switch on at least 6 of 40 trials with at most 2 infrastructure errors. Then S\*1 + switch runs on TB2-89 at k = 3 against S\*1 × 5 (MDE about 6.6 pp), exploratory.

Q2, options: (a) one version per task (from task features, or after a few probe steps); (b) change strategy mid-task when stuck; (c) both; or (a) plus the probe-based selector in paper 1. **Default if no answer by the Stage-1 freeze:** (a) only; mid-task switching moves to paper 2 and its reserve returns to contingency, logged and told to him in one line.

**Decisive evidence.** Meeting record, item 5. Simulations (estimates): same-run headroom +4.5 pp at k = 5 with no true difference; 12.3 / 6.5 / 4.7 pp phantom gaps for 4 identical strategies at k = 1 / 5 / 10. Cameron et al. (IJCAI 2016). `baselines/agent_loop.py:1-14` lists the fields the controller reads. Per-input routing over evolved harnesses on TB2 is published (Mixture of Self-Improving Branches; MemoHarness).

**Strongest dissent** (skeptical reviewer, statistician). Switching is not a contribution here: per-input routing on TB2 is published, our library is two seeds of one procedure plus a random-edit control, so headroom will probably be near 0. The mid-task arm changes outcomes only where the recovery trigger fires, has an MDE of 6 to 7 pp at best, and its reserve could fund validity work instead.

### M7. Scope of paper 1

**Question.** Move RQ3 (second-order loop), AppWorld transfer, rollback and mid-task switching to paper 2?

**Positions.** Five roles supported in round 1; the supervisor-requirements check amended. The proponent proposed moving mid-task switching out unconditionally, then conceded. The novelty scout wanted the freed budget assigned to B5 and T2, priced at 340 per day (a rate based on the refuted 270 s; section 4, row 1). The systems engineer argued that two GPUs would make a reduced RQ3 pilot feasible.

**Key objections.** RQ3 has no clean split: the plan reuses A, V and M. The loop is the replication unit, and a powered RQ3 needs 27 to 32 loops per arm. Even at 4 times the throughput that is at least 86 GPU-days. Harbor has no snapshot or restore, so rollback covers files only.

**Decision: adopt amended.**

- Paper 1 = RQ1 (H1 to H4) + RQ2 scoped as cross-source held-out generalisation from TB-Pro to TB2-89 (no cross-family claim) + a lean RQ4, "which strategy dimensions account for the gains" (leave-one-out attribution on S\*1 and T2; rollback removed from RQ4).
- Also in paper 1: the point-1 cost table, the efficiency index (M5), offline switching (M6), the conditional mid-task arm under M6's gates, the zero-episode threads (M14), the portability check (M16) and the 89-row per-task table.
- To paper 2: RQ3 and the second-order loop; rollback versus restart. Rollback values and fields are removed from the paper-1 edit space, with a unit test (M12).
- AppWorld goes to paper 2 unless Q1 = (b) and he wants our method scored across benchmarks. Then the minimum re-entry is S0 against S\* on AppWorld test-normal at k = 1, costed from the adapter and admitted only within the 12,500 cap.
- Internship objectives 4 (second-order loop) and 6 (second-benchmark transfer) become paper-2 objectives, logged as "defer to professor" with default "paper 2".
- Q4, options: (i) defer all three to paper 2; (ii) the second-order loop is essential: a descriptive single-loop demonstration on TB-Pro only (at most 1,365 episodes, about 6.4 GPU-days, no inferential claim, Tier C rank 1); (iii) essential: more GPU-days for a powered design (about 74,000 to 87,000 episodes, 345 to 409 GPU-days, stated as infeasible on one GPU). **Default if no answer by the Stage-1 freeze:** (i).

**Decisive evidence.** TECHNICAL_PLAN 6.4 and 9 (RQ3 needs a split not used to learn M, but its budget reuses V). Loop simulations (CV of final gain 0.65 for the hybrid, 1.33 for the plan rule; estimates). Harbor v0.23.0 has no snapshot or restore. `strategy_schema/model.py:85-89` holds the rollback value. AppWorld is about 2,500 planned episodes (TECHNICAL_PLAN 9).

**Strongest dissent** (supervisor-requirements check). The plan lists the second-order loop and second-benchmark transfer as two of six internship objectives, and the record does not say whether they are fixed requirements. Deferring both, even with a logged default, could remove what the internship was set up for, and the demonstration offered instead is descriptive only. The cut should go to him as options with costs before anything is marked decided.

### M8. Baseline repair

**Question.** Vendor sampling, a judge or self-test selector, pooled BoN with randomised N, and the B1 retry trigger.

**Positions.** All six roles supported repair. The proponent proposed the model card's TB2 setting (temperature 1.0) as default. The infrastructure cluster's first verdict proposed a 90-episode choice between 0.6 and 1.0 and a judge inside every trial. The systems engineer proposed a Harbor pre-verify hook.

**Key objections.** The temperature-1.0 setting was only partly verified. 45 trials per setting cannot separate nearby pass rates. A judge inside every trial puts judge time into S0's timeout. No pre-verify hook exists in Harbor.

**Decision: adopt amended.** Repairs land before any budgeted episode.

- Client sends temperature, `top_p`, `top_k` and a logged per-request seed; the 0.0 default is removed.
- Sampling pinned a priori for all arms at temperature 0.6, `top_p` 0.95, `top_k` 20 (the model card's precise-coding thinking setting). The 90-episode sampling choice is dropped.
- Judge: the same local model scores each trajectory once from the instruction, the trajectory and the outputs of agent-written tests; it never sees `tests/`. For the S0 pool it runs after the trial and is charged to BoN rows only. Only B1 uses a judge inside the run.
- B2 = pooled BoN from the S0 pool, choosing the highest judge score, ties random; oracle pass@N plotted dashed as a ceiling only.
- Judge check on about 600 TB-Pro E0 trajectories: AUROC (area under the ROC curve) ≥ 0.6 makes the judge the primary selector; below 0.6, "agent-written tests passed, ties random" is primary and the paper says a realistic BoN selector is weak for this model.
- B1 = in-episode reflection-retry: retry when the judge says fail or an agent-written test fails, never on hidden tests; at most 3 attempts; no environment reset; 60 steps and 64k generated tokens per attempt; timeout rate reported.
- CI unit tests before the infrastructure gate closes (B1 retries on a failing judge; B2 can pick an attempt index above 0; the request carries the sampling fields and seed; judge calls are charged to the right arm; the judge cannot read `tests/`).
- E1 = B1 smoke on the 15-task TB-Pro dev slice × 2 runs, attempt cap 2, at most 60 episode-equivalents.

**Decisive evidence.** Section 4, row 7. Harbor runs the verifier after `run()` and uploads tests only in `verify()`. The [Qwen3.6-35B-A3B model card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B) recommends temperature 0.6, `top_p` 0.95, `top_k` 20 for thinking mode on precise coding tasks. Unbiased pass@2 on the reference run is 31.7% against pass@1 23.8%, so BoN has real headroom.

**Strongest dissent** (proponent). A self-consistency selector on final file state avoids the same-model judge and is cheaper. A judge on a model near 25% may be near chance, so "BoN at matched compute" may mean "random pick at N times the cost", and a win over it would be over-read. Oracle-gap reporting should be co-primary.

### M9. Selection-noise fix

**Question.** A contested validation pool, common random numbers (CRN), an A/A-calibrated threshold, a confirmation set, and 6 or 8 rounds.

**Positions.** The proponent's round-1 null-acceptance figures were refuted (section 3). The red-team's strict gate (calibrated to 10% null acceptance, a confirmation set, stop after two empty rounds) was backed by the skeptical reviewer, the supervisor-requirements check and the novelty scout in round 1, then withdrawn. The proponent proposed V_pro 30 × 2 with a stop rule. The systems engineer proposed setting the threshold from one A/A run. The statistician asked for 8 rounds if affordable.

**Key objections.** In simulation (estimates), the strict gate accepts about 0.19 edits and stops after about 2 rounds, for about +0.7 pp. The proponent's gate gives +1.7 pp with the stop. One A/A run is one draw of a maximum-of-4 statistic. No gain was shown for rounds 7 and 8.

**Decision: adopt amended.** One hybrid rule for every adapted method (S\*1, S\*2, B4, B5 if run):

- R = 6 fixed rounds, no early stop.
- Each round: run the current version once on the 50-task diagnosis set; the proposer emits K = 4 candidates of at most 2 edit operations, each passing the M10 lint, from the paper-1 edit space (no rollback, no `switch_to`); run the parent fresh and the 4 candidates once each on V_pro (at most 25 contested TB-Pro tasks) with shared per-task seeds, but assuming zero correlation in every calibration; accept the best candidate if it solves at least 1 more task (net) than the parent; ties to lower mean MCU, then the earlier version.
- After round 6: run all 7 versions × 3 on V2_pro (at most 15 contested tasks, disjoint by sibling group); S\* = most net V2 successes, ties to the earlier version.
- Cap per method: 6 × (|A_diag| + 5 × |V_pro| × k_screen) + 7 × |V2_pro| × k_V2 ≤ 1,575 (nominal 1,365 at 50 / 25 × 1 / 15 × 3).
- Code fix before Stage 1: thresholds compared as integer counts in `adaptation_engine/first_order.py`, with unit tests at exact ties.
- Pre-Stage-1 re-simulation on the E0 fit: if P(chosen version worse than S0) exceeds 10% under edit effects N(0, 0.3²), raise V2_pro to k = 5 within the cap and re-check.
- Reporting: every candidate is logged; V_pro differences are screening data, never effect sizes; the chosen version's V2 score is not a gain estimate (winner's curse); "S\* = S0" is a pre-registered valid outcome. R = 8 is not adopted; M16 cut 4 (R from 6 to 4) is the only allowed change.

**Decisive evidence.** Section 4, row 4. Simulations (estimates): the hybrid ends at a gain of 0.82 logit (about +6.6 pp on TB2) and is worse than S0 in about 3.5% of loops, at 1,365 episodes per loop. Selection noise affects which S\* is chosen, not the held-out test of it. [Task-CoEvolve](https://arxiv.org/abs/2608.20169) supports variance-focused validation pools.

**Strongest dissent** (proponent, with the red-team report). The hybrid accepts about 4.4 edits per loop even when no edit helps. The adaptation trajectory, the most visible output of "strategy adapt", will look like progress while being mostly noise, and neutral edits raise S\*'s cost in the matched comparisons. A stricter gate gives an edit log that means something.

### M10. Leak fixes

**Question.** Sibling dedup, a lint on notes and lessons, an egress denylist, an append-only held-out ledger, a lessons-off ablation.

**Positions.** Most roles supported. The red-team report and the skeptical reviewer proposed a path-level egress denylist. The systems engineer's claim about `extra_allowed_hosts` was refuted (section 3). The skeptical reviewer proposed a general memorisation probe including TB2. The first cluster verdict proposed an allowlist fork for TB2 too.

**Key objections.** Harbor has no denylist mode and matches hosts, not paths. A model probe on TB2 before Stage 2 touches the held-out set. Forking TB2's network setting would change the benchmark condition, so reference comparisons would become cross-condition.

**Decision: adopt amended.** Five fixes, frozen at Stage 1:

1. Dedup: cross-source and within-TB-Pro grouping per M2; removal list and reasons published.
2. Lint on every proposer-written text field before evaluation: reject any TB2 or TB-Pro task id, any URL, any command string over 40 characters, and any path that appears in a task's files or instructions. Rejections count against K. Its false-positive rate is piloted on TB-Pro outputs before Stage 1.
3. Egress, TB-Pro only: run the Oracle agent (CPU only) with the agent phase in allowlist mode starting from package hosts, adding the minimum each failing oracle needs; ship a pinned, hashed fork changing only the agent network lines; publish the diff and host lists; DNS sinkhole for benchmark web domains. TB2-89 runs only in the final run, under its upstream setting (`allow_internet = true`), with per-trial SNI and DNS logging and a grep for the canary and benchmark names. Flagged trials count as failures in the primary analysis and are excluded in a sensitivity analysis.
4. Held-out ledger: the boolean guard keyed on split name (`evaluation/runner.py:112`) is replaced by a guard keyed on the held-out task-id set. Every access appends a record (time, commit, `pins.lock` hash, arm, tasks, runs, purpose); the ledger hash goes into each signed tag. Before Stage 2 the only allowed purpose is an image pull.
5. A lessons-off and notes-off arm inside attribution (M16), never cut. A memorisation probe on 20 TB-Pro tasks in Phase 0.

**Decisive evidence.** Every TB2 `task.toml` at `2fd12b8` sets `allow_internet = true` ([terminal-bench-2](https://github.com/harbor-framework/terminal-bench-2)); TB2 relies on a canary string only. Harbor offers only public, no-network and allowlist modes, with host, wildcard and CIDR entries per phase. The Oracle agent needs no model. No TB-Pro task sets `allow_internet`.

**Strongest dissent** (skeptical reviewer, with the red-team report). On TB2 the agent has the open internet, where public solutions and other agents' trajectories sit. Grep audits catch only what the agent echoes. A TLS-intercepting proxy with path rules on TB2 would block the channel at the cost of one auditable trust-store change.

### M11. Infrastructure

**Question.** One workstation with llama.cpp on the host and Harbor in Docker; GPU size; budgets in steps and tokens; timeout multiplier; native tool calling.

**Positions.** The systems engineer proposed running TB2 at timeout multiplier 1 if Phase 0 shows few timeouts, and about 500 episodes per GPU-day at concurrency 4. The proponent wanted at least 32 GB as the minimum GPU. The red-team report and the skeptical reviewer wanted a separate leaderboard-protocol B0 run.

**Key objections.** A 32 GB minimum conflicts with meeting point 6: the reference ran on 8 GB VRAM with offload. The 500-per-day figure is unmeasured. Adapted arms' timeout behaviour can only be measured on TB2.

**Decision: adopt amended.**

- Setup: one x86-64 Linux workstation; llama.cpp on the host; Harbor with local Docker; our agent loaded into the harness process.
- Infrastructure gate before any budgeted episode: an async Harbor agent; reward read from the Harbor trial result; an async client per trial that parses reasoning, tool calls, timings and cached tokens; native tool calling through the chat template; per-step JSONL logs; Harbor job configs with concurrency equal to llama.cpp slots. It closes after a 5-task TB-Pro smoke run with 0 harness errors and the M8 tests.
- Budgets, fixed by the experimenter and identical for every arm: 60 steps (logged as a change from S0's committed 40); 64k generated tokens per episode; a pinned per-call reasoning budget; per-slot context from TB-Pro measurements, ceiling 96k (planning about 80k); KV cache q8_0 unless f16 fits with 1 GiB headroom. Wall-clock is a backstop at multiplier 2 for all arms.
- Leaderboard comparability: no separate run. S0 trials are censored at 1 × the task timeout from logged agent time and reported as "approximately leaderboard-comparable, a slight lower bound". A 178-episode 1 × fallback is charged to contingency only if censoring proves invalid.
- Concurrency: a fit-gated sweep on the 15-task dev slice × 2 runs (at most 90 episodes); pin the fastest configuration that fits memory with at most 1 timeout in 30 trials.
- Hardware request to the professor (Q5): one NVIDIA GPU of at least 24 GB (32 GB recommended for more than one slot), 16 cores, 64 GB RAM, 500 GB NVMe (1 TB recommended), dedicated during budgeted runs; plus a consumer-class x86-64 machine (at least 8 GB VRAM, 32 GB RAM, Docker) for the portability check. Apple Silicon is out of scope (the task images are amd64 only).
- No model episodes on the shared development machine; CPU-only work there runs in Docker within its resource limits.

**Decisive evidence.** `llm/openai_compatible.py` has a synchronous client with a 120 s timeout that reads content only; there is no `tool` role. Harbor v0.23.0 runs the agent inside `asyncio.wait_for` and defaults to 4 concurrent trials. Memory arithmetic (section 4, row 14). The reference run had 8 agent timeouts in 445 trials; 1 of them still passed, so censoring biases down by about 0.2 pp.

**Strongest dissent** (systems engineer). If Phase 0 shows few timeouts, run every TB2 arm at multiplier 1. S0 is then leaderboard-protocol by construction, with no censoring assumption. Multiplier 2 makes the numbers non-comparable to the leaderboard and may read as quietly relaxing the benchmark.

### M12. `compile()` as a gate

**Question.** Must every strategy field either change code (with a test) or be labelled text-only, before pre-registration?

**Positions.** All six roles supported. The supervisor-requirements check asked that the gate be optional if it delays Phase 0. The first cluster verdict made `switch_to` an ordinary enum value.

**Key objections.** The gate costs no GPU time and runs alongside bring-up. An ordinary `switch_to` value would let the proposer put mid-task switching into S\* before the professor admits it.

**Decision: adopt amended.**

- Gate G1 closes before the Stage-1 tag. `compile(strategy)` returns a controller configuration and prompt text with independent switches, so the T2 cells can be built.
- A mechanism table in the paper (paper Table 2; Table 1 is the closest-work matrix), for every field: code path, unit-test id, status (compiled or text-only), adherence event, and the N4 mapping of published edits.
- A field counts as compiled only if a CI test (toy environment, scripted fake model) shows a non-default value changes the controller's actions as specified.
- Minimum compiled set: `exploration.*`, `tool_policy.*`, `verification.*`, and `recovery.retry_on`, `max_retries`, `on_repeated_failure` (continue, replan, restart_task). Planning, memory and notes may stay text-only if labelled.
- The paper-1 edit space excludes rollback values and fields and `switch_to`; `switch_to` sits behind a flag the proposer cannot emit; unit tests check both.
- If `recovery.*` cannot be compiled in time, the typed-strategy claim is narrowed in the pre-registration, never silently kept.

**Decisive evidence.** `baselines/agent_loop.py:1-14` lists the few fields that act as controller behaviour; every arm receives `Strategy.render()` text. `recovery.*` is text-only today. `strategy_schema/model.py:85-89` holds the enum.

**Strongest dissent** (supervisor-requirements check, on schedule). `compile()` plus the Harbor adapter is weeks of work in a 24-week internship. If it slips, Stage 1 slips. A leaner gate would compile only `recovery.*` and `verification.*` and label the rest text-only.

### M13. Model ladder (T1) and compiled vs advised (T2)

**Question.** Should a model ladder and the enforced-vs-advised contrast be in paper 1?

**Positions.** The proponent proposed T2 as one extra arm at k = 3. The statistician held T2's effect is likely below the MDE. The systems engineer proposed the ladder at about 1,400 episodes if throughput reaches 400 per day, then conceded. The statistician proposed an S0-only ladder in the appendix.

**Key objections.** Every arm gets the rendered strategy text, so a single extra arm measures enforcement on top of advice. A full ladder rung costs about 2,255 episodes (10.6 GPU-days). S0-only scores repeat vendor cards and answer no research question.

**Decision: adopt amended.**

- T2 in paper 1, main model only, after G1. Core cell "advised" = S0 controller with S\*1 text, on TB2-89 at k = 5 (445 episodes; 267 after M16 cut 2). Tier C rank 2: "enforce-only" = S\*1 controller with S0 text, k = 5 (445).
- Estimands, exploratory, in the Holm family with S\* − B5: Δ1 compiled S\*1 minus advised S\*1 (detectable from about 5.8 pp); Δ2 advised minus S0; with the enforce-only cell, Δ3 the main effect of enforcement (MDE about 3.8 pp) and the interaction (MDE about 8 pp, descriptive).
- Per-field adherence is a pilot readout, kept only if its instrumentation validates on TB-Pro logs before Stage 2.
- The advised cell runs only if at least one field S\*1 changed is compiled with a passing test.
- The full ladder moves to paper 2 on the TMax family (4B, 9B, 27B); Nemotron-Terminal is dropped from it. Optional T1-lite (Tier C rank 3): S0 and S\*1 on TMax-9B Q4_K_M, TB2-89 at k = 3 (534 episodes), labelled secondary transfer, behind a 20-episode TB-Pro pilot (at least 3 of 20 solved, format errors at most 10%, no training-data overlap found).

**Decisive evidence.** `baselines/agent_loop.py` builds the system message from `strategy.render()`. [Harness Updating Is Not Harness Benefit](https://arxiv.org/abs/2605.30621) finds weak models follow harness artefacts poorly (follow rate 0.142 for Qwen3-32B against 0.757 for Claude Opus 4.6 on SkillsBench), but does not test code enforcement or TB2. [It's Not the Capability: Harness Sensitivity Is Non-Monotone Across LLM Agent Tiers (Cho, arXiv 2605.26731, May 2026)](https://arxiv.org/abs/2605.26731) uses a 24-task synthetic benchmark and does not pre-empt T2. [TMax-9B](https://huggingface.co/allenai/tmax-9b): Apache-2.0, a 5.63 GB Q4_K_M file, vendor TB2 score 27.2% from its own harness.

**Strongest dissent** (novelty scout, supervisor-requirements check). A same-family ladder with per-rung adaptation turns "small models anyone can run" into a scientific result: who benefits from adaptation, and whether enforcement matters more for smaller models. Paper 1 with one model supports only "this model on these tasks", and Self-Harness already reports three models.

### M14. Other threads

**Question.** Index variants (T5, T13), diagnosis-noise injection (T6), failure-taxonomy shift (T12) in paper 1? Seed replication (T15) and others if budget allows? Any to add or drop?

**Positions.** The statistician wanted T12 and T15 in paper 2. The systems engineer proposed a reduced T6 at about 650 episodes, then withdrew it. The novelty scout wanted "unlocked versus reliability" as a main result. The proponent and the skeptical reviewer appealed to keep T6 in paper 1 (not upheld).

**Key objections.** A real noise-level arm needs a full adaptation run (about 1,810 episodes) and loop replication. Gross "newly unlocked" counts are about 11 to 12 pp even when S\* = S0; only the net difference is unbiased.

**Decision: adopt amended.**

- Paper-1 main, 0 episodes: the M5 index variants; cost-of-failure columns in the point-1 table.
- Paper-1 appendix, 0 episodes: failure-taxonomy shift across rounds with diagnoser agreement (Cohen's kappa) on 40 to 60 hand-labelled TB-Pro failures, never TB2; net pass@k of S\* minus S0 (never a count of "newly solved" tasks); per-test partial credit as a screening simulation on TB-Pro logs.
- Seed 2 is not an add-on: it is core (M16) and removable only by cut 5 before Stage 1. S\* naming is frozen at Stage 1 (seed average for H1 to H4, BoN and B1 matching, the index and S\* − B5; S\*1 for T2, T1-lite, attribution and the mid-task arm).
- Portability check (point 6): S0 on TB2-89 × 3 (267 episodes) on a consumer-class machine, descriptive, inside the final run; plus an optional S\*1 × 2 (178) only if off the main GPU.
- Tier C order (M16): the TB-Pro demonstration only if Q4 says essential; T2 enforce-only; T1-lite; B5.
- Paper 2: the full ladder, T3, T6 injection (the first paper-2 experiment if the S\* − B4 CI includes 0), T10, T14, and a give-up field. The paper states that S\* versus B4 gives no causal evidence on diagnosis quality. A possible follow-up on capability assessment of strategy versions (paper 2).
- Dropped: T9, T11, T16 as a thread (edit-effect predictions are folded into the edit log), the human-baseline index variant, B3.

**Decisive evidence.** Simulation: gross unlocked counts of 11.4 pp (k = 5) and 12.5 pp (k = 10) with S\* = S0, net 0.0 pp (estimates). [Agentic Context Engineering](https://arxiv.org/abs/2510.04618), section 4.6, reports graceful degradation under noisy reflections, which narrows T6's novelty. The plan already budgets 40 to 60 labelled failures (TECHNICAL_PLAN 10). [AHE](https://arxiv.org/abs/2604.25850) pairs each edit with a prediction.

**Strongest dissent** (proponent, skeptical reviewer, on T6). B4 tests diagnosis against random edits with only one loop per arm. Noise injection is the only design that varies diagnosis quality with the rest of the loop fixed. ACE's robustness is on a different benchmark with a prose playbook. Without T6, paper 1 has no causal evidence on diagnosis if B4 is close to S\*.

### M15. Phase 0 calibration and the fallback model

**Question.** Calibrate on TB-Pro rather than TB2, and set the rule for switching model.

**Positions.** The red-team rule (switch if S0 < 12% on TB-Pro) was carried by the supervisor-requirements check. The proponent proposed at least 50 contested tasks at k = 3 and a 12 to 45% band, then withdrew it. The skeptical reviewer proposed Nemotron-Terminal-32B as first fallback. The systems engineer, with the statistician and the novelty scout, proposed switching model below 40 contested tasks. The supervisor-requirements check asked for a mapping from the TB2 band to a TB-Pro threshold.

**Key objections.** A point threshold with an SE of about 2.6 pp cannot separate 10% from 14%. At least 40 contested at k = 3 fails 17 to 87% of the time on noise. Nemotron-32B does not fit 24 GB at a 32k slot. A TB2-to-TB-Pro mapping needs a TB2 run.

**Decision: adopt amended.**

- Phase 0 never runs a model on TB2 and uses the M2 TB-Pro pools.
- Bring-up (E-P0, 150 episodes): fit-gated sweep (at most 3 configurations × 15 dev tasks × 2) and a 60-episode A/A determinism run; fit MCU and k_occ; write `pins.lock`.
- E0: Qwen3.6-35B-A3B Q4_K_M as S0, × 3 on every surviving TB-Pro task outside the dev slice (at most 600 episodes).
- Gate G0, four separate checks. Fitness: fails if the CI upper bound of the TB-Pro pass rate is below 12% or the lower bound above 45%, or infrastructure errors exceed 5%. Supply: C3 ≥ 40 sizes pools directly; else 2 more runs on non-contested tasks (at most 400 episodes) and count C5: C5 ≥ 30 normal pools; 20 ≤ C5 < 30 smaller pools screened at k = 2; C5 < 20 is a fitness failure. Throughput: below 150 episodes per GPU-day or median episode above 600 s triggers M16 cuts, never a model switch. Memorisation: probe 20 TB-Pro tasks and report.
- Fallback order, each capped at 1,150 episodes and deducted from the GPU-day budget: Qwen3.5-35B-A3B Q4_K_M; TMax-9B Q4_K_M; Nemotron-Terminal-32B Q4_K_M only on at least 32 GB. At most 2 fallbacks on 24 GB, 3 on 32 GB. GPT-5-mini (API) only by the professor's decision.
- The recorded 20 to 40% TB2 starting band is checked on public scores only: Qwen3.6-35B-A3B scores 106/445 = 23.8% overall and 100/410 = 24.4% on the 82 tasks unchanged since the reference commit, so it passes.
- One fixed reference figure (24.39% on the 82 unchanged tasks), compared descriptively with our S0 from the final run, with its confounds listed (7 changed tasks, mixed agent versions, laptop offload, timeouts, harness and sampling).
- Q6, options: accept or change the order; if no local model passes, (a) GPT-5-mini via API, (b) the best local model with smaller pools, (c) re-scope to a smaller-model study. **Default:** the stated order, and (b) if no local model passes and there is no answer within one week. Logged as "defer to professor" against meeting item 6.

**Decisive evidence.** Supply simulations (estimates): about 22.6% of tasks contested at S0 × 3 if TB-Pro resembles TB2, which is unverified. Memory arithmetic for the three models. TB2 leaderboard dataset for the reference figures; the reference used task commit `69671fb`, 8 commits behind the project's pin.

**Strongest dissent** (statistician, systems engineer). Contested supply binds the whole design. A model with fewer than 30 contested TB-Pro tasks even at k = 5 is the wrong model, whatever its pass rate. Pools of 12 to 18 tasks at k = 2 give little selection power and an S\* close to S0. A clear switch at C5 < 30 is simpler to defend than a three-band rule.

### M16. Total compute and the cut order

**Question.** Total episodes and GPU-days for paper 1, and what is cut, in which order, if the GPU is smaller or slower.

**Positions.** Most round-1 budgets used 320 or 340 per day. The skeptical reviewer ranked B5 and seed 2 ahead of the six meeting-point items. The supervisor-requirements check wanted seed 2 cut first because it serves none of the six points. The systems engineer assumed about 500 per day at concurrency 4.

**Key objections.** The 320 and 340 figures rest on the refuted 270 s. A single loop makes RQ1 a claim about one artefact (about 35% of single loops yield a true gain below the MDE in simulation), so seed 2 outranks cost. The 500-per-day figure is unmeasured.

**Decision: adopt amended.**

- Planning rate: 213.5 episodes per GPU-day, ±30%, applied to TB-Pro work as well until G0 measures the real rate r. Budgets are in episodes first.
- Core (main GPU, default) = **9,653 episodes ≈ 45.2 GPU-days** (34.8 to 64.6 across the band):

| Item | Episodes |
|---|---|
| E-P0 bring-up (sweep + A/A), TB-Pro | 150 |
| E1 B1 smoke, TB-Pro | 60 |
| E0 S0 × 3, TB-Pro | 600 |
| E2 three hybrid loops (S\*1, S\*2, B4) × 1,365, TB-Pro | 4,095 |
| E3 TB2-89: S0 × 10 (890), S\*1 × 5 (445), S\*2 × 5 (445), B4 × 5 (445), B1 × 5 (at most 1,024) | 3,249 |
| E-ATTR attribution: up to 3 reverted-dimension arms + lessons-off arm, 40 TB2 tasks × 3 each | 480 |
| E-T2 advised cell, TB2-89 × 5 | 445 |
| E4b mid-task reserve (40 TB-Pro + 267 TB2) | 307 |
| E-PORT portability, S0 TB2-89 × 3 | 267 |

- With a consumer machine for E-PORT, the core is 9,386 episodes (44.0 GPU-days). The attribution set is fixed at Stage 1 from public third-party data only: the 35 tasks with at least one success in the reference run plus 5 of its 54 never-solved tasks (seed 20261015, stratified by category).
- Caps: core with contingency 10,500 episodes (49.2 GPU-days); absolute including Tier C 12,500 (58.6). API spend for paper-1 arms is $0. Contingency funds only named uses (E0 top-up, infrastructure reruns, the 1 × fallback, judge, selector and proposer calls), never new arms.
- Tier C, in order, each only if its verdict admits it: (1) TB-Pro second-order demonstration, at most 1,365, only if Q4 says essential; (2) T2 enforce-only, 445; (3) T1-lite, 534 + 20; (4) B5, 1,810.
- G0 rule: capacity C = 0.9 × r × remaining dedicated GPU-days. If C covers the remaining core (8,843 episodes), run it and admit Tier C in order. Otherwise apply cuts in order until the plan fits:

| Cut | Change | Plan after cut |
|---|---|---|
| 1 | Attribution to 2 arms | 9,413 (44.1 GPU-days) |
| 2 | T2 advised cell k 5 to 3 | 9,235 (43.3) |
| 3 | B1 × 5 to × 3 (cap 614) | 8,825 (41.3) |
| 4 | R 6 to 4 in all three loops | 7,505 (35.2) |
| 5 | Drop the S\*2 loop; S\* = S\*1 × 10; only before Stage 1 | 6,580 (30.8) |
| 6 | S0 pool × 10 to × 6 | 6,224 (29.2) |

- Floor: 6,224 episodes (29.2 GPU-days). Below the floor, halt before Stage 1 and escalate.
- Never cut: the two gates, E-P0, E0, all 89 TB2 tasks held out, S0 at least 6 and S\* at least 10 runs per task, B4 × 5, B1, BoN, the point-1 and point-2 tables, the index and selector analyses, E-PORT, the lessons-off arm, the mid-task reserve until Q2 or the freeze, pre-registration and the held-out ledger.
- Q5: how many dedicated GPU-days, on which GPU, and can a consumer machine be provided? **Default:** E-PORT runs on the main GPU in an emulated 8 GB-VRAM offload configuration, stated as emulated and logged against meeting item 6; plan the full core and halt at G0 if capacity is below the floor.

**Decisive evidence.** Section 4, rows 1 to 3. Hybrid loop cost of 1,365 episodes (arithmetic from the M9 rule). Episode time depends on outcome. Two seeds at k = 5 cost the same TB2 episodes as one at k = 10.

**Strongest dissent** (skeptical reviewer, with the novelty scout in round 1). B5 belongs in the core. A reviewer who knows Self-Harness, AHE and Meta-Harness will ask why typed edits were not compared with code edits under the same budget. B5 should displace B1 × 5 to × 3 and the T2 advised cell, not wait for headroom above 10,500 episodes.

---

## 6. Questions for Prof. Abdelrazek

These are open. Each has a default that applies only if there is no answer by the Stage-1 freeze (Q6: within one week of the case arising). Every default applied is logged as "defer to professor, default applied" and told to him.

| Q | Topic (meeting point) | Options | Default |
|---|---|---|---|
| Q1 | Intelligence index (4) | (a) one number, CER_test; (a) two numbers, CER_test + T\*; (b) composite for model choice; (c) other | (a) with CER_test headline and T\* companion |
| Q2 | Strategy switching (5) | (a) per-task selector; (b) mid-task switching; (c) both; (a) plus probe-based selector | (a) only; mid-task switching to paper 2 |
| Q3 | Task pools (2) | (i) hold out all 89 TB2 tasks, adapt on TB-Pro; (ii) keep the committed split; (iii) TB2 re-split | (i) |
| Q4 | Scope | (i) second-order loop, AppWorld and rollback to paper 2; (ii) essential: TB-Pro demonstration; (iii) essential: more GPU-days | (i) |
| Q5 | Compute (6) | GPU-days, GPU model, consumer machine provided or not | Emulated portability check; halt at G0 below the floor |
| Q6 | Model choice (6) | Fallback order; if none passes: (a) API, (b) best local model, (c) re-scope | Stated order; (b) |
| Q8 | Code-edit baseline | Promote B5 to the first Tier C slot; no preference | Tier C rank 4 |

The master list is [DECISIONS.md, section 1](DECISIONS.md#1-open-decisions). It also holds plan items 1 (duration and hours), 6 (model for the diagnoser and proposer) and 11 (venue and authorship), left from the 2026-10-15 plan.

How the six meeting points are carried:

| Point | Handled by |
|---|---|
| 1. "baseline cost : task" | M4 point-1 table, M8 charging, M6 selector cost, M14 cost-of-failure columns; never cut (M16) |
| 2. "benchmark : task" | M2 routing table and Q3, M10 ledger, the 89-row per-task table, M15 reference comparison |
| 3. "strategy adapt" | M9 selection rule, M12 compiled fields, M3 tests, M13 mechanism contrast, two seeds (M16), contribution (M1) |
| 4. "intelligence index" | M5 and Q1, variants at 0 episodes (M14), AppWorld re-entry rule (M7) |
| 5. "strategy switching" | M6 and Q2, reserve and gates, `switch_to` hook (M12) |
| 6. "small models on terminal bench, coz everyone can run small models on local machine" | Local model first and Q6 (M15), hardware request (M11), E-PORT and Q5 (M16), T1-lite (M13) |

## 7. What this changes in the plan

- **Contribution (TECHNICAL_PLAN 1, 6.5).** Reframed as a pre-registered, compute-matched test of typed, compiled strategy adaptation for a small local model on held-out Terminal-Bench tasks, against best-of-N and reflection-retry, with cost per task and mechanism evidence. A closest-work table (paper Table 1) adds the 2026 harness cluster and the evaluation study 2607.12227. No "first" claim.
- **Pools and splits (7.1).** Pending approval (Q3): all 89 TB2 tasks held out; adaptation, selection and calibration on deduplicated TB-Pro, after a CPU-only route pilot. The committed split stays in the repo; the TB2 re-split is the pre-registered fallback.
- **Statistics (7.2).** Paired t on per-task differences as primary, one-stage task bootstrap, fixed-sequence H1 to H4, McNemar dropped, and Holm kept only for the exploratory B5 and T2 contrasts. S0 × 10, S\* 10 runs over two seeds, B4 × 5, B1 × 5. Two-stage pre-registration (signed tag, Zenodo, OSF).
- **Baselines (4.1).** Sampling at 0.6 / 0.95 / 20 for all arms; B1 as in-episode reflection-retry with a judge or self-test trigger; B2 as pooled BoN from the S0 pool with a post-trial judge; B3 dropped; B5 added as gated Tier C.
- **Cost (4.2, 4.3, `baselines/cost.py`).** One cost function; MCU as the matching unit with a per-arm residual gate; dollars at two frozen rates; an extended point-1 table; per-task matching primary, payback curve secondary.
- **Selection rule (5.1, 5.2, `adaptation_engine/first_order.py`).** Hybrid rule, R = 6 fixed, K = 4, at most 2 edit operations, V_pro screen and V2_pro final choice, cap formula per loop; integer thresholds.
- **Strategy object (3.3).** `compile()` gate G1 with per-field tests; minimum compiled set includes `recovery.*`; rollback and `switch_to` out of the edit space.
- **Switching (5.4).** Cross-fitted VBS and SBS replace the same-run oracle; two TB-Pro-frozen selectors; mid-task arm behind Q2 and three gates.
- **Index (7.6).** Δp/C at T = 37 retired as the headline; candidates computed post hoc; the headline waits for Q1.
- **Scope (6, 7.3, 8).** Second-order loop, AppWorld transfer and rollback move to paper 2 by default (Q4); internship objectives 4 and 6 follow.
- **Leakage (7.5, `evaluation/runner.py`).** Dedup, a text lint, a TB-Pro egress allowlist, a TB2 network audit, an append-only held-out ledger keyed on task ids, a lessons-off arm.
- **Infrastructure (2, LOCAL_MODELS).** One workstation, llama.cpp on the host, async Harbor agent, native tool calling, 60-step and 64k-token budgets, multiplier 2 with 1 × censoring for S0; a revised hardware request including a consumer machine (Q5).
- **Phase 0 (PHASE0_CHECKLIST).** Calibration on TB-Pro with separate fitness, supply, throughput and memorisation checks; a fallback order with TMax-9B added (Q6).
- **Budget (9).** About 9,653 episodes and 45.2 GPU-days for the core at the laptop-measured rate (±30%), a floor of 6,224 episodes and 29.2 GPU-days, a fixed cut order, and API spend of $0 for paper-1 arms. The 270 s, 320 and 340 figures are retired.
- **Records.** Every deviation and every defaulted question goes into the decision log ([DECISIONS.md](DECISIONS.md), section 3).
- **Companion documents.** The experiment cards are in [EXPERIMENTS.md](EXPERIMENTS.md), the schedule and gates in [EXECUTION_PLAN.md](EXECUTION_PLAN.md), the paper outline in [PAPER_PLAN.md](PAPER_PLAN.md) and the risks in [RISK_REGISTER.md](RISK_REGISTER.md).
