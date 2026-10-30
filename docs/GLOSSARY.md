# Glossary

Sagandeep Kaur, October 2026. Status as of 2026-10-20.

This glossary explains the research-methodology, statistics, cost and systems terms used in the Project 2 documents. It is written for a reader who knows machine learning engineering well but is new to experimental design.

**How to read an entry.** Each term has four parts:

- **Definition.** One to three sentences.
- **Example.** A worked example with this project's numbers.
- **Common mistake.** One error that is easy to make.
- **Used in.** The documents and sections where the term matters.

**Where the numbers come from.** No experiment has been run and no model has been called. Every number below comes from one of four places:

- the committed repository (split file, task list, code);
- public third-party data, mainly the little-coder run of Qwen3.6-35B-A3B on Terminal-Bench 2.0, whose 445 trial records are on Hugging Face;
- published papers, cited by arXiv id;
- simulations and arithmetic from the 2026-10 design review ([DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md)).

Planned values are labelled *planned*. Illustrative numbers are labelled *illustrative*. Decisions that wait for Prof. Abdelrazek are marked with their question id in [DECISIONS.md](DECISIONS.md), with the default that applies if there is no answer. Experiment ids (E0, E3, E-ATTR and so on) refer to the cards in [EXPERIMENTS.md](EXPERIMENTS.md). Motion ids (M1 to M16) refer to the blocks in [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md).

---

## Contents

