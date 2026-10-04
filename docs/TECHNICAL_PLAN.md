# Project 2: Learning to Improve. Technical plan

Sagandeep Kaur, draft for discussion with Prof. Mohamed Abdelrazek (Deakin A2I2), October 2026.

**Status.** This is a plan, not a progress report. What exists today:

- an architecture note ([ARCHITECTURE.md](ARCHITECTURE.md));
- the empty package scaffold in this repository;
- this document and a survey of prior work and benchmarks ([PRIOR_WORK.md](PRIOR_WORK.md)).

No experiments have been run. All costs and timings below are estimates and are marked as such.

**A note on the word "steering".** In this plan, *steering* means changing how the agent behaves by editing its explicit, versioned strategy object (section 3). It does **not** mean activation or representation steering, that is, adding vectors to a model's hidden states as in Representation Engineering (Zou et al., 2023). The model is used as a frozen black box through an API, so activation steering is out of scope. To avoid the confusion, the rest of this document says "strategy adaptation" rather than "steering".

---

## 1. The project in my words

Most agents follow a procedure that a person wrote once: how they look around, plan, use tools, keep track of state, check their work and recover when something breaks. They may retry or reflect within one task, but the procedure itself does not change from one task to the next.

The project asks two things:

- whether an agent can use its own history of successes and failures to change that procedure, so that it does better on *future* tasks, while the model's weights stay fixed;
- whether the mechanism that proposes those changes can itself be improved, so that later rounds of improvement come faster or work better than earlier ones.

### Research questions

1. **First-order.** Does changing the strategy based on past trajectories and failures beat:
   - a fixed strategy,
   - reflection/retry,
   - best-of-N,

   when all of them are given the same budget?
2. **Generalisation.** Do the gains hold on tasks the adaptation never saw? Do they carry over to a different benchmark family, rather than reflecting memorised task instances?
3. **Second-order.** If we also revise the adaptation mechanism (how failures are diagnosed and how changes are proposed), does improvement get faster or larger over successive rounds?
4. **Attribution.** Which specific changes (verification, planning depth, tool policy, memory, retries/recovery) account for the gains?

### The six internship objectives, and where each is handled here

1. **Strong baselines:** a fixed strategy, reflection/retry, and best-of-N at matched cost. See section 4.
2. **The strategy as an explicit object:** a configurable, versioned policy covering planning, exploration, tool use, memory, retries and verification, that can be searched rather than living in prompt text. See section 3.
3. **An adaptation mechanism** that proposes, selects or combines strategy changes based on past outcomes. See section 5.
4. **A second-order loop** in which the adaptation mechanism (failure diagnosis, change proposal) is itself revised and evaluated. See section 6.
5. **Real generalisation on held-out tasks**, with strict separation between the tasks used to adapt and the tasks used to evaluate. See section 7.
6. **Transfer** of learned strategies to a second benchmark family. See section 7.

---

## 2. Setting (recommended; see Open decisions)

**Primary benchmark: Terminal-Bench 2.0** (89 tasks, pinned version), run through its Harbor harness in cloud sandboxes.

- It matches the example in the project description (long-horizon terminal tasks with environment setup and builds).
- Pass/fail is decided automatically by tests that check the final container state.
- The paper reports that a full pass costs "anywhere from one to a hundred dollars, depending on the model's price".
- Most trials take under 20 minutes.

**Transfer benchmark: AppWorld** (750 tasks over 9 apps, with built-in train/dev/test-normal/test-challenge splits).

- It is a different family: API-driven coding across apps instead of shell work.
- It is checked by database-state unit tests.
- It installs with `pip` and needs no Docker. It is also one of the 26 benchmarks already adapted to the Harbor format.

**Why not SWE-bench Lite and WebArena, as in the architecture note.** SWE-bench needs at least 120 GB disk, 16 GB RAM and 8 cores for local evaluation. WebArena needs several self-hosted websites (the map data alone is about 180 GB) and a reset between runs. Neither fits a shared machine, and WebArena is not a terminal benchmark. Sources are in [PRIOR_WORK.md](PRIOR_WORK.md), section 2.

**Model.** One inexpensive mid-tier model, held fixed for the whole project. Two candidates:

- **GPT-5-mini**: $0.25 per M input, $0.025 cached, $2.00 per M output (OpenAI pricing, 2026-10-02).
- **gpt-oss-120b**, open weights: $0.15 / $0.60 per M tokens on Together AI.

