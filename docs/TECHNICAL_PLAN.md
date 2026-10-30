# Project 2: Learning to Improve. Technical plan

Sagandeep Kaur, draft for discussion with Prof. Mohamed Abdelrazek (Deakin A2I2), October 2026.

**Status (updated 2026-10-20).** This is a plan, not a progress report. What exists today:

- an architecture note ([ARCHITECTURE.md](ARCHITECTURE.md));
- the Phase 0 code in this repository: the strategy schema, baselines B0–B2, seeded task splits (the Terminal-Bench 2.0 split is committed), the evaluation runner and a client for locally served models, with 98 offline tests (as collected by pytest on 2026-10-20). Progress is tracked in [PHASE0_CHECKLIST.md](PHASE0_CHECKLIST.md);
- this document and a survey of prior work and benchmarks ([PRIOR_WORK.md](PRIOR_WORK.md));
- the design review of 2026-10-20 ([DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md)), the experiment cards ([EXPERIMENTS.md](EXPERIMENTS.md)), the decision record ([DECISIONS.md](DECISIONS.md)), the schedule ([EXECUTION_PLAN.md](EXECUTION_PLAN.md)) and the risk register ([RISK_REGISTER.md](RISK_REGISTER.md)).

No experiments have been run. No agent has run on a real benchmark, and no model has been called. All costs and timings below are estimates and are marked as such.

**A note on the word "steering".** In this plan, *steering* means changing how the agent behaves by editing its explicit, versioned strategy object (section 3). It does **not** mean activation or representation steering, that is, adding vectors to a model's hidden states as in Representation Engineering (Zou et al., 2023). The model is used as a frozen black box through an OpenAI-compatible endpoint served locally by llama.cpp, so activation steering is out of scope. To avoid the confusion, the rest of this document says "strategy adaptation" rather than "steering".

### Amendments 2026-10-15

After the meeting with Prof. Abdelrazek on 2026-10-14 ([MEETING_2026-10-14.md](MEETING_2026-10-14.md)). Changed headings are marked "(amended 2026-10-15)" or "(added 2026-10-15)".

1. **Model** (section 2). Small open-weight models served locally are now the primary candidates; GPT-5-mini is the fallback. The 20–40% starting-score requirement is unchanged. Candidates are in [SMALL_MODELS.md](SMALL_MODELS.md). Meeting item 6.
2. **Cost per task reporting** (new section 4.3). Mean and median cost per task in tokens, wall-clock seconds and dollars, and pass rate per dollar, for every baseline and the adapted strategy. Meeting item 1.
3. **Strategy switching** (new section 5.4). A library of strategy versions with a per-task selector, as an extra condition against the single global strategy. Meeting item 5; the reading is to be confirmed.
4. **Adaptation efficiency index** (new section 7.6). Held-out gain over B0 per unit of cost spent to get it. Meeting item 4; the reading is to be confirmed.
5. **Budget** (section 9). A note that the dollar figures assume API prices and will be re-estimated for local models.
6. **Open decisions** (section 11). Items 2 and 5 updated; items 13 and 14 added for the two readings to confirm.

### Amendments 2026-10-20

After the design review of 2026-10-20 ([DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md)). Changed headings are marked "(amended 2026-10-20)" or "(added 2026-10-20)". Some changes wait for an answer from Prof. Abdelrazek. They are marked "pending Qn", and the question, its options and its default are in [DECISIONS.md](DECISIONS.md). A default applies only if there is no answer by the Stage-1 freeze, the date the first pre-registration tag is signed.

Abbreviations used below: TB2 is Terminal-Bench 2.0; TB-Pro is terminal-bench-pro; RQ is research question; BoN is best-of-N; MCU (model compute units) is the cost-matching unit of section 4.2; pp is percentage points. Stage 1 and Stage 2 are the two pre-registration tags (section 7.2): before the first adaptation episode, and before the first TB2 episode.