| Group | Terms |
|---|---|
| [Notation](#notation) | Arms, pools, runs, units, and symbols that have more than one meaning |
| [Evaluation](#evaluation) | Episode and trial; pass@k vs per-run success; best-of-N; oracle pass@N; contested task and floor effect; held-out set; selection vs test; stratified seeded split; sibling tasks; contamination; canary string; pre-registration; gatekeeping |
| [Statistics](#statistics) | Estimand; paired design; paired t-test; permutation test; task-level bootstrap; why not McNemar here; power; minimum detectable effect; intra-task correlation; multiple comparisons; winner's curse; common random numbers; cross-fitting; Cohen's kappa; size of a test; family-wise error rate; one-sided vs two-sided interval; beta-binomial model; logit scale; effect heterogeneity vs task heterogeneity; null acceptance and harm rate; Wilson interval; censoring; Kendall's tau; AUROC; GLMM |
| [Attribution](#attribution) | Ablation; leave-one-out; add-one; interaction; Shapley value |
| [Methods](#methods) | First-order vs second-order adaptation; hybrid selection rule; Reflexion; GEPA; ACE; harness self-evolution; failure taxonomy; typed strategy; compile() vs render(); compiled vs advised strategy |
| [Loop components](#loop-components) | Diagnoser and diagnosis set; proposer and edit operation; parent, candidate and version; dimension group; lessons vs notes; lint; strategy hash and provenance tag |
| [Cost and metrics](#cost-and-metrics) | Cost per task; model compute units; occupancy cost; compute matching; compute-equivalence ratio; payback; skill-acquisition efficiency; Pareto frontier; VBS and SBS; GPU-day and planning throughput |
| [Budget and protocol](#budget-and-protocol) | Episode-equivalent; core, contingency, floor and absolute cap; Tier C; cut order and single-seed branch; under-matched; realised strategy; gate; Stage-1 freeze and pins.lock; amendment vs deviation; A/A run; E-INTERP; held-out ledger |
| [Systems](#systems) | Mixture of experts and active parameters; Q4_K_M quantisation; KV cache; tokens per second; llama.cpp slots and prompt cache; Harbor; Terminus 2; Terminal-Bench 2.0 vs TB-Pro vs 2.1; egress allowlist; step and token budgets |

---

## Notation

| Symbol | Meaning |
|---|---|
| **S0** | The hand-written fixed strategy. Baseline B0 runs S0 unchanged |
| **S\*** | The strategy produced by adaptation. **S\*1** and **S\*2** come from two independent adaptation runs (seeds). In the confirmatory tests, S\* means the per-task average of S\*1 x5 and S\*2 x5 (the default two-seed branch). In the [single-seed branch](#cut-order-and-single-seed-branch), S\* is S\*1 x10 |
| **S_r, S0 to S6** | The loop's versions: S0 is the start, S_r the parent in round r, and S1 to S6 the versions after rounds 1 to 6 (see [parent, candidate and version](#parent-candidate-and-version)) |
| **B1** | In-episode reflection-retry (Reflexion-style) |
| **BoN** (was B2) | Best-of-N, computed from a pool of S0 runs |
| **B4** | Random strategy search: same budget, edit space and selection rule as S\*, but edits are sampled at random instead of proposed from diagnoses |
| **B5** | Free-form edits of the controller code. Optional (Tier C), run only if its sandbox gates pass |
| **TB2-89** | The 89 tasks of Terminal-Bench 2.0 (TB2) at task commit `2fd12b8` |
| **TB-Pro** | terminal-bench-pro, a separate pool of 200 public terminal tasks, planned as the adaptation source |
| **Pools** | On TB-Pro: a 15-task **dev slice** (debugging only), **A_pro** (adaptation; each round diagnoses a fixed 50-task sample of it, **A_diag**), **V_pro** (at most 25 contested tasks, for screening edits) and **V2_pro** (at most 15 contested tasks, for the final choice of version) |
| **A, V, M, H** | The committed TB2 split: adaptation 25, selection 12, meta-training 15 and held-out 37 tasks. **H37** is that held-out set and **H52** the held-out set of the fallback re-split. Both are task sets, not hypotheses |
| **C3, C5** | Contested TB-Pro tasks after S0 x3, and after a top-up to x5 |
| **K, R** | K = 4 candidate edits per round; R = 6 rounds per loop |
| **N, N\*, P, q** | Best-of-N: N samples per task; N\* the compute-matched N; P = 10 the S0 pool size; q the fractional part of N\* (see [compute matching](#compute-matching)) |
| **p\*, c_test\*, c_eq, A\*, T\*** | S\*'s pass rate and test-time cost per task, the equal-pass-rate BoN cost, the adaptation cost and the payback (see [compute-equivalence ratio](#compute-equivalence-ratio) and [payback](#payback)) |
| **rho** | Correlation between paired runs that share a seed (see [common random numbers](#common-random-numbers)) |
| **tau^2** | Between-task variance of the effect (see [effect heterogeneity](#effect-heterogeneity-vs-task-heterogeneity)). Kendall's tau is unrelated |
| **D_rem** | Dedicated GPU-days left before the analysis deadline, measured at G0 |
| **pp** | Percentage points |
| **Stage 1, Stage 2** | The two pre-registration tags (see [pre-registration](#pre-registration)) |

**Symbols with more than one meaning.** Several letters are reused across the documents. The context decides which is meant; this table lists every reading.

| Symbol | Readings |
|---|---|
| **k** | (1) Runs per task per arm, the usual meaning, as in "TB2-89 x5" or "k=5". (2) The k in pass@k, the number of runs pass@k is computed over. (3) k_screen and k_V2: runs per task on V_pro and V2_pro (1 and 3 by default). (4) k_occ: the occupancy factor, a ratio, not a run count (see [occupancy cost](#occupancy-cost)). (5) `lessons_k`: how many lessons a run retrieves, 0 to 5 (see [lessons vs notes](#lessons-vs-notes)). (6) "MoE layers offloaded 0 to k" in E-P0: an upper limit on offloaded layers. Capital **K** is the number of candidates per round |
| **C** | (1) The contested count that sizes the pools, as in V_pro = round(0.6 x C): this is C3 if C3 >= 40, otherwise C5. (2) The G0 capacity, C = 0.9 x r x D_rem, in episodes (see [gate](#gate)). (3) The extra cost of S\* over a baseline in the old index Δp / C. This glossary writes them as *contested count*, *G0 capacity* and *cost difference* |
| **H1** | (1) In E3, the first of the four confirmatory hypotheses H1 to H4: H1 S\* vs S0; H2 S\* vs B4; H3 S\* vs B1; H4 S\* vs pooled BoN (see [gatekeeping](#gatekeeping)). (2) In every other experiment card, just "the alternative hypothesis", with H0 the null. (3) The H in H37 and H52 names a held-out task set, not a hypothesis |
| **T** | (1) In E11, the number of held-out tasks (89, or 52 under the fallback re-split), and T\* the payback in tasks. (2) Thread ids from the design review, such as T2 (enforced vs advised) or T12 (failure-taxonomy shift). (3) The treatment arm in p_T - p_B (see [estimand](#estimand)) |
| **M** | (1) M1 to M16: the motions of the design review. (2) M, or M15, the committed split's 15-task meta-training part; motion M15 is unrelated. (3) M0 and M\*: the original and the meta-edited adaptation mechanism in E5-DEMO. MCU and MDE are separate acronyms |
| **a, b** | (1) The MCU coefficients, MCU = a x prompt_n + b x predicted_n. (2) The parameters of the Beta(a, b) fit to task pass rates (see [beta-binomial model](#beta-binomial-model)) |
| **r** | (1) The measured rate, in episodes per GPU-day, at G0. (2) The round index in S_r |

---

## Evaluation

### Episode and trial

**Definition.** An *episode* is one run of one agent configuration on one task, ending in one pass/fail grade. Harbor, the harness that runs Terminal-Bench, calls the same thing a *trial*. Budgets in this project are counted in episodes first and in GPU-days second.

**Example.** The planned paper-1 core is 9,653 episodes. One arm on TB2-89 at k=5 is 89 x 5 = 445 episodes. The little-coder reference run was exactly that: 445 trials of Qwen3.6-35B-A3B, 5 per task.

**Common mistake.** Counting only "task attempts" and forgetting extra model calls. An LLM judge or a strategy selector makes model calls that are not episodes. The plan charges them to the arm that makes them, through a separate non-episode call line in the budget.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), cost table; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M16.

### pass@k vs per-run success

**Definition.** *Per-run success* (also pass@1) is the fraction of single runs that pass, averaged over tasks. *pass@k* is the probability that at least one of k independent runs on a task passes, averaged over tasks. From n >= k runs with c successes it is estimated as 1 - C(n-c, k) / C(n, k), the unbiased estimator reported in Evaluating Large Language Models Trained on Code (Chen et al., arXiv 2107.03374, Jul 2021), [link](https://arxiv.org/abs/2107.03374), Section 2.1. Here C(n, k) is the binomial coefficient, not the C of the notation table.

**Example.** In the little-coder run (445 trials, 5 per task), 106 trials passed. Per-run success is 106/445 = 23.8%. The unbiased estimator gives pass@2 = 31.7% and pass@5 = 39.3% over the 89 tasks.

**Common mistake.** Estimating pass@k as 1 - (1 - p)^k from the overall pass rate p. Chen et al. report that this is biased. A second mistake is to compare one method's pass@5 with another method's pass@1: pass@k grows with k for any method that is not deterministic.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 4.1; [EXPERIMENTS.md](EXPERIMENTS.md), E3-BoN and E-N1 (net pass@k difference S\* minus S0, exploratory).

### Best-of-N

**Definition.** Run the base strategy N times on a task and submit one of the N results, chosen by a *selector* that cannot see the hidden tests. Its quality depends on the selector. Best-of-N (BoN) at equal compute is the key competitor for any adaptation method, because extra samples are the simplest way to spend compute.

**Example.** The planned BoN is *pooled*: S0 runs 10 times per task on TB2-89 (890 episodes, planned), and BoN@N is computed exactly over all subsets of N runs out of 10. The selector is an LLM judge, the same local model, scoring each trajectory once after the trial. The judge is checked on about 600 TB-Pro trajectories with known labels. If its AUROC (area under the receiver operating characteristic curve) is at least 0.6, it is the primary selector; otherwise the primary selector is "agent-written tests passed, ties broken at random". BoN@N is charged N episodes plus N judge calls per task.

**Common mistake.** Treating pooled BoN as free. Reusing the S0 pool costs nothing extra *to the experiment*, but a deployed BoN@N still spends N episodes per task, and the cost table must show that.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), sections 4.1-4.2; [EXPERIMENTS.md](EXPERIMENTS.md), E3-BoN and E0-JUDGE; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M4 and M8.

### Oracle pass@N

**Definition.** Best-of-N with a perfect selector: the task counts as solved if any of the N runs passes the hidden tests. It equals pass@N. It is an upper bound on any real selector, not a method anyone can deploy.

**Example.** For the little-coder run, oracle pass@2 is 31.7% against a per-run rate of 23.8%. So a perfect selector over two samples adds 7.9 pp. The plan shows the oracle curve dashed, as a ceiling, beside the judge-selected BoN curve.

**Common mistake.** Reporting oracle pass@N as "the best-of-N baseline". The hidden tests are not available at test time, so this makes the baseline look stronger and the comparison meaningless.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 4.1 (B2); [EXPERIMENTS.md](EXPERIMENTS.md), E3-BoN.

### Contested task and floor effect

**Definition.** A task is *contested* for a strategy if it passes in some runs but not all. Tasks that never pass or always pass carry almost no information about a difference between two strategies run the same number of times. A *floor effect* is when most tasks are never solved, so the informative set is small.

**Example.** In the little-coder run, 54 of 89 TB2 tasks were never solved in 5 attempts, 28 were contested and 7 always passed. In the committed held-out split H (37 tasks), 22 were never solved, 11 contested and 4 always passed.

On TB-Pro, E0 runs S0 x3 only on surviving tasks outside the 15-task dev slice: at most 185 tasks, and 105 at the planning floor of 120 survivors. If TB-Pro's difficulty resembles TB2's (unverified), about 22.6% of tasks are contested at k=3. The expected C3 is then about 24 of 105 at the floor and about 42 of 185 at the maximum (derived). So the C3 >= 40 supply check is expected to fail at the floor and to be close at the maximum. A failed check triggers a top-up of the non-contested tasks to x5. At k=5 a task is contested with probability 0.308, so the expected C5 at the floor is about 32. E0 is capped at 600 episodes, which is above the largest possible E0 of 185 x 3 = 555, so the cap never binds; the cost table charges the full 600.

**Common mistake.** Sizing an evaluation by its total task count. Thirty-seven held-out tasks sound like a lot, but only about 11 of them can move under a small change.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E0 (supply check); [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M2 and M15.

### Held-out set

**Definition.** Tasks used only once, for the final pre-registered evaluation. Nothing that is tuned (prompts, parsers, strategies, thresholds) may be chosen using them. In code, access is guarded and logged.

**Example.** The committed split holds out H = 37 tasks. The review proposes holding out all 89 TB2 tasks and adapting on deduplicated TB-Pro instead, because H37 has only 11 contested tasks and all 9 known sibling pairs straddle it. This needs the professor's approval (DECISIONS.md, Q3; default: approve). If the TB-Pro route fails its pilot, the fallback is a sibling-grouped re-split of TB2 with a 52-task held-out set (H52). The planned guard replaces the boolean `final_evaluation` flag (`evaluation/runner.py`) with an append-only ledger keyed on the held-out task ids. Before Stage 2, the only allowed contact with TB2 is pulling images by digest.

**Common mistake.** "Just one look" during debugging. Running a prompt fix on a held-out task, even once, makes every later choice partly selected on the test set.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 7.1; [EXPERIMENTS.md](EXPERIMENTS.md), P-M2, E3 and LEDGER; [DECISIONS.md](DECISIONS.md), Q3.

### Selection vs test

**Definition.** A *selection* set is used to choose between candidates (edits, strategy versions, thresholds). A *test* set is used once to estimate how good the final choice is. A score measured on the selection set is biased upward, because the winner was chosen for scoring well there.

**Example.** In the planned loop, each candidate edit is screened once on V_pro (at most 25 contested TB-Pro tasks). After 6 rounds, all 7 versions run 3 times on V2_pro (at most 15 tasks), and the best becomes S\*. Only TB2-89 then tests S\*. Because TB2 is never used for selection, noise in the V_pro screen biases the recorded edit deltas but not the final held-out comparison.

**Common mistake.** Reporting the chosen version's V2_pro score as its gain. See [winner's curse](#winners-curse).

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 5.1; [EXPERIMENTS.md](EXPERIMENTS.md), E2; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M9.

### Stratified seeded split

**Definition.** Tasks are assigned to splits at random with a fixed seed, separately within each stratum (here category x difficulty), so every split has a similar mix. The split file is committed before any agent run, so it cannot depend on results.

**Example.** `splits/terminal-bench-2.0.json` uses seed 20261015 and sizes A = 25, V = 12, M = 15, H = 37, stratified by category and difficulty. TB2 has 16 categories, 5 of them with a single task (for example `games` and `video-processing`), so small categories cannot appear in every split. Difficulty counts are easy 4, medium 55, hard 30.

**Common mistake.** Assuming stratification also prevents leakage. It balances the mix but ignores near-duplicate tasks. Grouping is a separate step (see [sibling tasks](#sibling-tasks)).

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 7.1; [PHASE0_CHECKLIST.md](PHASE0_CHECKLIST.md); `evaluation/splits.py`.

### Sibling tasks

**Definition.** Two tasks that ask for the same artefact, algorithm or tool chain, so that solving one teaches the other. If siblings fall on both sides of the adaptation/test boundary, a strategy can carry task-specific knowledge across it.

**Example.** The review found that all 9 sibling pairs it listed straddle H in the committed split: 5 partners are in A, 3 in M and 1 in V. `evaluation/splits.py` already supports a per-task `group`, so grouped tasks land in the same split. For the TB-Pro route, every TB-Pro and TB2 instruction is embedded with one pinned model, the owner reviews the 3 nearest TB2 tasks for each TB-Pro task, and same-artefact tasks are removed with a one-line reason. For example, TB-Pro `implement-tensor-parallel-matmul` and TB2 `torch-tensor-parallelism` cover the same topic with different specifications.

**Common mistake.** Deduplicating only exact copies. Most leakage comes from related tasks with different wording.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), P-M2 and E-RESPLIT; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M2 and M10.

### Contamination

**Definition.** The agent's score is inflated because it has seen the test material: in the model's training data, through internet access during the run, or through text the adaptation loop wrote into the strategy.

**Example.** TB2 is public. All 89 tasks set `allow_internet = true` and ship a public `solution/` directory. The plan has four controls. (1) Every note and lesson passes a lint that rejects task ids, URLs, commands over 40 characters and task file paths. (2) TB-Pro runs use an egress allowlist. (3) TB2 runs keep the upstream network setting, with per-trial DNS and SNI (Server Name Indication) logs and a grep for the canary and benchmark domains; flagged trials count as failures. (4) A memorisation probe runs on 20 TB-Pro tasks. TB-Pro and Qwen share Alibaba provenance, so the probe result is reported.

**Common mistake.** Arguing that contamination "affects all methods equally". A self-adapting loop is exactly the method that could learn to fetch or memorise solutions, so it is not equal.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 7.5; [EXPERIMENTS.md](EXPERIMENTS.md), E3-AUDIT, E-NET and E0-MEM; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M10.

### Canary string

**Definition.** A unique marker string placed in benchmark files so that model developers can filter them from training data, and so that leaks can be detected later. It is a request, not a protection.

**Example.** TB2 relies on a canary string only and has no private test set. The planned TB2 audit greps every command and observation for the canary GUID and for `terminal-bench`, `tbench`, `harborframework`, `laude-institute`, `terminal-bench-pro` and `solution/`.

**Common mistake.** Treating "has a canary" as "uncontaminated". The canary only helps if training pipelines honour it, which cannot be checked from outside.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 7.5; [EXPERIMENTS.md](EXPERIMENTS.md), E3-AUDIT.

### Pre-registration

**Definition.** Writing down the hypotheses, primary analysis, thresholds and stopping rules before seeing the data that test them, in a form that cannot be edited afterwards. It separates confirmatory claims from exploration.

**Example.** The plan has two stages. Stage 1 comes before the first adaptation episode (E2). Stage 2 comes before the first TB2 agent episode. Each stage is a signed git tag that freezes `pins.lock` (model file hash, llama.cpp commit and flags, Harbor version, image digests, sampling, cost coefficients), the analysis code, thresholds, pool lists and budget caps. The tag is archived on Zenodo with a DOI (Digital Object Identifier), and an OSF (Open Science Framework) registration quotes the tag SHA and DOI.

**Common mistake.** Pre-registering only the hypothesis and leaving the test, the runs per task or the exclusion rules open. Those choices are where most flexibility hides.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), PREREG-1 and PREREG-2; [PAPER_PLAN.md](PAPER_PLAN.md), pre-registration plan; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M3.

### Gatekeeping

**Definition.** A fixed-sequence testing procedure: hypotheses are tested in a pre-set order, each at the full alpha, and testing stops at the first one that is not rejected. It controls the [family-wise error rate](#family-wise-error-rate) without splitting alpha, as long as the order is fixed in advance.

**Example.** The planned order, each two-sided at alpha 0.05: H1 S\* vs S0; H2 S\* vs B4; H3 S\* vs B1 at matched compute; H4 S\* vs pooled BoN at matched compute. If H2 is not rejected, H3 and H4 are reported as estimates with 95% confidence intervals (CIs), not as tests. "Beats" is written only for a rejected hypothesis whose CI excludes 0.

**Common mistake.** Changing the order after seeing results, or continuing past a failed step "because the next one is significant". Either breaks the error control.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E3; [PAPER_PLAN.md](PAPER_PLAN.md), contributions; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M3.

---

## Statistics

### Estimand

**Definition.** The exact quantity an analysis is meant to estimate, stated before choosing a test. Different tests on the same data can target different estimands.

**Example.** The paper-1 estimand is the equal-weight mean, over the 89 TB2 tasks, of the per-task pass-rate difference p_T - p_B, in pp. A mixed-effects logistic model would instead estimate an effect on the log-odds scale for a typical task, which is a different number.

**Common mistake.** Pooling all runs as if they were independent coin flips. That weights tasks by their run count and treats runs on the same task as unrelated.

**Used in.** [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M3; [EXPERIMENTS.md](EXPERIMENTS.md), E3.

### Paired design

**Definition.** Every arm runs on the same tasks, and the comparison is made task by task. Differences between tasks (some are easy, most are hard) then cancel out of the comparison.

**Example.** TB2 tasks differ far more from each other than runs of one task do: a beta-binomial fit to the little-coder counts gives an intra-task correlation of 0.575. Pairing on tasks removes that between-task variance from the S\* vs S0 contrast.

**Common mistake.** Comparing two arms evaluated on different task sets, or on the same tasks but analysed as two independent samples. Both throw away the main source of power.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 7.2; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M3.

### Paired t-test

**Definition.** A one-sample t-test on the per-task differences d_i = mean(arm T runs on task i) - mean(arm B runs on task i). The unit of analysis is the task, so n = 89.

**Example.** This is the planned primary test for H1-H4. In the review's simulations it held its nominal 5% [size](#size-of-a-test) in the null-like cells tested (4.3-5.8%), but no null was simulated for a floor-heavy profile. So, before Stage 1, its size is simulated twice: with rates fitted to TB-Pro E0 and with the public little-coder TB2 rates. If size exceeds 6% in either, the sign-flip permutation test becomes primary. Sensitivity analyses: the sign-flip test and a GLMM (generalised linear mixed model) `pass ~ arm + (1 + arm | task)`.

**Common mistake.** Running the t-test on all 445 run-level outcomes. That treats 5 runs of one task as 5 independent tasks and overstates precision.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E3 and E0-SIM; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M3.

### Permutation test

**Definition.** A test that builds the null distribution by reshuffling labels the null says are exchangeable. In the paired *sign-flip* version, each task's difference d_i is multiplied by a random +1 or -1, and the observed sum is compared with the reshuffled sums. It assumes symmetry, not normality.

**Example.** The plan uses 100,000 sign flips as a sensitivity analysis. In simulation it was less powerful than the paired t on the same differences: 0.50 vs 0.54 on TB2-89 x5, and 0.59 vs 0.675 on H37 x5. The loss comes from the shifted mean entering the randomisation variance.

**Common mistake.** Believing a permutation test is always the safer choice. Here it costs power, so it is primary only if the t-test fails its size check.

**Used in.** [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M3; [EXPERIMENTS.md](EXPERIMENTS.md), E0-SIM.

### Task-level bootstrap

**Definition.** A confidence interval made by resampling tasks with replacement (keeping all runs of a resampled task together) and recomputing the statistic each time. It matches the paired design and needs no distributional assumption.

**Example.** The plan uses a one-stage task bootstrap with 10,000 resamples for every CI. In simulation at n = 89, k = 5 it reproduced the true sampling SD of the task-averaged difference (0.0207 vs 0.0209). A two-stage bootstrap (tasks, then runs within each task) overstated it by 28% (0.0267), because it counts within-task noise twice.

**Common mistake.** Adding the second stage "to be safe". It gives intervals that are too wide and underpowered tests.

**Used in.** [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M3; [EXPERIMENTS.md](EXPERIMENTS.md), E3, E3-COST and E11.

### Why not McNemar here

**Definition.** McNemar's test compares two classifiers on paired binary outcomes, using only the discordant pairs. It assumes one outcome per item per method. With several runs per task it needs either a majority vote per task or run-level pairs, and both fail here.

**Example.** The plan originally used McNemar per pair with Holm correction (TECHNICAL_PLAN section 7.2). In simulation, McNemar on per-task majority votes has a minimum detectable effect above 16 pp on H37 at every k tested, and 9.7 pp on TB2-89 x5 against 5.8 pp for the task-level t. On H37 x3 at a 12.3 pp effect its power is 0.35 against 0.82. McNemar on (task, run) pairs ignores that tasks differ in their effect: at a nominal 5% it rejected 12.8% of the time on TB2-89 x10 when the population effect was only +0.4 pp. McNemar is dropped.

**Common mistake.** Choosing a test because it is standard for paired binary data, without checking its unit of analysis against the design.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 7.2 (to be amended); [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M3.

### Power

**Definition.** The probability that a test rejects the null when a true effect of a given size exists. Studies are usually designed for 80% power at alpha 0.05.

**Example.** With 37 tasks x 3 runs, the paired t has 80% power only for effects of about 12 pp. The proposed paper-1 design (all 89 TB2 tasks held out, S0 x10, S\* 10 runs) exists mainly to raise power. Power is computed by simulation from the beta-binomial fit to the little-coder per-task counts.

**Common mistake.** Reading a non-significant result as "no effect". With low power, a real 5 pp gain is missed most of the time.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 7.2; [EXPERIMENTS.md](EXPERIMENTS.md), E0-SIM; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M2 and M3.

### Minimum detectable effect

**Definition.** The minimum detectable effect (MDE) is the smallest true effect that the design detects with the stated power (here 80%, two-sided alpha 0.05). It is a property of the design, fixed before any data.

**Example.** Simulated MDEs for the paired t. The effect is a shift on the [logit scale](#logit-scale) that varies from task to task with an SD of 0.5 logit (see [effect heterogeneity](#effect-heterogeneity-vs-task-heterogeneity)), and each MDE is quoted in pp averaged over tasks:

| Design | MDE (pp) |
|---|---|
| H37 x3 | about 12.0 |
| H37 x5 | about 9.5 |
| H37 x10 | about 7.1 |
| TB2-89 x3 | about 7.4 |
| TB2-89 x5 | about 5.8 |
| TB2-89 x10 | about 4.3-4.5 |
| H52 x5 (fallback re-split) | about 7.6 |

The planning MDE for H1 (S\* 10 runs vs S0 x10) is 4.5 pp. It assumes an effect-heterogeneity variance tau^2 = 0.008. The MDEs are restated after E0, but tau^2 stays a stated assumption, because S0-only runs cannot show how an effect varies across tasks.

**Common mistake.** Computing the within-task variance as p(1-p) from 5 runs. That plug-in value is biased low by the factor 4/5 and gives MDEs about 10% too small.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E3 and E0-SIM; [PAPER_PLAN.md](PAPER_PLAN.md), abstract; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M2 and M3.

### Intra-task correlation

**Definition.** The intra-task correlation (ICC) is the share of outcome variance that lies between tasks rather than between runs of one task. A high ICC means extra runs on the same tasks add little information compared with extra tasks.

**Example.** A beta-binomial fit to the little-coder counts (89 tasks x 5) gives Beta(0.170, 0.569), mean 0.230 and ICC = 1/(a + b + 1) = 0.575. On H, the mean unbiased within-task variance is 0.078, against 0.062 for the biased plug-in estimate. This is why 89 tasks x 5 runs (445 episodes, MDE about 5.8 pp) beats 37 tasks x 10 runs (370 episodes, MDE about 7.1 pp): extra tasks buy more than extra runs.

**Common mistake.** Computing a standard error as if all runs were independent. With ICC near 0.6, that understates it badly.

**Used in.** [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M3; [EXPERIMENTS.md](EXPERIMENTS.md), E0-SIM.

### Multiple comparisons

**Definition.** Running many tests raises the chance that at least one is a false positive. Corrections such as Holm's step-down procedure lower the threshold for each test, which raises the MDE.

**Example.** A Holm-style penalty to alpha 0.0125 (four tests) raises the TB2-89 MDE from 5.8 to 7.2 pp at k=5. The fixed sequence in [gatekeeping](#gatekeeping) avoids this penalty for H1-H4. Holm is still used for one exploratory family: S\* minus B5 and the three enforced-vs-advised contrasts.

**Common mistake.** Reporting p-values for every exploratory slice (per category, per dimension) without saying so. The plan reports no p-values in the abstract for exploratory analyses.

**Used in.** [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M3 and M13; [EXPERIMENTS.md](EXPERIMENTS.md), E-T2.

### Winner's curse

**Definition.** When the best of several noisy candidates is chosen, its measured score is biased upward, because selection favours candidates that got lucky. The bias grows with the number of candidates and the noise.

**Example.** The plan's original rule (K = 4 candidates, staged evaluation on the 12 V tasks, accept a gain of at least one task) was simulated with no truly better candidate. It accepted an edit in 52% of rounds, each recording a fake gain of about +13.4 pp. The new hybrid rule is deliberately lenient and accepts about 4.4 edits per 6-round loop even under a pure null. That is a count of edits, not a percentage (see [null acceptance and harm rate](#null-acceptance-and-harm-rate)). So V_pro deltas are screening data only, never effect sizes, and the chosen version's V2_pro score is not a gain estimate.

**Common mistake.** Using the adaptation log's recorded deltas as evidence of which edits helped.

**Used in.** [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M9; [EXPERIMENTS.md](EXPERIMENTS.md), E2 and E-ATTR.

### Common random numbers

**Definition.** Common random numbers (CRN) give two arms the same random draws (here, the same per-request sampling seed for each task and run index), so that part of their noise is shared and cancels in the difference. The gain depends on the correlation rho between paired outcomes.

**Example.** Candidates and their parent share per-(task, run) seeds on V_pro. llama.cpp accepts a per-request seed, but its prompt cache "can cause nondeterministic results". So every calibration assumes rho = 0, and a 60-episode A/A run (S0 against itself on the dev slice) measures rho. In the review's simulations, rho = 0.5 changed null acceptance by only 0.02-0.14.

**Common mistake.** Claiming variance reduction from shared seeds without measuring it. On a served model with batching and caching, identical seeds do not guarantee identical trajectories.

**Used in.** [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M9; [EXPERIMENTS.md](EXPERIMENTS.md), E0-AA.

### Cross-fitting

**Definition.** Splitting the data so that a choice (which version to pick for a task) is made on one half and scored on the other, then swapping the halves and averaging. It removes the bias of choosing and scoring on the same noisy runs.

**Example.** For the per-task oracle in strategy switching, each version's runs are split by run-index parity. The version with the best mean on odd runs is scored on even runs, and vice versa. In simulation, a naive same-run oracle over S0 and S\* shows a +4.5 pp "switching headroom" at k=5 (and +3.4 pp at k=10) even when S\* is identical to S0. Cross-fitting brings it to 0.0 pp. The plan cross-fits every per-task oracle or "newly solved" quantity.

**Common mistake.** Reporting a naive VBS or a count of "tasks unlocked" from the same runs used to pick them.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E4-SW and E-N1; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M3 and M6.

### Cohen's kappa

**Definition.** Agreement between two labellers corrected for chance: kappa = (p_o - p_e) / (1 - p_e), where p_o is observed agreement and p_e is the agreement expected by chance from each labeller's label frequencies. 0 means chance-level agreement and 1 means perfect agreement.

**Example.** The owner hand-labels 40-60 failed TB-Pro trajectories (never TB2) with a failure class. The diagnoser's labels are scored against them with kappa. *Illustrative:* if they agree on 30 of 50 and chance agreement is 0.20, kappa = (0.60 - 0.20) / 0.80 = 0.50.

**Common mistake.** Reporting raw percent agreement. With a few dominant classes, high agreement can be mostly chance.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 6.2; [EXPERIMENTS.md](EXPERIMENTS.md), E-T12; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M14.

### Size of a test

**Definition.** The size of a test is how often it rejects the null hypothesis when the null is true: its type I error rate. A test run at nominal alpha 0.05 should have size 5%. If its assumptions fail, the real size can be higher, and "significant" results then come too easily.

**Example.** Size is checked by simulation: generate many data sets in which the two arms are identical, run the test on each, and count the rejections. In the review's simulations the paired t-test rejected 4.3-5.8% of the time in the null-like cells tested. Before Stage 1 (E0-SIM) this is repeated with rates fitted to TB-Pro E0 and with the public little-coder TB2 rates. If the size exceeds 6% in either, the sign-flip permutation test becomes primary.

**Common mistake.** Confusing size with a p-value or with power. Size is a property of the test under the null, fixed before any data. A p-value comes from one data set. Power is the rejection rate when a real effect exists.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E0-SIM and E3; [EXECUTION_PLAN.md](EXECUTION_PLAN.md), gate G-SEL.

### Family-wise error rate

**Definition.** The family-wise error rate (FWER) is the probability of at least one false rejection in a family of tests. Running several tests, each at alpha 0.05, raises it above 5%.

**Example.** Four independent tests at alpha 0.05 give a FWER of 1 - 0.95^4 = 18.5% (derived). The fixed sequence in [gatekeeping](#gatekeeping) keeps the FWER of H1-H4 at 0.05 without lowering alpha. Holm's procedure controls it for the exploratory family {S\* - B5, Δ1, Δ2, Δ3}. E-ATTR's paired CIs are not adjusted, so each of its arms is read on its own and no family-wide claim is made.

**Common mistake.** Assuming that FWER control on H1-H4 also covers the exploratory analyses. It covers only the family it was designed for.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E3, E-T2 and E-B5; [PAPER_PLAN.md](PAPER_PLAN.md), contributions; [multiple comparisons](#multiple-comparisons).

### One-sided vs two-sided interval

**Definition.** A two-sided 95% CI leaves 2.5% of probability in each tail, so it gives a lower and an upper limit. A one-sided 95% bound puts all 5% in one tail, so it gives only one limit, which is tighter than the same end of the two-sided interval.

**Example.** All confirmatory tests are two-sided: H1 is "S\* ≠ S0", so a loss can be detected as well as a gain. *Illustrative:* 0 timeouts in 30 trials give a one-sided 95% upper bound of 1 - 0.05^(1/30) = 9.5%, but the upper end of a two-sided 95% interval is 1 - 0.025^(1/30) = 11.6% (derived). Against the E-P0 rule "an upper 95% bound ≤ 10%", the choice decides the outcome, so the rule must name which bound it uses.

**Common mistake.** Choosing a one-sided test after seeing which way the data point. The test then rejects at |z| > 1.645 in whichever direction the data fell, so its real size is 10%, not 5%.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E3 and E-P0; [gatekeeping](#gatekeeping).

### Beta-binomial model

**Definition.** A model for per-task success counts. Each task has its own pass probability p, drawn from a Beta(a, b) distribution. Given p, the k runs of the task pass independently with probability p. It captures that tasks differ much more from each other than runs of one task do.

**Example.** The fit to the little-coder counts (89 tasks x 5) is Beta(0.170, 0.569): mean a/(a + b) = 0.230 and ICC 1/(a + b + 1) = 0.575. Both parameters are below 1, so the distribution is U-shaped: most tasks sit near 0 or near 1, as in the 54 never-solved and 7 always-solved tasks. The fit drives the power and MDE simulations, and E0-SIM refits it on TB-Pro.

**Common mistake.** Using a plain binomial with one shared p. With p = 0.238 it predicts that 0.762^5 = 25.7% of tasks, about 23 of 89, fail all 5 runs (derived). The run had 54.

**Used in.** [power](#power); [intra-task correlation](#intra-task-correlation); [EXPERIMENTS.md](EXPERIMENTS.md), E0-SIM; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M3.

### Logit scale

**Definition.** The logit of a probability p is log(p / (1 - p)), the log-odds. In the simulations, effects are additive on this scale: a logit shift δ adds δ to a task's logit. For a task at rate p, a small shift changes the pass rate by about δ x p(1 - p). So it moves mid-range tasks most and tasks near 0 or 1 hardly at all.

**Example.** E2's planning simulation draws edit effects from N(0, 0.3^2) on the logit scale, and the chosen version gains 0.82 logit. For a task at p = 0.5 that is +19.4 pp; for a task at p = 0.05 it is +5.7 pp (derived). Averaged over tasks drawn from the [beta-binomial](#beta-binomial-model) fit, where most tasks sit near 0 or 1, it is about +6.5 pp (derived). The review's simulation, which applies the shift to the 89 TB2 tasks' fitted rates, reports about 6.6 pp. The MDE table works the same way: effects are logit shifts, and MDEs are quoted in pp after averaging over tasks.

**Common mistake.** Converting a logit shift to pp at the overall base rate. At p = 0.23, 0.82 logit is +17.4 pp (derived), almost three times the task-averaged figure, because few tasks sit near the average rate.

**Used in.** [minimum detectable effect](#minimum-detectable-effect); [hybrid selection rule](#hybrid-selection-rule); [EXPERIMENTS.md](EXPERIMENTS.md), E2.

### Effect heterogeneity vs task heterogeneity

**Definition.** Three different spreads appear in the power calculations. (1) Task heterogeneity: how much *baseline* pass rates differ between tasks, summarised by the [ICC](#intra-task-correlation) (0.575). (2) The spread of the *effect* across tasks on the logit scale: in the MDE simulations each task's own shift is the mean shift plus a normal draw with SD 0.5 logit. (3) tau^2, the between-task variance of the effect on the probability scale, used in the closed-form MDE: for two arms of k runs each, the variance of a task's difference is Var(d_i) = tau^2 + 2 x p(1 - p) / k.

**Example.** The planning value tau^2 = 0.008 means the true per-task effect has an SD of sqrt(0.008) = 0.089, about 9 pp, across tasks. With the unbiased within-task variance 0.0787 (all 89 TB2 tasks) and k = 5, Var(d_i) = 0.008 + 2 x 0.0787 / 5 = 0.0395. The SE over 89 tasks is sqrt(0.0395 / 89) = 0.0211, and the MDE is 2.8 x SE = 5.9 pp (derived; 2.8 = 1.96 + 0.84 for two-sided alpha 0.05 and 80% power). At 10 runs per arm the same formula gives about 4.6 pp, close to the planning 4.5 pp.

**Common mistake.** Treating tau^2 as measured. E0 runs only S0, and the spread of an effect across tasks needs two different strategies on the same tasks. So tau^2 stays a stated assumption until E3.

**Used in.** [minimum detectable effect](#minimum-detectable-effect); [EXPERIMENTS.md](EXPERIMENTS.md), E3 planning MDEs and E0-SIM.

### Null acceptance and harm rate

**Definition.** Two ways to score a selection rule in simulation. *Null acceptance* is how often the rule accepts an edit when no candidate is truly better (a pure null: all edit effects are zero). The *harm rate* is the share of simulated loops whose chosen version is truly worse than S0, under a stated distribution of edit effects.

**Example.** The plan's original rule accepted an edit in 52% of rounds under a pure null. The hybrid rule accepts about 4.4 edits per 6-round loop under a pure null; that is a count of edits, not a percentage. Its harm rate at the planned pool sizes is 3.5% of loops when edit effects are drawn from N(0, 0.3^2). Before Stage 1 the rule must show a harm rate of at most 10% under N(0, 0.3^2) at the real pool sizes (gate G-SEL), or V2_pro moves to k=5.

**Common mistake.** Mixing up the two. A rule can accept many null edits and still rarely end worse than S0, because the final choice on V2_pro can fall back to an earlier version, including S0.

**Used in.** [winner's curse](#winners-curse); [hybrid selection rule](#hybrid-selection-rule); [common random numbers](#common-random-numbers); [EXPERIMENTS.md](EXPERIMENTS.md), E2.

### Wilson interval

**Definition.** A confidence interval for a binomial proportion x/n that stays inside [0, 1] and keeps close to its stated coverage for small n or rates near 0 or 1. With z = 1.96, its centre is (x + z^2/2) / (n + z^2) and its half-width is z / (n + z^2) x sqrt(x(n - x)/n + z^2/4).

**Example.** The E4b pilot passes if the switch fires on at least 6 of 40 trials (15%). The Wilson 95% CI for 6/40 is 7.1% to 29.1% (derived). The simple Wald interval, p ± 1.96 sqrt(p(1 - p)/n), gives 3.9% to 26.1%.

**Common mistake.** Using the Wald interval for small counts. For 1 of 40 its lower end is -2.3% (derived), which is impossible.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E4b; [EXECUTION_PLAN.md](EXECUTION_PLAN.md), gate G-E4b.

### Censoring

**Definition.** A value is censored when the data show only that it lies beyond a bound, not where. The plan uses the word in two places.

**Example.** (1) CER_test is censored when S0's BoN@10 never reaches S\*'s pass rate: it is reported as "> c(10)/c_test\*" and never extrapolated. In the task bootstrap some resamples may be censored and others not, so an end of the CI can itself be open and is written "> value". E11 calls these censored CIs. (2) In E3-LB, S0 trials are censored at 1x the task timeout: a trial whose logged agent time passes the timeout counts as a failure, as on the leaderboard.

**Common mistake.** Replacing a censored value with the bound, or extending the BoN curve past N = 10. Both turn "at least" into a made-up number.

**Used in.** [compute-equivalence ratio](#compute-equivalence-ratio); [step and token budgets](#step-and-token-budgets); [EXPERIMENTS.md](EXPERIMENTS.md), E11 and E3-LB.

### Kendall's tau

**Definition.** A rank correlation between two orderings of the same items: (concordant pairs - discordant pairs) / total pairs. It is 1 for the same order, -1 for the reversed order and near 0 for unrelated orders. It is unrelated to tau^2.

**Example.** E11 compares how methods rank under pass rate, pass per MCU, CER_test and Δp / C. *Illustrative:* four methods ranked the same way except for one adjacent swap give 6 pairs, 5 concordant and 1 discordant, so tau = (5 - 1) / 6 = 0.67.

**Common mistake.** Reading much into tau over 4 or 5 methods. With 4 methods there are only 6 pairs, so tau takes only 7 possible values, and a single swap moves it by 0.33.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E11.

### AUROC

**Definition.** The area under the receiver operating characteristic curve (AUROC) is the probability that a randomly chosen passing trajectory gets a higher score than a randomly chosen failing one, with ties counted as half. 0.5 is chance and 1 is perfect. It does not depend on a threshold or on the pass rate.

**Example.** E0-JUDGE scores the same-model judge on about 600 E0 trajectories with known outcomes. If its AUROC is at least 0.6, the judge is the primary BoN selector. Otherwise the primary selector is "agent-written tests passed, ties broken at random".

**Common mistake.** Scoring the judge by accuracy. At a pass rate near 23%, a judge that always says "fail" is 77% accurate and useless; its AUROC is 0.5.

**Used in.** [best-of-N](#best-of-n); [EXPERIMENTS.md](EXPERIMENTS.md), E0-JUDGE; [EXECUTION_PLAN.md](EXECUTION_PLAN.md), gate G-JUDGE.

### GLMM

**Definition.** A generalised linear mixed model (GLMM) is a regression for non-normal outcomes, here a logistic regression for pass or fail, with random effects for groups. In `pass ~ arm + (1 + arm | task)`, arm is a fixed effect, each task has its own intercept (its difficulty), and each task has its own arm effect (effect heterogeneity).

**Example.** The GLMM is a sensitivity analysis in E3, beside the primary paired t-test. Its arm coefficient is a log-odds effect for a typical task. That is a different [estimand](#estimand) from the primary one, the equal-weight mean pp difference over the 89 tasks.

**Common mistake.** Reading the GLMM coefficient as pp and comparing it directly with the t-test estimate. It must first be converted, and the conversion depends on each task's base rate (see [logit scale](#logit-scale)).

**Used in.** [paired t-test](#paired-t-test); [EXPERIMENTS.md](EXPERIMENTS.md), E3.

---

## Attribution

### Ablation

**Definition.** Removing or reverting one component of a system and measuring how the result changes. It asks which parts the gain depends on.

**Example.** E-ATTR reverts parts of S\*1 to their S0 values on 40 fixed TB2 tasks at 3 runs each (planned). The 40 tasks are chosen at Stage 1 from public third-party data only: the 35 tasks with at least one success in the little-coder run, plus 5 of its 54 never-solved tasks drawn with seed 20261015, stratified by category. One arm sets `lessons_k = 0` and turns notes off. It is never cut, because it bounds the memorisation channel.

**Common mistake.** Choosing the ablation task set by looking at the arms' own TB2 results. That selects on the outcome being measured.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 7.4; [EXPERIMENTS.md](EXPERIMENTS.md), E-ATTR; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M10 and M16.

### Leave-one-out

**Definition.** An ablation that reverts exactly one dimension group of the final strategy and keeps the rest. The drop estimates that group's contribution given all the others.

**Example.** Planned: up to 3 groups (all changed groups if there are at most 3; otherwise the 3 with the most accepted edits in S\*1's lineage), each 40 x 3 = 120 episodes, paired with S\*1 x5 on the same tasks. Total E-ATTR is 480 episodes, or 240 after cut 1 of the budget plan. The MDE is about 12 pp, so results are exploratory. If S\*1 equals S0, E-ATTR does not run.

**Common mistake.** Adding leave-one-out drops and expecting them to sum to the total gain. With interactions they need not.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E-ATTR; [PAPER_PLAN.md](PAPER_PLAN.md), mechanism figure.

### Add-one

**Definition.** The mirror of leave-one-out: apply one dimension group of S\* to S0 and measure the gain on its own.

**Example.** TECHNICAL_PLAN section 7.4 lists add-one arms. The paper-1 budget does not fund them: E-ATTR runs leave-one-out arms only. The 2x2 enforced-vs-advised design (T2) is the one place where a single factor is added on its own (see [interaction](#interaction)).

**Common mistake.** Treating add-one and leave-one-out as interchangeable. Add-one measures a component in the S0 context; leave-one-out measures it in the S\* context.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 7.4 (to be amended); [EXPERIMENTS.md](EXPERIMENTS.md), E-ATTR.

### Interaction

**Definition.** Two factors interact when the effect of one depends on the level of the other. In a 2x2 design, the interaction is (11 - 10 - 01 + 00), where 1 means the factor is on.

**Example.** In T2 the factors are "S\*1 controller" and "S\*1 prompt text". The interaction contrast has twice the standard error of a main effect. Its MDE is about 8 pp, so it is reported descriptively, and only if the Tier C enforce-only cell runs.

**Common mistake.** Testing an interaction with the sample size planned for a main effect.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E-T2; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M13.

### Shapley value

**Definition.** A way to split a total gain fairly among components: each component gets its marginal contribution averaged over all orders in which components could be added. Exact Shapley values need every subset of components evaluated.

**Example.** TECHNICAL_PLAN section 7.4 says a sampled Shapley estimate is affordable only with at most 6 dimension groups. Exact Shapley over 3 groups needs 2^3 = 8 configurations; at 40 tasks x 3 runs that is 6 new arms (S0 and S\*1 already run), 720 episodes (derived). This exceeds the 480-episode E-ATTR budget, so Shapley values are not in paper 1.

**Common mistake.** Computing Shapley values from the noisy edit log's recorded deltas. Garbage in still gives a tidy-looking split.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 7.4.

---

## Methods

### First-order vs second-order adaptation

**Definition.** *First-order* adaptation changes the agent's strategy from its own results. *Second-order* adaptation changes the mechanism that makes those changes (the failure taxonomy, the diagnosis and proposal prompts, the selection rule). Model weights stay frozen in both.

**Example.** Paper 1 covers the first-order loop. The review plans to move the second-order loop (RQ3) to paper 2, because a powered comparison of two mechanisms needs 27-32 independent loops per arm: 73,710-87,360 episodes, or about 345-409 GPU-days at the planning rate. This needs the professor's answer (DECISIONS.md, Q4; default: move it to paper 2). If he says it is essential, one option is a descriptive single-loop demonstration on TB-Pro only, capped at 1,365 episodes.

**Common mistake.** Comparing one loop under each mechanism. One loop is a single high-variance draw: in simulation, two independent hybrid loops differ by more than 5 pp 47% of the time.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), sections 5 and 6; [DECISIONS.md](DECISIONS.md), Q4; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M7.

### Hybrid selection rule

**Definition.** The planned rule for choosing S\*. It searches leniently for 6 fixed rounds, then picks the best of all versions on a fresh pool. Every adapted arm (S\*1, S\*2, B4, and B5 if run) uses the same rule.

**Example.** Each round runs the current strategy once on the 50-task A_pro diagnosis set. The proposer emits 4 candidates of at most 2 edit operations each. The parent and the candidates run once on V_pro. The candidate with the largest net gain is accepted if it gains at least one task, compared as integers. After round 6, all 7 versions run 3 times on V2_pro and the best becomes S\*. One loop costs 6 x (50 + 25 + 100) + 7 x 15 x 3 = 1,365 episodes. In the review's simulation at these pool sizes, with edit effects drawn from N(0, 0.3^2) on the logit scale, the chosen version gained about 0.82 logit (about 6.6 pp on TB2) and was worse than S0 in 3.5% of loops. That 3.5% is the rule's [harm rate](#null-acceptance-and-harm-rate). It is a different quantity from the about 4.4 edits per loop that the rule accepts under a pure null.

**Common mistake.** Comparing success *rates* as floats. The current `first_order.py` compares float rate differences against `min_delta`; with min_delta = 1/12, rounding silently rejects some one-task gains. The fix is integer counts with exact-tie unit tests.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E2 and CODE-FIX; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M9.

### Reflexion

**Definition.** A method in which an agent writes a verbal reflection on its own failure and retries with that reflection in memory, without weight updates: Reflexion: Language Agents with Verbal Reinforcement Learning (Shinn et al., arXiv 2303.11366, Mar 2023), [link](https://arxiv.org/abs/2303.11366). It is the basis of baseline B1.

**Example.** Planned B1 retries inside one Harbor trial when the in-run judge says "fail" or an agent-written test fails, never on hidden tests. It allows at most 3 attempts, with no environment reset between attempts. The 60-step cap applies per attempt; one 64k generated-token cap is shared across agent, judge, and reflection calls for the task/run. The attempt cap is drawn per (task, run) from a mixture fixed at Stage 2 to match S*'s MCU, so the requested caps sum to at most 1,024 episode-equivalents at x5.

**Common mistake.** A retry trigger that never fires. The current code retries only when the agent's own check returns `False`. Under Harbor the tests are uploaded only at verification, so visible-test checks often have nothing to run (an inference from Harbor's code). The check then returns `None`, and B1 does not retry.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 4.1; [EXPERIMENTS.md](EXPERIMENTS.md), E1 and E3-B1; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M8.

### GEPA

**Definition.** A prompt optimiser that reflects on trajectories in natural language and evolves prompt text: GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning (Agrawal et al., arXiv 2507.19457, Jul 2025), [link](https://arxiv.org/abs/2507.19457). It reports beating GRPO, a reinforcement learning method, with up to 35x fewer rollouts.

**Example.** GEPA was the model for baseline B3 (free-text adaptation of prompt text instead of the typed strategy). The review removes B3 from paper 1, saving about 1,810 episodes. The question "does structure matter?" is answered instead by the enforced-vs-advised contrast and, if run, by B5.

**Common mistake.** Treating GEPA as a strategy method. It optimises prompt text with a fixed optimiser, so its edits are not typed or enforced in code.

**Used in.** [PRIOR_WORK.md](PRIOR_WORK.md), section 1.1; [LITERATURE_MAP.md](LITERATURE_MAP.md); [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M1.

### ACE

**Definition.** Agentic Context Engineering (ACE) keeps an evolving "playbook" of lessons, built by a generator, a reflector and a curator: Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models (Zhang et al., arXiv 2510.04618, Oct 2025), [link](https://arxiv.org/abs/2510.04618). It reports +10.6% on agent benchmarks including AppWorld.

**Example.** ACE is in the closest-work table. Its section 4.6 reports that it stays effective with a much weaker reflector and degrades gracefully under noisy reflections. That narrows the novelty of a diagnosis-noise injection experiment, which moves to paper 2.

**Common mistake.** Equating ACE's playbook with this project's `notes` field. ACE's playbook is the whole learned artefact; here notes are a fenced, length-limited slot that is attributed separately.

**Used in.** [PRIOR_WORK.md](PRIOR_WORK.md), section 1.1; [LITERATURE_MAP.md](LITERATURE_MAP.md); [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M14.

### Harness self-evolution

**Definition.** A 2026 line of work in which an agent with a frozen model edits its own *harness* (the code and prompts around the model: tools, loop, memory, recovery) from its failures. It is the closest prior work to this project.

**Example.** Self-Harness: Harnesses That Improve Themselves (Zhang et al., arXiv 2606.09498, Jun 2026), [link](https://arxiv.org/abs/2606.09498), edits a Python harness for a frozen Qwen3.5-35B-A3B. On a fixed 64-task TB2 subset it reports held-out 23.8% to 38.1%, consistent with 10/42 to 16/42 (inferred denominators). It served the model on four H200 GPUs and reports no best-of-N, reflection or cost baselines. Agentic Harness Engineering (Lin et al., arXiv 2604.25850, Apr 2026), [link](https://arxiv.org/abs/2604.25850), pairs each edit with a prediction and reports that harness structure transfers across models while prose-level strategy does not. Meta-Harness: End-to-End Optimization of Model Harnesses (Lee et al., arXiv 2603.28052, Mar 2026), [link](https://arxiv.org/abs/2603.28052), searches harness code. Rethinking the Evaluation of Harness Evolution for Agents (Wang et al., arXiv 2607.12227, Jul 2026), [link](https://arxiv.org/abs/2607.12227), already compares harness evolution with matched-budget best-of-N sampling on TB2.1, with frontier API models. So paper 1 is framed as a pre-registered, compute-matched test of typed, compiled strategy adaptation for a small local model on held-out tasks, with cost per task, not as "the first self-improving harness".

**Common mistake.** Calling a typed strategy "better than code" without a code baseline. The typed space is a deliberate restriction, chosen for enforcement, attribution and auditability. B5 (free-form code edits, optional) is the comparison; without it the paper says it makes no such comparison.

**Used in.** [LITERATURE_MAP.md](LITERATURE_MAP.md); [PRIOR_WORK.md](PRIOR_WORK.md), section 1.1; [EXPERIMENTS.md](EXPERIMENTS.md), E-B5 and E-N4; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M1.

### Failure taxonomy

**Definition.** A fixed list of failure classes the diagnoser assigns to failed trajectories. It turns free-form failure stories into countable categories that the proposer can act on.

**Example.** The starting taxonomy comes from the error analysis in Terminal-Bench: Benchmarking Agents on Hard, Realistic Tasks in Command Line Interfaces (Merrill et al., arXiv 2601.11868, Jan 2026), [link](https://arxiv.org/abs/2601.11868). Its trajectory-level classes include disobeying the specification, step repetition, context loss, premature termination, and no or incorrect verification. Each diagnosis records `failure_class`, `critical_step`, `evidence` and `implicated_dimensions`. A zero-episode appendix analysis (T12) tracks how the class mix shifts across rounds on TB-Pro logs.

**Common mistake.** Letting the diagnoser invent classes freely. The counts then cannot be compared across rounds.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 5.1; [EXPERIMENTS.md](EXPERIMENTS.md), E-T12.

### Typed strategy

**Definition.** The agent's procedure as a validated data object (a Pydantic model serialised to JSON) with typed fields and ranges, instead of free prompt text. Edits are schema-checked operations, and each version records its parent, edit and evidence.

**Example.** Dimensions: exploration, planning, tool policy, memory, verification, recovery and fenced `notes` (at most 300 characters per stage). Edits are JSON-Patch-like with at most 2 operations. Budget fields are not editable (`EDITABLE_DIMENSIONS` excludes `budget`). In paper 1 the proposer also cannot emit rollback values or the planned `switch_to` value; unit tests check both exclusions.

**Common mistake.** Assuming a typed field changes behaviour just because it exists in the schema. See [compile() vs render()](#compile-vs-render).

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 3; `strategy_schema/model.py`; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M12.

### compile() vs render()

**Definition.** `render()` turns a strategy into natural-language instructions for the prompt. `compile()` turns it into controller behaviour in code: which stages run, which commands are allowed, when checks fire. The planned `compile(strategy)` returns both `(controller_config, prompt_text)`, with independent switches for each.

**Example.** Today `Strategy.render()` (`strategy_schema/model.py`) goes into every arm's system message (`baselines/agent_loop.py`). Only `exploration.probes`/`probe_budget_steps`, some `tool_policy` fields, `verification` fields and the budget act in code. All `recovery.*` fields are text-only. Gate G1, before Stage 1, requires a CI unit test (toy environment, scripted model) for each field counted as compiled. The minimum compiled set is exploration, tool policy, verification and `recovery.retry_on`/`max_retries`/`on_repeated_failure`.

**Common mistake.** Claiming that adaptation "changed the agent's recovery policy" when the change only edited prompt text that a small model may ignore.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 3.3; [EXPERIMENTS.md](EXPERIMENTS.md), G1; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M12.

### Compiled vs advised strategy

**Definition.** The same strategy content delivered two ways: *compiled* (enforced by the controller, plus the rendered text) or *advised* (rendered text only, with the S0 controller). The difference measures what enforcement adds on top of advice.

**Example.** T2 cells, as (controller, text): (S0, S0) and (S\*1, S\*1) come from E3. The core cell is advised = (S0, S\*1 text) on TB2-89 at k=5, 445 episodes (planned). Its contrast with compiled S\*1 detects only effects of about 5.8 pp or more. The optional enforce-only cell (S\*1, S0 text) would allow a main effect of enforcement with an MDE of about 3.8 pp. Motivation: Harness Updating Is Not Harness Benefit (Lin et al., arXiv 2605.30621, May 2026), [link](https://arxiv.org/abs/2605.30621), reports a harness-following rate of 0.142 for Qwen3-32B against 0.757 for Claude Opus 4.6.

**Common mistake.** Calling "compiled S\* minus advised S\*" the effect of enforcement in general. Without the enforce-only cell it is enforcement *given* advice.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E-T2; [PAPER_PLAN.md](PAPER_PLAN.md), mechanism figure; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M13.

---

## Loop components

These are the parts of one first-order adaptation loop (E2). [Hybrid selection rule](#hybrid-selection-rule) describes how they fit together.

### Diagnoser and diagnosis set

**Definition.** The *diagnoser* is a model call that reads one trajectory and returns a structured diagnosis of what went wrong. The *diagnosis set* A_diag is the fixed group of tasks whose trajectories it reads each round.

**Example.** Each round, the current version runs once on A_diag, a fixed stratified 50-task sample of A_pro (seed 20261015). Hidden-test results are used here, because A_pro is training data. Each trajectory is first compressed, with no model call, into a step table (step, command, exit code, truncated output, time). The diagnoser reads every failed trajectory and a sample of successes, and returns `failure_class` (from the [failure taxonomy](#failure-taxonomy)), `critical_step`, `evidence` and `implicated_dimensions`. Diagnoses are then grouped by (class, dimension) and ranked by frequency for the proposer. In paper 1 the diagnoser is the same local model as the agent, and its calls count in the arm's one-time adaptation cost, not in episodes.

**Common mistake.** Treating the diagnosis set as a selection set. A_diag decides what to try; only V_pro and V2_pro decide what to keep.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 5.1; [EXPERIMENTS.md](EXPERIMENTS.md), E2 and E-T12; [Cohen's kappa](#cohens-kappa).

### Proposer and edit operation

**Definition.** The *proposer* is a model call that turns the top diagnosis groups into candidate edits. An *edit operation* is one schema-checked change to one strategy field, written in a JSON-Patch-like format.

**Example.** One operation: `{"op": "add", "path": "/exploration/probes/-", "value": "check_installed_packages"}`, stored with its rationale, the diagnosis ids behind it and the round. Each round the proposer emits K = 4 candidates of at most 2 operations each. Each candidate must validate against the schema, pass the [lint](#lint) and stay inside the paper-1 edit space: no rollback values or fields, no `switch_to`, no budget fields. A rejected candidate is logged and counts against K, so fewer than 4 may be screened. In B4, random sampling in the same edit space replaces the proposer.

**Common mistake.** Treating a 2-operation candidate as one change in attribution. Its two operations can touch different [dimension groups](#dimension-group), and E-ATTR reverts groups, not candidates.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), sections 3.2 and 5.1; [EXPERIMENTS.md](EXPERIMENTS.md), E2; [typed strategy](#typed-strategy).

### Parent, candidate and version

**Definition.** In round r the *parent* is the current version S_r. A *candidate* is the parent with one proposed edit applied. A *version* is a strategy the loop has committed: S0 is the start and S1 to S6 are the versions after rounds 1 to 6. The *lineage* of a version is its chain of parents back to S0, with the edit and its evidence recorded at each step.

**Example.** Each round, the parent is run afresh beside its 4 candidates on V_pro, with shared per-(task, run) seeds. The best candidate is accepted if it solves at least one more task, net. After round 6, all 7 versions (S0 to S6) run 3 times on V2_pro, and S\* is the one with the most net successes; ties go to the earlier version. Each version stores `version`, `parent_version` and a `changelog` of its edits with rationale and evidence. E-ATTR picks which groups to revert by counting accepted edits in S\*1's lineage.

**Common mistake.** Assuming S\* is the last version, S6. The final choice can pick any of S0 to S6, and "S\* = S0" is a pre-registered valid outcome.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), sections 3.1, 5.1 and 5.2; [EXPERIMENTS.md](EXPERIMENTS.md), E2 and E-ATTR.

### Dimension group

**Definition.** One top-level section of the strategy object. The groups are exploration, planning, tool_policy, memory, verification, recovery and notes, plus budget, which is fixed by the experiment and cannot be edited (`DIMENSIONS` and `EDITABLE_DIMENSIONS` in `strategy_schema/model.py`). A *changed group* of S\*1 is one in which any field differs from S0.

**Example.** E-ATTR reverts whole groups to their S0 values. *Illustrative:* if S\*1 changed `exploration.probes`, `verification.checks` and the verify-stage note, it has 3 changed groups. E-ATTR then runs 3 revert arms plus the lessons/notes-off arm: 4 x 40 x 3 = 480 episodes. With more than 3 changed groups, the 3 with the most accepted edits in S\*1's lineage are reverted.

**Common mistake.** Reading the lessons/notes-off arm as a revert of the memory group. It sets only `lessons_k` = 0 and turns notes off; the other memory fields keep S\*1's values.

**Used in.** [leave-one-out](#leave-one-out); [Shapley value](#shapley-value); [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), sections 3.2 and 7.4; [EXPERIMENTS.md](EXPERIMENTS.md), E-ATTR.

### Lessons vs notes

**Definition.** Both are free text that adaptation can add, and both must pass the [lint](#lint). *Notes* are part of the strategy: the `notes` field holds at most 300 characters for each stage (explore, plan, act, verify, recover), is edited by the proposer, and is the only free text inserted into the stage prompts. *Lessons* live outside the strategy: the diagnoser writes short cross-task lessons into a versioned lesson store, and a run retrieves up to `memory.lessons_k` (0 to 5) of them at task start.

**Example.** S0 has `lessons_k` = 0 and lesson store "none", so lessons reach the agent only if an accepted edit raises `lessons_k`. The E-ATTR arm with `lessons_k` = 0 and notes off measures how much of S\*1's gain flows through free text, the channel most able to carry task-specific content. That arm is never cut.

**Common mistake.** Thinking `lessons_k` = 0 alone closes the free-text channel. Notes are a separate channel, so the arm turns off both.

**Used in.** [ACE](#ace); [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), sections 3.2 and 5.2; [EXPERIMENTS.md](EXPERIMENTS.md), E-ATTR and LINT-PILOT.

### Lint

**Definition.** An automatic check on every note, lesson and other proposer-written text before it is evaluated. It rejects task ids, URLs, commands over 40 characters and file paths from any task.

**Example.** A candidate whose text fails the lint is logged and counts against K = 4. Before Stage 1, LINT-PILOT runs the lint on proposer outputs generated from TB-Pro E0 failure logs and reports its false-positive rate on generic advice. There is no pass threshold: the rate goes into the pre-registration, and the lint is revised before Stage 1 if it blocks generic advice.

**Common mistake.** Treating a passing lint as proof that nothing leaked. A paraphrase can carry task-specific content past any pattern check, which is why the lessons/notes-off arm exists.

**Used in.** [contamination](#contamination); [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 7.5; [EXPERIMENTS.md](EXPERIMENTS.md), LINT-PILOT and E2.

### Strategy hash and provenance tag

**Definition.** A *strategy hash* is a short fingerprint that identifies one exact strategy version in the logs. A *provenance tag* marks each strategy-triggered stage of an episode with the strategy field that caused it, plus a flag saying whether the stage was executed or overridden. Both are planned, not yet in the code.

**Example.** Gate G-INFRA requires per-step JSONL logs with strategy hash, provenance tag, seed, timings and Harbor trial id. The E2 edit log records, for every candidate, its strategy hash, edits, V_pro outcomes and MCU. Provenance tags feed the per-field adherence readout of E-T2 and the mechanism examples of E-ATTR, for example a probe that found a missing package.

**Common mistake.** Identifying versions by name or round number alone. Each loop has its own "S3", and only the hash ties a log line to the exact content that ran.

**Used in.** [EXECUTION_PLAN.md](EXECUTION_PLAN.md), G-INFRA and P0-14; [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 7.4; [EXPERIMENTS.md](EXPERIMENTS.md), E2, E-T2 and E-ATTR.

---

## Cost and metrics

### Cost per task

**Definition.** What one task costs a method at test time, reported per arm. It answers meeting point 1, "baseline cost : task". Because per-task costs are skewed, means alone mislead.

**Example.** In the little-coder run, mean trial time was 404.7 s but the median was 296.4 s, and the longest trial took 4,589 s. Failures cost more: mean agent time was 231 s on successes and 357 s on failures. The planned point-1 table gives, for every arm (S0, B1 at each k, BoN at each N, B4, S\*, the selector library): mean, median, interquartile range and task-bootstrap CI of dollars per task at two frozen rates, wall-clock with hardware named, generated tokens including reasoning, MCU, and pass rate per dollar. Every column is also split by outcome and by S0 task class.

**Common mistake.** Spreading the one-time adaptation cost over per-task figures. It is reported separately and combined only in the efficiency index.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 4.3; [MEETING_2026-10-14.md](MEETING_2026-10-14.md), item 1; [EXPERIMENTS.md](EXPERIMENTS.md), E3-COST.

### Model compute units

**Definition.** Model compute units (MCU) are a cost unit computed from llama.cpp's per-call `timings`: MCU = a x prompt_n + b x predicted_n. Here prompt_n counts prompt tokens actually processed (cached tokens excluded) and predicted_n counts generated tokens including reasoning. The coefficients a and b are fitted once and frozen.

**Example.** a and b are fitted by least squares of (prompt_ms + predicted_ms)/1000 on per-call records from the E-P0 TB-Pro sweep, and frozen in `pins.lock` at Stage 1. Before Stage 2, each arm with at least 40 TB-Pro episodes must show a mean episode residual within +/-3%, with its 95% CI within +/-5%. If an arm fails, a context-length term is added; if it still fails, processed tokens become the matching unit and MCU a sensitivity analysis. MCU is not claimed to equal GPU-seconds.

**Common mistake.** Matching on wall-clock or on the client's `model_s`. Both include waiting for a free server slot, so they change with concurrency and co-tenant load, not with the method.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E-P0 and E3-COST; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M4; `baselines/cost.py` (to be changed).

### Occupancy cost

**Definition.** The dollar cost of the GPU time a method occupies. With several requests batched at once, the sum of per-call times exceeds the GPU's busy time, so per-call times must be scaled before converting to dollars.

**Example.** E-P0 measures k_occ = (sum over calls of (prompt_ms + predicted_ms)/1000) / (GPU busy wall-seconds) at the pinned concurrency. Dollars = (MCU-hours / k_occ) x rate, at two frozen rates: an electricity rate and a cloud-GPU-equivalent rate, each with source and date. For scale: an RTX 4090 draws 450 W, about 12-13 Australian cents per hour at the 2026-27 Victorian Default Offer of 25.96-28.22 c/kWh (GPU only), and RunPod lists an RTX 4090 at US$0.34/h on its Community Cloud.

**Common mistake.** Charging the per-call times directly at -np > 1. That counts the same GPU-second several times.

**Used in.** [SMALL_MODELS.md](SMALL_MODELS.md), section 3.2; [EXPERIMENTS.md](EXPERIMENTS.md), E-P0; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M4.

### Compute matching

**Definition.** Giving each baseline the same per-task compute as the method it is compared with, so that a win cannot come from spending more. When the matched value falls between integers, it is matched by a mixture.

**Example.** Primary matching is per task: N\* = (S\* mean MCU per task) / (S0 mean MCU per episode + judge MCU per trajectory). A non-integer N\* = n + q is matched as (1 - q) x BoN@n + q x BoN@(n+1), with q fixed at Stage 2 from TB-Pro runs. If N\* exceeds the pool size of 10, BoN@10 is reported and flagged as under-matched. B1's attempt cap is randomised over {1, 2, 3} per (task, run), with a mean cap of at most 2.3.

**Common mistake.** Matching on the amortised total. One hybrid loop costs 1,365 episodes, so amortised over 89 tasks the matched N would be about 16, more than the pool holds.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 4.2; [EXPERIMENTS.md](EXPERIMENTS.md), E3-BoN and E3-B1; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M4.

### Compute-equivalence ratio

**Definition.** The test-time compute-equivalence ratio (CER) asks how many base-strategy best-of-N samples the adapted strategy is worth per task. CER_test = c_eq / c_test\*. Here c_test\* is S\*'s mean MCU per task, and c_eq is the per-task compute at which S0's best-of-N curve first reaches S\*'s pass rate.

**Example.** *Illustrative, not a result:* if S\* matches S0's BoN@3 and costs 1.2 S0 episodes of compute per task, CER_test = 3 / 1.2 = 2.5. If S0's BoN@10 never reaches S\*'s pass rate, CER is reported as censored, "> c(10)/c_test\*", never extrapolated. An amortised variant, CER(T) = c_eq / (c_test\* + A\*/T), adds the adaptation cost spread over T test tasks. At T = 89 it is bounded at about 0.6 by construction (derived): A\*/T is about 1,365 / 89 = 15.3 episodes per task, c_eq can be at most about c(10), roughly 10 episodes plus judge calls, and c_test\* is about 1 episode, so CER(89) is at most about 10 / (1 + 15.3) = 0.6. So it is shown only as a curve over T.

**Common mistake.** Using a ratio of differences, Δp/C, as the index, where C is the extra cost of S\* over the baseline. It is undefined when C <= 0 and unstable near it. That is why, under the default answer to Q1, the original section 7.6 index moves to the appendix.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E11; [DECISIONS.md](DECISIONS.md), Q1; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M5.

### Payback

**Definition.** The number of tasks after which adaptation's one-time cost is repaid by cheaper solving: T\* = A\* / (c_eq - c_test\*). A\* is the adaptation compute of the S\* loop, including diagnosis and proposal calls. If c_eq <= c_test\*, payback is "never".

**Example.** *Illustrative:* take A\* = 1,365 episode-equivalents, the episodes of one loop, and the CER example above (c_eq = 3, c_test\* = 1.2 episode-equivalents per task). Then T\* = 1,365 / 1.8, about 760 tasks. This is a lower bound: the full A\* is 1,365 plus the loop's diagnosis and proposal calls, which only raise T\*. That is more tasks than TB2 has, which is why the efficiency figure shows curves over T up to at least 500 tasks instead of one value at T = 89.

**Common mistake.** Leaving out the diagnosis and proposal calls from A\*. They are model calls the method needs, so they are part of its cost.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 4.2 ("pays for itself"); [EXPERIMENTS.md](EXPERIMENTS.md), E11; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M5.

### Skill-acquisition efficiency

**Definition.** Chollet's description of intelligence as the efficiency with which a system acquires new skills, given its priors and experience: On the Measure of Intelligence (Chollet, arXiv 1911.01547, Nov 2019), [link](https://arxiv.org/abs/1911.01547). It is one of two readings of meeting point 4, "intelligence index".

**Example.** Reading (a): one number for how efficiently the agent improves, with CER_test as headline and T\* as companion. Reading (b): a composite over several benchmarks, like the Artificial Analysis Intelligence Index, used to choose models. Version 4.3.2 of that index averages 10 evaluations and includes Terminal-Bench 4.0 at 10% weight. Which reading applies is the professor's decision (DECISIONS.md, Q1). Default if no answer by the Stage-1 freeze: reading (a), with the composite only in the model-choice table, never computed on TB2 held-out runs.

**Common mistake.** Calling the project's index "Chollet's measure". His formal definition also weighs priors and generalisation difficulty; the plan's index is "after Chollet", not his measure.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 7.6; [MEETING_2026-10-14.md](MEETING_2026-10-14.md), item 4; [DECISIONS.md](DECISIONS.md), Q1.

### Pareto frontier

**Definition.** The set of methods (or settings) for which no other option is both cheaper and better. On a pass-rate vs cost plot, it is the upper-left boundary.

**Example.** The planned figure plots pass rate against mean MCU per task, with dollars beside it. It shows BoN@N for N = 1 to 10 and B1 at each attempt cap as curves, and S\*, B4 and the library plus selector as points. S\* is interesting only if it lies above the BoN and B1 curves at its own cost.

**Common mistake.** Comparing methods at one arbitrary budget. A method can win at one cost and lose at another; the full curve shows both.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 7.2; [PAPER_PLAN.md](PAPER_PLAN.md), figures; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M4.

### VBS and SBS

**Definition.** From algorithm selection: the virtual best solver (VBS) picks, for each task, the version that does best on it; the single best solver (SBS) uses the one version that is best on average. VBS minus SBS is the headroom a per-task selector could gain. A real selector's regret is VBS minus selector.

**Example.** Reading (a) of meeting point 5, "strategy switching": a library of up to 5 versions {S0, S\*1, S\*2, B4-final, B5-final if run}, scored on TB2-89 at 0 extra episodes. Naive VBS is biased upward when solvers are random, as shown in Bias in Algorithm Portfolio Performance Evaluation (Cameron et al., IJCAI 2016), [link](https://www.cs.ubc.ca/~cchris13/docs/ijcai16_bias.pdf). In the review's simulation, four *identical* strategies on the little-coder task profile show a phantom VBS-SBS gap of 12.3 pp from single runs, 6.5 pp at k=5 and 4.7 pp at k=10; cross-fitting gives 0.0 pp. Two selectors are frozen on TB-Pro data before any TB2 episode. Whether point 5 means this or mid-task switching is the professor's decision (DECISIONS.md, Q2; default: per-task selection only).

**Common mistake.** Reporting "gap closed" when the headroom CI includes 0. The plan then reports "no detectable headroom".

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 5.4; [EXPERIMENTS.md](EXPERIMENTS.md), E4-SW and E4b; [DECISIONS.md](DECISIONS.md), Q2.

### GPU-day and planning throughput

**Definition.** A GPU-day is 24 hours of one dedicated GPU. The planning throughput converts episodes into GPU-days until the real rate is measured on the granted hardware.

**Example.** The 445 little-coder trial records sum to 50.03 h: a mean of 404.7 s per trial at concurrency 1, so 86,400 / 404.7 = 213.5 episodes per GPU-day. That run used an 8 GB-VRAM laptop with MoE CPU offload, so 213.5 is a conservative proxy with a +/-30% band (149-278 per day). At this rate the 9,653-episode core is 45.21 GPU-days (34.8-64.6 across the band). An earlier "about 270 s per trial" figure was wrong: the job's start and end timestamps cover only the 287 trials run after a resume, not all 445.

**Common mistake.** Dividing a job's wall-clock span by its trial count without checking for resumes or overlaps. Per-trial start and end times are the reliable source.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), cost table; [EXECUTION_PLAN.md](EXECUTION_PLAN.md), compute schedule; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M16.

---

## Budget and protocol

The numbers in this group come from the [cost table](EXPERIMENTS.md#cost-table) in EXPERIMENTS.md. Gate ids are listed in the [gates table](EXECUTION_PLAN.md#4-gates) in EXECUTION_PLAN.md.

### Episode-equivalent

**Definition.** The budget's unit for work that is not exactly one episode. One B1 attempt counts as one episode-equivalent. Model calls outside episodes (judge, selector, diagnosis and proposal calls) are measured in MCU and converted to episode-equivalents at gate G0.

**Example.** B1 at x5 has 89 x 5 = 445 runs with a mean attempt cap of at most 2.3, so its caps sum to at most 1,024 episode-equivalents (445 x 2.3 = 1,023.5, derived). The judge's about 1,490 calls (about 600 on E0 and 890 on TB2) are funded from contingency.

**Common mistake.** Counting a B1 run as one episode. A 3-attempt run can use three times the compute of one S0 episode.

**Used in.** [compute matching](#compute-matching); [payback](#payback); [EXPERIMENTS.md](EXPERIMENTS.md), terms table, E3-B1 and cost table.

### Core, contingency, floor and absolute cap

**Definition.** Four budget lines, in episodes. The *core* is the planned paper-1 run. *Contingency* is a reserve on top of it, for named uses only. The *absolute cap* bounds everything, optional work included. The *floor* is the smallest plan left after every allowed cut.

**Example.** Core 9,653 episodes (45.21 GPU-days). Core plus contingency 10,500 (49.18), so contingency is 847 episodes. It funds only the E0 top-up (at most 400), the 178-episode leaderboard fallback, non-episode model calls and infrastructure-error reruns, never new arms. Absolute cap 12,500 (58.55). Floor 6,224 (29.15).

**Common mistake.** Spending contingency on an extra arm because it fits. New arms are [Tier C](#tier-c) and need headroom under the absolute cap.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), cost table; [EXECUTION_PLAN.md](EXECUTION_PLAN.md), G0 budget rule; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M16.

### Tier C

**Definition.** Optional add-ons, funded only from headroom under the absolute cap. They are admitted at G0 in rank order, and only if their own gate passes. None counts in the core.

**Example.** Rank 1 E5-DEMO (at most 1,365 episodes, only if the professor asks for it); rank 2 the E-T2 enforce-only cell (445); rank 3 E-T1lite (554); rank 4 E-B5 (1,810). Items are admitted while remaining core plus admitted Tier C is at most min(G0 capacity, 12,500 - episodes spent). If headroom shrinks, B5 drops first, then T1-lite, then enforce-only, then E5-DEMO.

**Common mistake.** Reading a Tier C item as planned. Several may never run, and the paper must then say what it does not compare; for example, without B5 it makes no comparison with code-harness evolution.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), optional add-ons and cost table; [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 4.1.

### Cut order and single-seed branch

**Definition.** The *cut order* is a fixed list of reductions, applied one at a time when the G0 capacity is below the remaining core. The *single-seed branch* is the plan after cut 5, which drops the second adaptation loop.

**Example.** The cuts, in order: (1) E-ATTR to 2 arms, -240 episodes; (2) E-T2 advised cell from k=5 to k=3, -178; (3) B1 from x5 to x3, -410; (4) 4 rounds instead of 6 in all three loops, -1,320; (5) drop the S\*2 loop, -925; (6) S0 pool from x10 to x6, -356. Together they take 9,653 to the 6,224-episode floor. Cuts 4 and 5 must be decided before the Stage-1 tag; after it, only cuts 1 to 3 and 6 may be applied. In the single-seed branch S\* = S\*1 x10, the TB2 episode count is unchanged, and claims are about the [realised strategy](#realised-strategy).

**Common mistake.** Cutting out of order to protect a favourite arm. The order is fixed in advance so that what is cut cannot depend on results.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), cut order; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M16.

### Under-matched

**Definition.** A baseline is under-matched when it cannot be given as much per-task compute as S\*. The comparison then favours S\*, so the baseline is flagged in every table, not hidden.

**Example.** BoN: if the matched N\* exceeds the pool size P = 10, BoN@10 is reported and flagged. B1: if matching S\*'s TB-Pro per-task MCU needs a mean attempt cap above 2.3, B1 is flagged.

**Common mistake.** Reading "S\* beats an under-matched baseline" as a compute-matched win. It shows only that S\* beat a cheaper version of that baseline.

**Used in.** [compute matching](#compute-matching); [EXPERIMENTS.md](EXPERIMENTS.md), E3-BoN and E3-B1.

### Realised strategy

**Definition.** The particular strategy object that one loop produced, as opposed to the procedure that produced it. One loop is a single high-variance draw, so a claim about a realised strategy does not carry over to its procedure.

**Example.** E3's H2 compares S\* with B4 and is "worded about the realised strategies". B4 has one loop, so even a rejected H2 does not show that diagnosis beats random search, and paper 1 never claims that. In the single-seed branch, all claims are about S\*1 alone. In simulation, two independent hybrid loops differ by more than 5 pp 47% of the time.

**Common mistake.** Writing "diagnosis-driven adaptation beats random edits" from one S\* against one B4.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E3 hypotheses and cut order; [EXECUTION_PLAN.md](EXECUTION_PLAN.md), gate G-H2.

### Gate

**Definition.** A measurable condition that must hold before the next step, with a written action if it fails.

**Example.** Three gates have short ids used across the documents. G-INFRA (infrastructure) blocks every budgeted episode. G0 is the calibration gate after E0, with checks on fitness, contested supply, throughput and memorisation, plus the budget rule that sets the G0 capacity C = 0.9 x r x D_rem. G1 is the `compile()` gate, closed before Stage 1. The other gates have descriptive names: G-BASE (baseline repair), G-ROUTE (TB-Pro route), G-SWEEP (serving configuration), G-JUDGE (BoN selector), G-SEL (selection-noise calibration), G-B5, G-T1lite, G-T2, G-E4b, G-MCU (cost-unit validation) and G-H2. Criteria, deadlines and actions are in the [gates table](EXECUTION_PLAN.md#4-gates); zero-episode protocol items such as LEDGER and LINT-PILOT are in [EXPERIMENTS.md](EXPERIMENTS.md#gates-and-zero-episode-protocol-items).

**Common mistake.** Reading a failed gate as the end of the project. Most gates have a written fallback, such as a fallback model, a cut or a narrowed claim. G-H2 comes after the final run, and the run is never stopped or repeated because of it.

**Used in.** [EXECUTION_PLAN.md](EXECUTION_PLAN.md), section 4; [EXPERIMENTS.md](EXPERIMENTS.md), E0 and the gates table.

### Stage-1 freeze and pins.lock

**Definition.** The *Stage-1 freeze* is the moment the Stage-1 tag is signed, before the first adaptation episode. It is also the deadline for the professor's answers: questions still open then take their defaults, which are logged. `pins.lock` is the file that records everything that must not drift between runs.

**Example.** `pins.lock` holds the model file hash, llama.cpp commit and flags, GPU and driver, Harbor version, task commits, image digests, slots, KV cache type, context, reasoning budget, sampling and the MCU coefficients. The Stage-1 tag freezes it together with the analysis code, thresholds, pool lists, budget caps, the seed branch, the 40-task attribution set, E-INTERP and the decisions on cuts 4 and 5. The Stage-2 tag adds q, the B1 cap mixture, both switching selectors and the held-out ledger hash.

**Common mistake.** Updating a pinned item, such as a new Harbor release, because it is "only infrastructure". Any change after a tag is an [amendment](#amendment-vs-deviation) and is logged.

**Used in.** [pre-registration](#pre-registration); [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 2; [EXPERIMENTS.md](EXPERIMENTS.md), PREREG-1 and PREREG-2; [EXECUTION_PLAN.md](EXECUTION_PLAN.md), section 4.

### Amendment vs deviation

**Definition.** A *deviation* is any departure from an earlier plan or a committed artefact, logged in [DECISIONS.md](DECISIONS.md) with its reason. An *amendment* is a formal change to something already frozen, such as a pre-registration tag or the $0 API rule, also logged with its reason. Changes made after a tag are listed in the paper's appendix A14.

**Example.** A switching library of up to 5 versions, against the plan's estimate of at most 4, is a logged deviation. Falling back to the TB2 re-split (E-RESPLIT) is logged as a deviation from the committed split. Any API use in paper 1 needs a logged amendment with its own cap, and professor answers that arrive after the Stage-1 freeze become amendments.

**Common mistake.** Making a change silently because it seems small. Every change, and every default applied, is logged; unlogged flexibility is what pre-registration exists to prevent.

**Used in.** [DECISIONS.md](DECISIONS.md); [PAPER_PLAN.md](PAPER_PLAN.md), pre-registration plan; [EXECUTION_PLAN.md](EXECUTION_PLAN.md).

### A/A run

**Definition.** An experiment in which both arms are the same configuration. Any difference it shows is noise, so it measures the noise.

**Example.** E0-AA runs S0 against itself for 60 episodes on the dev slice, with shared per-(task, run) seeds, to measure the correlation rho between paired runs. Until rho is measured, every calibration assumes rho = 0, and no variance reduction from shared seeds is claimed.

**Common mistake.** Reading an A/A run as evidence about the method. It says nothing about S\*; it shows only how much two identical arms disagree.

**Used in.** [common random numbers](#common-random-numbers); [EXPERIMENTS.md](EXPERIMENTS.md), E-P0.

### E-INTERP

**Definition.** A pre-registered table that says, before B5 runs, how each possible B5 outcome will be read.

**Example.** If B5 scores at least as well as S\*, the typed-strategy claim retreats to auditability, attribution and seed stability. The table is committed before Stage 1 and frozen in the Stage-1 tag.

**Common mistake.** Deciding after the fact what a B5 result means. Without the table, almost any outcome could be described as support for the typed strategy.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), gates table and E-B5; [EXECUTION_PLAN.md](EXECUTION_PLAN.md), PREREG-1.

### Held-out ledger

**Definition.** An append-only record of every access to a held-out TB2 task id. It replaces the boolean held-out flag in the current code.

**Example.** Every call that names a TB2 task id goes through a task-id guard and appends a record. Before Stage 2 the only accepted purpose is an image pull by digest. The ledger's hash goes into each signed tag, so a reader can check that no TB2 agent episode ran before Stage 2. See [held-out set](#held-out-set).

**Common mistake.** Guarding a split name instead of the task ids. The current guard keys on the split name, so a held-out task reached through another task list would not be caught.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), LEDGER; [EXECUTION_PLAN.md](EXECUTION_PLAN.md), section 4; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M10.

---

## Systems

### Mixture of experts and active parameters

**Definition.** A mixture-of-experts (MoE) model has many expert sub-networks per layer but routes each token through only a few. *Total parameters* set the memory needed to hold the model; *active parameters* (those used per token) set most of the compute per token.

**Example.** The primary model, Qwen3.6-35B-A3B, has about 35B total parameters and, as the "A3B" in its name indicates, about 3B active per token. Gemma 4 26B-A4B has 25.2B total and 3.8B active. MoE is why little-coder could run the 35B model on an 8 GB-VRAM laptop: llama.cpp's `--n-cpu-moe N` keeps the expert weights of the first N layers in CPU RAM, and the laptop generated about 44 tokens per second.

**Common mistake.** Treating "3B active" as "fits like a 3B model". All 35B parameters must sit in GPU or CPU memory.

**Used in.** [SMALL_MODELS.md](SMALL_MODELS.md), sections 1.2 and 2; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M11 and M15.

### Q4_K_M quantisation

**Definition.** Q4_K_M is one of llama.cpp's 4-bit "k-quant" weight formats in GGUF files (GGUF is llama.cpp's model file format). It averages just under 5 bits per weight: llama.cpp's quantize README lists 4.89 bits per weight for Llama-3.1-8B ([link](https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md)).

**Example.** The unsloth UD-Q4_K_M file of Qwen3.6-35B-A3B is 22.13 GB (20.61 GiB); Ollama's `qwen3.6:35b-a3b-q4_K_M` tag is listed at 24 GB. As a check, 35B x 4.89 / 8 is about 21.4 GB (derived). The model, quantisation and file hash are pinned in `pins.lock`.

**Common mistake.** Comparing scores across quantisations or harnesses as if they were the same model. The vendor's 51.5% for Qwen3.6-35B-A3B and little-coder's 23.8% differ in harness, timeout, resources and hardware as well as precision.

**Used in.** [SMALL_MODELS.md](SMALL_MODELS.md), section 2.1; [LOCAL_MODELS.md](LOCAL_MODELS.md); [EXPERIMENTS.md](EXPERIMENTS.md), E-P0.

### KV cache

**Definition.** During generation, a transformer stores each past token's attention keys and values (the key-value, or KV, cache) so they need not be recomputed. Its size grows with context length and with the number of parallel sequences, and it competes with the weights for GPU memory.

**Example.** Qwen3.6-35B-A3B uses full attention in only 10 of its 40 layers (the rest are linear attention), with 2 KV heads of dimension 256. Its f16 KV cache is about 20 KiB per token: 1.25 GiB per 64k-token sequence. Estimated GPU memory with the Q4_K_M weights is about 23.4 GiB for one 64k slot, 24.7 GiB for two and 27.3 GiB for four. By contrast, the dense Nemotron-Terminal-32B needs about 256 KiB per token and does not fit a 24 GB GPU with one 32k slot. The plan pins q8_0 KV unless f16 fits with at least 1 GiB of headroom.

**Common mistake.** Sizing the GPU from the model file alone. A 40-step trajectory with 4,000-character observations already needs about 55k tokens of context.

**Used in.** [SMALL_MODELS.md](SMALL_MODELS.md), section 2; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M11 and M15.

### Tokens per second

**Definition.** Generation speed in output tokens per second for one sequence. Prompt processing (reading input tokens) is usually much faster than generation, so the two are measured separately.

**Example.** little-coder reports about 44 tokens/s for Qwen3.6-35B-A3B Q4_K_M on an 8 GB laptop with offload. A llama.cpp community benchmark gives 221.95 tokens/s for gpt-oss-20b on an RTX 4090. At 44 tokens/s, the repository client's default 120 s timeout allows at most about 5,280 generated tokens per call, which a reasoning model can exceed. The llama.cpp quantize README shows the gap between the two speeds: about 822 tokens/s prompt processing against 72 tokens/s generation for Llama-3.1-8B Q4_K_M.

**Common mistake.** Estimating episode time from generation speed alone. Agent episodes also spend time in container setup, command execution and verification: in the little-coder run, the verifier took 13.5% of trial time.

**Used in.** [SMALL_MODELS.md](SMALL_MODELS.md), section 2.2; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M11.

### llama.cpp slots and prompt cache

**Definition.** `llama-server` serves several requests at once through *slots* set by `-np` (parallel sequences). Each slot keeps its KV cache, so a request that repeats an earlier prompt prefix can reuse it (the *prompt cache*). Responses include a `timings` object with `prompt_n`, `cache_n`, `predicted_n` and their milliseconds.

**Example.** The plan sets Harbor's concurrent trials equal to `-np`. It sweeps at most 3 configurations that fit memory on the dev slice (at most 90 episodes) and pins the fastest one with at most 1 agent timeout in 30 trials. `cache_n` tells MCU which prompt tokens were reused. The llama.cpp README warns that `cache_prompt` (on by default) "can cause nondeterministic results", which is why CRN is not assumed to work.

**Common mistake.** Leaving `-np` on auto. The default is -1 (auto) with a unified KV cache, so the context per slot, and with it the cost and the overflow rate, can change between machines.

**Used in.** [LOCAL_MODELS.md](LOCAL_MODELS.md); [EXPERIMENTS.md](EXPERIMENTS.md), E-P0; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M4 and M11.

### Harbor

**Definition.** Harbor is the harness that runs Terminal-Bench tasks: it builds or pulls each task's Docker image, runs an agent against the container, then runs the task's tests and records a reward. It does not serve the model; the agent reaches a model server through an API endpoint.

**Example.** The plan runs a custom agent in the Harbor process (loaded by `import_path`, as little-coder did), llama.cpp on the same host and task containers in local Docker. In Harbor v0.23.0 the agent's `setup` and `run` are async. `run` is wrapped in a timeout that raises `AgentTimeoutError`, the job default is 4 concurrent trials, and the tests are uploaded only at verification. Harbor also ships an Oracle agent that runs the reference solution with no model, used to check TB-Pro tasks. The proposed pin is v0.23.0; the latest tag on 2026-10-20 is v0.24.0, and the repository moved to `harbor-framework/harbor`.

**Common mistake.** Relying on visible tests inside the agent loop. Harbor uploads the tests only at verification, so unless they are baked into the image, "run visible tests" checks have nothing to run.

**Used in.** [PHASE0_CHECKLIST.md](PHASE0_CHECKLIST.md); [LOCAL_MODELS.md](LOCAL_MODELS.md); [EXPERIMENTS.md](EXPERIMENTS.md), G-INFRA; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M11.

### Terminus 2

**Definition.** Terminus 2 is the Terminal-Bench authors' neutral reference agent, used with many models in the Terminal-Bench 2.0 paper. Scores are always for a model *and* an agent harness together.

**Example.** Qwen's vendor figure of 51.5% for Qwen3.6-35B-A3B used Harbor with Terminus-2, a 3-hour timeout and 32 CPUs / 48 GB RAM per task. little-coder's laptop run with its own agent scored 106/445 = 23.8% (the leaderboard and README report 24.6%; that denominator could not be reproduced). This project uses its own Harbor agent, so its S0 is compared with the little-coder run only descriptively: 100/410 = 24.4% on the 82 tasks unchanged between the two task commits.

**Common mistake.** Treating a vendor score as the starting score to expect. The same model's score more than halves under a different harness and settings.

**Used in.** [SMALL_MODELS.md](SMALL_MODELS.md), sections 1.1-1.2; [EXPERIMENTS.md](EXPERIMENTS.md), E3-REF; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M15.

### Terminal-Bench 2.0 vs TB-Pro vs 2.1

**Definition.** Three related task sets. **Terminal-Bench 2.0** (TB2) has 89 tasks, each a Docker image with an instruction, tests and a reference solution. **Terminal-Bench 2.1** is a revision: the authors say it fixes issues in 28 of the 89 TB2 tasks. **terminal-bench-pro** (TB-Pro, `alibaba/terminal-bench-pro`) is a separate set of 200 public tasks in the same format. The current "continuous" Terminal-Bench is version 4.0, with 66 tasks and an 8-hour agent timeout.

**Example.** The project pins TB2 at commit `2fd12b8`, whose tasks use prebuilt amd64 images (48.98 GB compressed in total). Between little-coder's commit `69671fb` and this pin, 8 commits changed 7 tasks; one is titled "Various task fixes for TB2.1". TB-Pro ships no prebuilt images, uses an older `version = "1.0"` task schema, sets a 3,600 s agent timeout on all tasks, and has Apache-2.0 only in its Hugging Face metadata. So the plan confirms its licence before use.

**Common mistake.** Mixing versions in one comparison. A result on TB2 at one commit is not directly comparable with 2.1, 4.0 or a different commit.

**Used in.** [PRIOR_WORK.md](PRIOR_WORK.md), section 2; [PHASE0_CHECKLIST.md](PHASE0_CHECKLIST.md); [EXPERIMENTS.md](EXPERIMENTS.md), P-M2; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M2.

### Egress allowlist

**Definition.** A network policy that blocks all outbound traffic from a container except to listed hosts. Harbor offers three modes: public, no-network and allowlist. On Docker, an egress-control sidecar enforces the allowlist and needs host nftables support. There is no denylist mode.

**Example.** For TB-Pro runs only, the Oracle agent runs each task under an allowlist that starts from package hosts (PyPI, Debian/Ubuntu mirrors, npm, crates.io, CRAN). Hosts are added only where an oracle run fails without them. The result ships as a pinned, hashed fork that changes only the agent network lines, with a DNS sinkhole for benchmark domains. In Harbor, `extra_allowed_hosts` is ignored under public, merged under allowlist, and turns no-network into allowlist. TB2 keeps its upstream `allow_internet = true` so that results stay comparable with public numbers, and is audited instead (see [contamination](#contamination)).

**Common mistake.** Trying to block "just the benchmark's site". Without a denylist mode, blocking must be an allowlist or a DNS sinkhole outside Harbor.

**Used in.** [EXPERIMENTS.md](EXPERIMENTS.md), E-NET and E3-AUDIT; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M10.

### Step and token budgets

**Definition.** Hard limits on an episode set by the experimenter: maximum agent steps, maximum generated tokens, and a wall-clock timeout. Adaptation cannot edit them, or it could buy success by spending more.

**Example.** Planned budgets: max_steps = 60 (a logged change from S0's committed 40) and at most 64k generated tokens per episode, counted from model-reported output tokens and including reasoning. B1 shares its episode cap across retries, judge, and reflection calls. Wall-clock is only a backstop, with Harbor's agent timeout multiplier set to 2 for all arms. For an approximately leaderboard-comparable number, S0 trials are censored at 1x the task timeout using the logged agent time. In the little-coder run, 1 of 8 timed-out trials still passed. Censoring turns that one pass into a failure, so it biases the score down by about 1/445 = 0.2 pp (derived).

**Common mistake.** Using wall-clock as the binding limit. A faster GPU would then solve more tasks, and results would depend on hardware rather than strategy.

**Used in.** [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 3.1; [EXPERIMENTS.md](EXPERIMENTS.md), G-INFRA and E3-LB; [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md), M11.