Terminal-Bench reports that the cheapest models (GPT-5-Nano, GPT-OSS-20B) sit near the floor. That would leave nothing to adapt, so the model should solve roughly 20–40% of tasks at the start. This is a judgement, to be checked in Phase 0. The same chart places GPT-OSS-120B near the bottom as well, which is why it is only the second candidate; its starting score has to be checked before it is used.

**Agent loop.** A small custom loop, similar in spirit to mini-SWE-agent or Terminus 2 (both used in the Terminal-Bench paper), running as a custom agent inside Harbor. Every strategy field must change behaviour *in code* (section 3.3).

The architecture note proposes LangGraph. LangGraph would work, but it is not needed for a loop this size (see Open decisions).

---

## 3. The strategy object

### 3.1 Design rules

- **The strategy is data.** It is a typed object (a Pydantic model) and is serialised to JSON.
- **Every field has an effect in code.** Each field changes what the agent loop *does*, not just what the prompt *says*. For example:
  - `verification.checks` adds a stage that runs before `submit` is accepted;
  - `exploration.probes` runs real commands before the first plan.
- **Free text is fenced.** Free text is allowed only in named, length-limited slots (`notes`). It is attributed as its own dimension, so that we can tell structured changes apart from prompt-text changes.
- **Versioning.** Each version records:
  - its parent;
  - the edit that produced it;
  - the evidence for that edit (diagnoses and task ids);
  - the measured effect.
- **Budgets are fixed, not adapted.** The experimenter fixes the budget caps. The adaptation mechanism may not raise them, or it could "buy" success by spending more. Actual spend is measured for every run.

### 3.2 Fields

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

**Edit format.** Edits are JSON-Patch-like operations, validated against the schema:

```json
{"op": "add", "path": "/exploration/probes/-", "value": "check_installed_packages",
 "rationale": "...", "diagnosis_ids": ["d-0412", "d-0419"], "round": 3}
```

Composite edits (at most 2 operations) are allowed, so the mechanism can "compose" changes as the project text asks.

### 3.3 From strategy to behaviour

A `compile(strategy) -> AgentLoop` function builds the controller. The loop has fixed stages: explore → plan → act → verify → (recover) → submit. Strategy fields switch stages on or off and set their parameters. The prompt for each stage is rendered from a template using the strategy, and `notes` text is the only free text inserted.

Each field gets a unit test that checks it changes the controller's actions. For example, with `probes=[]` no probe commands are issued. This is what makes the strategy "a searchable object, not buried prompt text".

---

## 4. Baselines and cost matching

### 4.1 Baselines

All baselines use the same model, the same agent loop and the same tools.

| ID | Baseline | Definition |
|---|---|---|
| B0 | **Fixed strategy** | A sensible hand-written default S0 (explore briefly, plan, act, check before submitting). Not a straw man |
| B1 | **Reflection/retry** (Reflexion-style) | S0 plus up to *k* attempts per task, with a written self-reflection between attempts. The retry trigger is **the agent's own checks only**, never the hidden tests, because the hidden tests are not available at test time |
| B2 | **Best-of-N** | *N* independent S0 runs per task. One is picked by the agent's own checks or an LLM judge. Oracle pass@N (picking with the hidden tests) is reported separately and labelled as an upper bound |
| B3 | **Free-text adaptation**, GEPA/ACE-style (recommended, see Open decisions) | Learns from the same adaptation tasks with the same budget, but by rewriting prompt text or a playbook instead of the typed strategy. It tests whether the *structured* object matters. GEPA and ACE are the strongest prior methods of this kind (see [PRIOR_WORK.md](PRIOR_WORK.md)) |
| B4 | **Random strategy search** | The same adaptation budget and the same edit space, but edits are sampled at random instead of proposed from diagnoses. It tests whether *diagnosis* matters, or whether any search would do |

### 4.2 How costs are matched

- **Cost unit.** Cost is counted as dollars under one **price table frozen at project start**, and token counts are logged as well. This keeps price changes during the project from moving the results.
- **Test-time matching (the main comparison).** For each method, measure the mean cost per held-out task.
  - Choose *k* for B1 and *N* for B2 so that their mean cost per task is close to the adapted agent's.
  - Also report the full success-vs-cost curves (N = 1…5, k = 1…4), so that the comparison does not depend on one chosen point.
