# Prior work and benchmarks for Project 2

Checked on 2026-10-02 with web search and fetch, as background for [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md). Every entry below has a URL that was opened during the check. "Verified" means the title, authors and date were read from that page, usually the arXiv abstract page. It does not mean the full paper was read. Most "left open" judgements in section 1 come from abstracts and are marked as inference. Anything that could not be confirmed says so.

---

## 1. Closest prior work

Every paper here was opened on its arXiv abstract page. "Left open" is inferred from the abstract unless stated otherwise. The full texts still need reading before any of these is cited in a paper, since a paper may have, for example, a cost-matched baseline that the abstract does not mention. RQ1–RQ4 refer to the research questions in [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), section 1.

### 1.1 Closest to Project 2: frozen-model agents that improve their own procedure

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
   - **Results.** Gains of +23.5, +16.1 and +1.9 points on three environments (OfficeQA, SealQA and ALFWorld, according to a search snippet; not confirmed on the abstract page). All components use one frozen backbone.
   - **Left open** (inference): no terminal tasks; it is unclear whether baselines are cost-matched or whether the gains are attributed to specific changes.
   - This is the closest *structured* two-timescale design.

3. **Meta-TTL: Meta-Learning Self-Improvement Policies for Language Agents**. Zhanzhi Lou, Hui Chen, Yibo Li, Qian Wang, Bryan Hooi. arXiv 2604.00830, Apr 2026. https://arxiv.org/abs/2604.00830
   - **What it does.** A bi-level setup. The inner loop is test-time learning across episodes; the outer loop meta-trains the *self-improvement policy* across tasks.
   - **Results.** Up to +23% in-distribution and +27% out-of-distribution over the strongest baseline, on Jericho, WebArena-Lite and a third benchmark whose name could not be read from the fetched page.
   - **Left open:** whether model weights are frozen is not stated in the abstract (**could not verify**). No terminal tasks. Attribution unclear.
   - This is a direct threat to the RQ2 and RQ3 framing: "learned improvement policies transfer".

4. **Hierarchical Self-Improvement: A Framework for Task-Specific Evolvable Agent Harnesses**. Tailin Zhou. arXiv 2608.08466, Aug 2026. https://arxiv.org/abs/2608.08466
   - **What it does.** Three levels: a task harness, an evolver that edits it, and a meta-evolver that edits the evolver's strategy. The model is frozen.
   - **Results.** Gains on BabyAI, Crafter, TextWorld and MiniHack. The abstract says there was no gain on tasks beyond the model's base capability.
   - **Left open:** games, not terminal tasks. The harness is code. Cost-matching and attribution are unclear.

5. **Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents**. Jenny Zhang, Shengran Hu, Cong Lu, Robert Lange, Jeff Clune. arXiv 2505.22954, May 2025. https://arxiv.org/abs/2505.22954
   - **What it does.** Keeps an archive of coding agents that rewrite their own code. SWE-bench went from 20.0% to 50.0% and Polyglot from 14.2% to 30.7%.
   - **Left open:** the self-modification procedure is fixed (Hyperagents addresses exactly this). Coding only. Attribution is narrative. Very expensive.

6. **Huxley-Gödel Machine**. Wenyi Wang, Piotr Piękos, Li Nanbo, et al. (Schmidhuber). arXiv 2510.21614, Oct 2025. https://arxiv.org/abs/2510.21614
   - **What it does.** Guides self-modification search by how well an agent's *descendants* perform. Reported on SWE-bench Lite with fewer CPU-hours than earlier self-improvers.
   - **Left open:** it improves selection, not the proposer. It edits code.

7. **Gödel Agent: A Self-Referential Agent Framework for Recursive Self-Improvement**. Xunjian Yin, Xinyi Wang, Liangming Pan, et al. arXiv 2410.04444. ACL 2025 (per a search result, not verified). https://arxiv.org/abs/2410.04444
   - **What it does.** The agent rewrites its own logic, including the code that does the rewriting.
   - **Left open:** free-form edits. Improvement rate across rounds and per-dimension attribution are not measured.

8. **Self-Taught Optimizer (STOP): Recursively Self-Improving Code Generation**. Eric Zelikman, Eliana Lorch, Lester Mackey, Adam Tauman Kalai. arXiv 2310.02304. COLM 2024. https://arxiv.org/abs/2310.02304
   - **What it does.** An "improver" program is applied to improve itself.
   - **Left open:** small tasks and shallow recursion.