1. **Contribution and scope of paper 1** (sections 1 and 6.5). Paper 1 is a pre-registered, compute-matched test of typed, compiled strategy adaptation for a small local model on held-out Terminal-Bench tasks, against best-of-N and reflection-retry, with cost per task and mechanism evidence. It makes no "first" claim. RQ2 is narrowed to cross-source generalisation (TB-Pro to TB2). RQ4 asks which strategy dimensions account for the gains, without rollback. RQ3 and objectives 4 and 6 move to paper 2 by default (pending Q4). [M1](DESIGN_REVIEW_2026-10.md#m1-novelty-reframe-and-a-code-edit-baseline-b5), [M7](DESIGN_REVIEW_2026-10.md#m7-scope-of-paper-1).
2. **Task pools** (sections 2 and 7.1). All 89 TB2 tasks are held out for the final run. Adaptation and calibration use deduplicated TB-Pro after a CPU-only pilot, with a TB2 re-split as fallback (pending Q3). [M2](DESIGN_REVIEW_2026-10.md#m2-task-pools).
3. **Model and serving** (section 2). Qwen3.6-35B-A3B on llama.cpp on one workstation, with Harbor and local Docker. Fixed budgets of 60 steps and 64k generated tokens. A revised hardware request (pending Q5) and a fallback order with TMax-9B added (pending Q6). API spend for paper-1 arms is $0. [M11](DESIGN_REVIEW_2026-10.md#m11-infrastructure), [M15](DESIGN_REVIEW_2026-10.md#m15-phase-0-calibration-and-the-fallback-model).
4. **Strategy object** (section 3). A field is "compiled" only with a passing test; every other field is labelled text-only. `compile()` is a gate before pre-registration. Rollback values and `switch_to` are outside the paper-1 edit space. [M12](DESIGN_REVIEW_2026-10.md#m12-compile-as-a-gate).
5. **Baselines** (section 4.1). Sampling pinned for every arm. B1 becomes in-episode reflection-retry; B2 becomes pooled BoN with a judge. B3 is dropped. An optional code-edit baseline B5 is added. [M8](DESIGN_REVIEW_2026-10.md#m8-baseline-repair), [M1](DESIGN_REVIEW_2026-10.md#m1-novelty-reframe-and-a-code-edit-baseline-b5).
6. **Cost matching and reporting** (sections 4.2 and 4.3). MCU is the matching unit. Matching is per task; adaptation cost is shown as a payback curve. One cost function, and dollars at two frozen rates. [M4](DESIGN_REVIEW_2026-10.md#m4-cost-unit-and-matching).
7. **Selection rule** (sections 5.1 and 5.2). One hybrid rule with 6 fixed rounds, a contested screening pool and an end-of-loop choice pool. [M9](DESIGN_REVIEW_2026-10.md#m9-selection-noise-fix).
8. **Strategy switching** (section 5.4). Cross-fitted headroom and two frozen selectors at 0 extra episodes. Mid-task switching only behind its gates (pending Q2). [M6](DESIGN_REVIEW_2026-10.md#m6-strategy-switching-deferred-to-the-professor).
9. **Second-order loop, AppWorld and rollback** (sections 6, 7.3 and 8). Paper 2 by default (pending Q4). [M7](DESIGN_REVIEW_2026-10.md#m7-scope-of-paper-1).
10. **Statistics and pre-registration** (section 7.2). Paired t on per-task differences, fixed-sequence tests, more runs per task, two pre-registration stages. McNemar is dropped. [M3](DESIGN_REVIEW_2026-10.md#m3-statistics).
11. **Attribution and leakage** (sections 7.4 and 7.5). A fixed leave-one-out design on 40 tasks, five leak fixes and a held-out ledger. [M10](DESIGN_REVIEW_2026-10.md#m10-leak-fixes), [M16](DESIGN_REVIEW_2026-10.md#m16-total-compute-and-the-cut-order).
12. **Efficiency index** (section 7.6). The headline waits for Prof. Abdelrazek (pending Q1). [M5](DESIGN_REVIEW_2026-10.md#m5-the-intelligence-index-deferred-to-the-professor).
13. **Budget** (section 9). Re-costed at the measured reference throughput: about 9,653 episodes and 45.2 GPU-days for the core, with a cut order and a floor. [M16](DESIGN_REVIEW_2026-10.md#m16-total-compute-and-the-cut-order).
14. **Timeline and open decisions** (sections 10 and 11). Replaced by pointers to [EXECUTION_PLAN.md](EXECUTION_PLAN.md) and [DECISIONS.md](DECISIONS.md).
15. **Corrections.** TB-Pro has 200 public tasks. The AppWorld adapter wording is corrected (section 2). "Decomposing LLM Self-Correction" was first posted in December 2025, not 2026 (section 8).

---

## 1. The project in my words (amended 2026-10-20)

Most agents follow a procedure that a person wrote once: how they look around, plan, use tools, keep track of state, check their work and recover when something breaks. They may retry or reflect within one task, but the procedure itself does not change from one task to the next.

The project asks two things:

- whether an agent can use its own history of successes and failures to change that procedure, so that it does better on *future* tasks, while the model's weights stay fixed;
- whether the mechanism that proposes those changes can itself be improved, so that later rounds of improvement come faster or work better than earlier ones.

*Amended 2026-10-20.* Paper 1 answers the first question. The second goes to paper 2 by default (pending Q4).

### Research questions (amended 2026-10-20)

1. **First-order.** Does changing the strategy based on past trajectories and failures beat:
   - a fixed strategy,
   - reflection/retry,
   - best-of-N,

   when all of them are given the same budget?

   *Amended 2026-10-20.* "The same budget" means matched compute per held-out task, in MCU (section 4.2). Random strategy search (B4) is added as a comparison. The one-time adaptation cost is reported as a payback curve, not matched. The tests are H1 to H4 in section 7.2.
2. **Generalisation.** Do the gains hold on tasks the adaptation never saw? Do they carry over to a different benchmark family, rather than reflecting memorised task instances?

   *Amended 2026-10-20.* In paper 1 this is cross-source held-out generalisation: adapt on TB-Pro, test on all 89 TB2 tasks (pending Q3). Paper 1 makes no cross-family transfer claim. Transfer to a second family moves to paper 2 by default (pending Q4).
3. **Second-order.** If we also revise the adaptation mechanism (how failures are diagnosed and how changes are proposed), does improvement get faster or larger over successive rounds?

   *Amended 2026-10-20.* Paper 2 by default (pending Q4). The adaptation loop is the unit of replication. A powered comparison of two mechanisms needs 27 to 32 independent loops per arm, 73,710 to 87,360 episodes (estimate). That does not fit one GPU.
4. **Attribution.** Which specific changes (verification, planning depth, tool policy, memory, retries/recovery) account for the gains?

   *Amended 2026-10-20.* Paper 1 asks which strategy dimensions account for the gains. It uses leave-one-out attribution on S\*1 (the strategy chosen by the first adaptation loop) and the enforced-versus-advised contrast (section 7.4). Both are exploratory. Rollback is removed from RQ4 (section 8).

### Paper-1 contribution and claims (added 2026-10-20)

**Contribution.** "A pre-registered, compute-matched test of whether adapting a typed, compiled strategy of a small, locally served model on Terminal-Bench beats a fixed strategy, random edits, reflection-retry and best-of-N, with cost per task reported for every arm and mechanism evidence (enforced-vs-advised contrast, leave-one-out attribution over changed strategy-dimension groups)."

Closely related work already shows a harness on TB2 improving itself with a frozen Qwen3.5-35B-A3B (Self-Harness). It already applies typed operators to a self-hosted Qwen3.5-35B-A3B on a sealed TB2.1 split under equal budgets, with the weights frozen only in its harness-only condition (MetaRSI). And an evaluation study already compares harness evolution with matched-budget best-of-N sampling and sequential refinement on TB2.1 with frontier API models, finding no gain (2607.12227). So the contribution is neither the loop nor a compute-matched comparison as such. It is that comparison made for a typed, compiled strategy of a small, locally served model: on held-out tasks, against best-of-N and reflection-retry matched per task, with a random-edit control, cost per task for every arm, the enforced-versus-advised contrast and a pre-registered analysis (section 6.5).

| Claim | What it says | How it is tested |
|---|---|---|
| C1 | The adapted strategy S\* beats the fixed strategy S0 | H1, first in the fixed sequence |
| C2 | S\* beats random strategy search B4, worded about the realised strategies | H2 |
| C3 | S\* against reflection-retry B1 and against pooled BoN, at matched per-task compute | H3 and H4, two-sided, last in the sequence |
| C4 | Mechanism evidence: enforced-versus-advised contrast and leave-one-out attribution | Exploratory, outside the sequence |

S\* here means the per-task average of two adaptation loops (seeds 1 and 2), each run 5 times per task. "Beats" is claimed only for a rejected hypothesis whose confidence interval (CI) excludes 0. Otherwise the result is an estimate with its CI.

**Not claimed:** a "first" self-improving harness on TB2 or for small models; the first compute-matched comparison of harness adaptation with test-time sampling or refinement on Terminal-Bench (2607.12227 ran one with frontier models); the first typed or frozen-weight harness adaptation of a small self-hosted model on Terminal-Bench (MetaRSI); the first adaptation on a task source disjoint from TB2 with TB2 used only for evaluation (ModularRSI); second-order gains; transfer across benchmark families or models; "typed beats code"; "diagnosis beats random search" in general. The typed strategy space is stated as a deliberate restriction of code space. It is chosen for compiled enforcement, attribution and auditability.

### The six internship objectives, and where each is handled here (amended 2026-10-20)

1. **Strong baselines:** a fixed strategy, reflection/retry, and best-of-N at matched cost. See section 4.
2. **The strategy as an explicit object:** a configurable, versioned policy covering planning, exploration, tool use, memory, retries and verification, that can be searched rather than living in prompt text. See section 3.
3. **An adaptation mechanism** that proposes, selects or combines strategy changes based on past outcomes. See section 5.
4. **A second-order loop** in which the adaptation mechanism (failure diagnosis, change proposal) is itself revised and evaluated. See section 6. *Paper 2 by default (pending Q4).*
5. **Real generalisation on held-out tasks**, with strict separation between the tasks used to adapt and the tasks used to evaluate. See section 7.
6. **Transfer** of learned strategies to a second benchmark family. See section 7. *Paper 2 by default (pending Q4). Paper 1 covers cross-source transfer within terminal tasks.*

---

## 2. Setting (amended 2026-10-20)

**Primary benchmark: Terminal-Bench 2.0** (89 tasks, pinned at task commit `2fd12b8`), run through its Harbor harness.

*Amended 2026-10-20 (pending Q3).* All 89 TB2 tasks are held out and used only in the final pre-registered run (section 7.1). Adaptation, selection and calibration use terminal-bench-pro (TB-Pro: 200 public tasks, [GitHub](https://github.com/alibaba/terminal-bench-pro), [Hugging Face](https://huggingface.co/datasets/alibabagroup/terminal-bench-pro)), after deduplication against TB2. TB-Pro tasks build their images locally, use the older `version = "1.0"` task schema and set a 3,600 s agent timeout.

*Note (updated 2026-10-20).* Cloud sandboxes are one option, not the only one. A custom Harbor agent runs in the harness process and sends commands to the task container. The model can then be served on the same host, and the task containers can run in local Docker. The little-coder runs in [SMALL_MODELS.md](SMALL_MODELS.md) (section 4.1) ran the model and the task containers (local Docker) on one laptop. The cloud option stays open for tasks that need more CPU or RAM than the local machine has. The design review chose the local option (see "Serving and run settings" below).

- It matches the example in the project description (long-horizon terminal tasks with environment setup and builds).
- Pass/fail is decided automatically by tests that check the final container state.
- The paper reports that a full pass costs "anywhere from one to a hundred dollars, depending on the model's price".
- Most trials take under 20 minutes.

**Transfer benchmark: AppWorld** (750 tasks over 9 apps, with built-in train/dev/test-normal/test-challenge splits).

*Amended 2026-10-20.* AppWorld moves to paper 2 by default (pending Q4). It re-enters paper 1 only if Prof. Abdelrazek reads the "intelligence index" as a cross-benchmark composite and wants our method scored across benchmarks (Q1). The minimum re-entry is then S0 against S\* on test-normal at k = 1 (one run per task).

- It is a different family: API-driven coding across apps instead of shell work.
- It is checked by database-state unit tests.
- It installs with `pip` and needs no Docker. *(Corrected 2026-10-20.)* The Terminal-Bench paper lists it among 26 benchmarks adapted to the Terminal-Bench task format. The Harbor repository had no AppWorld adapter on 2026-10-20.

**Why not SWE-bench Lite and WebArena, as in the architecture note.** SWE-bench needs at least 120 GB disk, 16 GB RAM and 8 cores for local evaluation. WebArena needs several self-hosted websites (the map data alone is about 180 GB) and a reset between runs. Neither fits a shared machine, and WebArena is not a terminal benchmark. Sources are in [PRIOR_WORK.md](PRIOR_WORK.md), section 2.

**Model (amended 2026-10-15; amended 2026-10-20).** One model, held fixed for the whole project. After the meeting of 2026-10-14 ([MEETING_2026-10-14.md](MEETING_2026-10-14.md), item 6), the primary candidates are **small open-weight models served locally**, so that anyone can rerun the experiments on their own machine. The candidates and their published scores are in [SMALL_MODELS.md](SMALL_MODELS.md).

- **Primary model (added 2026-10-20): Qwen3.6-35B-A3B, Q4_K_M**, served by llama.cpp. The recorded starting band is checked on public TB2 scores only, so no model touches TB2 before the final run. The public little-coder run scores 106/445 = 23.8% of trials overall, and 100/410 = 24.4% on the 82 tasks unchanged between its task commit (`69671fb`) and our pin. Both are inside the band. Phase 0 adds a calibration gate on TB-Pro (G0) as a supplement to the band ([EXPERIMENTS.md](EXPERIMENTS.md), E0).
- **Starting score, unchanged.** Terminal-Bench reports that the cheapest models (GPT-5-Nano, GPT-OSS-20B) sit near the floor. That would leave nothing to adapt, so the model should solve roughly 20–40% of tasks at the start. This is a judgement, to be checked in Phase 0. For small models it is the main risk.
- **Fallback order (amended 2026-10-20; pending Q6).** If the primary model fails G0: Qwen3.5-35B-A3B Q4_K_M, then TMax-9B Q4_K_M, then Nemotron-Terminal-32B Q4_K_M only on a GPU with at least 32 GB. Each fallback costs at most 1,150 episodes. GPT-5-mini (API) is used only by Prof. Abdelrazek's decision. Its price, for reference: $0.25 per M input, $0.025 cached, $2.00 per M output (OpenAI pricing, 2026-10-02).
- **gpt-oss-120b** is no longer planned for paper 1 *(amended 2026-10-20)*. It was a possible second model for a robustness check at $0.15 / $0.60 per M tokens on Together AI. Paper-1 API spend is $0, so any API use needs a logged amendment with its own cap.

**Serving and run settings (added 2026-10-20).** From [M11](DESIGN_REVIEW_2026-10.md#m11-infrastructure) and [M8](DESIGN_REVIEW_2026-10.md#m8-baseline-repair).

| Item | Setting |
|---|---|
| Machine | One x86-64 Linux workstation. llama.cpp on the host. Harbor with local Docker. Our agent is loaded into the Harbor harness process, as in little-coder |
| Infrastructure gate | Before any budgeted episode: an async Harbor agent; reward read from the Harbor trial result; an async client per trial that parses reasoning, tool calls, timings and cached tokens; native tool calling through the chat template; per-step JSONL logs; Harbor concurrency equal to the llama.cpp slot count. It closes after a 5-task TB-Pro smoke run with 0 harness errors |
| Budgets (same for every arm, not editable by adaptation) | 60 steps (a logged change from S0's committed 40); at most 64k generated tokens per episode, reasoning included; a pinned per-call reasoning budget; per-slot context measured on TB-Pro, ceiling 96k (planning value about 80k) |
| Wall-clock | A backstop only: Harbor agent timeout multiplier 2 for every arm. For leaderboard comparison, S0 trials are censored at 1× the task timeout |
| Sampling | Temperature 0.6, `top_p` 0.95, `top_k` 20 and a logged per-request seed for every arm: the model card's setting for precise coding in thinking mode |
| Concurrency | Pinned from a sweep on a 15-task TB-Pro dev slice: the fastest configuration that fits memory with at most 1 timeout in 30 trials (or an upper 95% bound of at most 10%) |
| Pins | `pins.lock` holds the model file hash, llama.cpp commit and flags, GPU and driver, Harbor version, task commits, image digests, slots, key-value (KV) cache type, context, reasoning budget, sampling and the MCU coefficients. The Stage-1 tag freezes it |
| Hardware request (pending Q5) | 1 NVIDIA GPU with at least 24 GB (32 GB or more recommended for 2 or more slots), 16 cores, 64 GB RAM, 500 GB NVMe (1 TB recommended), dedicated during budgeted runs. Plus a consumer-class x86-64 machine (at least 8 GB of video memory, VRAM; 32 GB RAM; Docker) for the portability check |
| Shared machine | No model episodes on the shared development machine. CPU-only work there runs in Docker within its resource limits |

Why 24 GB (estimate): the primary model fully on the GPU needs about 23.4 GiB for one slot at 64k context with an f16 KV cache, and 24.7 GiB for two. More slots on 24 GB need a q8_0 KV cache or mixture-of-experts (MoE) offload to the CPU. Apple Silicon is out of scope, because the task images are amd64 only.

**Agent loop.** A small custom loop, similar in spirit to mini-SWE-agent or Terminus 2 (both used in the Terminal-Bench paper), running as a custom agent inside Harbor. *(Amended 2026-10-20.)* Each strategy field is either compiled, with a test, or labelled text-only (section 3.3).

The architecture note proposes LangGraph. LangGraph would work, but it is not needed for a loop this size. *(Settled 2026-10-20: a custom agent in the Harbor process; [DECISIONS.md](DECISIONS.md), section 1.3.)*

---

## 3. The strategy object

### 3.1 Design rules (amended 2026-10-20)

- **The strategy is data.** It is a typed object (a Pydantic model) and is serialised to JSON.
- **Every field has an effect in code.** Each field changes what the agent loop *does*, not just what the prompt *says*. For example:
  - `verification.checks` adds a stage that runs before `submit` is accepted;
  - `exploration.probes` runs real commands before the first plan.

  *Amended 2026-10-20.* This is now a tested property, not an assumption. A field counts as **compiled** only if a unit test in continuous integration shows that a non-default value changes the controller's actions as specified. Every other field is labelled **text-only**. Text-only fields are still adapted, but they are excluded from every "compiled" or "enforced" claim, and their edits are reported as advice.
- **Free text is fenced.** Free text is allowed only in named, length-limited slots (`notes`). It is attributed as its own dimension, so that we can tell structured changes apart from prompt-text changes.
- **Versioning.** Each version records:
  - its parent;
  - the edit that produced it;
  - the evidence for that edit (diagnoses and task ids);
  - the measured effect.
- **Budgets are fixed, not adapted.** The experimenter fixes the budget caps. The adaptation mechanism may not raise them, or it could "buy" success by spending more. Actual spend is measured for every run.

### 3.2 Fields (amended 2026-10-20)

This field list supersedes the one in the architecture note. Its four fields (`max_retries`, `planning_depth`, `tools_allowed`, `verification_required`, marked *(original)* below) are kept and placed under the dimensions the project text names: exploration, planning, tool use, memory, verification, and recovery/retries.

| Dimension | Field | Type / range | What it controls |
|---|---|---|---|
| **meta** | `strategy_id`, `version`, `parent_version` | str, int, int \| null | Identity and lineage |
| | `changelog` | list[Edit] | Every edit applied, with rationale and evidence |
| **exploration** | `probes` | list[enum: `list_workdir`, `read_readme`, `inspect_tests`, `check_toolchain_versions`, `check_installed_packages`, `check_services`, `git_status`] | Commands run *before* planning. This is the "environment probe" example from the project description |
| | `probe_budget_steps` | int 0–10 | Maximum steps spent exploring before the first state-changing action |
| | `read_tests_first` | bool | Look at any visible tests or examples before acting |
| **planning** | `mode` | enum: `none`, `upfront`, `upfront_with_replan` | Whether an explicit plan is written |
| | `planning_depth` *(original)* | int 0–12 | Maximum number of sub-goals in the plan |
| | `replan_trigger` | enum: `never`, `on_error`, `on_verify_fail`, `every_k_steps` | When the plan is revised |
| | `replan_every_k` | int \| null | Used with `every_k_steps` |
| **tool_policy** | `tools_allowed` *(original)* | set[enum: `bash`, `file_view`, `file_edit`, `python`] | Which tools the loop exposes |
| | `command_timeout_s` | int 10–600 | Per-command timeout |
| | `max_observation_chars` | int 500–20000 | How much command output the model sees (truncation) |
| | `forbidden_patterns` | list[str] | Commands the loop refuses (e.g. destructive ones). A safety dimension |
| | `edit_via_tool_not_shell` | bool | Edit files through the edit tool rather than `sed`/`echo` |
| **memory** | `context_mode` | enum: `full`, `sliding_window`, `summarise` | How past steps are kept in context |
| | `window_or_summary_k` | int | Window size, or how many steps between summaries |
| | `state_notes` | bool | Keep an explicit running record of environment state (files created, packages installed, services started). The Terminal-Bench paper's error analysis names state-memory loss as a failure form |
| | `lessons_k` | int 0–5 | Number of cross-task lessons retrieved from the lesson store at task start |
| | `lesson_store_version` | str | Which version of the lesson store is used (lessons are versioned too) |
| **verification** | `verification_required` *(original)* | bool | Master switch for the check stage |
| | `checks` | list[enum: `run_visible_tests`, `build`, `run_task_example`, `reread_instructions_checklist`, `check_output_artifacts`] | What "checking my work" means |
| | `when` | enum: `before_submit`, `after_each_subgoal` | When checks run |
| | `max_verify_cycles` | int 0–5 | How many times the agent may go back to fixing after a failed check |
| **recovery** (retries and backtracking) | `max_retries` *(original)* | int 0–5 | Retries of a failing action or sub-goal |
| | `retry_on` | set[enum: `nonzero_exit`, `timeout`, `verify_fail`] | What counts as a failure that triggers a retry |
| | `on_repeated_failure` | enum: `continue`, `replan`, `rollback`, `restart_task` | What happens when retries run out |
| | `checkpoint_policy` | enum: `none`, `before_risky_commands`, `after_each_verified_subgoal` | When a checkpoint of the working state is taken |
| | `rollback_target` | enum: `last_checkpoint`, `last_verified_subgoal`, `diagnosed_step` | Where a rollback returns to |
| | `max_rollbacks` | int 0–3 | Rollback budget per task |
| **notes** | `notes` | dict[stage → str ≤ 300 chars], stages = {explore, plan, act, verify, recover} | Free-text advice per stage. Attributed as its own dimension |
| **budget** (fixed by the experiment, not editable) | `max_steps`, `max_tokens`, `max_wall_s` | int | Caps used for cost matching |

*Amended 2026-10-20.*

- **Paper-1 edit space.** The proposer may not emit `on_repeated_failure = rollback`, `rollback_target`, `max_rollbacks` or `checkpoint_policy`, because rollback moves to paper 2 by default (section 8). Unit tests check this.
- **`switch_to`.** A value `switch_to:<version>` of `on_repeated_failure` is added behind a flag that the proposer cannot emit. `compile()` rejects it unless the mid-task switching arm is admitted (section 5.4, pending Q2).
- **`max_retries` and B1.** `recovery.max_retries` stays distinct from the attempt cap of baseline B1.
- **Budget values.** For every arm: 60 steps, at most 64k generated tokens per episode, and wall-clock as a backstop (section 2).
- **Text lint.** Every note, lesson and other proposer-written text must pass a lint before evaluation (section 7.5).

**Edit format.** Edits are JSON-Patch-like operations, validated against the schema:

```json
{"op": "add", "path": "/exploration/probes/-", "value": "check_installed_packages",
 "rationale": "...", "diagnosis_ids": ["d-0412", "d-0419"], "round": 3}
```

Composite edits (at most 2 operations) are allowed, so the mechanism can "compose" changes as the project text asks.

### 3.3 From strategy to behaviour (amended 2026-10-20)

A `compile(strategy) -> AgentLoop` function builds the controller. The loop has fixed stages: explore → plan → act → verify → (recover) → submit. Strategy fields switch stages on or off and set their parameters. The prompt for each stage is rendered from a template using the strategy, and `notes` text is the only free text inserted.

Each field gets a unit test that checks it changes the controller's actions. For example, with `probes=[]` no probe commands are issued. This is what makes the strategy "a searchable object, not buried prompt text".

*Amended 2026-10-20.* From [M12](DESIGN_REVIEW_2026-10.md#m12-compile-as-a-gate).

- **Signature.** `compile(strategy)` returns a controller configuration and the prompt text, with independent switches. This lets the enforced-versus-advised cells of section 7.4 be built, for example S0's controller with S\*1's text.
- **Gate G1.** It must close before the Stage-1 pre-registration tag. It runs in parallel with the infrastructure work and costs no GPU time.
- **Minimum compiled set.** `exploration.*`, `tool_policy.*`, `verification.*`, and `recovery.retry_on`, `max_retries` and `on_repeated_failure` (values `continue`, `replan`, `restart_task`). Recovery comes first, because today it is text-only. Planning, memory and notes may stay text-only if labelled.
- **Mechanism table (paper Table 2).** The paper records, for every field: its code path, unit-test id, status (compiled or text-only) and adherence event.
- **If recovery cannot be compiled in time,** the typed-strategy claim is narrowed in the pre-registration and logged. It is never kept silently.

Today the controller reads only a few fields, and every arm receives the rendered strategy text. So without this gate, most edits would only change the prompt.

---

## 4. Baselines and cost matching (amended 2026-10-20)

### 4.1 Baselines (amended 2026-10-20)

All baselines use the same model, the same agent loop and the same tools. *(Amended 2026-10-20.)* They also use the same sampling settings and budgets (section 2).

| ID | Baseline | Definition (amended 2026-10-20) |
|---|---|---|
| B0 | **Fixed strategy** | A sensible hand-written default S0 (explore briefly, plan, act, check before submitting). Not a straw man. Its committed step cap of 40 is raised to 60, like every arm |
| B1 | **Reflection/retry**, in-episode | Inside one Harbor trial: retry when the in-run judge says "fail" or an agent-written test fails, never on the hidden tests. At most 3 attempts, with a written reflection between them and no environment reset. The 60-step cap applies per attempt; one 64k generated-token cap applies to the full task/run across agent, judge, and reflection calls. The attempt cap is drawn per task and run from {1, 2, 3} to match compute (4.2); budget exhaustion may end the run earlier. Reflection and judge calls are charged to B1 |
| B2 | **Best-of-N**, pooled | Computed exactly from the pool of S0 runs on TB2-89 (10 runs per task, or 6 after budget cut 6), over all subsets of size N. The pick is the highest judge score, ties at random. Oracle pass@N (picking with the hidden tests) is plotted dashed, as a ceiling only |
| B3 | **Free-text adaptation**, GEPA/ACE-style | **Dropped from paper 1.** Whether structure matters is answered with content held fixed, by the enforced-versus-advised contrast (7.4), and expressiveness by a zero-episode audit of published harness edits (6.5) |
| B4 | **Random strategy search** | The same adaptation budget and the same edit space, but edits are sampled at random instead of proposed from diagnoses. It tests whether *diagnosis* matters, or whether any search would do. It uses the hybrid selection rule of 5.1 |
| B5 | **Free-form code edits** (optional, added 2026-10-20) | The same proposer edits our controller code from the same diagnoses, on the same TB-Pro pools, under the same selection rule, scored on TB2-89 at k = 5. Tier C rank 4 (Tier C is optional work, admitted only within the absolute episode cap, in the order of section 9), at most 1,810 episodes. Runs only in a per-trial sandbox whose only network route is the model server. An estimation arm, outside the confirmatory tests |

**The judge (added 2026-10-20).** The same local model scores each trajectory once, from the instruction, the trajectory and the outputs of agent-written tests. It never sees `tests/`. For the S0 pool it runs after the trial, so S0's time and cost contain no judge time. Its cost goes to the BoN rows only. A check on about 600 TB-Pro calibration trajectories sets the BoN selector: if the judge's AUROC (area under the receiver operating characteristic curve) is at least 0.6, the judge is primary; below 0.6, "agent-written tests passed, ties random" is primary, and the paper says that a realistic BoN selector is weak for this model.

**Why the repair (added 2026-10-20).** As coded on 2026-10-20, the client defaults to temperature 0.0 and cannot send `top_p`, `top_k` or a seed. Harbor uploads the tests only at verification, so the agent's own checks return nothing. B1 never retries when no check applies, and B2 picks attempt 0 when no check passes ([DESIGN_REVIEW_2026-10.md, section 4](DESIGN_REVIEW_2026-10.md#4-main-errors-found-and-corrected), row 7). Unit tests for each repair must pass before the infrastructure gate closes.

### 4.2 How costs are matched (amended 2026-10-20)

From [M4](DESIGN_REVIEW_2026-10.md#m4-cost-unit-and-matching).

- **Cost unit: MCU.** MCU = a × prompt tokens + b × generated tokens, from llama.cpp's per-call `timings`. Prompt tokens exclude cached tokens; generated tokens include reasoning. a and b are fitted on Phase 0 TB-Pro runs and frozen at Stage 1. MCU is not claimed to equal GPU-seconds.
- **Validation gate, before Stage 2, on TB-Pro data only.** An arm passes if its mean episode residual is within ±3% and the CI of that mean is within ±5%, with at least 40 episodes. If a validated arm fails, a context term is added and the fit repeated. If it still fails, matching uses processed tokens (prompt plus generated), with MCU as a sensitivity analysis.
- **Charging.** Every model call is charged to the arm that makes it: BoN judge calls to BoN rows, B1's judge and reflection calls to B1, selector calls to the selector arm, diagnosis and proposal calls to the arm's one-time adaptation cost.
- **Matching (the main comparison).** Matching is per task, as in deployment. BoN gets N\* = S\*'s mean MCU per task / (S0's MCU per episode + judge MCU per trajectory). A non-integer N\* is matched as a mixture of the two neighbouring N. If N\* exceeds the pool size, BoN at the pool size is reported and flagged as under-matched. B1's cap mixture is fixed at Stage 2 to match S\*'s per-task MCU on TB-Pro, with a mean cap of at most 2.3. The realised TB2 ratio is a sensitivity analysis.
- **Total-cost view.** Adaptation has a one-time cost. It is shown as a payback curve: T\* = adaptation MCU / (c_eq − c_test\*). Here c_eq is the lowest mean MCU per task at which S0's pooled best-of-N frontier (selector cost included) reaches S\*'s pass rate, and c_test\* is S\*'s mean MCU per task. T\* is "never" if c_eq ≤ c_test\*. Section 7.6 and [EXPERIMENTS.md](EXPERIMENTS.md), E11, give the full definition. There is no confirmatory amortised test. Amortising over the 89 test tasks would need BoN with N of about 16, above the 10-run pool.
- **Compute caution.** [To Backtrack or Not to Backtrack: When Sequential Search Limits Model Reasoning (Qin et al., arXiv 2504.07052, Apr 2025)](https://arxiv.org/abs/2504.07052) found sequential correction loses to parallel sampling on one of its tasks (Countdown). This is why best-of-N at equal cost is the comparison that matters.

*History.* The 2026-10-15 version used dollars under a price table frozen at project start as the cost unit. It chose k for B1 and N for B2 to match mean cost, with curves for N = 1…5 and k = 1…4.

### 4.3 Cost per task reporting (added 2026-10-15; amended 2026-10-20)

From the meeting of 2026-10-14 ([MEETING_2026-10-14.md](MEETING_2026-10-14.md), item 1). *Amended 2026-10-20.* For every arm, in the final evaluation on TB2-89, the point-1 table reports:

| Rows | Columns |
|---|---|
| S0 (B0); B1 at each attempt cap; BoN at N = 1 to 5 and at the pool size; B4; S\* (seed average and each seed); library plus selector (selector cost included); B5 if run; the enforced-versus-advised cells | Mean, median, interquartile range (IQR) and task-bootstrap CI of dollars per task at two rates; wall-clock, labelled with GPU model, slots and concurrency; generated tokens (reasoning included); prompt tokens; cached tokens; MCU; pass rate per dollar. Every column is split by outcome (solved or failed) and by S0 task class (never, contested or always solved in the S0 pool) |

**Dollars (amended 2026-10-20).** Phase 0 measures an occupancy factor, k_occ: time inside model calls divided by GPU busy time. Dollars = (MCU-hours / k_occ) × rate, at two frozen named rates (electricity, and a cloud-GPU equivalent). Their sources and dates go into the price table at Stage 1. MCU never appears without dollars next to it. Occupancy-inclusive dollars are shown only for runs on a dedicated GPU.

**One cost function (added 2026-10-20).** `baselines/cost.py` gets one `episode_cost()`, replacing the pricing of time inside model calls (`cost.py:64`), which also counts waiting for a free server slot. Section 7.6 and [SMALL_MODELS.md](SMALL_MODELS.md) section 3.2 are to point to it. This resolves three conflicting local-cost definitions.

Means are used for cost matching (4.2). Medians are reported as well because cost per task is skewed: the Terminal-Bench paper reports most trials under 20 minutes but some up to 2 hours. In the public reference run, the mean trial time is 1.37 times the median. The one-time adaptation cost is reported separately and is not spread over the per-task figures; section 7.6 combines the two.

---

## 5. First-order adaptation (objective 3) (amended 2026-10-20)

### 5.1 One round (amended 2026-10-20)

The current strategy is S_r. One round has six steps. *(Amended 2026-10-20.)* The rule below is the same for every adapted arm: S\*1, S\*2, B4, and B5 if run ([M9](DESIGN_REVIEW_2026-10.md#m9-selection-noise-fix)). The pools are on TB-Pro (section 7.1).

1. **Run.** Execute S_r once on the diagnosis set **A_diag**: a fixed, stratified 50-task sample of the TB-Pro adaptation pool A_pro (seed 20261015). Hidden-test results *are* used here, because A_pro is training data.
2. **Compress.** Turn each trajectory into a step table: step, command, exit code, truncated output, time. Attach the test summary. This is deterministic and involves no LLM.
3. **Diagnose.** The diagnoser D, an LLM with a diagnosis prompt and a **failure taxonomy**, reads every failed trajectory and a sample of successes. For each it returns a structured `Diagnosis`:
   - `failure_class` (from the taxonomy);
   - `critical_step` (the step index where things went wrong);
   - `evidence` (a quoted line of output);
   - `implicated_dimensions`.

   The starting taxonomy can be seeded from the Terminal-Bench paper's error analysis. Its trajectory-level classes are:

   - disobeying the specification;
   - step repetition;
   - being unaware of termination conditions;
   - reasoning–action mismatch;
   - context loss;
   - task derailment;
   - premature termination;
   - no or incorrect verification;
   - weak verification.

   The paper also has command-level classes, such as resource exhaustion. Environment-setup classes like "acted before checking installed dependencies", from the project description's example, are then added on top.
4. **Aggregate.** Group diagnoses by (class, dimension) and rank the groups by frequency.
5. **Propose.** The proposer P turns the top groups into **K = 4 candidate edits**, which may be composite (at most 2 operations). Every edit must validate against the schema, pass the text lint (7.5) and stay inside the paper-1 edit space (3.2). A rejected candidate is logged and counts against K.
6. **Select and commit (amended 2026-10-20).**
   - Run the parent S_r afresh and the 4 candidates once each on the screening pool **V_pro**: at most 25 contested TB-Pro tasks. Runs share per-(task, run) seeds, but every calibration assumes zero correlation between them.
   - The statistic is an integer: tasks solved by the candidate minus tasks solved by the parent. Accept the best candidate if it solves at least 1 more task, net. Ties go to the lower mean MCU, then to the earlier version.
   - Log every candidate: strategy hash, edits, V_pro outcomes and MCU. V_pro differences are screening data, never effect sizes.

*History.* The 2026-10-15 rule ran every candidate on half of V, then the top two on all of V, and accepted on a rate-difference threshold. In simulation (estimate), it accepted an edit in about 52% of rounds when no edit helped, recording a fake gain of about +13.4 pp. The code also compared float rate differences, which silently rejects about a third of one-task gains. Thresholds are now integer counts in `adaptation_engine/first_order.py`, with unit tests at exact ties.

### 5.2 Stopping, final choice and lessons (amended 2026-10-20)

- **Stopping (amended 2026-10-20).** R = 6 fixed rounds, with no early stop. The 2026-10-15 plan of 8 rounds, or a stop after two empty rounds, is not adopted: simulation showed no gain from rounds 7 and 8, and the stop rule ended loops after about 2 rounds.
- **Final choice (added 2026-10-20).** After round 6, run all 7 versions (S0 to S6) × 3 on **V2_pro**: at most 15 contested TB-Pro tasks, disjoint by sibling group from A_pro and V_pro. The loop's S\* is the version with the most net V2 successes, ties to the earlier version. Its V2 score is not a gain estimate, because of the winner's curse.
- **Cap per loop.** 6 × (|A_diag| + 5 × |V_pro| × k_screen) + 7 × |V2_pro| × k_V2 ≤ 1,575 episodes. The nominal cost is 1,365 at 50 / 25 × 1 / 15 × 3.
- **Pre-registration check (0 episodes).** Before Stage 1, re-simulate the rule on the TB-Pro calibration rates. If the chance that the chosen version is worse than S0 exceeds 10% under edit effects drawn from N(0, 0.3²), raise V2_pro to k = 5 within the cap and re-check.
- **Valid outcomes.** "Few or no accepted edits" and "S\* = S0" are pre-registered valid outcomes.
- **Loops.** Two independent loops for the adapted strategy (seeds 1 and 2) and one for B4. In simulation (estimate), the gain of one loop's chosen strategy has a between-loop standard deviation (SD) of about 4.7 pp, so one loop is a high-variance draw.
- **Lessons.** The diagnoser may also write short cross-task lessons into the versioned lesson store. These are only used through `memory.lessons_k`, so they appear in the attribution like any other dimension. *(Amended 2026-10-20.)* Lessons pass the text lint, and an attribution arm turns lessons and notes off (7.4).

### 5.3 The two models

D and P use the same model as the agent in the main results. Using a stronger model for D and P is run as a variant and reported separately. Otherwise gains could come from the stronger model's knowledge rather than from adaptation (see Open decisions).

*Amended 2026-10-20.* The stronger-model variant has no budget in paper 1. Paper-1 API spend is $0, so it needs a logged amendment with its own cap ([DECISIONS.md](DECISIONS.md), plan item 6).

### 5.4 Strategy switching (added 2026-10-15; amended 2026-10-20)

From the meeting of 2026-10-14 ([MEETING_2026-10-14.md](MEETING_2026-10-14.md), item 5). *Amended 2026-10-20.* Which reading applies is Prof. Abdelrazek's decision (pending Q2). Paper 1 carries reading (a) whatever the answer, at 0 extra episodes ([M6](DESIGN_REVIEW_2026-10.md#m6-strategy-switching-deferred-to-the-professor); card E4-SW in [EXPERIMENTS.md](EXPERIMENTS.md)).

**Reading (a): one version per task.**

- **Library.** L = {S0, S\*1, S\*2, B4-final}, plus B5-final if run: up to 5 versions. This is a logged deviation from the 2026-10-15 estimate of at most 4. All of them are already run on TB2-89 in the final run, so the library costs no extra episodes.
- **Headroom.** The headroom is VBS minus SBS: the virtual best solver (the best version for each task) minus the single best solver (the best version overall). Both are cross-fitted: choose on odd-numbered runs, score on even-numbered runs, swap, and average. The CI comes from a task bootstrap. Choosing and scoring on the same runs is biased upward: by +4.5 pp at k = 5 even when S\* = S0 (simulation, estimate). The same-run figure is shown only labelled "biased; for illustration".
- **Selectors.** Two selectors are designed on TB-Pro logs only and frozen by commit at the Stage-2 tag: a rule table (category × difficulty → version) and one local-model call per task over the instruction text. Each is scored on TB2 by the mean of all runs of its chosen version.
- **Report.** Regret (cross-fitted VBS minus selector), the fraction of the gap closed (only if the headroom CI excludes 0), and library plus selector against S\* at matched per-task MCU. All exploratory.
- **Cost.** The selector's model calls are counted in the per-task cost (4.3). Building the library counts the B4 loop (and B5's) in the adaptation cost.
- The probe-then-choose selector needs new episodes. It moves to paper 2 unless Q2 asks for it.

**Reading (b): switching in the middle of a task.** A reserve of 307 episodes (a 40-episode TB-Pro pilot plus 267 on TB2) is held until Q2 is answered. The arm runs only if all three gates pass:

1. Q2 is answered (b) or (c) before the Stage-1 freeze, and the arm is written into the Stage-1 pre-registration.
2. Gate G1 passes with `switch_to:<version>` executed by the controller behind a flag (3.2). The trigger is the compiled recovery event: `recovery.max_retries` exhausted under `recovery.retry_on`.
3. In the TB-Pro pilot (20 tasks × 2 runs), the switch fires on at least 6 of 40 trials, with at most 2 infrastructure errors.

Then S\*1 with switching runs on TB2-89 at k = 3 against S\*1 × 5, exploratory. Its minimum detectable effect (MDE: the smallest true difference found with 80% power at two-sided alpha 0.05) is about 6.6 pp. If Q2 is (a) or unanswered, the reserve returns to contingency and mid-task switching moves to paper 2.

*History.* The 2026-10-15 version compared the library with an oracle selector using the hidden tests on the same runs. That oracle is replaced by the cross-fitted VBS.

---

## 6. Second-order loop (objective 4) (amended 2026-10-20)

*Amended 2026-10-20.* **Paper 2 by default (pending Q4).** A powered test of RQ3 needs 27 to 32 independent adaptation loops per arm: 73,710 to 87,360 episodes, or about 345 to 409 GPU-days at the planning rate (estimate). The design below also had no clean task split: its budget reused A, V and M. Paper 2 will redesign it with loop-level replication and an independent meta-training pool. Sections 6.1 to 6.4 are kept as its starting point. If Prof. Abdelrazek says the loop is essential, the option within paper 1 is a descriptive demonstration on TB-Pro only (at most 1,365 episodes, no inferential claim; [EXPERIMENTS.md](EXPERIMENTS.md), E5-DEMO).

### 6.1 What gets revised

The adaptation mechanism **M** is itself a versioned object:

- the failure taxonomy (classes and definitions);
- the diagnosis prompt slots;
- the proposal prompt slots and rules (K, maximum edit size, which dimensions may be edited);
- the selection rule (threshold, number of selection seeds).

### 6.2 How a version of M is scored

1. **Diagnosis precision (cheap).** A hand-labelled set of 40–60 failed trajectories, each labelled with its root-cause class and critical step. These come from Phase 1 runs on A, and I would label them myself. Score M's diagnoser by how often its class and its critical step (within ±2 steps) match the labels. This measures the example in the project text: "failure diagnoses become more precise".
2. **Improvement speed (expensive).** Starting from the same S0, run a short first-order loop (4 rounds) with M on a meta-training task split. Score it by the area under the selection-success-vs-round curve, divided by cost.

*Amended 2026-10-20.* The labelled failure set stays in paper 1, drawn from TB-Pro logs only. It is used for a zero-episode appendix analysis: the shift in failure classes across rounds, and the diagnoser's agreement with the labels (Cohen's kappa).

### 6.3 The meta-round

Every few first-order rounds, a meta-diagnoser reads the adaptation log. It looks at:

- which edits were accepted or rejected;
- the predicted versus the measured effect of each edit;
- diagnoses that were later contradicted, for example "missing dependency" where the fix did not help.

From this it proposes 2 candidate edits to M, such as adding a taxonomy class, adding the instruction "check the test log before blaming the environment", or changing K. Each candidate M′ is scored with both scores from 6.2, and it is accepted only if it improves on M.

### 6.4 Testing RQ3

On a task split that was **not** used to learn M, run first-order adaptation from the same S0 with three mechanisms:

- (a) the original M0;
- (b) the meta-learned M*;
- (c) a control: M edited at random with the same meta-budget.

Compare:

- rounds needed to reach a target success rate;
- area under the improvement curve;
- the proportion of proposed edits that are accepted, per round;
- final held-out success.

If (b) beats (a) but not (c), the gain comes from extra compute, not from meta-learning.

### 6.5 Prior work and the paper-1 contribution (amended 2026-10-20)

Second-order self-improvement already exists:

- Promptbreeder (mutation prompts that evolve);
- Hyperagents (2026), where the meta-level code is editable and transfers across domains;
- Meta-TTL, MetaSkill-Evolve, and Hierarchical Self-Improvement (all 2026).

So the contribution here is not "the first agent that improves its improver". What I could not find in the abstracts I checked is all of the following together:

- a typed, interpretable strategy;
- cost-matched baselines including best-of-N;
- an improvement-rate measure tested on held-out tasks and a second benchmark;
- per-dimension attribution;
- long-horizon terminal tasks.

*Superseded 2026-10-20.* This conjunction no longer holds. Typed or structured harness edits (MetaRSI, MemoHarness), matched-budget sampling baselines on TB2.1 (2607.12227), benchmark-disjoint held-out evaluation (ModularRSI) and component ablations (Agentic Harness Engineering, AHE) all exist. The improvement-rate and second-benchmark items have moved to paper 2. The current positioning is in section 1 and below.

[PRIOR_WORK.md](PRIOR_WORK.md) gives details. These are inferences from abstracts, and the full papers need reading before any claim is written.

*Amended 2026-10-20.* The design review found a 2026 cluster of work on self-improving agent harnesses that neither this plan nor PRIOR_WORK cited at the time ([M1](DESIGN_REVIEW_2026-10.md#m1-novelty-reframe-and-a-code-edit-baseline-b5); [LITERATURE_MAP.md](LITERATURE_MAP.md)). The closest is [Self-Harness: Harnesses That Improve Themselves (Zhang et al., arXiv 2606.09498, Jun 2026)](https://arxiv.org/abs/2606.09498). It runs a self-improvement loop on TB2, SWE-bench Verified and AppWorld, with Qwen3.5-35B-A3B among three base models, served on four H200 GPUs. On a 64-task TB2 subset it reports a held-out rise from 23.8% to 38.1%. Those rates fit 10/42 to 16/42, but the paper does not print the denominators, so they are labelled inferred. It compares only the initial against the final harness, reports no token or cost figures, merges four retained edits with no per-edit contribution, and edits Python code.

The closest-work table of paper 1 (Table 1) also covers:

- [Agentic Harness Engineering: Observability-Driven Automatic Evolution of Coding-Agent Harnesses (Lin et al., arXiv 2604.25850, Apr 2026)](https://arxiv.org/abs/2604.25850);
- [Meta-Harness: End-to-End Optimization of Model Harnesses (Lee et al., arXiv 2603.28052, Mar 2026)](https://arxiv.org/abs/2603.28052);
- [ModularRSI: Modular and Generalizable Recursive Harness Self-Improvement (Wu et al., arXiv 2609.14857, Sep 2026)](https://arxiv.org/abs/2609.14857);
- [MetaRSI / RSI2: A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems Themselves (Tan et al., arXiv 2609.06396, Sep 2026)](https://arxiv.org/abs/2609.06396);
- [SEAGym: An Evaluation Environment for Self-Evolving LLM Agents (Zheng et al., arXiv 2606.17546, Jun 2026)](https://arxiv.org/abs/2606.17546);
- [Harness Updating Is Not Harness Benefit: Disentangling Evolution Capabilities in Self-Evolving LLM Agents (Lin et al., arXiv 2605.30621, May 2026)](https://arxiv.org/abs/2605.30621);
- [MemoHarness: Agent Harnesses That Learn from Experience (Huang et al., arXiv 2607.14159, Jul 2026)](https://arxiv.org/abs/2607.14159);
- [Mixture of Self-Improving Branches For Agent Harness Optimization (Dong et al., arXiv 2609.37834, Sep 2026)](https://arxiv.org/abs/2609.37834);
- [Task-CoEvolve: Efficient Harness Optimization via Adaptive Validation Task Selection (Miyai et al., arXiv 2608.20169, Aug 2026)](https://arxiv.org/abs/2608.20169);
- [Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models (Zhang et al., arXiv 2510.04618, Oct 2025)](https://arxiv.org/abs/2510.04618);
- [Rethinking the Evaluation of Harness Evolution for Agents (Wang et al., arXiv 2607.12227, Jul 2026)](https://arxiv.org/abs/2607.12227): AHE-style evolution against parallel sampling and sequential refinement at a matched rollout budget on TB2.1, with three frontier API models; evolution does not win, and on a 34-task held-out split the evolved harness is flat against the initial harness.

Together these already cover ablation, modular and typed harness edits, per-input routing, benchmark-disjoint adaptation, and a matched-budget comparison of harness evolution with test-time sampling and refinement (2607.12227, frontier models, searched tasks). Paper 1's contribution is the one in section 1. The paper says "among the harness-evolution methods we checked, none reports a test-time best-of-N comparison at matched compute; the evaluation study 2607.12227 does, with frontier API models", and never "no paper does". A zero-episode audit maps each published edit of Self-Harness, Agentic Harness Engineering and MemoHarness onto our schema as compiled, text-only or not expressible.

---

## 7. Evaluation design (objectives 5 and 6) (amended 2026-10-20)

### 7.1 Pools and splits (amended 2026-10-20)

Fix the splits at the start: stratify Terminal-Bench 2.0 by category and difficulty, use a fixed seed, and commit the split file before any agent run.

**Committed split (2026-10-15).** This is in `splits/terminal-bench-2.0.json` (seed 20261015) and stays in the repository as history. It is superseded if Q3 is approved, or by default at the Stage-1 freeze.

| Split | Tasks | Used for |
|---|---|---|
| **A**: adaptation | 25 | Running and diagnosing in first-order rounds |
| **V**: selection | 12 | Accepting or rejecting edits |
| **M**: meta-training | 15 | Scoring M′ in the second-order loop |
| **H**: held-out | 37 | **Only** the final evaluation. Never looked at during development, including prompt debugging |

*History (2026-10-15).* If `terminal-bench-pro` (200 tasks on the Harbor hub, not yet examined) turns out to be similar in weight and kind, it could enlarge A and M so that all 89 Terminal-Bench 2.0 tasks can be held out. This is an open decision.

*Amended 2026-10-20 (pending Q3).* **Why the split changes.** In the public reference run (little-coder with Qwen3.6-35B-A3B, 5 attempts per task), 54 of 89 tasks were never solved, 28 were contested and 7 were always solved. H37 holds only 11 contested tasks. All 9 known sibling pairs straddle H (5 siblings in A, 3 in M, 1 in V). The planning MDE is about 9.5 pp for H37 × 5 against 5.8 pp for TB2-89 × 5 (simulation, estimate).

**Target design.** From [M2](DESIGN_REVIEW_2026-10.md#m2-task-pools) and [M15](DESIGN_REVIEW_2026-10.md#m15-phase-0-calibration-and-the-fallback-model).

- **Held out:** all 89 TB2 tasks (TB2-89), used only in the final pre-registered run. Before Stage 2, the only TB2 contact is pulling images by digest, logged in the held-out ledger (7.5).
- **Route pilot (CPU only, before any GPU episode).** Build every TB-Pro image once and record digests; drop tasks above 4 CPUs or 8,192 MB for now; measure disk. Dedup each TB-Pro task against its 3 nearest TB2 tasks by embedding, with owner review and a one-line reason for each removal; near-siblings share a group. Run Harbor's Oracle agent (no model) on TB-Pro survivors and drop tasks whose oracle scores 0. Confirm the licence.
- **GO** if the licence is confirmed, at least 120 tasks survive, Harbor runs them within 5 engineer-days of adapter work, and the disk fits with 20% headroom.
- **Pools.** A 15-task TB-Pro dev slice for bring-up and debugging only. The calibration run E0 runs S0 × 3 on the rest. Let C be the number of contested tasks (solved in some but not all calibration runs; the counting rule is in [EXPERIMENTS.md](EXPERIMENTS.md), E0). Then V_pro = round(0.6 × C), capped at 25; V2_pro = C − V_pro, capped at 15; everything else goes to A_pro. The per-round diagnosis set is a fixed, stratified 50-task sample of A_pro (seed 20261015). A contested-supply shortfall never triggers a TB2 re-split.
- **Fallback, only if the route pilot fails.** A sibling-grouped TB2 re-split, H52 + A15 / V12 / V2 10, seed 20261015, stratified by category and difficulty, logged as a deviation. MDE about 7.6 pp at k = 5, stated in the abstract.
- **Fixed deliverables (meeting item 2).** A per-task routing table (task id, source, pool, group, image digest, drop or dedup reason) and an 89-row per-task pass/fail table.

### 7.2 Measurement and statistics (amended 2026-10-20)

From [M3](DESIGN_REVIEW_2026-10.md#m3-statistics).

**Runs per task on TB2-89.**

| Arm | Runs per task | Episodes |
|---|---|---|
| S0 (also the BoN pool) | 10 | 890 |
| S\*: S\*1 × 5 + S\*2 × 5, averaged per task | 10 | 890 |
| B4 | 5 | 445 |
| B1 | 5 | at most 1,024 episode-equivalents |

In the single-seed branch (only if budget cut 5 of section 9 is applied before Stage 1), S\* = S\*1 × 10. The branch is fixed in the Stage-1 tag.

- **Metrics:** pass rate; the point-1 cost table (4.3); steps; wall-clock with hardware named; success-vs-cost (Pareto) plots.
- **Estimand.** The equal-weight mean over the 89 tasks of the per-task pass-rate difference, in pp. The unit of analysis is the task.
- **Primary test.** A paired t-test on the 89 per-task mean differences, alpha 0.05, two-sided.
- **Fixed-sequence gatekeeping** at alpha 0.05: H1 S\* vs S0; H2 S\* vs B4; H3 S\* vs B1 at matched compute; H4 S\* vs pooled BoN at matched compute. Estimates and 95% CIs for all four are reported wherever the sequence stops.
- **Sensitivity.** A paired sign-flip permutation test (100,000 flips) and a mixed-effects logistic model, pass ~ arm + (1 + arm | task).
- **CIs.** One-stage task bootstrap, 10,000 resamples. A two-stage bootstrap overstates the standard error by about 22 to 28% (simulation, estimate).
- **Dropped.** McNemar's test, which has an MDE above 16 pp on H37 (simulation, estimate). Holm correction is kept only for the exploratory B5 and enforced-versus-advised contrasts.
- **Power (planning values, estimates).** About 4.3 to 4.5 pp for H1 at 10 runs against 10, 5.8 to 5.9 pp for arms at k = 5, and about 6.1 pp for S\* × 10 against B1 × 3. Before Stage 1, a beta-binomial fit to the TB-Pro calibration rates re-states the MDE in the abstract.
- **Size check (0 episodes).** Before Stage 1, simulate the t-test's size on the TB-Pro calibration rates and on the public little-coder TB2 rates. If size exceeds 6% at nominal 5% in either, the sign-flip test becomes primary.
- **Exploratory, with no p-values in the abstract:** attribution, the enforced-versus-advised contrast, switching, per-category results, the lessons-off arm, and net pass@k. Every per-task oracle or "newly solved" quantity is 2-fold cross-fitted.
- **Wording.** Claims are about the realised strategies. "Diagnosis beats random search" is never claimed with fewer than 2 loops per arm. The between-seed SD is reported.
- **Reference comparison.** One fixed figure, 100/410 = 24.39% for the little-coder run on the 82 unchanged tasks, compared descriptively with our S0. The confounds are listed: 7 changed tasks, mixed agent versions, a laptop with offload, different timeouts, harness and sampling.

**Pre-registration (added 2026-10-20).** Two stages. Stage 1 comes before the first adaptation episode; Stage 2 before the first TB2 agent episode. Each stage is a signed git tag that freezes `pins.lock`, the analysis code, thresholds, pool lists and budget caps. Each tag is archived on Zenodo with a DOI (digital object identifier), plus an OSF (Open Science Framework) registration quoting the tag and DOI. OSF text is drawn only from this public repository.

*History.* The 2026-10-15 version planned 3 runs per task on H37, McNemar's test per pair with Holm correction, and expected to detect only differences of about 10 to 15 pp.

### 7.3 Transfer to AppWorld (amended 2026-10-20)

*Amended 2026-10-20.* Paper 2 by default (pending Q4). It re-enters paper 1 only through Q1, as S0 against S\* on test-normal at k = 1 (section 2). The design below is kept for paper 2.

Strategy fields are written to be environment-agnostic. A thin adapter maps them to each environment. For example, `probes` becomes "list available apps and read the API docs", and `run_visible_tests` becomes "re-query the database state the task asks about".

Two transfer tests:

1. **Strategy transfer.** Run S*, learned on Terminal-Bench, on AppWorld test-normal (168 tasks) with no further adaptation. Compare against B0–B2 on AppWorld.
2. **Mechanism transfer.** Run first-order adaptation on AppWorld train/dev with M0 versus M*, and compare improvement speed. Split by scenario, not by task, because each scenario has 3 related tasks.

### 7.4 Attribution (RQ4) (amended 2026-10-20)

*Amended 2026-10-20.* From [M16](DESIGN_REVIEW_2026-10.md#m16-total-compute-and-the-cut-order) and [M13](DESIGN_REVIEW_2026-10.md#m13-model-ladder-t1-and-compiled-vs-advised-t2). All of it is exploratory.

1. **Edit log.** Every candidate and accepted edit is logged with its V_pro outcome. This is screening data only, never an effect size.
2. **Leave-one-out attribution (E-ATTR).** The attribution set is 40 TB2 tasks, fixed at Stage 1 from public third-party data only: the 35 tasks with at least one success in the little-coder run, plus 5 of its 54 never-solved tasks (seed 20261015, stratified by category). Each arm is S\*1 with one changed dimension group reverted to S0, for up to 3 groups (the 3 with the most accepted edits in S\*1's lineage, if there are more). One more arm turns lessons and notes off (`lessons_k = 0`); it is never cut. Each arm runs 40 × 3 = 120 episodes and is paired with S\*1's 5 runs on the same tasks. The MDE is about 12 pp (estimate). If S\*1 = S0, E-ATTR does not run.
3. **Enforced versus advised (E-T2).** It needs gate G1 (3.3). The cells are (controller, prompt text). (S0, S0) and (S\*1, S\*1) come from the main run. The core "advised" cell is S0's controller with S\*1's text, on TB2-89 × 5 (445 episodes). An "enforce-only" cell, S\*1's controller with S0's text, is optional (Tier C rank 2). The contrasts are compiled minus advised (detectable from about 5.8 pp), advised minus S0, and, with the enforce-only cell, the main effect of enforcement (MDE about 3.8 pp). The advised cell runs only if at least one field that S\*1 changed is compiled with a passing test.
4. **Per-field adherence.** Every strategy-triggered stage gets a provenance tag and an executed-or-overridden flag. This readout is kept only if its instrumentation validates on TB-Pro logs before Stage 2.
5. **Mechanism evidence.** For tasks that flipped from fail to pass, link the flip to trajectory events. For example: "the environment probe found a missing package at step 2, which S0 never discovered".

*History.* The 2026-10-15 version planned leave-one-dimension-out and add-one-dimension runs on H, and a sampled Shapley estimate. Add-one and Shapley runs are not budgeted in paper 1.

### 7.5 Contamination and leakage (amended 2026-10-20)

Terminal-Bench is public and relies on a canary string only. Compare S0's score with published numbers for the same model, and state the caveat. Contamination affects all methods equally, so comparisons *between* methods are less exposed than absolute scores.

*Amended 2026-10-20.* Five fixes, frozen at Stage 1 ([M10](DESIGN_REVIEW_2026-10.md#m10-leak-fixes)):

1. **Dedup.** TB-Pro against TB2, and sibling groups within TB-Pro (7.1). The removal list and reasons are published.
2. **Lint.** Every note, lesson and proposer-written text must pass a lint before evaluation. It rejects any TB2 or TB-Pro task id, any URL, any command string over 40 characters, and any path that appears in a task's files or instructions. Its false-positive rate is piloted on TB-Pro outputs before Stage 1.
3. **Egress.** On TB-Pro only: an allowlist starting from package hosts, built from the Oracle runs, shipped as a pinned and hashed fork of the task directories that changes only the agent network lines, plus a DNS sinkhole for benchmark web domains. TB2-89 runs only in the final run, under its upstream setting (`allow_internet = true`), with per-trial SNI (Server Name Indication) and DNS logging and a grep for the canary and benchmark names. Flagged trials count as failures in the primary analysis and are excluded in a sensitivity analysis.
4. **Held-out ledger.** The boolean guard keyed on the split name (`evaluation/runner.py:112`) is replaced by a guard keyed on the held-out task ids. Every access appends a record (time, commit, `pins.lock` hash, arm, tasks, runs, purpose) to an append-only ledger. Its hash goes into each signed tag.
5. **Lessons-off arm.** Inside attribution (7.4), never cut. A memorisation probe on 20 TB-Pro tasks runs in Phase 0. A TB2 probe, if wanted, is pre-registered and runs only in the final run.

### 7.6 Adaptation efficiency index (added 2026-10-15; amended 2026-10-20)

From the meeting of 2026-10-14 ([MEETING_2026-10-14.md](MEETING_2026-10-14.md), item 4). *Amended 2026-10-20.* Which reading applies, and which number is the headline, is Prof. Abdelrazek's decision (pending Q1; [M5](DESIGN_REVIEW_2026-10.md#m5-the-intelligence-index-deferred-to-the-professor)).

Every candidate is computed after the final run, from logs already budgeted, at 0 extra episodes. None feeds back into adaptation or selection. Costs use the matching unit of section 4.2.

| Candidate | Definition |
|---|---|
| CER_test | Test-time compute-equivalence ratio: c_eq / c_test\*. c_eq is the lowest mean MCU per task at which S0's pooled best-of-N frontier (selector cost included) reaches S\*'s pass rate p\*. c_test\* is S\*'s mean MCU per task. It reads as "how many S0 best-of-N samples S\* is worth per task". If the frontier never reaches p\*, it is censored, never extrapolated |
| T\* | Payback in tasks: adaptation MCU / (c_eq − c_test\*); "never" if c_eq ≤ c_test\* |
| Amortised CER(T) | c_eq / (c_test\* + adaptation MCU / T), as a curve over T. At T = 89 it is bounded at about 0.6 by construction, so it goes to the appendix |
| Δp/C(T) | The 2026-10-15 index below, only where C > 0, in the appendix |
| Pass per MCU | Pass rate divided by mean MCU per task |

The same quantities are computed for B1, B4 and B5. Kendall's tau compares the method rankings under each index. Δp and C are always reported next to any index, with task-bootstrap CIs. Reading (b), a composite score across benchmarks, is used only in the model-choice table of Phase 0, never on TB2 held-out runs. A Chollet-weighted variant is computed only if its weights are pre-registered at Stage 1.

**Default if no answer by the Stage-1 freeze:** reading (a), with CER_test as headline and T\* as companion.

*History (2026-10-15 definition).* One number for how much held-out improvement a method buys per unit of cost. For a method X evaluated on T held-out tasks:

- **Gain.** Δp(X) = pass rate of X on H minus pass rate of B0 on H, in percentage points.
- **Cost.** C(X, T) = the one-time adaptation cost of X + T × (mean cost per task of X − mean cost per task of B0).
  - For the adapted strategy, B3 and B4, the one-time part is everything spent on A and V, including diagnosis and proposal calls.
  - For B1 and B2 it is zero; their extra cost is all at test time. This is the baselines' equivalent.
- **Index.** E(X, T) = Δp(X) / C(X, T), in percentage points per $100 (or per GPU hour for local models).

It was to be reported at T = 37 (the size of H) and as a curve over T. It is retired as the headline: it is undefined when C ≤ 0 and unbounded near 0, and T = 37 belongs to the superseded split.

This is an operationalisation of Chollet's idea of intelligence as skill-acquisition efficiency ([On the Measure of Intelligence (Chollet, arXiv 1911.01547, Nov 2019)](https://arxiv.org/abs/1911.01547)). It is not his formal measure. His definition also weighs priors and generalisation difficulty. Here the model, and so the priors, is the same for every method, and generalisation is handled by measuring only on held-out tasks.

---

## 8. Where backtracking fits (amended 2026-10-20)

*Amended 2026-10-20.* The rollback sub-question moves to paper 2 by default (pending Q4). Rollback values and fields are excluded from the paper-1 edit space, with a unit test (3.2). The reason is in the implementation note below: rollback covers files only, which would confuse "rollback" with incomplete state restoration. The section is kept for paper 2.

A question I was interested in before this project is whether a model can go back and fix a *specific earlier step* instead of only polishing its final answer. Two of the strategy dimensions above capture that idea, so it is not dropped:

- **verification** is the "check step": noticing that something is wrong;
- **recovery** is the "revise step": `on_repeated_failure = rollback`, `checkpoint_policy`, and `rollback_target = diagnosed_step` roll the working state and context back to a chosen point and continue from there.

This allows a focused sub-question inside RQ4, without a separate project: **does targeted rollback beat retry, replan or restart at the same cost, and how accurate is the agent at finding the step to roll back to?**

The literature makes the second half essential:

- Tyen et al. (2024) found that LLMs are poor at *locating* the wrong step, but correct it well once told where it is.
- *(Corrected 2026-10-20.)* [Decomposing LLM Self-Correction: The Accuracy-Correction Paradox and Error Depth Hypothesis (Li, arXiv 2601.00828, Dec 2025)](https://arxiv.org/abs/2601.00828) reports that model-generated location hints can even hurt.
- Rollback for agents has very recent close work: Rollback-Induced Reflection (Sep 2026) and AgentRewind (Aug 2026). These must be compared against.

**Implementation.** Rollback needs a snapshot of the task environment. The simplest version keeps the working directory under git inside the container and rolls back files and context together. *(Updated 2026-10-20.)* This was checked on 2026-10-04 ([PHASE0_CHECKLIST.md](PHASE0_CHECKLIST.md), "Snapshot support in Harbor"). Harbor gives an agent no snapshot, checkpoint or restore operation. Rollback is therefore done with git inside the container, and it covers files only: installed packages, running services and files outside the working directory are not rolled back. `restart_task` is the only full reset. This stays a technical risk, and the limitation should be stated wherever the rollback results are reported.

---

## 9. Budget (amended 2026-10-20)

From [M16](DESIGN_REVIEW_2026-10.md#m16-total-compute-and-the-cut-order). Budgets are in episodes first and GPU-days second. All figures are estimates.

**Planning rate: 213.5 episodes per GPU-day** at concurrency 1. It is 86,400 s divided by 404.7 s, the mean trial time over all 445 trials of little-coder's public Qwen3.6-35B-A3B run on TB2 (trial records in the [TB2 leaderboard dataset](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard)). That run used a laptop with 8 GB of VRAM and MoE offload to the CPU. So the rate is a conservative proxy with a ±30% band (149 to 278 episodes per GPU-day). It is applied to TB-Pro episodes too, until gate G0 measures the real rate r on TB-Pro.

**Core (main GPU, default).**

| Item | Pool | Episodes |
|---|---|---|
| E-P0 bring-up: throughput sweep (at most 90) and A/A determinism run (60) | TB-Pro dev slice | 150 |
| E1 B1 smoke test | TB-Pro dev slice | 60 |
| E0 calibration, S0 × 3 | TB-Pro | 600 |
| E2 three adaptation loops (S\*1, S\*2, B4) × 1,365 | TB-Pro | 4,095 |
| E3 final run: S0 × 10 (890), S\*1 × 5 (445), S\*2 × 5 (445), B4 × 5 (445), B1 × 5 (at most 1,024) | TB2-89 | 3,249 |
| E-ATTR attribution: up to 4 arms × 40 tasks × 3 | TB2, 40 tasks | 480 |
| E-T2 advised cell, × 5 | TB2-89 | 445 |
| E4b mid-task switching reserve (40 pilot + 267), released if Q2 is (a) or unanswered | TB-Pro, TB2-89 | 307 |
| E-PORT portability check, S0 × 3 (emulated on the main GPU unless a consumer machine is provided) | TB2-89 | 267 |
| **Core total** | | **9,653 (45.21 GPU-days; 34.8 to 64.6 across the band)** |

With a consumer machine for E-PORT, the core is 9,386 episodes (43.96 GPU-days).

**Caps.**

- Core with contingency: 10,500 episodes. Contingency funds only named uses: the E0 top-up (at most 400), infrastructure reruns, a 178-episode leaderboard-protocol fallback, and the model calls that are not episodes (judge, selector, diagnosis and proposal). It never funds new arms.
- Absolute, including Tier C: 12,500 episodes.
- API spend for paper-1 arms: $0. Any API use needs a logged amendment with its own cap.
- Each fallback model: at most 1,150 episodes, deducted from the GPU-day budget.

**Tier C (optional), in this order,** each only if its own gate admits it: (1) the descriptive second-order demonstration on TB-Pro, at most 1,365, only if Q4 says essential; (2) the enforce-only cell, 445; (3) a second small model row on TMax-9B, 534 plus a 20-episode pilot; (4) the code-edit baseline B5, 1,810.

**Rule at gate G0.** After Phase 0, measure r on TB-Pro and the dedicated GPU-days left, D_rem (Q5). Capacity C = 0.9 × r × D_rem. If C covers the remaining core (8,843 episodes), run it and admit Tier C items in order within min(C, 12,500 − spent). Otherwise apply the cuts below in order until the plan fits. Cuts 4 and 5 must be decided before the Stage-1 tag. A throughput below 150 episodes per GPU-day, or a median episode above 600 s, triggers this re-plan, never a model switch.

| Cut | Change | Plan after the cut |
|---|---|---|
| 1 | Attribution down to 2 arms | 9,413 (44.09 GPU-days) |
| 2 | Advised cell from k = 5 to k = 3 | 9,235 (43.26) |
| 3 | B1 from × 5 to × 3 (cap 614) | 8,825 (41.33) |
| 4 | 4 rounds instead of 6 in all three loops | 7,505 (35.15) |
| 5 | Drop the S\*2 loop; S\* = S\*1 × 10; only before Stage 1 | 6,580 (30.82) |
| 6 | S0 pool from × 10 to × 6 | 6,224 (29.15) |

**Floor:** 6,224 episodes (29.15 GPU-days). Below the floor, work halts before Stage 1 and is escalated to Prof. Abdelrazek. **Never cut:** the two gates, E-P0, E0, holding out all 89 TB2 tasks, at least 6 S0 runs and 10 S\* runs per task, B4 × 5, B1, BoN, the point-1 and point-2 tables, the index and selector analyses, E-PORT, the lessons-off arm, the mid-task reserve until Q2 or the freeze, pre-registration and the held-out ledger. Planned and realised episodes and GPU-days are published as an appendix table.

*History.* The 2026-10-15 budget assumed API prices: about 7,400 TB2 episodes and 2,500 AppWorld episodes, for about $600–$4,700, and about 80 hours of run time on 16 parallel sandboxes. A later estimate of about 270 s per reference trial (about 340 episodes per GPU-day) is refuted and retired: it divided a job window that covers only the 287 trials run after a resume by all 445 trials.

---

<a name="10-timeline-assumes-about-24-weeks-part-time-scale-if-different"></a>

## 10. Timeline (amended 2026-10-20)

*Amended 2026-10-20.* The schedule, gates and phase order are in [EXECUTION_PLAN.md](EXECUTION_PLAN.md). The experiment cards are in [EXPERIMENTS.md](EXPERIMENTS.md). The internship's length, start date and weekly hours are still to be agreed ([DECISIONS.md](DECISIONS.md), plan item 1), so the schedule will be rescaled once they are settled. That schedule currently assumes 20 hours per week, about 31 weeks to a draft paper (estimate).

The order of work that the schedule follows: the TB-Pro route pilot (CPU only); the infrastructure gate, which ends with a 5-task TB-Pro smoke run; Phase 0 bring-up and calibration on TB-Pro, ending at gate G0; gate G1 (built in parallel, no GPU) and the Stage-1 tag; the adaptation loops on TB-Pro; the Stage-2 tag; the single final run on TB2-89; analysis and write-up.

*History.* The 2026-10-15 timeline assumed about 24 weeks part-time in six phases: setup (weeks 1–2), strategy and baselines (3–6), first-order loop (7–12), second-order loop (13–17), held-out evaluation, attribution and AppWorld transfer (18–21), and write-up (22–24). It had a checkpoint after the first-order phase: stop and analyse if adaptation did not beat cost-matched best-of-N on V. That checkpoint is replaced by the pre-registered gates, and "S\* = S0" is now a valid pre-registered outcome.

---

<a name="11-open-decisions"></a>

## 11. Open decisions (amended 2026-10-20)

*Amended 2026-10-20.* The open decisions, their options, defaults, deadline gates and owners are in [DECISIONS.md](DECISIONS.md). That file also records the decisions of the design review and a log of deviations.

*History.* The 2026-10-15 list had 14 items. Each is now either settled by the design review or carried as an open question in [DECISIONS.md](DECISIONS.md). Section 1.3 of that file maps each old item to where it went.