- **Total-cost view.** Adaptation has a one-time cost, which is reported too, along with the number of future tasks after which it pays for itself.
- **Compute caution.** "To Backtrack or Not to Backtrack" (Qin et al., 2025) found sequential correction loses to parallel sampling on one of its tasks (Countdown). This is why best-of-N at equal cost is the comparison that matters.

---

## 5. First-order adaptation (objective 3)

### 5.1 One round

The current strategy is S_r. One round has six steps.

1. **Run.** Execute S_r on the adaptation set **A**, one run per task. Hidden-test results *are* used here, because A is training data.
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
5. **Propose.** The proposer P turns the top groups into **K = 4 candidate edits**, which may be composite. Every edit must validate against the schema.
6. **Select and commit.**
   - Run each candidate S_r ⊕ e on the selection set **V**, together with S_r itself, on the same tasks and seeds.
   - Accept the best candidate if it improves success by at least a threshold without going over the cost cap. Otherwise keep S_r.
   - Log the accepted or rejected edit with its measured Δ (change in success rate).
   - To save cost, evaluate in stages: run every candidate on half of V, then only the top two on all of V.

### 5.2 Stopping and lessons

- **Stopping.** Stop after R = 8 rounds (estimate), or after two rounds in a row with no accepted edit.
- **Lessons.** The diagnoser may also write short cross-task lessons into the versioned lesson store. These are only used through `memory.lessons_k`, so they appear in the attribution like any other dimension.

### 5.3 The two models

D and P use the same model as the agent in the main results. Using a stronger model for D and P is run as a variant and reported separately. Otherwise gains could come from the stronger model's knowledge rather than from adaptation (see Open decisions).

---

## 6. Second-order loop (objective 4)

### 6.1 What gets revised

The adaptation mechanism **M** is itself a versioned object:

- the failure taxonomy (classes and definitions);
- the diagnosis prompt slots;
- the proposal prompt slots and rules (K, maximum edit size, which dimensions may be edited);
- the selection rule (threshold, number of selection seeds).

### 6.2 How a version of M is scored

1. **Diagnosis precision (cheap).** A hand-labelled set of 40–60 failed trajectories, each labelled with its root-cause class and critical step. These come from Phase 1 runs on A, and I would label them myself. Score M's diagnoser by how often its class and its critical step (within ±2 steps) match the labels. This measures the example in the project text: "failure diagnoses become more precise".
2. **Improvement speed (expensive).** Starting from the same S0, run a short first-order loop (4 rounds) with M on a meta-training task split. Score it by the area under the selection-success-vs-round curve, divided by cost.

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

### 6.5 Prior work

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

[PRIOR_WORK.md](PRIOR_WORK.md) gives details. These are inferences from abstracts, and the full papers need reading before any claim is written.

---

## 7. Evaluation design (objectives 5 and 6)

### 7.1 Splits

Fix the splits at the start: stratify Terminal-Bench 2.0 by category and difficulty, use a fixed seed, and commit the split file before any agent run.

Suggested split of the 89 tasks (an estimate, adjusted in Phase 0):

| Split | Tasks | Used for |
|---|---|---|
| **A**: adaptation | 25 | Running and diagnosing in first-order rounds |
| **V**: selection | 12 | Accepting or rejecting edits |
| **M**: meta-training | 15 | Scoring M′ in the second-order loop |
| **H**: held-out | 37 | **Only** the final evaluation. Never looked at during development, including prompt debugging |

If `terminal-bench-pro` (200 tasks on the Harbor hub, not yet examined) turns out to be similar in weight and kind, it could enlarge A and M so that all 89 Terminal-Bench 2.0 tasks can be held out. This is an open decision.

### 7.2 Measurement on H

- 3 runs per task per configuration. The Terminal-Bench authors used at least 5.
- **Metrics:**
  - success rate;
  - cost per task;
  - success per dollar;
  - steps;
  - wall-clock time;
  - success-vs-cost (Pareto) plots.
- **Statistics:**
  - paired comparisons on the same tasks;
  - bootstrap confidence intervals over tasks;
  - McNemar's test for each pair of methods;
  - Holm correction across the comparisons.
- **Power (estimate).** With 37 held-out tasks × 3 runs, I expect only differences of roughly 10–15 percentage points or more to be clearly detectable. A power check on Phase 1 data will confirm this, and this limit is stated up front.

### 7.3 Transfer to AppWorld

Strategy fields are written to be environment-agnostic. A thin adapter maps them to each environment. For example, `probes` becomes "list available apps and read the API docs", and `run_visible_tests` becomes "re-query the database state the task asks about".