9. **Promptbreeder: Self-Referential Self-Improvement via Prompt Evolution**. Chrisantha Fernando, Dylan Banarse, Henryk Michalewski, Simon Osindero, Tim Rocktäschel. arXiv 2309.16797, Sep 2023. ICML 2024. https://arxiv.org/abs/2309.16797
   - **What it does.** From the abstract: "not just improving task-prompts, but it is also improving the mutation-prompts that improve these task-prompts". This is a second-order loop, on single-turn prompts.
   - **Left open:** no agents, tools or long horizons, and the second-order effect is not isolated as a faster improvement rate.

**First-order: automated agent and strategy design (main threat to the "explicit strategy object" claim)**

10. **AgentSquare: Automatic LLM Agent Search in Modular Design Space**. Yu Shang, Yu Li, Keyu Zhao, et al. arXiv 2410.06153, Oct 2024. ICLR 2025 (per a search result, not verified). https://arxiv.org/abs/2410.06153
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
    - **The strongest "reflective adaptation" baseline.**

16. **Agentic Context Engineering (ACE): Evolving Contexts for Self-Improving Language Models**. Qizheng Zhang, Changran Hu, Shubhangi Upasani, et al. arXiv 2510.04618. https://arxiv.org/abs/2510.04618
    - **What it does.** An evolving "playbook" maintained by a generator, reflector and curator. It reports +10.6% on agent benchmarks, including AppWorld.
    - **Left open:** the playbook is free text, and there is no second-order loop.

17. **ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory**. Siru Ouyang, et al. arXiv 2509.25140. https://arxiv.org/abs/2509.25140
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

**Assessment (inference, based on abstracts)**

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

### 1.2 Closest prior work to the backtracking idea

**Step-level revision in reasoning**

1. **LLMs cannot find reasoning errors, but can correct them given the error location**. Gladys Tyen, Hassan Mansoor, Victor Cărbune, et al. arXiv 2311.08516. Findings of ACL 2024. https://arxiv.org/abs/2311.08516
   - **What it does.** Shows that LLMs are poor at *locating* the wrong step, but correct it well once told where it is. It releases the BIG-Bench Mistake dataset.
   - **Implication:** in a propose → check → revise loop, the "check" step is the bottleneck. It has to be measured separately.

2. **Toward Adaptive Reasoning in Large Language Models with Thought Rollback**. Sijia Chen, Baochun Li. arXiv 2412.19707. ICML 2024 (per a search result, not verified). https://arxiv.org/abs/2412.19707
   - **What it does.** Error analysis, then rollback to the mistaken earlier thought, then revision; this is prompting only, mostly on maths.
   - **This is already very close to step-level backtracking as a standalone method, in the pure-reasoning setting.**

3. **Stepwise correction (StepCo)**. Zhenyu Wu, Qingkai Zeng, Zhihan Zhang, et al. arXiv 2410.12934. https://arxiv.org/abs/2410.12934
   - **What it does.** Alternates verify and revise using a process-supervised verifier on maths. It reports beating best-of-N at lower token cost.

4. **To Backtrack or Not to Backtrack: When Sequential Search Limits Model Reasoning**. Tian Qin, David Alvarez-Melis, Samy Jelassi, Eran Malach. arXiv 2504.07052 (COLM 2025 per a search result, not verified). https://arxiv.org/abs/2504.07052
   - **What it does.** Finds that sequential backtracking loses to parallel sampling on one task (Countdown) and wins on another (Sudoku).
   - **Implication:** any backtracking result needs an **equal-compute best-of-N** baseline.

5. **Decomposing LLM Self-Correction**. arXiv 2601.00828 (2026). https://arxiv.org/abs/2601.00828
   - Authors could not be read from the fetched page.
   - **What it does.** Separates detection, localisation and correction. It reports that giving location hints *hurt* the models it tested, which is in tension with Tyen et al.
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
   - **What it does.** Restores execution to a selected prior state and carries forward knowledge distilled from the abandoned branch. Tested on "three long-horizon benchmarks" whose names were not visible in the abstract (**could not verify** which).
   - **The closest existing work to "backtracking inside an agent".**

8. **AgentRewind: Recoverable Execution for Long-Horizon LLM Agents**. Yu Zhuang, et al. arXiv 2608.14380, Aug 2026. https://arxiv.org/abs/2608.14380
   - **What it does.** Checkpoints the agent's context and its environment together, plus a "rewind memory". Evaluated on its own benchmark.

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

**Seen in search but not opened. Do not cite without checking:** 2608.04003 (PAST-Bench), 2607.07663 (a survey of recursive self-improvement), 2609.19526, 2608.20485 (a survey of terminal agents), 2602.08100, 2608.24735 (Meta^n; a search snippet said it was evaluated on Terminal-Bench 2.0, but the fetched abstract did not confirm that), 2608.07645 (Mendel Gödel Machine), 2609.06396 (MetaRSI).

