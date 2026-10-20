# Prior work and benchmarks for Project 2

Checked on 2026-10-02 with web search and fetch, as background for [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md). Every entry below has a URL that was opened during the check. "Verified" means the title, authors and date were read from that page, usually the arXiv abstract page. It does not mean the full paper was read. Most "left open" judgements in section 1 come from abstracts and are marked as inference. Anything that could not be confirmed says so.

**What changed (updated 2026-10-20).** A claim-by-claim re-check and a new literature search were done on 2026-10-20. The changes are:

- **Section 1.1 is rewritten** around a 2026 line of work on harness self-evolution, much of it on Terminal-Bench 2.0. This line was missing from the 2026-10-02 version and is now the closest prior work. The earlier section 1.1 is kept, with corrections, as section 1.3.
- **The "do not cite without checking" list** at the end of section 1.2 is resolved. All eight papers were opened.
- **New section 1.4** covers test-time compute, cost-aware evaluation, efficiency measures and agent capability assessment.
- **Corrections** found in the re-check are marked "(corrected 2026-10-20)". Earlier verified content is otherwise unchanged.
- [LITERATURE_MAP.md](LITERATURE_MAP.md) has the cluster diagram, the 25 key papers with the experiments they bear on, and the comparison matrix that will become Table 1 of paper 1.

---

## 1. Closest prior work