Two transfer tests:

1. **Strategy transfer.** Run S*, learned on Terminal-Bench, on AppWorld test-normal (168 tasks) with no further adaptation. Compare against B0–B2 on AppWorld.
2. **Mechanism transfer.** Run first-order adaptation on AppWorld train/dev with M0 versus M*, and compare improvement speed. Split by scenario, not by task, because each scenario has 3 related tasks.

### 7.4 Attribution (RQ4)

1. **Edit log.** Every accepted edit has its measured Δ on V. This is noisy, but it is free.
2. **Leave-one-dimension-out on H.** Revert one dimension of S* to its S0 value and measure the drop.
3. **Add-one-dimension on H.** Apply one dimension of S* to S0 and measure the gain.
4. **Interactions.** If there are at most 6 dimension groups, a sampled Shapley estimate is affordable; otherwise report only items 2 and 3.
5. **Mechanism evidence.** For tasks that flipped from fail to pass, link the flip to trajectory events. For example: "the environment probe found a missing package at step 2, which S0 never discovered".

### 7.5 Contamination

Terminal-Bench is public and relies on a canary string only. Compare S0's score with published numbers for the same model, and state the caveat. Contamination affects all methods equally, so comparisons *between* methods are less exposed than absolute scores.

---

## 8. Where backtracking fits

A question I was interested in before this project is whether a model can go back and fix a *specific earlier step* instead of only polishing its final answer. Two of the strategy dimensions above capture that idea, so it is not dropped:

- **verification** is the "check step": noticing that something is wrong;
- **recovery** is the "revise step": `on_repeated_failure = rollback`, `checkpoint_policy`, and `rollback_target = diagnosed_step` roll the working state and context back to a chosen point and continue from there.

This allows a focused sub-question inside RQ4, without a separate project: **does targeted rollback beat retry, replan or restart at the same cost, and how accurate is the agent at finding the step to roll back to?**

The literature makes the second half essential:

- Tyen et al. (2024) found that LLMs are poor at *locating* the wrong step, but correct it well once told where it is.
- A 2026 study ("Decomposing LLM Self-Correction") reports that location hints can even hurt.
- Rollback for agents has very recent close work: Rollback-Induced Reflection (Sep 2026) and AgentRewind (Aug 2026). These must be compared against.

**Implementation.** Rollback needs a snapshot of the task environment. The simplest version keeps the working directory under git inside the container and rolls back files and context together. Whether Harbor's cloud sandboxes support full container snapshots needs checking in Phase 0. This is a technical risk.

---

## 9. Budget (estimate; assumptions shown)

**Assumptions.**

- One Terminal-Bench episode costs **$0.05–$0.40** with a cheap model. This is consistent with the paper's "$1–$100 per full pass" for 89 tasks, at the cheap end.
- One AppWorld episode costs **$0.03–$0.15**. This scales the paper's GPT-4o costs down by the price ratio, and is a rough figure.
- Diagnosis and proposal calls add about 10%.
- Contingency for bugs and reruns adds 30%.

| Item | Episodes (Terminal-Bench unless noted) | How counted |
|---|---|---|
| Phase 0 calibration | ~180 | Model choice and smoke tests on A∪V∪M only (52 tasks × ~3–4 runs); H is not touched |
| Development baselines on A∪V | ~600 | B0/B1/B2, including N and k multiples |
| First-order runs | ~1,800 | 8 rounds × (25 + 4 candidates × 12) ≈ 580 per run; × 3 for the main run, the random-search control (B4) and the free-text baseline (B3) |
| Second-order | ~2,700 | 3 meta-rounds × 2 candidates × short inner loops of 4 rounds, each round ≈ 15 meta-training tasks + 4 candidates on half of V (≈ 940), plus the final M0 / M* / random-M comparison: 3 × 8 rounds × ~73 (≈ 1,750) |
| Final held-out evaluation | ~1,200 | 37 tasks × 3 runs × ~7 configs, weighted by cost multiples |
| Attribution | ~900 | 6 dimensions × 2 (leave-out / add-one) × 37 × 2 runs |
| **Terminal-Bench subtotal** | **~7,400** | **$370–$3,000** |
| AppWorld transfer | ~2,500 | test-normal × 5 configs × 2 runs, plus mechanism transfer on train/dev: **$75–$375** |
| Diagnosis and proposal calls, plus 30% contingency | | ×1.4 |
| **Total (estimate)** | | **about $600–$4,700 in API costs**. With prompt caching and GPT-5-mini, I would expect the lower half |