---

## 2. Benchmarks

The architecture note ([ARCHITECTURE.md](ARCHITECTURE.md)) names SWE-bench Lite and WebArena. Both are heavy, and WebArena is not a terminal benchmark. The facts below come from the official pages listed. Where a number was not stated on any page that was opened, it says "not stated".

### Summary table

| Benchmark | Tasks | Pass/fail check | Setup weight | Fit for Project 2 (judgement) |
|---|---|---|---|---|
| **Terminal-Bench 2.0** | 89 | Tests inside the task's container check final state | One Docker image per task, run through the Harbor harness. Cloud sandboxes supported. Total disk not stated | **Best match** for "long-horizon terminal tasks" (the example in the project description) |
| Terminal-Bench "continuous" (4.0 at time of writing) | 66 on the Harbor hub | Same | Same, plus a flat 8-hour agent timeout | Moving target; harder to reproduce |
| SWE-bench Lite / Verified | 300 / 500 | Repo unit tests in Docker | **≥120 GB disk, 16 GB RAM, 8 cores** (official). Modal / sb-cli cloud evaluation exist | Heavy, single domain (Python repos), likely in training data |
| SWE-bench Verified Mini | 50 | Same | About 5 GB instead of 130 GB | Cheap sanity check, but too small to split |
| WebArena | 812 | State/URL/string checks | Five self-hosted sites in Docker, map backend about 180 GB, AWS AMI with 1000 GB EBS, reset between runs | **Not suitable** on a shared machine; not terminal tasks |
| **AppWorld** | 750 (train 105 / dev 60 / test-normal 168 / test-challenge 417) | Database-state unit tests, including collateral damage | `pip install appworld`; **Docker optional** | **Best second family for transfer** |
| τ²-bench | retail 115, airline 50, telecom 114 | Database state, with an LLM-simulated user | `uv`, Python ≥3.12, no Docker mentioned | Alternative transfer family; user simulator adds noise and cost |
| InterCode (Bash/SQL/CTF) | Bash 200, SQL 1034, CTF 100 | Execution-based score 0–1 | Docker, small images | Short tasks, old: a smoke test only |
| ALFWorld / ScienceWorld | ALFWorld: split sizes not confirmed. ScienceWorld: 10 task types, 5,282 variations | Environment reward | Python (+Java for ScienceWorld), no Docker | Cheap, but text games, not terminal |
| OSWorld | 369 | Execution-based | Full desktop VMs | Not suitable |

### Details and sources

**Terminal-Bench 2.0**

Merrill, Shaw, Carlini, et al. "Terminal-Bench: Benchmarking Agents on Hard, Realistic Tasks in Command Line Interfaces". arXiv 2601.11868, Jan 2026. https://arxiv.org/abs/2601.11868. Site: https://www.tbench.ai. Harness: https://github.com/laude-institute/harbor, docs at https://docs.harborframework.com/. Licence Apache-2.0.

Read directly from the paper PDF:

- **Task set.** 89 tasks selected from 229 crowd-sourced tasks. Each task has a Dockerfile, an instruction, tests and a reference solution.
- **Costs.** "Running Terminal-Bench 2.0 costs anywhere from one to a hundred dollars, depending on the model's price". "Most trials are completed in under 20 minutes, using fewer than 25 model calls and 10 million tokens". Extreme trials ran up to 2 hours and used nearly 100M tokens.
- **Protocol.** Each model–agent pair was run at least five times (32,155 trials in total).
- **Model scores.** The resolution-rate chart (Fig. 1) ranks GPT-OSS-120B, GPT-5-Nano and GPT-OSS-20B at the bottom; the exact percentages are read from a chart. Cheap models are therefore near the floor.
- **Contamination.** It relies on a canary string only, with no private test set.
- **Other benchmarks in the same format.** Appendix D lists 26 benchmarks adapted to the same format, including **AppWorld**, SWE-bench Verified and SWE-smith. So the primary and transfer benchmarks could run through one harness.
- **Agent scaffolds.** Terminus 2, the authors' neutral agent, and Mini-SWE-Agent were among the scaffolds used.

From tbench.ai and the Harbor hub:

