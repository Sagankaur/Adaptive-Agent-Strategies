# Paper plan for paper 1

Sagandeep Kaur, draft for discussion with Prof. Mohamed Abdelrazek (Deakin A2I2), 2026-10-20.

**Status (2026-10-20).** No experiment has been run and no model has been called. This file plans the paper, not its results. Every number below is either a fixed design value, a planning estimate (labelled as such), or a placeholder in square brackets. Experiment ids follow [EXPERIMENTS.md](EXPERIMENTS.md), which holds the full designs, costs and decision rules. Where this file and [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md) disagree, [EXPERIMENTS.md](EXPERIMENTS.md) and this file hold the later decisions (2026-10-20).

Some parts of the paper depend on Prof. Abdelrazek's answers to open questions. They are marked **to confirm with Prof. Abdelrazek**, with the default that applies if there is no answer by the Stage-1 freeze. Defaults are logged in [DECISIONS.md](DECISIONS.md) when applied.

---

## Contents

1. [Terms and acronyms](#1-terms-and-acronyms)
2. [Working title options](#2-working-title-options)
3. [Abstract skeleton](#3-abstract-skeleton)
4. [Contributions](#4-contributions)
5. [Section-by-section plan](#5-section-by-section-plan)
6. [Figures and tables](#6-figures-and-tables)
7. [Appendices](#7-appendices)
8. [Pre-registration plan](#8-pre-registration-plan)
9. [Candidate venues](#9-candidate-venues)
10. [Paper 2 outline](#10-paper-2-outline)
11. [Where the six meeting points are answered](#11-where-the-six-meeting-points-are-answered)

---

## 1. Terms and acronyms

| Term | Meaning |
|---|---|
| LLM | Large language model |
| TB2 | Terminal-Bench 2.0, 89 tasks, pinned at task commit `2fd12b8` |
| TB2-89 | All 89 TB2 tasks, held out for the final pre-registered run only |
| TB-Pro | terminal-bench-pro, 200 public tasks, used for all adaptation and calibration |
| A_pro, V_pro, V2_pro, dev slice | TB-Pro pools: adaptation, screening (at most 25 contested tasks), end-of-loop choice (at most 15 contested tasks), and a 15-task slice for bring-up only |
| S0 | The fixed hand-written strategy. Older files call this baseline B0; this file uses S0 only |
| S\*1, S\*2 | The strategies chosen by two independent adaptation loops (seed 1 and seed 2) |
| S\* | The per-task average of S\*1 ×5 and S\*2 ×5 (10 runs per task). In the single-seed branch, S\*1 ×10. S\* is an estimate for the adaptation procedure, not one strategy a reader can reuse; S\*1 and S\*2 are the reusable artefacts and are always reported next to it |
| B1 | Reflection-retry inside one episode |
| BoN | Best-of-N: one of N runs of S0, picked by a selector. Older files call this baseline B2; this file uses BoN only |
| Test-time scaling | Spending more compute on each task at inference time. Two forms appear here: parallel sampling (several independent runs, one picked; best-of-N is this form) and sequential refinement (one run revised over several attempts; B1 is close to this form) |
| B4 | Random strategy edits, same edit space, same loop and budget |
| B5 | Free-form edits of our controller code (optional) |
| Episode | One Harbor trial of one strategy on one task |
| MCU | Model Compute Units: a × prompt tokens + b × generated tokens, from llama.cpp per-call timings. a and b are fitted in E-P0 and frozen. MCU is the cost-matching unit |
| k_occ | Model-busy seconds per GPU wall-second, used to turn MCU into dollars |
| pp | Percentage points |
| MDE | Minimum detectable effect at 80% power, alpha 0.05 |
| CI | 95% confidence interval from a one-stage task bootstrap (10,000 resamples), unless stated otherwise |
| CER_test | Compute-equivalence ratio: how many S0 best-of-N samples S\* is worth per task |
| T\* | Payback point: the number of tasks after which adaptation pays for itself |
| VBS, SBS | Virtual best solver (best version per task) and single best solver (best version overall). CF-VBS and CF-SBS are their cross-fitted estimates (choose on odd-index runs, score on even, swap, average) |
| OSF | Open Science Framework |
| DOI | Digital object identifier |
| AoE | Anywhere on Earth (UTC−12), the usual deadline time zone |
| Tier C | Optional add-ons, run only from headroom under the absolute cap of 12,500 episodes |
| RQ1 to RQ4 | The research questions in [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md) section 1: RQ1 adaptation against baselines, RQ2 generalisation, RQ3 second-order loop, RQ4 attribution |
| pass@N | Probability that at least one of N runs passes; "oracle" pass@N picks with the hidden tests |
| AUROC | Area under the ROC (receiver operating characteristic) curve |
| CRN | Common random numbers: the same seed for a (task, run) pair across candidates |
| AA-style composite | A weighted average over several benchmarks, in the style of the Artificial Analysis Intelligence Index |
| KV cache | The key-value attention cache kept by the model server |
| VRAM | GPU memory |
| Small model | In this project, an open-weight model served on one machine. The main model, Qwen3.6-35B-A3B, is a mixture-of-experts (MoE) model with 35B total parameters, of which about 3B are active per token. At Q4_K_M it needs a 24 GB GPU for the main runs (32 GB recommended), or 8 GB VRAM plus 32 GB RAM with MoE layers offloaded to the CPU |
| MoE | Mixture of experts: only a few expert blocks of the model run for each token |
| SNI | Server Name Indication, the host name a TLS connection asks for |
| SHA | The hash that identifies a git commit or tag |
| SD, IQR | Standard deviation; interquartile range |

The six meeting points of 2026-10-14 ([MEETING_2026-10-14.md](MEETING_2026-10-14.md)) are numbered 1 to 6 throughout: 1 "baseline cost : task", 2 "benchmark : task", 3 "strategy adapt", 4 "intelligence index", 5 "strategy switching", 6 "small models on terminal bench, coz everyone can run small models on local machine".

---

## 2. Working title options

The paper does not use the word "steering". In this field it usually means activation steering, which this project does not do (see the note in [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md)). No title claims a "first".

| # | Title | What it stresses |
|---|---|---|
| 1 | Does Strategy Adaptation Pay for a Small Local Agent? A Pre-Registered, Compute-Matched Test on Terminal-Bench | The first test (H1, adapted against fixed) and its cost per task (point 1) (preferred) |
| 2 | What Strategy Adaptation Buys a Small Local Agent: Cost per Task on Terminal-Bench 2.0 | Cost per task (point 1) and local models (point 6) |
| 3 | Typed, Compiled Strategies for Small LLM Agents: A Held-Out, Compute-Matched Evaluation | The typed object and the evaluation design |
| 4 | Does Adapting a Typed Strategy Beat Best-of-N at Equal Compute? Evidence from a Small Local Model on Terminal-Bench 2.0 | The best-of-N question (H4); see the condition below |
| 5 | Adapt or Resample? A Pre-Registered, Compute-Matched Test of Strategy Adaptation for a Small Local Agent on Terminal-Bench | The best-of-N comparison (H4); see the condition below |

Option 1 is the default. It is built on H1, the first test in the fixed sequence (section 4.1), so the paper always answers the question in its title. The best-of-N comparison is H4, the last test. It is tested only if H1, H2 and H3 all reject, and its true gap may be at or below the MDE (the E3 risks in [EXPERIMENTS.md](EXPERIMENTS.md)). A title built on it (options 4 and 5) could name a question the paper never formally tests, for example if S\* does not beat B4. The E0-SIM power simulation therefore also reports the simulated probability of reaching H4 and of rejecting it, under the planning effect sizes, before the Stage-1 tag. Options 4 and 5 are used only if that probability is high. The test order is not changed to suit a title. Options 1 to 3 read correctly whether or not H3 and H4 reject. The final title is fixed after Stage 2, before the results are known, so that it does not follow the outcome.

---

## 3. Abstract skeleton

Square brackets are placeholders for numbers from the final run. "Beats" appears only for a hypothesis that is rejected with a CI that excludes 0; otherwise the sentence reports the estimate and its CI. No exploratory result gets a p-value in the abstract.

> Agents built on small, locally served LLMs usually follow a hand-written strategy that does not change across tasks. We test whether adapting that strategy from the agent's own failures helps, once its cost is counted. The strategy is a typed, versioned object. Its compiled fields change controller behaviour, each with a unit test, and the rest are labelled text-only. A diagnose-and-propose loop edits it on [n_A] tasks of terminal-bench-pro, with a frozen [Qwen3.6-35B-A3B, Q4_K_M] (a mixture-of-experts model with 35B total and 3B active parameters) served on one [24 GB] GPU. We then run a pre-registered evaluation on all 89 Terminal-Bench 2.0 tasks, none of which was used for adaptation. The two adapted strategies, averaged over two adaptation seeds, score [p_S\*]% ([p_S\*1]% and [p_S\*2]% separately) against [p_S0]% for the fixed strategy ([d1] pp, CI [l1, u1]) and [p_B4]% for random edits in the same space ([d2] pp, CI [l2, u2]). At matched per-task compute, the seed average [beats / does not detectably differ from] reflection-retry ([d3] pp, CI [l3, u3]) and best-of-N sampling ([d4] pp, CI [l4, u4]). The design detects differences of about [MDE] pp. We report dollars per task for every arm: [c_S\*] for the adapted strategies against [c_S0] to [c_max] for the baselines. The adapted strategies are worth [CER_test] best-of-N samples per task and repay their one-time adaptation cost after [T\*] tasks. Enforcing the same strategy content in code rather than as prompt advice changes the pass rate by [dE] pp (CI [lE, uE]). [One sentence on which dimension groups carry the gain, with CIs, or that none is detectable.] [Inference with the fixed strategy runs end to end in [an 8 GB-VRAM configuration (emulated) / spec], where it scores [p_port]%; adaptation was not run there.] Code, pins, per-task results and the pre-registration are public.

**Notes on the skeleton.**

- The MDE sentence uses the value re-stated after E0-SIM. The planning value for H1 is about 4.5 pp (estimate).
- The CER_test and T\* sentence follows the default reading of point 4, **to confirm with Prof. Abdelrazek** (Q1). Under reading (b) it is replaced by one sentence on the model-choice table.
- The portability sentence uses the machine E-PORT actually ran on. Under the default it reads "an 8 GB-VRAM configuration (emulated)". E-PORT runs S0 only, so the sentence never says that the method or the adaptation runs on consumer hardware.
- If the TB-Pro route fails and E-RESPLIT applies, "all 89" becomes "52 held-out" and the MDE sentence changes (about 7.6 pp at k=5, estimate).

---

## 4. Contributions

The contribution sentence (fixed 2026-10-20): *a pre-registered, compute-matched test of whether adapting a typed, compiled strategy of a small, locally served model on Terminal-Bench beats a fixed strategy, random edits, reflection-retry and best-of-N, with cost per task reported for every arm and mechanism evidence (enforced-vs-advised contrast, leave-one-out attribution over changed strategy-dimension groups).*

### 4.1 Claims

C1 to C3 follow the fixed-sequence gatekeeping order of E3 (H1, then H2, then H3, then H4, alpha 0.05, all two-sided). A later claim is tested only if every earlier one is rejected. Every claim is worded about the realised strategies.

| Claim | Statement (if supported) | Hypothesis | Evidence | Experiment cards |
|---|---|---|---|---|
| C1 | Adapting the typed strategy on TB-Pro raises the held-out pass rate on TB2-89 over the fixed strategy | H1: S\* vs S0 | Table 3, Figure 4 | E2, E3 |
| C2 | The realised diagnosis-driven strategies beat the realised random-edit strategy under the same rule and budget | H2: S\* vs B4 | Table 3, Figure 2 | E2, E3 |
| C3 | At matched per-task compute, the adapted strategy beats reflection-retry and pooled best-of-N | H3: S\* vs B1; H4: S\* vs BoN | Table 3, Table 4, Figure 3 | E3, E3-B1, E3-BoN, E3-COST |
| C4 | Exploratory mechanism evidence: how much of the effect needs code enforcement, and which dimension groups carry it | Estimation only. E-T2 and B5 contrasts share one Holm family {S\* − B5, Δ1, Δ2, Δ3}; E-ATTR uses paired CIs without adjustment | Figure 5, Figure 6, Table 5 | E-T2, E-ATTR, E-B5 if run |

**Where a claim fails.** Each estimate and CI is reported wherever the sequence stops. A non-rejection is written as an estimate with its CI, never as "no difference". "Few or no accepted edits" and "S\* = S0" are pre-registered valid outcomes. If S\* = S0, the paper reports a negative result and E-ATTR does not run.

### 4.2 Deliverables that support the claims (not claims)

| Deliverable | Experiment cards | Meeting point |
|---|---|---|
| Cost per task for every arm, in dollars at two frozen rates, split by outcome and S0 task class | E3-COST, E-N3 | 1 |
| The 89-row per-task pass/fail table and the per-task routing table | E3, P-M2 | 2 |
| The mechanism table: every schema field with its code path, unit-test id and status (compiled or text-only) | G1, E-N4 | 3 |
| Adaptation efficiency (CER_test with T\*), computed from logs | E11 | 4 |
| Offline strategy switching: cross-fitted VBS − SBS headroom, selector regret and cost | E4-SW | 5, 1 |
| A portability run of S0 only (inference with the fixed strategy, no adaptation) in an 8 GB-VRAM configuration: emulated on the main GPU by default, or on a consumer-class machine if one is provided | E-PORT | 6 |
| Pins, the held-out ledger and two pre-registration tags | PREREG-1, PREREG-2, LEDGER | 2 |

### 4.3 What the paper does not claim

- A "first" self-improving harness on TB2, or for small models.
- The first compute-matched comparison of harness adaptation with test-time sampling or refinement on Terminal-Bench. 2607.12227 ran one with frontier models.
- The first typed or frozen-weight harness adaptation of a small self-hosted model on Terminal-Bench. MetaRSI's Harness-RSI arm already does this.
- The first adaptation on a task source disjoint from TB2 with TB2 used only for evaluation. ModularRSI already does this.
- Any gain from a second-order loop (paper 2).
- Transfer across benchmark families or across models. RQ2 (the generalisation question) is scoped as cross-source, TB-Pro to TB2.
- That typed beats code. The typed space is a deliberate restriction of code space, chosen for compiled enforcement, attribution and auditability.
- That diagnosis beats random search in general. H2 compares realised strategies, and the paper states that S\* vs B4 gives no causal evidence on diagnosis quality.

If B5 is not run, the paper states that it makes no comparison with code-harness evolution.

---

## 5. Section-by-section plan

Page lengths assume a 9-page main body. They are estimates and will be trimmed to the chosen venue's limit (section 9). Bold labels such as **3.1** or **6.1** inside each plan are subsections of the paper, not of this file.

| § | Section | Pages (estimate) |
|---|---|---|
| 1 | Introduction | 1.25 |
| 2 | Related work | 1.0 |
| 3 | Method | 1.75 |
| 4 | Experimental setup | 1.25 |
| 5 | Results | 1.75 |
| 6 | Analysis | 1.25 |
| 7 | Limitations | 0.5 |
| 8 | Conclusion | 0.25 |
| | **Total** | **9.0** |

### 5.1 Introduction (about 1.25 pages)

- **Purpose.** State the question and why cost has to be in it. Small open-weight models can be served on one local machine (point 6). In the harness-evolution methods we checked, adapting the strategy is not compared with spending the same compute on test-time best-of-N. One evaluation study does compare them, on TB2.1 with frontier API models and on the searched tasks, and finds that evolution does not beat sampling (2607.12227). Whether this holds for a small local model, on tasks the adaptation never saw, is open.
- **Key claims.**
  - Recent work already shows harness self-improvement on TB2, including with a frozen Qwen3.5-35B-A3B. Whether it pays at equal compute has been tested only with frontier API models (2607.12227).
  - Wang et al. (2607.12227) compared harness evolution with test-time scaling (parallel sampling, which includes best-of-N, and sequential refinement) at a matched rollout budget on TB2.1, with three frontier API models, on the searched tasks. Evolution did not win. We ask a related question for a small local model: whether a typed, compiled strategy adapted once on TB-Pro beats best-of-N and reflection-retry on held-out TB2 tasks at matched per-task compute, with a random-edit control, a pre-registered analysis, cost per task in dollars for every arm and the enforced-versus-advised contrast. That combination, not the loop or the matched comparison as such, is the contribution.
  - Contribution paragraph: the contribution sentence and C1 to C4 (section 4), plus the "not claimed" list in one sentence.
- **Evidence needed.** Verified citations only (section 5.2). The headline numbers from Table 3 and Table 4, in the form of the abstract.
- **Source experiments.** E3 (headline), E3-COST (cost per task), E11 (one efficiency number).
- **Figure.** Figure 1 (overview), placed here or in section 3.

### 5.2 Related work (about 1.0 page)

- **Purpose.** Place the paper against the closest work, state the differences precisely, and avoid any "no paper does X" claim. The wording is: "Among the harness-evolution methods we checked, none reports a test-time best-of-N comparison at matched compute. The evaluation study of Wang et al. (arXiv 2607.12227) does. On TB2.1 with three frontier API models, it compares AHE-style evolution with parallel sampling and sequential refinement at a matched rollout budget (K = 5) on the tasks being searched, and finds that evolution does not win. Its held-out split (45/10/34) compares the evolved harness only with the initial harness."
- **Key claims, by cluster.**
  - **Harness self-evolution on terminal tasks.** Self-Harness: Harnesses That Improve Themselves ([Zhang et al., arXiv 2606.09498, Jun 2026](https://arxiv.org/abs/2606.09498)) improves a frozen Qwen3.5-35B-A3B harness on a 64-task TB2 subset, held-out 23.8% to 38.1%. Those rates fit 10/42 and 16/42; the denominators are our inference and are labelled "inferred". No significance test is quoted. Its models were served on four NVIDIA H200 GPUs. Also: Agentic Harness Engineering: Observability-Driven Automatic Evolution of Coding-Agent Harnesses ([Lin et al., arXiv 2604.25850, Apr 2026](https://arxiv.org/abs/2604.25850)); Meta-Harness: End-to-End Optimization of Model Harnesses ([Lee et al., arXiv 2603.28052, Mar 2026](https://arxiv.org/abs/2603.28052)), whose best-of-N is a search control on text classification, not a TB2 comparison; ModularRSI: Modular and Generalizable Recursive Harness Self-Improvement ([Wu et al., arXiv 2609.14857, Sep 2026](https://arxiv.org/abs/2609.14857)), which evolves on 2,000 tasks disjoint from TB2 and uses TB2 only for evaluation; MetaRSI / RSI2: A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems Themselves ([Tan et al., arXiv 2609.06396, Sep 2026](https://arxiv.org/abs/2609.06396)), which applies typed operators to a self-hosted Qwen3.5-35B-A3B on a sealed TB2.1 split; only its Harness-RSI-only condition keeps the weights frozen, and it compares improvement schedules rather than test-time sampling; SEAGym: An Evaluation Environment for Self-Evolving LLM Agents ([Zheng et al., arXiv 2606.17546, Jun 2026](https://arxiv.org/abs/2606.17546)); MemoHarness: Agent Harnesses That Learn from Experience ([Huang et al., arXiv 2607.14159, Jul 2026](https://arxiv.org/abs/2607.14159)); Mixture of Self-Improving Branches For Agent Harness Optimization ([Dong et al., arXiv 2609.37834, Sep 2026](https://arxiv.org/abs/2609.37834)); Task-CoEvolve: Efficient Harness Optimization via Adaptive Validation Task Selection ([Miyai et al., arXiv 2608.20169, Aug 2026](https://arxiv.org/abs/2608.20169)).
  - **Evaluation of harness evolution.** Rethinking the Evaluation of Harness Evolution for Agents ([Wang et al., arXiv 2607.12227, Jul 2026](https://arxiv.org/abs/2607.12227)) finds that harness evolution does not beat simple test-time scaling on TB2.1 under matched budgets. Its models are three frontier API models (Claude Opus 4.6, GPT-5.4 and GPT-5.4 mini), its baselines are parallel sampling (picked by a self-judge or by unit tests) and sequential refinement at K = 5 rollouts, and the comparison is on the searched tasks. It is the closest precedent for our design and is cited as such.
  - **Updating versus benefiting.** Harness Updating Is Not Harness Benefit: Disentangling Evolution Capabilities in Self-Evolving LLM Agents ([Lin et al., arXiv 2605.30621, May 2026](https://arxiv.org/abs/2605.30621)) reports that weak models gain little because they fail to activate or follow harness artifacts. This motivates enforcing strategy fields in code (E-T2).
  - **Experience as text.** GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning ([Agrawal et al., arXiv 2507.19457, Jul 2025](https://arxiv.org/abs/2507.19457)) and Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models ([Zhang et al., arXiv 2510.04618, Oct 2025](https://arxiv.org/abs/2510.04618)). Cited, not run; the prose baseline B3 left paper 1.
  - **Test-time compute.** Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters ([Snell et al., arXiv 2408.03314, Aug 2024](https://arxiv.org/abs/2408.03314)) and To Backtrack or Not to Backtrack: When Sequential Search Limits Model Reasoning ([Qin et al., arXiv 2504.07052, Apr 2025](https://arxiv.org/abs/2504.07052)). Reflexion: Language Agents with Verbal Reinforcement Learning ([Shinn et al., arXiv 2303.11366, Mar 2023](https://arxiv.org/abs/2303.11366)) is the basis of B1.
  - **Cost-aware evaluation.** AI Agents That Matter ([Kapoor et al., arXiv 2407.01502, Jul 2024](https://arxiv.org/abs/2407.01502)) argues for weighing cost with accuracy and for proper holdout sets.
  - **Efficiency as intelligence.** On the Measure of Intelligence ([Chollet, arXiv 1911.01547, Nov 2019](https://arxiv.org/abs/1911.01547)). Our index is an operationalisation, not his formal measure.
  - **Second-order loops.** Hyperagents ([Zhang et al., arXiv 2603.19461, Mar 2026](https://arxiv.org/abs/2603.19461)), a loop that also edits its own improvement mechanism, and related work, one sentence, pointing to paper 2.
  - **Benchmarks.** Terminal-Bench: Benchmarking Agents on Hard, Realistic Tasks in Command Line Interfaces ([Merrill et al., arXiv 2601.11868, Jan 2026](https://arxiv.org/abs/2601.11868)); TB-Pro, introduced in Let It Flow: Agentic Crafting on Rock and Roll, Building the ROME Model within an Open Agentic Learning Ecosystem ([Wang et al., arXiv 2512.24873, Dec 2025](https://arxiv.org/abs/2512.24873)).
- **Evidence needed.** Table 1, from the comparison matrix in [LITERATURE_MAP.md](LITERATURE_MAP.md) section 4. Each "no" cell means "not found in a keyword search of the full text".
- **Source experiments.** E-N4 (expressiveness audit: map the published edits of Self-Harness, AHE and MemoHarness onto our schema as compiled, text-only or not expressible). 0 episodes.

### 5.3 Method (about 1.75 pages)

- **Purpose.** Define the strategy object, `compile()`, the adaptation loop with the adopted selection rule, and the baselines, precisely enough to reproduce.
- **3.1 Typed strategy.** Dimensions: exploration, planning, tool policy, memory, verification, recovery, and fenced free-text notes. Budgets (steps, generated tokens) are fixed by the experimenter and are not editable. Each version records its parent, its edits, the evidence for them and a strategy hash. Field list as in [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md) section 3.2.
- **3.2 `compile()`.** `compile(strategy)` returns a controller configuration and prompt text, with independent switches for each. This makes the E-T2 cells buildable. A field counts as **compiled** only if a CI unit test (toy environment, scripted fake model) shows that a non-default value changes the controller's action sequence in a specified way. Every other field is **text-only**, is excluded from every "enforced" claim, and its edits are reported as advice. The minimum compiled set is exploration, tool_policy, verification, and recovery.retry_on / max_retries / on_repeated_failure (values continue, replan, restart_task). Table 2 lists every field. If recovery cannot be compiled by the Stage-1 date, the typed-strategy claim is narrowed in the pre-registration, never silently kept.
- **3.3 Adaptation loop (hybrid rule, R = 6 fixed rounds, no early stop).** Round r:
  1. Run S_r once on a fixed 50-task diagnosis sample of A_pro (seed 20261015).
  2. The diagnoser and proposer (the same local model as the agent) emit K = 4 candidates of at most 2 edit operations each. Each passes a lint that rejects task ids, URLs, commands over 40 characters and task paths. The paper-1 edit space excludes rollback values, rollback fields and `switch_to`, enforced by a unit test.
  3. Run the parent S_r fresh and the 4 candidates once each on V_pro (at most 25 contested TB-Pro tasks), with shared per-(task, run) seeds.
  4. Statistic: the integer net count of tasks solved by the candidate minus the parent. Accept the best candidate if it is at least +1 task. Ties go to the lower mean MCU, then the earlier version.
  5. After round 6, run all 7 versions (S0 to S6) ×3 on V2_pro (at most 15 contested tasks, disjoint by sibling group). S\* is the version with the most net V2 successes, ties to the earlier version.
  - The cap per loop is a formula: 6 × (|A_diag| + 5 × |V_pro| × k_screen) + 7 × |V2_pro| × k_V2 ≤ 1,575 episodes (nominal 1,365).
  - The text states plainly that the rule is lenient: under a pure null it accepts edits often, so the edit log is screening data, not evidence of gains. The chosen version's V2 score is not a gain estimate (winner's curse).
- **3.4 Baselines.** B0 = S0. B1 = reflection-retry inside one Harbor trial: it retries when the in-run judge says fail or an agent-written test fails, never on hidden tests; at most 3 attempts, no environment reset, a 60-step cap per attempt and one shared 64k generated-token cap across the B1 task/run including judge and reflection calls. The requested attempt cap is randomized per (task, run) to match S*'s per-task MCU, while realized attempts may be lower if the token ceiling is reached. BoN = pooled best-of-N from the S0 x 10 pool, selected by a same-model judge that never sees `tests/`, computed exactly over all subsets; oracle pass@N is drawn dashed, as a ceiling only. B4 = random edits from the same edit space, same rule and budget. B5 (optional) = free-form controller-code edits by the same proposer, sandboxed.
- **3.5 Cost.** One cost function. MCU is the matching unit; it is not claimed to equal GPU-seconds. Dollars per task = (MCU-hours / k_occ) × rate, at two frozen named rates (electricity; cloud-GPU-equivalent). Every model call is charged to the arm that makes it (judge calls to BoN rows; reflection and in-run judge calls to B1; selector calls to library + selector; diagnosis and proposal calls to the one-time adaptation cost).
- **Evidence needed.** Table 2 (mechanism table, after G1 sign-off). Figure 1. The MCU fit (Appendix A4).
- **Source experiments.** G1, CODE-FIX, LINT-PILOT, E-N4, E-P0 (MCU fit), E0-SIM2 (selection-rule simulation).

### 5.4 Experimental setup (about 1.25 pages)

- **Purpose.** State pools, model, serving, budgets, cost unit, statistics and pre-registration, so a reader can judge validity before seeing results.
- **Pools.** Adaptation and calibration on deduplicated TB-Pro only. All 89 TB2 tasks are held out for the final run. Before Stage 2 the only TB2 contact is image pulls by digest, logged in an append-only ledger. This replaces the committed split A25/V12/M15/H37 (seed 20261015), whose held-out part has only 11 contested tasks in little-coder's public run, with all 9 known sibling pairs straddling it. The change is **to confirm with Prof. Abdelrazek** (Q3; default: approve). The fallback, used only if the TB-Pro route fails, is a sibling-grouped TB2 re-split with 52 held-out tasks (E-RESPLIT). The per-task routing table goes in Appendix A1.
- **Model.** Qwen3.6-35B-A3B, Q4_K_M. It passes the recorded starting rule (20 to 40% on TB2) on public figures: 106 of 445 trials (23.8%) in little-coder's run. Fallback order and the no-local-model case are **to confirm with Prof. Abdelrazek** (Q6). Default order: Qwen3.5-35B-A3B, then TMax-9B, then Nemotron-Terminal-32B on 32 GB or more; GPT-5-mini only by his decision.
- **Serving.** llama.cpp on one x86-64 Linux host, Harbor with local Docker, our agent loaded in the harness process. Concurrency pinned from the E-P0 sweep. Sampling temperature 0.6, top_p 0.95, top_k 20, logged per-request seed, for every arm.
- **Budgets.** max_steps = 60 (a logged change from S0's committed 40). At most 64k generated tokens per task/run, reasoning included; B1 shares the cap across all attempts and judge/reflection calls. Prompt/input tokens are costed but do not consume this cap. Wall-clock is a backstop only (agent timeout multiplier 2 for every arm).
- **Network and leak controls.** TB-Pro runs under a pinned allowlist fork. TB2 runs under its upstream setting with per-trial SNI and DNS (domain name system) logs and a text search for benchmark and solution strings; flagged trials count as failures in the primary analysis.
- **Cost unit.** MCU, validated per arm before Stage 2 (mean residual within ±3%, CI within ±5%, at least 40 TB-Pro episodes). If a validated arm fails, a context-length term is added and the fit is redone. If it still fails, the unit becomes processed tokens and MCU is kept as a sensitivity analysis.
- **Statistics.** Unit of analysis: the task. Estimand: equal-weight mean over tasks of p(S\*) − p(B). Primary test: paired t on per-task mean differences, two-sided, alpha 0.05, fixed sequence H1 to H4. Sensitivity: paired sign-flip permutation (100,000 flips) and a generalised linear mixed model, pass ~ arm + (1 + arm | task). If the simulated size of the t-test exceeds 6% in either E0-SIM simulation, the sign-flip test becomes primary.
- **Pre-registration.** Two stages, each a signed git tag archived on Zenodo with a DOI, plus an OSF entry quoting the tag SHA and DOI (section 8).
- **Evidence needed.** Table 7 (pools and run settings). Planning MDEs re-stated after E0-SIM.
- **Source experiments.** P-M2, E-P0, E0, E0-SIM, E0-JUDGE, PREREG-1, PREREG-2.

### 5.5 Results (about 1.75 pages)

- **Purpose.** Report the confirmatory run in gatekeeping order, then cost per task.
- **Key claims.** C1, C2, C3 as supported or not. One paragraph per hypothesis, in order, with estimate and CI. Between-seed difference reported. Cost per task for every arm.
- **Evidence needed.**
  - Table 3: H1 to H4 estimates, CIs, the MDE, the between-seed row and the E3-REF footnote.
  - Table 4: cost per task (point 1).
  - Figure 3: pass rate against MCU per task, with BoN and B1 curves.
  - Figure 4: per-task difference distribution and per-seed estimates.
  - Figure 2: adaptation trajectories, as context for what S\*1 and S\*2 are, with the E5-DEMO loop overlaid if it runs.
  - Table 6: portability row (E-PORT) and, if admitted, the second-model row (E-T1lite).
  - The E3-REF comparison with little-coder's 100 of 410 trials (24.39%) on the 82 unchanged tasks, as a descriptive footnote with its confounds listed.
- **Source experiments.** E2, E3 (E3-B1, E3-BoN, E3-COST, E3-LB, E3-REF, E3-AUDIT), E-PORT, E-T1lite if admitted, E4b row if run, E5-DEMO overlay if run.

### 5.6 Analysis (about 1.25 pages)

All exploratory. Paired CIs, no p-values in the abstract.

- **6.1 Why typed: enforcement against advice (E-T2).** Δ1 = compiled S\*1 minus advised S\*1; Δ2 = advised minus S0; Δ3 and the interaction only if the enforce-only cell runs. Holm-adjusted within {S\* − B5, Δ1, Δ2, Δ3}. Planning MDE for Δ1 about 5.8 pp (estimate). Figure 5.
- **6.2 Attribution (E-ATTR).** Leave-one-out by changed dimension group on a 40-task TB2 set fixed from public third-party data, plus a lessons_k = 0 and notes-off arm. MDE about 12 pp (estimate), so per-group effects of a few pp cannot be confirmed. Figure 6, Table 5.
- **6.3 Adaptation efficiency (E11).** Default reading of point 4 (**to confirm with Prof. Abdelrazek**, Q1): CER_test as headline, T\* as companion. Censored when the BoN frontier never reaches S\*'s pass rate, never extrapolated. Δp and cost are always shown next to any index. Figure 7.
- **6.4 Strategy switching (E4-SW).** Reading (a) of point 5 is in paper 1 under every answer: a library of up to 5 versions, cross-fitted VBS − SBS headroom, two selectors frozen on TB-Pro, regret and cost per task. Reading (b), mid-task switching (E4b), runs only behind its three gates; its default is paper 2 (**to confirm with Prof. Abdelrazek**, Q2). Figure 8.
- **6.5 Code-edit baseline (E-B5), if run.** S\* − B5 with a Holm-adjusted CI, read through the pre-registered E-INTERP table. If B5 ≥ S\*, the typed claim retreats to auditability, attribution and seed stability.
- **6.6 Smaller analyses (appendix pointers).** Failure-taxonomy shift and diagnoser agreement (E-T12, TB-Pro logs only); net pass@k (E-N1); per-category results; leak flag rates per arm.
- **Source experiments.** E-T2, E-ATTR, E11, E4-SW, E4b, E-B5, E-T12, E-N1, E-N3, E3-AUDIT.

### 5.7 Limitations (about 0.5 page)

- **Purpose.** State what the design cannot show, before reviewers do.
- **Key points.**
  - One main model and one benchmark family. RQ2 is cross-source (TB-Pro to TB2), not cross-family.
  - Power. Planning MDEs (estimates) are about 4.5 pp for H1 (S\* 10 runs against S0 ×10), about 5.2 pp for S\* against a ×5 arm (H2 against B4 ×5, H3 against B1 ×5; our interpolation between the E3 planning rows), 5.8 to 5.9 pp for two ×5 arms (for example S\*1 against B4), and about 6.1 pp for H3 only after cut 3 (B1 ×3). The true gaps to B1 and BoN may be smaller. In little-coder's public run only 28 of the 89 TB2 tasks were contested (54 never solved, 7 always solved).
  - One or two adaptation loops are high-variance draws of the procedure. Claims are about the realised strategies.
  - The same-model judge may be weak. The E0-JUDGE AUROC gate and the dashed oracle make that visible.
  - Per-task matching treats the one-time adaptation cost as free; T\* reports it. Reading point 1 as total project cost would change this.
  - TB2 runs with internet access; the audit cannot close every leak channel. TB-Pro and the Qwen models share a provider, so calibration scores could be inflated; the memorisation probe reports this.
  - The leaderboard comparison is approximate (censoring at 1× the task timeout).
  - The typed space restricts what edits are possible. Without B5 there is no comparison with code-harness evolution.
  - E-PORT under the default is an emulated configuration, not a specific consumer machine. It runs S0 only, so adaptation on consumer hardware is not shown.
- **Source experiments.** E0-SIM, E0-JUDGE, E0-MEM, E3-AUDIT, E3-LB, E-PORT.

### 5.8 Conclusion (about 0.25 page)

- **Purpose.** One paragraph: the answer to the question, its cost, what the mechanism evidence suggests, and what paper 2 will test.
- **Evidence needed.** Table 3, Table 4, Figure 7. No new numbers.

---

## 6. Figures and tables

Ids are stable labels shared with [EXPERIMENTS.md](EXPERIMENTS.md). Print order may change when the paper is typeset. The two tables required by meeting points 1 and 2 are **Table 4** (cost per task) and **Appendix A1** (per-task table); both are on the never-cut list.

### 6.1 Main-text tables

| Id | What it shows | Columns | Source experiment | Meeting point |
|---|---|---|---|---|
| Table 1 | Closest-work matrix | Work; typed strategy; frozen weights; terminal benchmark; small local model; cost-matched BoN; held-out evaluation; per-component attribution; second-order loop; cross-model | Literature check, E-N4 | 3 |
| Table 2 | Mechanism table: every schema field | Dimension; field; code path; unit-test id; status (compiled or text-only); adherence event definition; E-N4 mapping of published edits (Self-Harness, AHE, MemoHarness, or "not expressible") | G1, E-N4 | 3 |
| Table 3 | Confirmatory results on TB2-89 | Hypothesis; comparison; runs per task; pass rate of each arm; difference (pp); 95% CI; p (paired t); rejected in sequence (yes, no, not tested); MDE. Extra rows: S\*1 and S\*2 separately, between-seed SD, E3-LB leaderboard-comparable S0, E4b row if run, S\* − B5 row if run. Footnote: E3-REF and its confounds | E3, E4b, E-B5 | 2, 3 |
| Table 4 | **Cost per task, every arm** | Rows: S0, B1 (each cap), BoN (N = 1 to 5 and P), B4, S\* (seed average and each seed), library + selector, B5 if run, E-T2 cells. Columns: mean, median, IQR and CI of dollars per task at both rates; wall-clock (with GPU model, slot count, concurrency); generated tokens including reasoning; prompt tokens; cached tokens; MCU; pass rate per dollar. Each column split by outcome (solved, failed) and by S0 task class (never, contested, always). MCU never appears without dollars next to it | E3-COST, E-N3, E4-SW | 1 |
| Table 5 | Exploratory mechanism estimates | Estimand (Δ1, Δ2, Δ3 if run, each E-ATTR arm, lessons/notes-off, S\* − B5 if run); runs per task; difference (pp); CI (Holm-adjusted where in the family); planning MDE | E-T2, E-ATTR, E-B5 | 3 |
| Table 6 | Portability and second model | Row; machine (GPU, VRAM, RAM, or "emulated 8 GB-VRAM"); model; arm; runs per task; pass rate with CI; seconds per step; dollars per task | E-PORT, E-T1lite if admitted | 6, 1 |
| Table 7 | Pools and run settings | Pool; source; size; use; runs per task. Settings: model file, sampling, budgets, concurrency, network, cost unit | P-M2, E0, E-P0 | 2, 6 |

### 6.2 Main-text figures

| Id | What it shows | Axes | Source experiment | Meeting point |
|---|---|---|---|---|
| Figure 1 | Overview: typed strategy, `compile()`, the adaptation loop on TB-Pro, and the one-time held-out run on TB2-89 | Diagram, no axes | Method | 3, 2 |
| Figure 2 | Adaptation trajectories of S\*1, S\*2 and B4 | x: version (S0 to S6); y: V2_pro pass rate with CI; markers for accepted edits; E5-DEMO loop overlaid if it runs | E2; E5-DEMO overlay if run | 3 |
| Figure 3 | Pass rate against compute per task, with BoN and B1 curves, and a T\* inset | x: mean MCU per task (log scale), with a dollar secondary axis; y: TB2-89 pass rate with CI; BoN@N points joined, dashed oracle pass@N; B1 by cap; S\*, S\*1, S\*2, B4, B5 if run | E3, E3-BoN, E3-B1 | 1, 3 |
| Figure 4 | Per-task differences and per-seed estimates | Left: per-task p(S\*) − p(S0), sorted, coloured by S0 task class; right: estimates for S\*1, S\*2 and S\* with CIs | E3 | 2, 3 |
| Figure 5 | Enforced against advised | x: cell (S0; advised; S\*1; enforce-only if run); y: pass rate with paired CIs; adherence panel if validated | E-T2 | 3 |
| Figure 6 | Attribution by dimension group | x: arm (each reverted group, lessons/notes-off); y: paired difference from S\*1 with CI | E-ATTR | 3 |
| Figure 7 (F7) | Adaptation efficiency | Left: CER_test per method with censored CIs; right: payback curve, x: number of tasks T, y: cumulative MCU saved minus adaptation MCU, T\* marked | E11 | 4 |
| Figure 8 (F8) | Strategy switching: cross-fitted VBS/SBS, selector regret and cost | Bars: CF-SBS, each selector, CF-VBS pass rate with CIs; second axis or table: mean MCU per task including selector cost | E4-SW | 5, 1 |

### 6.3 Appendix figures

| Id | What it shows | Axes | Source experiment | Meeting point |
|---|---|---|---|---|
| Figure A1 | TB-Pro pre-screen difficulty and the contested histogram | x: successes out of k per task; y: number of tasks | E0 | 2 |
| Figure A2 | BoN pass@N with the judge selector against the oracle | x: N; y: pass rate; judge solid, oracle dashed | E3-BoN, E0-JUDGE | 1 |
| Figure A3 | Failure mix across rounds | x: round; y: share of failures by taxonomy class | E-T12 | 3 |
| Figure A4 | Net pass@k of S\* minus S0 | x: k (1 to 5 per seed); y: net difference with CI | E-N1 | 3 |
| Figure A5 | Amortised CER(T) and Δp / C(T) | x: T; y: index value with CI | E11 | 4 |

---

## 7. Appendices

| Id | Contents | Source experiment | Meeting point |
|---|---|---|---|
| A1 | **Per-task table:** 89 rows, one per TB2 task, with category, difficulty, pass/fail counts per arm, routing column (selected version per selector) and leak flags. Plus the TB-Pro routing table (task id, source, pool, group, image digest, drop or dedup reason) | E3, P-M2, E4-SW, E3-AUDIT | 2 |
| A2 | Phase-0 calibration: TB-Pro pass rate with CI, C3 and C5, infrastructure error rate, throughput by configuration, rho, model-choice table (AA-style composite column; a named result only under reading (b) of point 4) | E-P0, E0, E0-FB if any | 6, 4 |
| A3 | Reproducibility: `pins.lock`, hardware table, KV cache and context pins, per-arm timeout rates, TB-Pro allowlist fork diff and per-task host lists | E-P0, P-M2 | 6 |
| A4 | MCU fit: a, b, k_occ, per-arm residuals with CIs, the validation gate result and any unit switch | E-P0, E0, E1, E2 | 1 |
| A5 | Power and size simulations, selection-rule simulation (expected gain, chance of a worse-than-S0 choice, null acceptances), CRN rho, the probability of reaching and rejecting H4, and the per-test partial-credit screening check if TB-Pro writes per-test results | E0-SIM, E0-SIM2, E0-AA, E-N2 | 3 |
| A6 | Baseline details: judge AUROC on TB-Pro, sampling record, B1 cap mixture and timeout rate | E0-JUDGE, E1, E3-B1 | 1 |
| A7 | Leakage controls: dedup removal list, lint false-positive rate, TB2 flag rates per arm, memorisation probe, held-out ledger hash, and the lessons/notes-off row (S\*1 with lessons and free-text notes removed) | P-M2, LINT-PILOT, E3-AUDIT, E0-MEM, LEDGER, E-ATTR | 2 |
| A8 | Cross-fitted oracle quantities (VBS − SBS, headroom), with the naive same-run values labelled "biased; for illustration" | E4-SW | 5 |
| A9 | Efficiency index variants: amortised CER(T), Δp / C(T), pass per MCU, Kendall's tau between method rankings | E11 | 4 |
| A10 | Expressiveness audit: each published edit of Self-Harness (4 retained edits), AHE and MemoHarness mapped to a field, or "not expressible" | E-N4 | 3 |
| A11 | Failure taxonomy, diagnoser agreement (Cohen's kappa) on 40 to 60 hand-labelled TB-Pro trajectories | E-T12 | 3 |
| A12 | Edit log: every candidate with strategy hash, edits, V_pro outcomes and MCU, labelled screening data | E2 | 3 |
| A13 | Budget: planned against realised episodes and GPU-days, cuts applied, Tier C admissions | All | 6 |
| A14 | Deviations from the pre-registration, from [DECISIONS.md](DECISIONS.md), including any defaults applied for open questions | PREREG-1, PREREG-2 | all |
| A15 | E-INTERP table (if B5 runs) and the B5 sandbox design | E-B5 | 3 |
| A16 | AppWorld re-entry, only if point 4 is read as (b) with our method scored across benchmarks (Q1 in [DECISIONS.md](DECISIONS.md)): S0 against S\* on AppWorld test-normal at k=1, descriptive. Absent otherwise | E8 re-entry | 4 |

---

## 8. Pre-registration plan

Two stages. Each is a signed git tag in this repository, archived on Zenodo with a DOI, plus an OSF registration that quotes the tag SHA and the DOI. OSF text is drawn only from this public repository. Changes after a tag are amendments, logged with a reason and listed in Appendix A14.

### 8.1 Stage 1: before the first E2 adaptation episode

| Item | Contents |
|---|---|
| Pins | `pins.lock`: model file sha256, llama.cpp commit and flags, GPU and driver, Harbor tag and commit, task commits, image digests, slot count, KV cache type, per-slot context, reasoning budget, sampling, MCU coefficients a and b, k_occ |
| Pools | Final TB-Pro lists for the dev slice, A_pro, the 50-task diagnosis sample (seed 20261015), V_pro and V2_pro, with sibling groups. The held-out set (TB2-89, or H52 under E-RESPLIT) |
| Selection rule | R = 6, K = 4, at most 2 edit operations, the +1 net-task threshold as integer counts, tie rules, the V2_pro choice, the cap formula, and the cost-aware tie-break only if the simulation admitted it |
| Edit space | Allowed fields and values; the unit tests that exclude rollback values and `switch_to`; the lint rules |
| Mechanism | G1 sign-off: Table 2 with every field's status and test id; the adherence rule for text-only fields |
| Hypotheses and tests | H1 to H4 and their order; primary test (paired t, or sign-flip if E0-SIM triggered the switch); sensitivity analyses; the MDE re-stated from the E0 fit; the seed branch (two seeds by default, or single-seed if cut 5 was applied) |
| Exploratory analyses | E-T2 estimands and the Holm family; the E-ATTR 40-task set (from public third-party data) and arm rule; E-N1, E-T12 definitions |
| Index | The headline label of E11: the answer to point 4, or the default (CER_test with T\*); Chollet-weighted weights, if any variant is to be computed |
| Switching | Whether E4b runs (only if point 5 is answered (b) or (c)), with its gate, retry_on and max_retries for the arm |
| Optional arms | E-INTERP table if B5 may run; the Tier C order |
| Budget | Core, contingency and absolute caps; cuts 4 and 5 decided |
| Ledger | Hash of the held-out access ledger to date |

### 8.2 Stage 2: before the first TB2 agent episode

| Item | Contents |
|---|---|
| Strategies | Final hashes of S\*1, S\*2, B4-final, and B5-final if run |
| Matching | B1 attempt-cap mixture and its seeded draw (sum of caps ≤ 1,024 at ×5, or 614 at ×3); BoN q and N\* rule from TB-Pro V2_pro runs |
| Cost unit | MCU validation-gate results per arm, and the unit used (MCU or processed tokens) |
| Selectors | The rule table, the TB2-to-TB-Pro category map, and the LLM selector prompt, frozen by commit hash |
| Judge | E0-JUDGE AUROC and the primary BoN selector it implies; judge prompt and temperature |
| Adherence | Validation result of the instrumentation on TB-Pro E0 logs (kept or dropped) |
| Run plan | Arms, runs per task and seeds for E3, E-ATTR, E-T2, E-PORT, E4b if admitted, Tier C items admitted at G0; E-PORT host; any TB2 memorisation probe |
| Leak audit | Search strings and the flag rule |
| Ledger | Ledger hash; confirmation that TB2 contact so far is image pulls by digest only |

---

## 9. Candidate venues

Deadlines were checked on 2026-10-20 on the official site of each venue. "Unverified" means the official call was not yet posted, so no date is given as fact.

### 9.1 Timeline (estimate)

The dated plan is in [EXECUTION_PLAN.md](EXECUTION_PLAN.md). Owner hours, not the GPU, set the critical path. Before the Stage-1 tag the plan needs about 392 owner-hours, 213 of them before the first GPU episode. After the final run it needs about 80 more. The core also needs about 45 GPU-days (9,653 episodes at the planning rate of 213.5 episodes per GPU-day, a laptop-measured proxy). At 20 hours per week this comes to about 31 weeks, from 2026-10-19 to a draft for Prof. Abdelrazek in the week of 2027-05-17. All figures are estimates.

The start date and the weekly hours are still open (plan item 1 in [DECISIONS.md](DECISIONS.md)); the dates below assume a start on 2026-10-19 and 20 hours per week. No GPU has been granted yet (Q5).

| Milestone | Week | Dates (estimate) | Note |
|---|---|---|---|
| Start | W1 | 2026-10-19 | Assumed |
| GPU host available | W7 | from 2026-11-30 | Assumption, not granted (Q5). The end date holds if it arrives by about W13 (2027-01-11); each later week moves every later date by one |
| G-INFRA closed (harness bring-up, 5-task smoke run) | W11 | 2026-12-28 to 2027-01-03 | |
| First GPU episode | W12 | week of 2027-01-04 | Phase 0 starts |
| G0 (Phase-0 calibration) | W13 | 2027-01-11 to 2027-01-17 | |
| G1 and Stage-1 tag | W20 | 2027-03-01 to 2027-03-07 | Deadline for the answers to Q1 to Q4 and Q8 |
| End of E2 (adaptation on TB-Pro) | W23 | about 2027-03-27 | |
| Stage-2 tag, final run starts | W24 | 2027-03-29 to 2027-04-04 | |
| End of E3 | W26 | about 2027-04-16 | |
| Final run complete (E-T2, E-ATTR, E-PORT) | W27 | about 2027-04-23 | Q5 asks for GPU-days "before the analysis deadline". In this schedule that is the end of W27 (2027-04-25); it is not yet agreed |
| Draft paper to Prof. Abdelrazek | W31 | 2027-05-17 to 2027-05-23 | |
| NeurIPS 2027 paper deadline | about W30 | mid-May 2027 | Unverified (third-party trackers) |
| End of internship | not set | not set | Plan item 1 in [DECISIONS.md](DECISIONS.md) |

**What this means for the venue.** Confirmatory results arrive in late April 2027 at the earliest. At 20 hours per week the draft reaches Prof. Abdelrazek in the week of 2027-05-17, at or after the expected NeurIPS 2027 deadline, with no slack and no time for his review. So NeurIPS 2027 is missed at 20 hours per week. It stays possible only if owner hours rise to about 28 per week (the 24-week plan, with the draft in about W24, the week of 2027-03-29) or scope is cut with the cut order in [EXECUTION_PLAN.md](EXECUTION_PLAN.md). Otherwise the fallback is TMLR, which has no deadline, or a later venue such as ICLR 2028.

### 9.2 Venues

| Venue | Deadline | Status of the date | Fit |
|---|---|---|---|
| NeurIPS 2027 | Not posted on [neurips.cc](https://neurips.cc) | Unverified. Third-party trackers expect mid-May 2027 | Good topical fit, but missed at 20 hours per week (draft in the week of 2027-05-17, section 9.1). A target only if hours rise to about 28 per week or scope is cut. To discuss with Prof. Abdelrazek |
| ICML 2027 | Not posted on [icml.cc](https://icml.cc) | Unverified. Third-party trackers expect late January 2027 | Probably too early for results from the final run |
| COLM 2027 | Not posted; [colm.cc](https://colm.cc/) still shows COLM 2026 | Unverified | Good topical fit (language agents) if the date falls after the final run |
| IJCAI 2027 | Not posted | Unverified. Third-party trackers expect mid-January 2027 | Probably too early |
| ACL 2027 via ACL Rolling Review (ARR) | "January, 2027" final ARR submission date, no exact day ([ARR dates](https://aclrollingreview.org/dates)) | Partly verified (month only) | Probably too early |
| TMLR (Transactions on Machine Learning Research) | Rolling submission ([TMLR](https://jmlr.org/tmlr/)) | Verified | Fallback at 20 hours per week. Suits a pre-registered result in either direction; no deadline risk |
| ICLR 2028 main track | Not posted | Unverified. ICLR 2027's paper deadline was 25 Sep 2026, so late September 2027 is likely, but this is an inference | First large conference after the 20-hours-per-week draft |
| ICLR 2027 workshops | Workshops 29 to 30 April 2027 ([ICLR 2027 dates](https://www.iclr.cc/Conferences/2027/Dates)); paper deadlines not posted | Workshop dates verified; paper deadlines unverified | Possible venue for the design and Phase-0 results only |
| ICLR 2027 main track | Abstract 18 Sep 2026, paper 25 Sep 2026, AoE ([call](https://www.iclr.cc/Conferences/2027/CallForPapers)) | Verified, passed | Not possible |
| AAMAS 2027 main track | Abstract 1 Oct 2026, paper 8 Oct 2026, AoE; conference 3 to 7 May 2027 ([call](https://warwick.ac.uk/fac/sci/dcs/aamas2027/calls/call-for-main-track/)) | Verified, passed | Not possible |
| ARR October 2026 cycle | 12 Oct 2026 ([ARR dates](https://aclrollingreview.org/dates)) | Verified, passed | Not possible |

Venue choice is not decided. The dates marked unverified are re-checked when each official call appears, and this table is updated.

---

## 10. Paper 2 outline

Paper 2 takes the items that paper 1 cannot power on one GPU, or that need new infrastructure. Its scope is **to confirm with Prof. Abdelrazek** (Q4). The default is that internship objectives 4 (second-order loop) and 6 (second-benchmark transfer) become paper-2 objectives.

| Item | Question | Why it is not in paper 1 | Design sketch |
|---|---|---|---|
| RQ3, second-order loop (E5) | Does revising the adaptation mechanism (taxonomy, diagnosis and proposal prompts, selection rule) make improvement faster or larger? | The loop is the unit of replication. Detecting a 50% relative change needs about 27 to 32 loops per arm: 73,710 to 87,360 episodes, 345 to 409 GPU-days (estimate) | Loop-level replication, an independent meta-training pool, M0 against meta-learned M\* against a random-edit control of M. Hyperagents' imp@k metric (its measure of meta-level improvement, computed with the meta agent held fixed) is a candidate measure. If Prof. Abdelrazek says the second-order loop is essential for the internship, the options are a descriptive single-loop demonstration on TB-Pro only (E5-DEMO, at most 1,365 episodes, no inferential claim) or more GPU-days |
| Transfer to a second family (E8) | Does S\*, learned on terminal tasks, help on AppWorld (a benchmark of agent tasks in simulated everyday apps; test-normal is its standard test split)? Does the mechanism transfer? | About 2,500 episodes (about 11.7 GPU-days at the TB2 rate, a proxy). The Harbor main repository had no AppWorld adapter on 2026-10-20 | Strategy transfer on AppWorld test-normal, then mechanism transfer split by scenario. Cross-model transfer (T3) and a model-by-dimension sensitivity map (T14) also go here. A minimal paper-1 re-entry (S0 against S\* on AppWorld test-normal at k=1) exists only if point 4 is read as (b) with our method scored across benchmarks. Its slot is Appendix A16 |
| Rollback against restart (E9) | Does returning to a checkpoint beat restarting the task? | Harbor offers no snapshot or restore, so rollback would be files-only and could be confused with incomplete state restoration | Needs a state snapshot and restore that Harbor does not offer today; design to be defined. Rollback values return to the edit space only then |
| Mid-task switching (E4b) | Does switching to another strategy version when recovery is exhausted help? | Default if point 5 is read as per-task choice, or not answered | The flag-gated `switch_to` value of `recovery.on_repeated_failure`; also the probe-then-choose selector |
| Model ladder (E10) | How does the gain from adaptation change with model size? | One full rung with its own adaptation run costs about 2,255 episodes (10.56 GPU-days, estimate) | The TMax family of open models from AllenAI (4B, 9B, 27B), same hybrid architecture. Nemotron-Terminal is dropped from the ladder |
| Capability assessment (T7) | A possible follow-up on capability assessment of strategy versions (paper 2) | Not in the paper-1 scope | To be defined |
| Diagnosis-noise injection (T6) | Does diagnosis quality cause the gain? | Needs a full adaptation run per noise level and loop-level replication | First paper-2 experiment if the paper-1 S\* − B4 CI includes 0 |
| Others | Free-form code baseline B5 if not run in paper 1; a "give up" field | Budget or new schema field | As in [EXPERIMENTS.md](EXPERIMENTS.md), "Moved to paper 2" |

---

## 11. Where the six meeting points are answered

Paper sections use the paper's own numbering (section 5 of this file plans paper section n under 5.n).

| Point | Note as recorded | Paper section | Experiments | Figures and tables | Status |
|---|---|---|---|---|---|
| 1 | "baseline cost : task" | 5 Results; 6.4 for switching cost | E3-COST, E-N3, E3-BoN, E3-B1, E4-SW | Table 4 (cost per task, every arm, both rates, split by outcome and S0 class); Figure 3; Figure A2; Appendix A4 and A6 | Planned, never cut |
| 2 | "benchmark : task" | 4 Experimental setup; 5 Results | P-M2, E3, E3-REF, E3-AUDIT, LEDGER | Appendix A1 (89-row per-task table and routing table); Table 7; Table 3; Appendix A7 | Planned, never cut. Replacing the committed split is **to confirm with Prof. Abdelrazek** (Q3) |
| 3 | "strategy adapt" | 3 Method; 5 Results; 6.1 and 6.2 Analysis | G1, E-N4, E2, E3, E-T2, E-ATTR | C1 to C4; Tables 2, 3, 5; Figures 2, 4, 5, 6 | Planned |
| 4 | "intelligence index" | 6.3 Adaptation efficiency | E11; under reading (b), the E0 model-choice table and, if asked, the E8 re-entry | Figure 7 and Appendix A9 under reading (a); the model-choice table in Appendix A2, and Appendix A16 if run, under reading (b) | Reading **to confirm with Prof. Abdelrazek** (Q1); default reading (a), CER_test with T\* |
| 5 | "strategy switching" | 6.4 Strategy switching | E4-SW; E4b only if admitted | Figure 8 and Appendix A8 (per-task choice, in paper 1 under every answer); E4b row in Table 3 only if mid-task switching is asked for | Reading **to confirm with Prof. Abdelrazek** (Q2); default per-task choice only |
| 6 | "small models on terminal bench, coz everyone can run small models on local machine" | 4 Experimental setup (model and serving); 5 Results (Table 6) | E-P0, E0, E-PORT, E-T1lite if admitted | Table 6; Table 7; Appendix A2, A3, A13 | Partly answered. Every run uses a small open-weight model served locally (35B total, 3B active, MoE), but the main runs need a 24 GB-class GPU. E-PORT shows only that inference with S0 runs in an 8 GB-VRAM configuration (emulated on the main GPU by default) and what S0 scores there. Adaptation on consumer hardware is not shown. The GPU-days and a consumer-class machine are **to confirm with Prof. Abdelrazek** (Q5) |