**Not included: sandbox compute.**

- Terminal-Bench tasks run in Docker containers. I would not run them on a shared machine.
- Harbor supports Modal, Daytona and other cloud sandboxes, but I have not priced them.
- A Deakin machine or credits could replace them (see Open decisions).

**Wall-clock (estimate).** Most trials take under 20 minutes. At an average of about 10 minutes and 16 sandboxes in parallel, the ~7,400 Terminal-Bench episodes need roughly 80 hours of run time, spread over the project.

---

## 10. Timeline (assumes about 24 weeks part-time; scale if different)

The internship's length, start date and weekly hours are still to be agreed, so the timeline assumes part-time work and will be rescaled once they are settled.

| Phase | Weeks | Work | Deliverable |
|---|---|---|---|
| 0. Setup | 1–2 | Pin the benchmark version. Fix the splits and commit the split file. Get Harbor running in a cloud sandbox. Choose the model by running S0 on 20 tasks from A∪V. Check `terminal-bench-pro`. Check snapshot support. Agree the budget | Split file, the price table, a smoke-test report |
| 1. Strategy + baselines | 3–6 | Strategy schema, `compile()`, per-field tests. Implement B0–B2 and run them on A∪V. Collect and label 40–60 failure trajectories | Objectives 1–2; the labelled failure set |
| 2. First-order loop | 7–12 | Diagnoser, proposer, selection, version log. Random-search control (B4). Optional B3 | Objective 3; adaptation curves on V |
| 3. Second-order loop | 13–17 | Versioned M, meta-diagnoser, both scores for M, the three-way RQ3 comparison | Objective 4 |
| 4. Held-out, attribution, transfer | 18–21 | The single held-out evaluation, ablations, AppWorld transfer | Objectives 5–6, RQ4 |
| 5. Write-up | 22–24 | Paper draft, released code and logs | Draft paper |

**Checkpoint after Phase 2.** If first-order adaptation does not beat cost-matched best-of-N on V, stop and analyse why before building the second-order loop. That result is itself worth reporting.

---

## 11. Open decisions

These are questions for discussion. Some are Prof. Abdelrazek's to decide, and the rest we would agree together. Each has my suggestion, which is only a starting point.

1. **Duration, start date, hours per week and supervision rhythm.** To agree together.
   - Suggestion: about 24 weeks part-time, with a short weekly update.
2. **Who pays for API calls and sandboxes, and what is the cap?** Prof. Abdelrazek's decision.
   - Suggestion: a fixed cap agreed in Phase 0, around the lower half of the estimate in section 9, with a review after Phase 2.
3. **Which benchmark pair and version?**
   - Suggestion: Terminal-Bench 2.0, pinned, as primary, and AppWorld for transfer. The continuous Terminal-Bench (4.0, 8-hour timeouts) is current but a moving target. τ²-bench is the fallback transfer family.
4. **Should the task pool be enlarged?**
   - Suggestion: check `terminal-bench-pro` in Phase 0. Use it for A/M only if it is comparable, and keep Terminal-Bench 2.0 as the held-out set.
5. **Which model?**
   - Suggestion: one cheap mid-tier model that solves about 20–40% at the start (GPT-5-mini is the first candidate). gpt-oss-120b, open weights, as a second model for a robustness check, if its starting score is high enough.
6. **Same model for the diagnoser and proposer, or a stronger one?**
   - Suggestion: the same model for the main claims, and a stronger model as a labelled variant.
7. **How much free text may the strategy contain?**
   - Suggestion: typed fields plus small labelled `notes` slots, with notes attributed separately.
8. **Which agent framework and tracking tools?** The architecture note plans LangGraph and MLflow/LangSmith.
   - Suggestion: a minimal custom loop run inside Harbor, logging to JSONL files with MLflow for comparing runs. LangSmith is optional.
9. **Should the GEPA/ACE-style free-text baseline (B3) be included?**
   - Suggestion: yes, if the budget allows. It is the comparison reviewers are most likely to ask for.
10. **Is the rollback sub-question (section 8) in scope?**
    - Suggestion: yes, as part of RQ4, not as a separate study.
11. **Publication target and authorship.** Prof. Abdelrazek's decision.
12. **Naming.**
    - Suggestion: avoid "steering" in titles, since it is easily read as activation steering. "Strategy adaptation" says what is meant.