- Terminal-Bench is now "a continuous benchmark" with semantic versioning (https://www.tbench.ai/news/terminal-bench-4-0). 4.0 "removed 8 tasks", "fixed 19 tasks", and sets "a flat agent timeout of 8 hours".
- The Harbor hub (https://hub.harborframework.com/datasets) lists `terminal-bench-2` (89), `terminal-bench-2-1` (89), `terminal-bench` (66), `terminal-bench-pro` (200) and `terminal-bench-science` (70).
- A Harbor docs line seen during the check says some tasks need a GPU sandbox; it was not re-checked.
- `terminal-bench-pro` (200 tasks) could enlarge the task pool, but its contents and weight were **not examined**.

Not stated anywhere opened: total disk use, per-image sizes, default per-task CPU/RAM. Harbor exposes `--override-cpus` and `--override-memory-mb`.

**SWE-bench**

Paper: https://arxiv.org/abs/2310.06770. Repo: https://github.com/SWE-bench/SWE-bench. Docs: https://www.swebench.com/SWE-bench/.

- **Requirements.** The README states "x86_64 machine with at least 120GB of free storage, 16GB of RAM, and 8 CPU cores".
- **Cloud evaluation.** `--modal true` (https://www.swebench.com/SWE-bench/guides/evaluation/) and sb-cli (https://www.swebench.com/sb-cli/). Free quotas were not found.
- **Lite size.** The HF card (https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite) gives 300 test + 23 dev. The swebench.com datasets page appeared to give a different figure. **Unresolved; the HF card figure is used here.**
- **Verified Mini.** 50 instances, "requires 5GB instead of 130GB of storage": https://huggingface.co/datasets/MariusHobbhahn/swe-bench-verified-mini.
- **Reported costs.** The HAL leaderboard for Verified Mini (https://hal.cs.princeton.edu/swebench_verified_mini) lists runs from about $5 to over $1,000. It is **not verified** whether these are totals per 50 tasks.

**WebArena**

- Repo: https://github.com/web-arena-x/webarena. Environment notes: https://github.com/web-arena-x/webarena/blob/main/environment_docker/README.md (five site containers, map data about 180 GB, AMI with 1000 GB EBS, reset by recreating containers).
- WebArena-Verified (https://github.com/ServiceNow/webarena-verified) has smaller images and a 258-task hard subset. It is still multi-site and stateful.

**AppWorld**

Trivedi, Khot, Hartmann, et al. "AppWorld: A Controllable World of Apps and People for Benchmarking Interactive Coding Agents". ACL 2024. https://arxiv.org/abs/2407.18901. Repo: https://github.com/StonyBrookNLP/appworld.

- **Scale.** 9 apps, 457 APIs, 750 tasks.
- **Baseline scores.** "GPT-4o solves only ~49% of our 'normal' tasks and ~30% of 'challenge' tasks".
- **Install.** `pip install appworld; appworld install; appworld download data`. The README says Docker is optional.
- **Splits.** Taken from the paper's HTML version (not re-checked): train 105 / dev 60 / test-normal 168 / test-challenge 417.
- **Costs.** From the paper (not re-checked): roughly $0.33–$1.33 per task for the main agents with GPT-4o at mid-2024 prices.
- **Splitting caution.** Tasks come in groups of 3 per scenario, so split by scenario, not by task.

**τ-bench family**

- τ-bench: https://arxiv.org/abs/2406.12045. The repo https://github.com/sierra-research/tau-bench is marked deprecated.
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
  - **AppWorld** as the transfer family. It needs no Docker, has built-in splits, and is also available as a Harbor adapter.
  - SWE-bench Verified Mini or a few InterCode tasks only as a smoke test.
- **Main risk.** 89 tasks is small once it is split into adaptation, selection, meta-training and held-out sets, and cheap models score low on it (see [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md), sections 2 and 7).

---

## 3. Other works cited in the technical plan

- **Reflexion: Language Agents with Verbal Reinforcement Learning**. Noah Shinn, Federico Cassano, Edward Berman, et al. (last author Shunyu Yao). arXiv 2303.11366, Mar 2023. https://arxiv.org/abs/2303.11366
  - Agents "verbally reflect on task feedback" and keep reflections in an episodic memory buffer, with no weight updates. This is the basis of baseline B1.
  - Venue: NeurIPS 2023 is widely reported, but the arXiv page does not show it, so it is not verified here.
- **Representation Engineering: A Top-Down Approach to AI Transparency**. Andy Zou, Long Phan, Sarah Chen, et al. (includes Dan Hendrycks). arXiv 2310.01405, Oct 2023. No peer-reviewed venue seen. https://arxiv.org/abs/2310.01405
  - Reads and steers population-level representations inside the model. This is the "activation steering" sense of *steering*, which Project 2 does not use.