Every paper here was opened on its arXiv abstract page. "Left open" is inferred from the abstract unless stated otherwise. The full texts still need reading before any of these is cited in a paper, since a paper may have, for example, a cost-matched baseline that the abstract does not mention. RQ1–RQ4 refer to the research questions in [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 1.

Papers added on 2026-10-20 were also searched in their HTML full text for baselines, splits, models and ablations. Only Self-Harness was read in full. An absence such as "no best-of-N baseline" means "not found in a keyword search of the full text".

### 1.1 Closest to Project 2: harness self-evolution on terminal tasks (rewritten 2026-10-20)

**Positioning.** Between March and October 2026 a group of papers appeared that improve the *harness* around a frozen model from the agent's own failures. The harness is the prompts, tools, control flow, memory and context handling around the model. Most of these papers evaluate on Terminal-Bench 2.0 (TB2) or its revision TB2.1, which fixes 28 of the 89 tasks. This cluster is now the closest prior work, closer than Hyperagents or AgentSquare (section 1.3).

The most direct threat is Self-Harness. It already shows a frozen Qwen3.5-35B-A3B improving its own harness on TB2, with gains on held-out tasks. An evaluation study, *Rethinking the Evaluation of Harness Evolution for Agents*, also already compares harness evolution against matched-budget best-of-N sampling and sequential refinement on TB2.1, with frontier API models. So paper 1 is not framed as a new kind of self-improving agent, nor as the first compute-matched comparison. It is framed as that comparison for a typed, compiled strategy of a small, locally served model, on held-out tasks, with cost per task for every arm and the enforced-versus-advised contrast. The contribution sentence, fixed on 2026-10-20, is:

> A pre-registered, compute-matched test of whether adapting a typed, compiled strategy of a small, locally served model on Terminal-Bench beats a fixed strategy, random edits, reflection-retry and best-of-N, with cost per task reported for every arm and mechanism evidence (enforced-vs-advised contrast, leave-one-out attribution over changed strategy-dimension groups).

The paper-1 claims follow the pre-registered test order. The adapted strategy S\* is compared first with the base strategy S0, then with random edits (B4). Then it is compared with reflection-retry (B1) and with pooled best-of-N at matched per-task compute; these two come last. All four tests are two-sided, and "beats" is claimed only when a test rejects and its confidence interval excludes zero. Mechanism evidence (enforced versus advised, leave-one-out attribution) is exploratory.

**What paper 1 does not claim:**

- a "first" self-improving harness on TB2, or a first one for small models;
- the first compute-matched comparison of harness adaptation with test-time sampling or refinement on Terminal-Bench (2607.12227 ran one with frontier models);
- the first typed or frozen-weight harness adaptation of a small self-hosted model on Terminal-Bench (MetaRSI's Harness-RSI arm);
- the first adaptation on a task source disjoint from TB2 with TB2 used only for evaluation (ModularRSI);
- gains from a second-order loop (planned for paper 2, pending confirmation with Prof. Abdelrazek);
- transfer across benchmark families or across models;
- that a typed strategy beats code;
- that diagnosis beats random search in general.

The typed strategy space is presented as a deliberate restriction of code space. It is chosen for compiled enforcement, attribution and auditability.

**Papers in the cluster.** Entries give what was read. "Left open" items are checked against the HTML full text by keyword search unless marked as inference. The comparison matrix is in [LITERATURE_MAP.md](LITERATURE_MAP.md), section 4.

1. **Self-Harness: Harnesses That Improve Themselves**. Hangfan Zhang, et al. arXiv 2606.09498, 8 Jun 2026 (v3 20 Aug 2026). https://arxiv.org/abs/2606.09498
   - **What it does.** A fixed model improves its own harness in three stages: Weakness Mining, Harness Proposal (minimal edits tied to failures) and Proposal Validation (accept only after regression testing). No stronger external agent is used. The initial harness is a Python file that configures a DeepAgent; edits are code diffs.
   - **Setting.** MiniMax M2.5, Qwen3.5-35B-A3B and GLM-5 on TB2, SWE-bench Verified and AppWorld. Qwen3.5-35B-A3B was served on four NVIDIA H200 GPUs.
   - **Results.** For Qwen3.5-35B-A3B on a fixed 64-task TB2 subset: overall 18.0% → 36.7%, held-in 15.1% → 36.0%, held-out 23.8% → 38.1%. The held-out rates fit 10/42 → 16/42 (21 tasks, 2 attempts each); these denominators are inferred, not printed in the paper.
   - **Left open.** Only the initial and final harnesses are compared. No best-of-N, reflection or cost-matched baseline, no token or cost figures, and no confidence intervals. The four retained Qwen edits (dependency prechecking, loop breaking, command-retry discipline, artifact-focused recovery) are merged with no per-edit contribution. Each model is evolved separately.
   - **Status.** Full HTML text read. Code is public at https://github.com/qzzqzzb/Self-Harness, with no licence file as of 2026-10-20.

2. **Rethinking the Evaluation of Harness Evolution for Agents**. Yike Wang, et al. arXiv 2607.12227, 14 Jul 2026 (v4 5 Oct 2026). https://arxiv.org/abs/2607.12227
   - **What it does.** Compares harness evolution (AHE with its retrieval agent disabled) with parallel sampling and sequential refinement under matched rollout budgets on TB2.1. Parallel sampling selects by a self-judge, or by unit tests when allowed. A second experiment splits TB2.1 into 45 training, 10 validation and 34 test tasks.
   - **Results.** With Claude Opus 4.6, GPT-5.4 and GPT-5.4 mini and no unit tests, parallel sampling raises average pass@1 from 68.2 to 72.3, while harness evolution does not beat direct sampling on average. On the held-out split the evolved harness is flat on average (+1.2, 0 and -1.4 points). Harness evolution does help on long-horizon games (ARC-AGI-3, EdgeBench).
   - **Left open.** Frontier API models only; free-form harness; no typed strategy and no small local model. Its sampling and refinement comparisons are on the searched tasks; its held-out split has no sampling baseline. Budgets are matched by rollout count and include the evolution rollouts, harness-modification cost is excluded, and results are means of two runs with no CIs.
   - **For us.** The closest precedent for our best-of-N and reflection comparisons. Paper 1 must cite it and say how it differs.

3. **Agentic Harness Engineering: Observability-Driven Automatic Evolution of Coding-Agent Harnesses (AHE)**. Jiahang Lin, et al. arXiv 2604.25850, 28 Apr 2026. https://arxiv.org/abs/2604.25850
   - **What it does.** Every harness component is a file; trajectories are distilled into a layered evidence corpus; each edit carries a self-declared prediction checked against the next round's outcomes.
   - **Results.** Ten iterations lift TB2 pass@1 from 69.7% to 77.0% with GPT-5.4, above Codex-CLI (71.9%). The frozen harness gives +5.1 to +10.1 percentage points (pp) on TB2 across three other model families. Ablations place the gain in tools, middleware and long-term memory rather than the system prompt; the abstract suggests that "factual harness structure transfers while prose-level strategy does not".
   - **Left open.** Evolution and evaluation use the same 89 TB2 tasks. No best-of-N baseline. Attribution is per component file, not per typed strategy dimension.

4. **Meta-Harness: End-to-End Optimization of Model Harnesses**. Yoonho Lee, et al. (incl. Omar Khattab, Chelsea Finn). arXiv 2603.28052, 30 Mar 2026. https://arxiv.org/abs/2603.28052
   - **What it does.** Searches over harness code. The proposer (Claude Code with Opus 4.6) reads the code, scores and traces of all earlier candidates through a filesystem. The base model is frozen.
   - **Results.** On TB2: 76.4% with Opus 4.6 and 37.6% with Haiku 4.5, above the hand-engineered harnesses compared. On maths, one harness gains 4.7 points on average across five held-out models.
   - **Left open.** Its "Best-of-N" is a compute-matched control for search, used on text classification only, not on TB2. On TB2, search and final evaluation use the same 89 tasks.

5. **MemoHarness: Agent Harnesses That Learn from Experience**. Yue Huang, et al. arXiv 2607.14159, 14 Jul 2026. https://arxiv.org/abs/2607.14159
   - **What it does.** Six control dimensions (context assembly, tool interaction, generation control, orchestration, memory management, output processing) in a structured policy file with text instructions. It adapts the harness to each case at test time from retrieved experience.
   - **Results.** On an 89-task Terminal-Bench suite with an 80/20 split (18 held-out tasks), 0.806 against 0.722 for the strongest product-harness baseline, as point estimates. Search uses GPT-5.3-Codex.
   - **Left open.** No best-of-N, reflection or cost-matched baseline; no per-dimension ablation; no confidence intervals. The abstract leaves statistical robustness and component attribution to future work. It does not say which parts are code and which are prompt text.

6. **ModularRSI: Modular and Generalizable Recursive Harness Self-Improvement**. Siwei Wu, et al. arXiv 2609.14857, 14 Sep 2026 (v2 9 Oct 2026). https://arxiv.org/abs/2609.14857
   - **What it does.** Recursive self-improvement (RSI) of a harness split into five modules (Agent Loop, Tool Use, Observation Management, Context Management, Task Completion Detection). The modules evolve separately and are then merged. It evolves on 2,000 curated tasks disjoint from the test benchmarks.
   - **Results.** With DeepSeek-V4-Flash-Preview, TB2 accuracy rises from 47.57% to 52.43%, above Meta-Harness (49.44%) and AHE (49.81%) under one benchmark-disjoint protocol with matched evolution budgets.
   - **Left open.** No best-of-N baseline. Ablations remove parts of the method, not individual modules. Its modules are close to our strategy dimensions, so it threatens a "dimension-wise structure" claim.

7. **RRSI: Regularized Recursive Self-Improvement of Agent Harnesses**. Peng Xia, et al. arXiv 2609.24972, 21 Sep 2026 (v3 4 Oct 2026). https://arxiv.org/abs/2609.24972
   - **What it does.** Limits how many edits a candidate may bundle (an annealed budget), screens out benchmark-specific proposals with a critic, and prunes changes that stopped paying for themselves. The policy model is frozen.
   - **Results.** Across eight benchmarks including TB2.1, up to +6.0 points on the evolve split and up to +4.3 on five out-of-distribution benchmarks, with 30% fewer policy tokens than unregularised evolution.
   - **Left open.** Frontier models (Claude Opus 4.8, Gemini 3.5 Flash) only. No best-of-N baseline.

8. **MetaRSI / RSI2: A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems Themselves**. Zihan Tan, et al. (31 authors). arXiv 2609.06396, 6 Sep 2026. https://arxiv.org/abs/2609.06396
   - **What it does.** Three typed operators share one loop kernel: Data-RSI, Harness-RSI (edits a five-slot scaffold under a typed patch, without touching weights) and Model-RSI (training of low-rank LoRA adapters). A meta-level policy revises the operator schedule.
   - **Results.** On a self-hosted Qwen3.5-35B-A3B, with sealed held-out splits of TB2.1 and SWE-bench Pro, identical budgets for all conditions and five seeds, the scheduled composition beats the best single operator and a hand-fixed pipeline.
   - **Left open.** In the main setting Model-RSI changes the weights; only the Harness-RSI-only condition keeps them frozen (23.6 to 29.4 on TB2.1). Baselines are other improvement schedules, not test-time best-of-N or reflection. Attribution is per operator, not per scaffold slot. Its typed slots overlap our typed strategy, so it must be cited.

9. **Mixture of Self-Improving Branches For Agent Harness Optimization**. Haoyu Dong, et al. arXiv 2609.37834, 29 Sep 2026. https://arxiv.org/abs/2609.37834
   - **What it does.** Branches with their own development subsets and proposal guidance; a router sends each input to one branch head, chosen on development data only.
   - **Results.** +11.6% relative over Meta-Harness on TB2 (30 development, 58 held-out tasks, Claude Sonnet 4.5), +34.8% on Olympiad-level maths and +3.8% on SWE-bench Lite.
   - **Left open.** Total token use differs between methods, as the authors note. No best-of-N baseline. It is the closest work to per-task strategy switching (meeting item 5).

10. **SEAGym: An Evaluation Environment for Self-Evolving LLM Agents**. Congjie Zheng, et al. arXiv 2606.17546, 16 Jun 2026. https://arxiv.org/abs/2606.17546
    - **What it does.** Turns Harbor-compatible benchmarks into self-evolution sources with training batches, frozen update-validation, held-out in- and out-of-distribution views, replay and cost records.
    - **Results.** On TB2 and the HLE benchmark with DeepSeek-V4-Flash it compares ACE, Training-Free GRPO and AHE. Frequent updates may fail to improve held-out performance, and useful intermediate snapshots may collapse later.
    - **For us.** Supports a strict held-out separation and choosing the final strategy on a separate confirmation set.

11. **Task-CoEvolve: Efficient Harness Optimization via Adaptive Validation Task Selection**. Atsuyuki Miyai, et al. arXiv 2608.20169, 20 Aug 2026. https://arxiv.org/abs/2608.20169
    - **What it does.** Picks validation tasks by variance-weighted sampling of past outcomes, so evaluation focuses on tasks where candidates disagree.
    - **Results.** Matches full-set search with 80% fewer evaluations, on online text classification and TB2.1. On TB2.1 with Qwen3.6-35B-A3B, the starting harnesses score 34.8% (Terminus 2) and 32.6% (Terminus-KIRA). Search and final evaluation use the same 89 tasks.
    - **For us.** Supports a validation pool made of contested tasks.

12. **Harness Updating Is Not Harness Benefit: Disentangling Evolution Capabilities in Self-Evolving LLM Agents**. Minhua Lin, et al. arXiv 2605.30621, 28 May 2026. https://arxiv.org/abs/2605.30621
    - **Results.** Harness-updating ability is flat in base capability: updates written by Qwen3.5-9B give gains comparable to those by Claude Opus 4.6. Harness benefit is non-monotonic: weak models gain little because they fail to activate or to follow harness artifacts. On SkillsBench the harness-following rate is 0.142 for Qwen3-32B and 0.757 for Opus 4.6.
    - **Left open.** No Terminal-Bench; no test of enforcing harness content in code. This motivates our enforced-versus-advised experiment.

13. **HarnessBank: Semantic Gene-Bank Search with Gated Verification for Agent-Harness Self-Evolution**. Xiaotian Luo, et al. arXiv 2607.13683, 15 Jul 2026. https://arxiv.org/abs/2607.13683
    - A separate evolver agent, a bank of diverse harnesses and gated screening. +5.1% to 15.4% on seven benchmarks. Cross-model experiments indicate that the gains come from model-specific evolution, not one universal harness (abstract only).

14. **SelfSearch: Reward-Free Search for Self-Improving Agents**. Jungwoo Yang, et al. arXiv 2609.37968, 29 Sep 2026. https://arxiv.org/abs/2609.37968
    - Self-modification from records of earlier attempts, without downstream reward during search. Up to +11.2 pp on TB2.1; 82.0% on TB2.1 with DeepSeek V4 Flash for $4.03 of search cost (abstract only).

15. **It's Not the Capability: Harness Sensitivity Is Non-Monotone Across LLM Agent Tiers**. Yong-eun Cho. arXiv 2605.26731, 26 May 2026. https://arxiv.org/abs/2605.26731
    - Six models under light, balanced and strict harnesses on a 24-task synthetic benchmark (432 runs). The abstract does not say whether any condition enforces behaviour in code, so it does not pre-empt the enforced-versus-advised experiment.

16. **AI4AI at Test-Time: Strong-to-Weak Capability Transfer via Harnesses**. Cheng Qian, et al. arXiv 2608.12307, 12 Aug 2026. https://arxiv.org/abs/2608.12307
    - A strong builder model writes harnesses for weaker targets on four Theory-of-Mind benchmarks, without parameter updates. Average target performance rises from 0.49 to 0.91. Gains are attributed to moving unstable model reasoning into deterministic code.

17. **Contrasts in which weights change.**
    - *Self-Evolving Coding Agents via Harness-Policy Optimization* (Self-HPO). Zhepei Wei, et al. arXiv 2610.22791, 16 Oct 2026. https://arxiv.org/abs/2610.22791. Alternates harness search and reinforcement learning (RL) on Qwen3.5-35B-A3B.
    - *Tmax: A simple recipe for terminal agents*. Hamish Ivison, et al. arXiv 2606.23321, 22 Jun 2026. https://arxiv.org/abs/2606.23321. An outcome-only RL recipe reaching 27% on TB2 with 9B parameters; data, models and code are released. Relevant as a candidate model, not as a method.

**Seen in a 2026-10-20 search report but not checked by us. Do not cite without checking:** 2607.15524 (Recursive Harness Self-Improvement), 2608.09096 (Evo-Bench), 2608.06301 (HarnessOpt-Bench), 2605.23019 (PACE), 2605.25430 (CODESKILL), 2609.04128 (Environment Evolution for Terminal Agents), 2610.15150 (Harmony Harness), 2610.18813 (Self-Evolving Agent Harness), 2610.13025 (Evo²), 2610.26676 (Which Model for Which Role? Cost-Efficient Pareto Recommendation for LLM Agentic Workflows), 2609.32459 (Beyond the Model), 2609.24974 (Harness-Zero), 2602.12670 (SkillsBench), 2605.24117 (SkillEvolBench), 2505.19435 (Route to Reason), 2608.26195 (Cost-Utility Alignment in LLM Agent Trajectories: Profiling, Attribution, Diagnosis, Adaptation, and Evaluation; abstract not read).

**Assessment (updated 2026-10-20)**

What is already covered by others:

- Frozen-model harness evolution on TB2, including held-out gains with Qwen3.5-35B-A3B (Self-Harness).
- Structured or modular harnesses (AHE, ModularRSI, MemoHarness) and typed operators on a self-hosted Qwen3.5-35B-A3B on TB2.1, with frozen weights only in its harness-only condition (MetaRSI).
- Component ablations (AHE) and cross-model transfer (AHE, ModularRSI, RRSI, MemoHarness).
- Matched-budget sampling baselines on TB2.1, with frontier models (Rethinking the Evaluation of Harness Evolution).
- Per-input routing between evolved harnesses (Mixture of Self-Improving Branches).
- Benchmark-disjoint adaptation with TB2 used only for evaluation, with repeated runs and paired task-bootstrap CIs (ModularRSI; 2,000 external evolution tasks).

What we did not find in the papers checked:

- a strategy whose fields are each compiled into controller behaviour with a test, or labelled text-only, plus a test of enforcement against the same content given as advice;
- a small, locally served model on Terminal-Bench compared at matched per-task compute with reflection-retry and best-of-N, with cost per task for every arm and a pre-registered analysis;
- a leave-one-out reversion of the changed dimension groups of one adapted typed strategy, as exploratory mechanism evidence (component ablations already exist in AHE; ours differs in unit, not in kind).

None of the harness-evolution methods checked reports a test-time, cost-matched best-of-N comparison on a terminal benchmark. The evaluation study in entry 2 does, with frontier API models. Our distinct part is that test on a small, locally served model with a typed, compiled strategy, with cost per task for every arm and the enforced-versus-advised contrast. This is an inference from the papers listed, not proof that no such paper exists.

### 1.2 Closest prior work to the backtracking idea

**Step-level revision in reasoning**

1. **LLMs cannot find reasoning errors, but can correct them given the error location**. Gladys Tyen, Hassan Mansoor, Victor Cărbune, et al. arXiv 2311.08516. Findings of ACL 2024. https://arxiv.org/abs/2311.08516
   - **What it does.** Shows that LLMs are poor at *locating* the wrong step, but correct it well once told where it is. It releases the BIG-Bench Mistake dataset.
   - **Implication:** in a propose → check → revise loop, the "check" step is the bottleneck. It has to be measured separately.

2. **Toward Adaptive Reasoning in Large Language Models with Thought Rollback**. Sijia Chen, Baochun Li. arXiv 2412.19707. ICML 2024 (confirmed by the arXiv comment, 2026-10-20). https://arxiv.org/abs/2412.19707
   - **What it does.** Error analysis, then rollback to the mistaken earlier thought, then revision; this is prompting only, mostly on maths.
   - **This is already very close to step-level backtracking as a standalone method, in the pure-reasoning setting.**

3. **Stepwise correction (StepCo)**. Zhenyu Wu, Qingkai Zeng, Zhihan Zhang, et al. arXiv 2410.12934. https://arxiv.org/abs/2410.12934
   - **What it does.** Alternates verify and revise using a process-supervised verifier on maths. It reports beating best-of-N at lower token cost.

4. **To Backtrack or Not to Backtrack: When Sequential Search Limits Model Reasoning**. Tian Qin, David Alvarez-Melis, Samy Jelassi, Eran Malach. arXiv 2504.07052. COLM 2025 (venue confirmed 2026-10-20). https://arxiv.org/abs/2504.07052
   - **What it does.** Finds that sequential backtracking loses to parallel sampling on one task (Countdown) and wins on another (Sudoku).
   - **Implication:** any backtracking result needs an **equal-compute best-of-N** baseline.

5. **Decomposing LLM Self-Correction: The Accuracy-Correction Paradox and Error Depth Hypothesis**. Yin Li. arXiv 2601.00828, first submitted 24 Dec 2025 (corrected 2026-10-20: single author, 2025 not 2026). https://arxiv.org/abs/2601.00828
   - **What it does.** Separates detection, localisation and correction, on GSM8K-Complex with three LLMs (500 problems each). It reports that giving location hints *hurt* the models it tested. The hints were generated by a model, not taken from ground truth.
   - The tension with Tyen et al. is our reading; the paper does not cite Tyen et al.
   - Cite carefully.

6. **Trained backtracking and self-correction** (all change weights, so they are not directly comparable to a prompting method):
   - Step Back to Leap Forward / Self-Backtracking: https://arxiv.org/abs/2502.04404
   - Stream of Search: https://arxiv.org/abs/2404.03683
   - SCoRe (ICLR 2025): https://arxiv.org/abs/2409.12917
   - RISE (Recursive Introspection): https://arxiv.org/abs/2407.18219
   - S³cMath: https://arxiv.org/abs/2409.01524
   - Physics of Language Models Part 2.2: https://arxiv.org/abs/2408.16293
   - Let's Verify Step by Step (process supervision): https://arxiv.org/abs/2305.20050
   - Backtracking Improves Generation Safety (a token-level reset for safety): https://arxiv.org/abs/2409.14586

**Rollback in agents: the version of backtracking that fits Project 2**

7. **Rollback the World, Keep the Reflection: Rollback-Induced Reflection for Long-Horizon LLM Agents**. Yi Yu, Liuyi Yao, Yaliang Li, Enshu Wang, Libing Wu. arXiv 2609.18304, 16 Sep 2026. https://arxiv.org/abs/2609.18304
   - **What it does.** Restores execution to a selected prior state and carries forward knowledge distilled from the abandoned branch. Tested on ALFWorld, ScienceWorld and GAIA, with Qwen3-14B, DeepSeek-V3 and Qwen3.8-27B as backbones (from the HTML; corrected 2026-10-20).
   - **The closest existing work to "backtracking inside an agent".**

8. **AgentRewind: Recoverable Execution for Long-Horizon LLM Agents**. Yu Zhuang, et al. arXiv 2608.14380, Aug 2026. https://arxiv.org/abs/2608.14380
   - **What it does.** Checkpoints the agent's context and its environment together, plus a "rewind memory". Evaluated on its own MettleBench and also on Terminal-Bench 2.0 tasks (corrected 2026-10-20).

9. **TRAJDEBUG: Tracing Error Lifecycle to Identify Critical Failures in Long-Horizon Agent Trajectories**. Yunjia Qi, et al. arXiv 2608.06346, Aug 2026. https://arxiv.org/abs/2608.06346
   - **What it does.** Locates the early step that caused a failure, on τ²-bench and SWE-Bench Pro trajectories.
   - Relevant to Project 2's *failure-diagnosis* component.

10. **Systems support for rollback** (infrastructure, not methods):
    - Crab checkpoint/restore runtime: https://arxiv.org/abs/2604.28138
    - Planarian statepoints: https://arxiv.org/abs/2609.35366
    - Recoverability as a system primitive: https://arxiv.org/abs/2609.13672

**Assessment (inference)**

- As a standalone project, "step-level backtracking in reasoning" now has close prior work (Thought Rollback, StepCo, Tyen et al.) and cautions (Qin et al.; Decomposing LLM Self-Correction).
- It is more defensible as **one strategy dimension inside Project 2**: whether, when and how far an agent rolls back, with the locator's accuracy measured separately. Even there, Rollback-Induced Reflection and AgentRewind (Sep and Aug 2026) must be cited and compared against.
- *Update 2026-10-20.* Rollback versus restart moves to paper 2 by default. The rollback values of the recovery field are removed from the paper-1 edit space.

**Seen in search but not opened on 2026-10-02 (resolved 2026-10-20).** All eight were opened on their arXiv abstract pages on 2026-10-20.

| arXiv id | What it is | Status for us |
|---|---|---|
| 2608.04003 | *PAST-Bench: Benchmarking the Foundations of Recursive Self-Improvement in Personal Agents*, Shuhan Xue, et al., Aug 2026. 26 scenarios and 204 episodes with retained experience switched on and off; checks whether gains follow the intended save, retrieve and update pathway | Cite. Supports mechanism evidence (section 1.4) |
| 2607.07663 | *Recursive Self-Improvement in AI: From Bounded Self-Refinement to Autonomous Research Loops*, Mingguang Chen, et al., Jul 2026. A survey of 1,250 papers | Cite in related work. Our loop is "bounded self-refinement" in its terms |
| 2609.19526 | *Self Improvement via Fast Tree-search* (SIFT), Xinghong Fu, et al., Sep 2026. A pairwise LLM judge with a Bradley-Terry model ranks candidate self-modifications before full evaluation; Polyglot | A possible cheap screen for candidate selection; not adopted |
| 2608.20485 | *Terminal Agents: A Survey of AI Agents in Command-Line Environments*, Yi Bin, et al., Aug 2026. Argues that behaviour depends on model, interface, harness, runtime and environment together | Cite. Supports pinning runtime settings |
| 2602.08100 | *Emergent Search and Backtracking in Latent Reasoning Models*, Jasmine Cui and Charles Ye, Feb 2026. Backtracking inside a latent-reasoning transformer's hidden states | Not relevant. Dropped |
| 2608.24735 | *Meta^n: Recursive Self-Improvement through Emergent Depth*, Zae Myung Kim, et al., Aug 2026. Recursive meta-layers across eight benchmark families; the only system above zero on ARC-AGI-2 | Relevant to the second-order loop (paper 2). The abstract does not mention Terminal-Bench, so the earlier search snippet is not confirmed |
| 2608.07645 | *Mendel Gödel Machine: Recursive Self-Improving Coding Agents via Comparative Evolution*, Changzhi Liu, et al., Aug 2026. Edits an agent from its trajectories on several tasks at once, or from another lineage's trajectory; SWE-bench and Polyglot | Cite. Close to our aggregate-then-propose step |
| 2609.06396 | *MetaRSI / RSI2*, Zihan Tan, et al., Sep 2026 | Must cite. See section 1.1, entry 8 |

### 1.3 Self-improving agents, second-order loops and experience as text (moved from section 1.1 on 2026-10-20)

This was section 1.1 on 2026-10-02. The content is kept; corrections from the 2026-10-20 re-check are marked.

**Second-order: the improver is itself improved (the main threat to RQ3)**

1. **Hyperagents**. Jenny Zhang, Bingchen Zhao, Wannan Yang, Jakob Foerster, Jeff Clune, Minqi Jiang, Sam Devlin, Tatiana Shavrina. arXiv 2603.19461, 19 Mar 2026. https://arxiv.org/abs/2603.19461
   - **What it does.** Extends the Darwin Gödel Machine so that "the meta-level modification procedure is itself editable". The task agent and the meta agent are one editable Python program, and the model is frozen.
   - **Results.** It measures meta-level improvement with an imp@k metric, holding the meta agent fixed. It reports that meta-level improvements (persistent memory, performance tracking) "transfer across domains and accumulate across runs".
   - **Domains.** Coding (Polyglot), paper review, robotics reward design, maths grading.
   - **Left open** (from the paper's HTML version):
     - What gets edited is free-form code, not an interpretable strategy object.
     - No cost-matched best-of-N in the main results.
     - Attribution of gains is qualitative.
     - No long-horizon terminal tasks.
     - Parent selection and evaluation stay fixed.

2. **MetaSkill-Evolve: Recursive Self-Improvement of LLM Agents via Two-Timescale Meta-Skill Evolution**. Zefeng Wang, Minxi Yan, Jinhe Bi, Sikuan Yan, Volker Tresp, Yunpu Ma. arXiv 2607.05297, Jul 2026. https://arxiv.org/abs/2607.05297
   - **What it does.** Task skills evolve on a fast loop. A "meta-skill" evolves on a slower loop; it has five explicit components: Analyzer, Retriever, Allocator, Proposer, Evolver.
   - **Results.** Gains of +23.5, +16.1 and +1.9 points on OfficeQA, SealQA and ALFWorld (confirmed on the abstract page, corrected 2026-10-20). All components use one frozen backbone.
   - **Left open** (inference): no terminal tasks; it is unclear whether baselines are cost-matched or whether the gains are attributed to specific changes.
   - This is the closest *structured* two-timescale design.

3. **Meta-TTL: Meta-Learning Self-Improvement Policies for Language Agents**. Zhanzhi Lou, Hui Chen, Yibo Li, Qian Wang, Bryan Hooi. arXiv 2604.00830, Apr 2026. https://arxiv.org/abs/2604.00830
   - **What it does.** A bi-level setup. The inner loop is test-time learning across episodes; the outer loop meta-trains the *self-improvement policy* across tasks.
   - **Results.** Up to +23% in-distribution and +27% out-of-distribution over the strongest baseline, on Jericho, WebArena-Lite and τ²-bench. The third benchmark is named in v4 of the abstract; v1 listed only the first two (corrected 2026-10-20).
   - **Weights.** The HTML version states that the actor is a frozen LLM (Gemini-3-Flash) and that its system prompt is the only part that changes (confirmed 2026-10-20).
   - **Left open:** no terminal tasks. Attribution unclear.
   - This is a direct threat to the RQ2 and RQ3 framing: "learned improvement policies transfer".

4. **Hierarchical Self-Improvement: A Framework for Task-Specific Evolvable Agent Harnesses**. Tailin Zhou. arXiv 2608.08466, Aug 2026. https://arxiv.org/abs/2608.08466
   - **What it does.** Three levels: a task harness, an evolver that edits it, and a meta-evolver that edits the evolver's strategy. The model is frozen.
   - **Results.** Gains on BabyAI, Crafter, TextWorld and MiniHack. The abstract says there was no gain on tasks beyond the model's base capability.
   - **Left open:** games, not terminal tasks. The harness is code. Cost-matching and attribution are unclear.

5. **Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents**. Jenny Zhang, Shengran Hu, Cong Lu, Robert Lange, Jeff Clune. arXiv 2505.22954, May 2025. https://arxiv.org/abs/2505.22954
   - **What it does.** Keeps an archive of coding agents that rewrite their own code. SWE-bench went from 20.0% to 50.0% and Polyglot from 14.2% to 30.7%.
   - **Left open:** the self-modification procedure is fixed (Hyperagents addresses exactly this). Coding only. Attribution is narrative. Very expensive.

6. **Huxley-Gödel Machine**. Wenyi Wang, Piotr Piękos, Li Nanbo, et al. (Schmidhuber). arXiv 2510.21614, Oct 2025. https://arxiv.org/abs/2510.21614
   - **What it does.** Guides self-modification search by how well an agent's *descendants* perform. It reports fewer CPU-hours than earlier self-improvers on SWE-bench Verified and Polyglot (2.38x fewer on Verified); SWE-bench Lite is its transfer evaluation (corrected 2026-10-20).
   - **Left open:** it improves selection, not the proposer. It edits code.

7. **Gödel Agent: A Self-Referential Agent Framework for Recursive Self-Improvement**. Xunjian Yin, Xinyi Wang, Liangming Pan, et al. arXiv 2410.04444. ACL 2025 (confirmed by the arXiv comments, 2026-10-20). https://arxiv.org/abs/2410.04444
   - **What it does.** The agent rewrites its own logic, including the code that does the rewriting.
   - **Left open:** free-form edits. Improvement rate across rounds and per-dimension attribution are not measured.

8. **Self-Taught Optimizer (STOP): Recursively Self-Improving Code Generation**. Eric Zelikman, Eliana Lorch, Lester Mackey, Adam Tauman Kalai. arXiv 2310.02304. COLM 2024. https://arxiv.org/abs/2310.02304
   - **What it does.** An "improver" program is applied to improve itself.
   - **Left open:** small tasks and shallow recursion.

9. **Promptbreeder: Self-Referential Self-Improvement via Prompt Evolution**. Chrisantha Fernando, Dylan Banarse, Henryk Michalewski, Simon Osindero, Tim Rocktäschel. arXiv 2309.16797, Sep 2023. ICML 2024. https://arxiv.org/abs/2309.16797
   - **What it does.** From the abstract: "not just improving task-prompts, but it is also improving the mutation-prompts that improve these task-prompts". This is a second-order loop, on single-turn prompts.
   - **Left open:** no agents, tools or long horizons, and the second-order effect is not isolated as a faster improvement rate.

**First-order: automated agent and strategy design (main threat to the "explicit strategy object" claim)**

10. **AgentSquare: Automatic LLM Agent Search in Modular Design Space**. Yu Shang, Yu Li, Keyu Zhao, et al. arXiv 2410.06153, Oct 2024. ICLR 2025 (per the ICLR 2025 poster listing, seen in a search result). https://arxiv.org/abs/2410.06153
    - **What it does.** Searches a fixed modular design space of Planning, Reasoning, Tool Use and Memory modules, using module evolution and recombination plus a performance predictor. It reports +17.2% over the best human designs on six benchmarks.
    - **Left open:** the search procedure itself is not adapted, there are no terminal tasks, and no cost-matched best-of-N appears in the abstract.
    - **This is the nearest thing to "strategy as a searchable structured object".**

11. **Automated Design of Agentic Systems (ADAS / Meta Agent Search)**. Shengran Hu, Cong Lu, Jeff Clune. arXiv 2408.08435, Aug 2024. https://arxiv.org/abs/2408.08435
    - **What it does.** A fixed meta agent writes new agents in code, with an archive.
    - **Left open:** no second-order loop, free-form code, short tasks.

12. **AFlow: Automating Agentic Workflow Generation**. Jiayi Zhang, Jinyu Xiang, Zhaoyang Yu, et al. arXiv 2410.10762, Oct 2024. https://arxiv.org/abs/2410.10762
    - **What it does.** Monte Carlo tree search (MCTS) over code-represented workflows.
    - **Left open:** fixed search procedure, single-turn QA/code/math, no attribution.

13. **A Self-Improving Coding Agent**. Maxime Robeyns, Martin Szummer, Laurence Aitchison. arXiv 2504.15228, Apr 2025. https://arxiv.org/abs/2504.15228
    - **What it does.** The agent edits its own code: 17% → 53% on a random subset of SWE-bench Verified.

14. **Live-SWE-agent: Can Software Engineering Agents Self-Evolve on the Fly?** Chunqiu Steven Xia, Zhe Wang, Yan Yang, et al. arXiv 2511.13646, Nov 2025. https://arxiv.org/abs/2511.13646
    - **What it does.** Starts bash-only and evolves its own scaffold while solving each issue.
    - **Left open:** changes are not carried across tasks as a versioned strategy.

**First-order: learning from experience as text, memory or prompts (strongest RQ1 baselines)**

15. **GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning**. Lakshya A. Agrawal, et al. arXiv 2507.19457. ICLR 2026 (per the arXiv page). https://arxiv.org/abs/2507.19457
    - **What it does.** Reflects on trajectories in natural language, proposes prompt updates, and keeps a Pareto set of candidates. It reports beating GRPO with up to 35x fewer rollouts.
    - **Left open:** the optimiser is fixed and it optimises prompt text.
    - **The strongest "reflective adaptation" baseline.** The prose baseline B3 left the paper-1 plan on 2026-10-20, so GEPA is cited but not run. Prompts optimised with Qwen3 8B also helped GPT-4.1 Mini (HTML, checked 2026-10-20).

16. **Agentic Context Engineering (ACE): Evolving Contexts for Self-Improving Language Models**. Qizheng Zhang, Changran Hu, Shubhangi Upasani, et al. arXiv 2510.04618. https://arxiv.org/abs/2510.04618
    - **What it does.** An evolving "playbook" maintained by a generator, reflector and curator. It reports +10.6% on agent benchmarks, including AppWorld.
    - **Left open:** the playbook is free text, and there is no second-order loop.
    - **Added 2026-10-20.** The base model is DeepSeek-V3.1. Section 4.6 reports that ACE still works with a much weaker reflector. Like GEPA, it is cited but not run in paper 1.

17. **ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory**. Siru Ouyang, et al. arXiv 2509.25140. ICLR 2026 (per the arXiv comments). https://arxiv.org/abs/2509.25140
    - **What it does.** Distils strategies from self-judged successes and failures into a memory, on web and software-engineering tasks.
    - **Left open:** memory is the only dimension it adapts.

18. **Agent Workflow Memory (AWM)**. Zora Zhiruo Wang, Jiayuan Mao, Daniel Fried, Graham Neubig. arXiv 2409.07429. https://arxiv.org/abs/2409.07429
    - **What it does.** Induces reusable workflows; WebArena +51.1% relative. Reports cross-task and cross-domain generalisation.
    - **Left open:** web only.

19. **ExpeL: LLM Agents Are Experiential Learners**. Andrew Zhao, Daniel Huang, Quentin Xu, et al. arXiv 2308.10144. AAAI 2024. https://arxiv.org/abs/2308.10144
    - **What it does.** Extracts natural-language insights from training tasks and includes a transfer study.

20. **AutoManual: Constructing Instruction Manuals by LLM Agents via Interactive Environmental Learning**. Minghao Chen, et al. arXiv 2405.16247. NeurIPS 2024. https://arxiv.org/abs/2405.16247
    - **What it does.** Builds a structured, human-readable rule manual (ALFWorld).

21. **Dynamic Cheatsheet: Test-Time Learning with Adaptive Memory**. Mirac Suzgun, Mert Yuksekgonul, Federico Bianchi, et al. arXiv 2504.07952. https://arxiv.org/abs/2504.07952

22. **MetaReflection: Learning Instructions for Language Agents using Past Reflections**. Priyanshu Gupta, et al. arXiv 2405.13009. https://arxiv.org/abs/2405.13009

23. **TextGrad: Automatic "Differentiation" via Text**. Mert Yuksekgonul, et al. arXiv 2406.07496. https://arxiv.org/abs/2406.07496

24. **Trace is the Next AutoDiff (OptoPrime)**. Ching-An Cheng, Allen Nie, Adith Swaminathan. arXiv 2406.16218. https://arxiv.org/abs/2406.16218

25. **Voyager: An Open-Ended Embodied Agent with Large Language Models**. Guanzhi Wang, et al. arXiv 2305.16291. https://arxiv.org/abs/2305.16291
    - Learns a skill library; Minecraft only.

26. **Retroformer**. Weiran Yao, et al. arXiv 2308.02151. ICLR 2024. https://arxiv.org/abs/2308.02151
    - **Trains** a small retrospective model, so it does not satisfy "no weight changes". Included only as a contrast.

**Assessment as of 2026-10-02 (inference, based on abstracts; superseded by the assessment in section 1.1)**

The parts of Project 2 that are already well covered:

- Self-improving agents with a frozen model: DGM, ADAS, AFlow, GEPA, ACE.
- The second-order idea of improving the improver: Promptbreeder, Hyperagents, MetaSkill-Evolve, Meta-TTL, Hierarchical Self-Improvement.

The main novelty threats:

- **Hyperagents** threatens RQ3: it already measures meta-level improvement and cross-domain transfer.
- **Meta-TTL** threatens RQ2 and RQ3: it reports out-of-distribution transfer of a learned improvement policy.
- **AgentSquare** threatens the "structured strategy object" claim.
- A paper claiming "first agent that improves its own improvement mechanism" would not survive review.

None of the papers opened was seen to do all four of the following:

- (i) adapt a **typed, interpretable, versioned strategy object**, not free code or prompt text;
- (ii) compare against **fixed, reflection, best-of-N and GEPA/ReasoningBank-style baselines at matched cost**;
- (iii) report **held-out and cross-benchmark transfer and an improvement-rate-across-rounds measure for the second-order loop**, on **long-horizon terminal tasks**;
- (iv) **attribute gains to specific strategy dimensions by ablation**.

That conjunction is the defensible contribution. Its strength is rigour and interpretability, not a new paradigm. This is an inference from abstracts, and full texts must be checked before claiming it.

*Note (2026-10-20).* This conjunction no longer holds as written. The harness self-evolution papers in section 1.1 cover parts of (i), (iii) and (iv), and the evaluation study 2607.12227 covers part of (ii): a matched-budget best-of-N comparison on TB2.1 with frontier API models. The second-order loop and cross-benchmark transfer move to paper 2 by default, pending confirmation with Prof. Abdelrazek. The current positioning is in section 1.1.

### 1.4 Test-time compute, cost-aware evaluation, efficiency measures and capability assessment (added 2026-10-20)

Each entry was opened on its arXiv abstract page on 2026-10-20 unless stated otherwise.

**Test-time compute and best-of-N**

1. **Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters**. Charlie Snell, Jaehoon Lee, Kelvin Xu, Aviral Kumar. arXiv 2408.03314, Aug 2024. https://arxiv.org/abs/2408.03314
   - A compute-optimal allocation of test-time compute is more than 4x more efficient than a best-of-N baseline. In a comparison matched on floating-point operations (FLOPs), a smaller model with test-time compute can beat a 14x larger model on prompts where it has non-trivial success.
   - **For us.** The compute-equivalence ratio in the efficiency index asks the same question per task: how much best-of-N compute equals the adapted strategy.

2. **Large Language Monkeys: Scaling Inference Compute with Repeated Sampling**. Bradley Brown, et al. arXiv 2407.21787, Jul 2024. https://arxiv.org/abs/2407.21787
   - Coverage grows with the number of samples over four orders of magnitude. On SWE-bench Lite, DeepSeek-Coder-V2-Instruct goes from 15.9% with one sample to 56% with 250. Without automatic verifiers, majority voting and reward models plateau beyond several hundred samples.
   - **For us.** Best-of-N is only as good as its selector. The plan checks the judge before using it, and plots oracle pass@N only as a ceiling.

3. **Does Reinforcement Learning Really Incentivize Reasoning Capacity in LLMs Beyond the Base Model?** Yang Yue, et al. arXiv 2504.13837, Apr 2025. https://arxiv.org/abs/2504.13837
   - RL-trained models beat their base models at small k, but base models reach higher pass@k at large k.
   - **For us.** Report the net pass@k difference between the adapted and base strategies across k, not only pass@1.

**Cost-aware evaluation**

4. **AI Agents That Matter**. Sayash Kapoor, Benedikt Stroebl, Zachary S. Siegel, Nitya Nadgir, Arvind Narayanan. arXiv 2407.01502, Jul 2024. https://arxiv.org/abs/2407.01502
   - Argues for optimising cost and accuracy jointly, and for adequate holdout sets to avoid overfitting to benchmarks.

5. **Holistic Agent Leaderboard: The Missing Infrastructure for AI Agent Evaluation (HAL)**. Sayash Kapoor, et al. arXiv 2510.11977, Oct 2025. https://arxiv.org/abs/2510.11977
   - 21,730 agent rollouts across 9 models and 9 benchmarks, for about $40,000. Higher reasoning effort reduced accuracy in most runs. Log inspection found agents searching for the benchmark on Hugging Face instead of solving the task.
   - **For us.** Supports the cost-per-task table (meeting item 1) and a text search of held-out trials for benchmark names.

6. **Finding the Right Fit: Model-Harness Interactions across Agent Tasks**. Yixuan Li, et al. arXiv 2610.00917, 1 Oct 2026. https://arxiv.org/abs/2610.00917
   - 66 model and harness configurations on TUA-Bench, ALE-CLI and Terminal-Bench 4. Model rankings reverse across harnesses, a vendor's own harness is not reliably its best, and higher cost does not reliably buy a higher score.

**Intelligence and efficiency measures**

7. **ARC-AGI-3: A New Challenge for Frontier Agentic Intelligence**. ARC Prize Foundation. arXiv 2603.24621, Mar 2026. https://arxiv.org/abs/2603.24621
   - An interactive benchmark with efficiency-based scoring grounded in human action baselines. Considered for the efficiency index and not used.

8. **Artificial Analysis Intelligence Index**, methodology page, version 4.3.2. https://artificialanalysis.ai/methodology/intelligence-benchmarking
   - A weighted average of ten evaluations across four categories. It includes Terminal-Bench 4.0 (not 2.0) at 10% weight. This is reading (b) of meeting item 4; under that reading it belongs with the model-choice table in [SMALL_MODELS.md](SMALL_MODELS.md).

Chollet (2019) is in section 3.

**Agent capability assessment and mechanism evidence**

9. **Differential Assessment of Black-Box AI Agents**. Rashmeet Kaur Nayyar, et al. arXiv 2203.13236, AAAI 2022. https://arxiv.org/abs/2203.13236
   - Updates a known model of an agent after its behaviour drifts, using an active querying policy, at a cost the abstract describes as proportional to the drift.

10. **Autonomous Assessment of Generalizability of AI Agent Capabilities**. Daniel Bramblett, et al. arXiv 2512.16733, Dec 2025 (v4 14 Sep 2026). https://arxiv.org/abs/2512.16733
    - Learns symbolic, stochastic capability models of black-box AI systems by tree-search query synthesis. The abstract mentions foundation-model agents but does not name the systems evaluated.

    Entries 9 and 10 are background for a possible follow-up on capability assessment of strategy versions (paper 2). Nothing from them is planned for paper 1.

11. **PAST-Bench** (see the table at the end of section 1.2). Supports reporting whether a gain follows the intended mechanism, which paper 1 does with an arm that switches lessons and notes off.

12. **Agentic Abstention: Do Agents Know When to Stop Instead of Act?** Han Luo, Bingbing Wen, Lucy Lu Wang. arXiv 2606.28733, Jun 2026. https://arxiv.org/abs/2606.28733
    - Studies when an agent should stop acting, across web shopping, terminal environments and question answering. Background for a possible "give up" strategy field in paper 2.


---

## 2. Benchmarks

The architecture note ([ARCHITECTURE.md](ARCHITECTURE.md)) names SWE-bench Lite and WebArena. Both are heavy, and WebArena is not a terminal benchmark. The facts below come from the official pages listed. Where a number was not stated on any page that was opened, it says "not stated".

### Summary table

| Benchmark | Tasks | Pass/fail check | Setup weight | Fit for Project 2 (judgement) |
|---|---|---|---|---|
| **Terminal-Bench 2.0** | 89 | Tests inside the task's container check final state | One Docker image per task, run through the Harbor harness. Cloud sandboxes supported. Total disk not stated | **Best match** for "long-horizon terminal tasks" (the example in the project description) |
| Terminal-Bench 2.1 (added 2026-10-20) | 89 | Same | Same | Fixes 28 of the 89 TB2 tasks. Several 2026 harness papers report on it; scores are not directly comparable with TB2 |
| Terminal-Bench Pro (added 2026-10-20) | 200 public | Same format | One Docker image per task; contents to be checked in a CPU-only pilot | Adaptation pool in the paper-1 plan, pending approval |
| Terminal-Bench "continuous" (4.0 at time of writing) | 66 on the Harbor hub | Same | Same, plus a flat 8-hour agent timeout | Moving target; harder to reproduce |
| SWE-bench Lite / Verified | 300 / 500 | Repo unit tests in Docker | **≥120 GB disk, 16 GB RAM, 8 cores** (official). Modal / sb-cli cloud evaluation exist | Heavy, single domain (Python repos), likely in training data |
| SWE-bench Verified Mini | 50 | Same | About 5 GB instead of 130 GB | Cheap sanity check, but too small to split |
| WebArena | 812 | State/URL/string checks | Six self-hosted sites and services in Docker, map backend about 180 GB, AWS AMI with 1000 GB EBS, reset between runs | **Not suitable** on a shared machine; not terminal tasks |
| **AppWorld** | 750 (train 105 / dev 60 / test-normal 168 / test-challenge 417) | Database-state unit tests, including collateral damage | `pip install appworld`; **Docker optional** | **Best second family for transfer** |
| τ²-bench | retail 115, airline 50, telecom 114 | Database state, with an LLM-simulated user | `uv`, Python ≥3.12, no Docker mentioned | Alternative transfer family; user simulator adds noise and cost |
| InterCode (Bash/SQL/CTF) | Bash 200, SQL 1034, CTF 100 | Execution-based score 0–1 | Docker, small images | Short tasks, old: a smoke test only |
| ALFWorld / ScienceWorld | ALFWorld: split sizes not confirmed. ScienceWorld: 10 topics, 30 subtasks, about 7,200 variations (corrected 2026-10-20; 5,282 was not found in the paper or README) | Environment reward | Python (+Java for ScienceWorld), no Docker | Cheap, but text games, not terminal |
| OSWorld | 369 | Execution-based | Full desktop VMs | Not suitable |

### Details and sources

**Terminal-Bench 2.0**

Merrill, Shaw, Carlini, et al. "Terminal-Bench: Benchmarking Agents on Hard, Realistic Tasks in Command Line Interfaces". arXiv 2601.11868, Jan 2026. https://arxiv.org/abs/2601.11868. Site: https://www.tbench.ai. Harness: https://github.com/harbor-framework/harbor, docs at https://docs.harborframework.com/. Licence Apache-2.0.

Read directly from the paper PDF:

- **Task set.** 89 tasks selected from 229 crowd-sourced tasks. Each task has a Dockerfile, an instruction, tests and a reference solution.
- **Costs.** "Running Terminal-Bench 2.0 costs anywhere from one to a hundred dollars, depending on the model's price". "Most trials are completed in under 20 minutes, using fewer than 25 model calls and 10 million tokens". Extreme trials ran up to 2 hours and used nearly 100M tokens.
- **Protocol.** Each model–agent pair was run at least five times (32,155 trials in total).
- **Model scores.** By Table 2 (best agent per model), the bottom three are GPT-OSS-20B (3.4%), GPT-5-Nano (11.5%) and Gemini 2.5 Flash (17.1%); GPT-OSS-120B is fourth lowest (18.7%). Cheap models are therefore near the floor.
- **Contamination.** It relies on a canary string only, with no private test set.
- **Other benchmarks in the same format.** Appendix D lists 26 benchmarks adapted to the same format, including **AppWorld**, SWE-bench Verified and SWE-smith. So the primary and transfer benchmarks could run through one harness.
- **Agent scaffolds.** Terminus 2, the authors' neutral agent, and Mini-SWE-Agent were among the scaffolds used.

From tbench.ai and the Harbor hub:

- Terminal-Bench is now "a continuous benchmark" with semantic versioning (https://www.tbench.ai/news/terminal-bench-4-0). 4.0 "removed 8 tasks", "fixed 19 tasks", and sets "a flat agent timeout of 8 hours".
- The Harbor hub (https://hub.harborframework.com/datasets) lists `terminal-bench-2` (89), `terminal-bench-2-1` (89), `terminal-bench` (66), `terminal-bench-pro` (200) and `terminal-bench-science` (70).
- The Harbor docs list which sandbox backends support GPUs. We did not find a statement that any TB2 task needs a GPU.
- `terminal-bench-pro` (200 tasks) could enlarge the task pool, but its contents and weight were **not examined**.
- *Updated 2026-10-20.* Terminal Bench Pro was introduced in *Let It Flow: Agentic Crafting on Rock and Roll, Building the ROME Model within an Open Agentic Learning Ecosystem* (Weixun Wang, et al., arXiv 2512.24873, Dec 2025, https://arxiv.org/abs/2512.24873). The Hugging Face dataset `alibabagroup/terminal-bench-pro` shows 200 rows under Apache-2.0. Its card describes 400 tasks, 200 public and 200 private. The paper-1 plan now adapts on deduplicated TB-Pro tasks and holds out all 89 TB2 tasks.
- *Added 2026-10-20.* Terminal-Bench 2.1 was released "to fix issues in 28 of the 89 tasks in Terminal-Bench 2.0" (https://www.tbench.ai/news/terminal-bench-2-1).

Per-task resources are set in each task's `task.toml` `[environment]` block (for example, chess-best-move: `cpus = 1`, `memory_mb = 2048`, `storage_mb = 10240`). Harbor exposes `--override-cpus`, `--override-memory-mb` and `--override-storage-mb`. Not stated anywhere opened: total disk use, per-image sizes.

**SWE-bench**

Paper: https://arxiv.org/abs/2310.06770. Repo: https://github.com/SWE-bench/SWE-bench. Docs: https://www.swebench.com/SWE-bench/.

- **Requirements.** The README states "x86_64 machine with at least 120GB of free storage, 16GB of RAM, and 8 CPU cores".
- **Cloud evaluation.** `--modal true` (https://www.swebench.com/SWE-bench/guides/evaluation/) and sb-cli (https://www.swebench.com/sb-cli/). Free quotas were not found.
- **Lite size.** The HF card (https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite) gives 300 test + 23 dev. The swebench.com datasets page appeared to give a different figure. **Unresolved; the HF card figure is used here.**
- **Verified Mini.** 50 instances, "requires 5GB instead of 130GB of storage": https://huggingface.co/datasets/MariusHobbhahn/swe-bench-verified-mini.
- **Reported costs.** The HAL leaderboard for Verified Mini (https://hal.cs.princeton.edu/swebench_verified_mini) lists runs from about $5 to over $1,000. It is **not verified** whether these are totals per 50 tasks.

**WebArena**

- Repo: https://github.com/web-arena-x/webarena. Environment notes: https://github.com/web-arena-x/webarena/blob/main/environment_docker/README.md (six site and service sections: shopping, CMS, Reddit, GitLab, Wikipedia, map; map data about 180 GB, AMI with 1000 GB EBS, reset by recreating containers).
- WebArena-Verified (https://github.com/ServiceNow/webarena-verified) has smaller images and a 258-task hard subset. It is still multi-site and stateful (our inference, not stated in the README).

**AppWorld**

Trivedi, Khot, Hartmann, et al. "AppWorld: A Controllable World of Apps and People for Benchmarking Interactive Coding Agents". ACL 2024. https://arxiv.org/abs/2407.18901. Repo: https://github.com/StonyBrookNLP/appworld.

- **Scale.** 9 apps, 457 APIs, 750 tasks.
- **Baseline scores.** "GPT-4o solves only ~49% of our 'normal' tasks and ~30% of 'challenge' tasks".
- **Install.** `pip install appworld; appworld install; appworld download data`. The README says Docker is optional.
- **Splits.** Taken from the paper's HTML version (not re-checked): train 105 / dev 60 / test-normal 168 / test-challenge 417.
- **Costs.** From the paper (not re-checked): about $0.02–$1.33 per task with GPT-4o at mid-2024 prices on Test-Normal ($0.02 FullCodeRefl, $0.33 IPFunCall, $0.70 ReAct, $1.33 PlanExec).
- **Splitting caution.** Tasks come in groups of 3 per scenario, so split by scenario, not by task.

**τ-bench family**

- τ-bench: https://arxiv.org/abs/2406.12045. The README of https://github.com/sierra-research/tau-bench says it is outdated and points to tau3-bench; the repo is not archived (corrected 2026-10-20).
- τ²-bench: https://arxiv.org/abs/2506.07982 and https://github.com/sierra-research/tau2-bench. The paper reports about $40 for one trial over all domains with gpt-4.1 as both agent and user simulator.

**Others**

- InterCode: https://arxiv.org/abs/2306.14898, https://github.com/princeton-nlp/intercode
- ALFWorld: https://github.com/alfworld/alfworld
- ScienceWorld: https://arxiv.org/abs/2203.07540, https://github.com/allenai/ScienceWorld
- AgentBench: https://arxiv.org/abs/2308.03688
- OSWorld: https://github.com/xlang-ai/OSWorld
- mini-SWE-agent, a minimal bash-only agent scaffold: https://github.com/SWE-agent/mini-swe-agent

### API prices seen on 2026-10-02 (re-check before spending)

| Model | Input $/M tok | Cached input | Output $/M tok | Source |
|---|---|---|---|---|
| GPT-5-mini | 0.25 | 0.025 | 2.00 | https://developers.openai.com/api/docs/pricing |
| GPT-5-nano | 0.05 | 0.005 | 0.40 | same |
| gpt-oss-120b (Together AI) | 0.15 | n/a | 0.60 | https://www.together.ai/models/gpt-oss-120b |
| Claude Haiku 4.5 | 1.00 | 0.10 | 5.00 | https://platform.claude.com/docs/en/about-claude/pricing (seen during the check, not re-opened) |

### What this means for the benchmark choice (judgement)

- **SWE-bench Lite.** It is too heavy for a shared machine without cloud evaluation, and it is a single domain.
- **WebArena.** It is the heaviest option here and does not match the terminal-task example in the project description.
- **Recommended pairing:**
  - **Terminal-Bench 2.0 (pinned, 89 tasks)** as the primary benchmark, run in cloud sandboxes through Harbor rather than on a shared machine.
  - **AppWorld** as the transfer family. It needs no Docker, has built-in splits, and is listed among the 26 adapted benchmarks in the Terminal-Bench paper (Table 5). The Harbor main repository had no AppWorld adapter directory on 2026-10-20 (corrected 2026-10-20).
  - SWE-bench Verified Mini or a few InterCode tasks only as a smoke test.
- **Main risk.** 89 tasks is small once it is split into adaptation, selection, meta-training and held-out sets, and cheap models score low on it (see [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), sections 2 and 7).
- *Update 2026-10-20.* The paper-1 plan now adapts on deduplicated Terminal-Bench Pro tasks and keeps all 89 TB2 tasks for the final held-out run. This answers the main risk above and is pending Prof. Abdelrazek's approval (Q3 in [DECISIONS.md](DECISIONS.md#q3-task-pools-meeting-point-2)). AppWorld transfer moves to paper 2 by default.

---

## 3. Other works cited in the technical plan

- **On the Measure of Intelligence**. François Chollet. arXiv 1911.01547, Nov 2019. https://arxiv.org/abs/1911.01547
  - Defines intelligence as skill-acquisition efficiency: how much new skill a system gains per unit of experience and prior knowledge. The adaptation efficiency index in the technical plan (section 7.6, added 2026-10-15) is an operationalisation of this idea, to be confirmed with Prof. Abdelrazek.
  - The abstract also describes a formal definition that weighs scope, generalisation difficulty, priors and experience. The plan's index does not implement that formal measure. Related measures are in section 1.4.
- **Reflexion: Language Agents with Verbal Reinforcement Learning**. Noah Shinn, Federico Cassano, Edward Berman, et al. (last author Shunyu Yao). arXiv 2303.11366, Mar 2023. https://arxiv.org/abs/2303.11366
  - Agents "verbally reflect on task feedback" and keep reflections in an episodic memory buffer, with no weight updates. This is the basis of baseline B1.
  - Venue: NeurIPS 2023 is widely reported, but the arXiv page does not show it, so it is not verified here.
- **Representation Engineering: A Top-Down Approach to AI Transparency**. Andy Zou, Long Phan, Sarah Chen, et al. (includes Dan Hendrycks). arXiv 2310.01405, Oct 2023. No peer-reviewed venue seen. https://arxiv.org/abs/2310.01405
  - Reads and steers population-level representations inside the model. This is the "activation steering" sense of *steering*, which Project 2 does not use.
