# Risk register for paper 1

Sagandeep Kaur, draft for discussion with Prof. Mohamed Abdelrazek (Deakin A2I2), 2026-10-20.

**Status (2026-10-20).** No experiment has been run and no model has been called. Every episode count, GPU-day figure and probability below is an estimate. Each comes from public data, a simulation or arithmetic, and is labelled as such. The likelihood and impact ratings are judgements, not measurements. Experiment ids are those of [EXPERIMENTS.md](EXPERIMENTS.md). Gate ids are those of EXPERIMENTS.md and [EXECUTION_PLAN.md, section 4](EXECUTION_PLAN.md#4-gates). The decisions behind the mitigations are recorded in [DESIGN_REVIEW_2026-10.md](DESIGN_REVIEW_2026-10.md).

Some mitigations depend on Prof. Abdelrazek's answers to open questions. Those are marked **to confirm with Prof. Abdelrazek**. Each has a stated default, listed in [DECISIONS.md, section 1](DECISIONS.md#1-open-decisions).

---

## How to read this file

### Terms and acronyms

| Term | Meaning |
|---|---|
| TB2 | Terminal-Bench 2.0, 89 tasks, pinned at task commit `2fd12b8`. TB2-89 means all 89 tasks, held out for the final run |
| TB-Pro | terminal-bench-pro, 200 public tasks, used for calibration and adaptation only |
| GPU, VRAM | Graphics processing unit; its on-board memory |
| MoE | Mixture of experts. "MoE offload" keeps some expert layers in CPU (central processing unit) memory |
| KV cache | The key-value cache of the model's attention layers, stored per token |
| Slot | One llama.cpp request slot; the slot count sets how many trials run at once |
| Episode | One Harbor trial of one strategy on one task |
| GPU-day | 24 hours of one dedicated GPU |
| r | Measured episodes per GPU-day at the pinned configuration |
| D_rem, C | Dedicated GPU-days left before the analysis deadline; the episode budget C = 0.9 × r × D_rem computed at gate G0 |
| A_pro, V_pro, V2_pro | TB-Pro pools: diagnosis, per-round screening, and the end-of-loop choice |
| Stage 1, Stage 2 | Signed git tags that freeze the plan: before the first adaptation episode, and before the first TB2 agent episode. Each is archived with a DOI (digital object identifier) |
| G-INFRA, G1, G0 | Gates: harness bring-up, `compile()`, and Phase-0 calibration (see [EXPERIMENTS.md](EXPERIMENTS.md#gates-and-zero-episode-protocol-items)) |
| G-BASE, G-ROUTE, G-SWEEP, G-JUDGE, G-SEL, G-MCU, G-T2, G-E4b, G-B5, G-T1lite, G-H2 | Schedule gates: baseline repair, TB-Pro route go/no-go, serving configuration, BoN judge, selection-noise calibration, cost-unit validation, advised-cell applicability, mid-task switching pilot, B5 sandbox, TMax-9B pilot, and the S\* against B4 test (see [EXECUTION_PLAN.md, section 4](EXECUTION_PLAN.md#4-gates)) |
| Tier C | Optional add-ons funded only from headroom under the 12,500-episode absolute cap |
| S0, S\*1, S\*2, S\* | The fixed strategy; the strategies chosen by adaptation loops 1 and 2; their per-task average |
| B1, BoN, B4, B5 | Reflection-retry; best-of-N; random edits; free-form code edits (optional) |
| MCU | Model Compute Units: a × prompt tokens + b × generated tokens, from llama.cpp `timings`. The cost-matching unit |
| MDE | Minimum detectable effect at 80% power, alpha 0.05 |
| pp | Percentage points |
| CI | 95% confidence interval |
| C3, C5 | Contested TB-Pro tasks (solved in some but not all runs) after 3 runs, and after a top-up to 5 |
| API | Application programming interface; here, a paid hosted model |
| DNS, TLS, SNI | Domain Name System; Transport Layer Security; Server Name Indication, the host name a client sends when it opens a TLS connection |
| GUID | Globally unique identifier; TB2's canary string is one |
| AUROC | Area under the receiver operating characteristic curve; 0.5 is chance |
| NVMe | A fast solid-state disk interface |

### Scales

| Rating | Likelihood | Impact |
|---|---|---|
| L | Unlikely (roughly below 20%) | A table, appendix or estimate changes; no confirmatory claim at risk |
| M | Plausible (roughly 20 to 50%) | A secondary result is lost, or the plan is cut or delayed by weeks |
| H | Likely (roughly above 50%) | A confirmatory claim, the held-out test or the whole schedule is at risk |

### Owners

- **SK**: Sagandeep Kaur (research intern, project owner).
- **MA**: Prof. Mohamed Abdelrazek (supervisor). He owns a risk only where the response is his decision.

---

## Register

| ID | Risk | L | I | Early indicator | Mitigation | Contingency | Owner | Linked experiment or gate |
|---|---|---|---|---|---|---|---|---|
| RK-01 | No GPU is granted, or it arrives late | M | H | No answer to Q5 (compute) when G-INFRA closes | Do all CPU-only work first (P-M2, G-INFRA, G1, CODE-FIX, LEDGER, LINT-PILOT, simulations), in Docker within resource limits. Ask once for the full rig | No budgeted episode starts without a dedicated GPU. Escalate. An API model only by MA's decision, with a logged amendment and its own cap | SK (request), MA (decision) | E-P0, G0; Q5 in [DECISIONS.md](DECISIONS.md#q5-compute-meeting-point-6) |
| RK-02 | The GPU is smaller than requested, or 24 GB rather than 32 GB or more | M | M | E-P0 finds that only one slot, or only MoE-offload configurations, fit | Fit-gated sweep over slot count, KV type and MoE offload. The reference run used 8 GB of VRAM with offload, so small cards work, only slower | Re-plan at G0 with the measured rate. Apply the cut order. Halt and escalate below the floor | SK | E-P0, G0, E0-FB |
| RK-03 | Throughput is below the planning rate | M | H | r below 150 episodes per GPU-day, or a median episode above 600 s, in E-P0 or E0 | Budget in episodes first. Pin concurrency from the sweep. Re-measure on a shared host and flag its wall-clock columns | G0 rule C = 0.9 × r × D_rem, then cuts 1 to 6 in order. Never switch model for speed | SK | E-P0, G-SWEEP, G0, cut order |
| RK-04 | The primary model scores below the starting band in our harness | L | H | E0 pass rate with an upper CI bound below 12%, or infrastructure errors above 5% | The public TB2 figure is inside the 20 to 40% band. G-INFRA parses reasoning content and uses native tool calling | Next local fallback, at most 1,150 episodes each. If none passes, keep the best local model with smaller pools (**to confirm with Prof. Abdelrazek**, Q6) | SK; order MA (Q6) | E0, G0, E0-FB, E3-REF |
| RK-05 | Floor effect: the true gain is below the detectable effect | H | H | E0-SIM re-states MDEs above the planning values; V2_pro trajectories stay flat in E2 | Hold out all 89 TB2 tasks. S0 ×10 and S\* 10 runs per task. Paired t on per-task means. MDE in the abstract. "S\* = S0" is a pre-registered valid outcome | Report estimates with CIs. A non-rejection is never called "no difference". No runs are added after Stage 2 | SK | E3, E0-SIM, P-M2, G-H2 |
| RK-06 | TB-Pro supplies too few contested tasks | M | H | C3 below 40 after E0; C5 below 30 after the top-up | Top up non-contested tasks to 5 runs (at most 400 episodes, from contingency). Pool sizes follow C5 | 20 ≤ C5 < 30: screen V_pro at k=2 within the cap formula. C5 < 20: fitness failure, next fallback model. Supply never triggers a TB2 re-split | SK | E0, G0, E2 |
| RK-07 | The TB-Pro route fails (images, schema, survivors) | M | H | Fewer than 120 survivors after build, resource filter, dedup and Oracle check; adapter work passes 5 engineer-days | CPU-only route pilot before any GPU episode | E-RESPLIT: sibling-grouped TB2 re-split (52 held out), logged as a deviation, MDE about 7.6 pp stated in the abstract | SK | P-M2, G-ROUTE, E-RESPLIT |
| RK-08 | Sibling or content leakage from TB-Pro into the TB2 held-out set | M | H | Dedup review finds a TB-Pro task that asks for the same artefact, algorithm or tool chain as a TB2 task | Embedding search plus owner review of the 3 nearest TB2 tasks for every TB-Pro task. Near-siblings share a group. Removal list and routing table published | Remove the task before E0. A leak found after Stage 2 is reported as a deviation, with the affected tasks listed | SK | P-M2; Appendix A1 routing table |
| RK-09 | Notes and lessons carry task-specific content | M | M | Lint rejection rate in E2; false-positive rate in LINT-PILOT | Lint every note, lesson and proposer text: no task ids, URLs, commands over 40 characters or task paths. Rejected candidates count against K | The lessons-off and notes-off arm in E-ATTR, never cut, bounds this channel. Revise the lint before Stage 1 if it blocks generic advice | SK | LINT-PILOT, E2, E-ATTR |
| RK-10 | TB2 is touched before Stage 2 | L | H | Any ledger record before Stage 2 whose purpose is not an image pull by digest | Replace the split-name guard with a guard keyed on the TB2-89 task ids, and an append-only access ledger hashed into each tag. No TB2 Oracle run | Record the access in a pre-registration amendment and in the paper | SK | LEDGER, PREREG-2 |
| RK-11 | Contamination through internet access on TB2 | M | H | E3-AUDIT flags: lookups of benchmark hosts, or grep hits on the canary or solution strings | TB-Pro pools, where selection acts, run under a pinned allowlist fork with a DNS sinkhole for benchmark domains. TB2 keeps its upstream network setting, with a per-trial audit | Flagged trials count as failures (primary) and are excluded (sensitivity). Flag rates reported per arm. A path-filtering proxy stays a last resort | SK | E-NET, E3-AUDIT |
| RK-12 | Memorisation of TB-Pro, which shares a provider with the Qwen models | M | M | E0-MEM: the model completes TB-Pro instructions from task names. E0 lower CI bound above 45% | TB-Pro is used for calibration and selection only; confirmatory claims rest on TB2. E-T1lite checks TMax training data for task overlap | Report the probe. A pass rate above the band is a fitness failure. A TB2 probe runs only inside the final run, if pre-registered | SK | E0-MEM, G0, E-T1lite, G-T1lite |
| RK-13 | Selection overfitting: noise accepted as gains | H | M | E0-SIM2 gives P(chosen version worse than S0) above 10% at the actual pool sizes | Hybrid rule: 6 fixed rounds, a V_pro screen, an end-of-loop choice on a separate V2_pro at k=3. Integer thresholds. V_pro deltas are never effect sizes. TB2 is never used for selection | Raise V2_pro to k=5 within the cap formula. If still above 10%, proceed and flag the harm rate in the pre-registration | SK | E2, E0-SIM2, CODE-FIX, G-SEL |
| RK-14 | One adaptation loop is a high-variance draw | H | H | S\*1 and S\*2 diverge on V2_pro; large between-seed difference in E3 | Two seeds are core. S\* is their per-task average, at the same TB2 cost as one strategy at 10 runs. Claims are worded about the realised strategies | Cut 5 (drop S\*2) only before the Stage-1 tag, with claims reworded | SK | E2, E3, cut 5, G-H2 |
| RK-15 | Baselines are still weak (straw men) | M | H | Baseline unit tests fail; B1 never retries in E1; S0 runs are identical across seeds | Repairs before any budgeted episode: pinned sampling for all arms, per-request seeds, a judge, pooled BoN from S0 ×10, B1 with a judge or self-test trigger, unit tests | G-INFRA stays open until the tests pass. B1 or BoN is flagged "under-matched" if matching fails | SK | G-BASE, G-INFRA, E1, E3-B1, E3-BoN |
| RK-16 | The same-model judge is near chance | M | M | E0-JUDGE AUROC below 0.6 on about 600 TB-Pro trajectories | The judge runs after the trial, never sees `tests/`, and is charged to BoN rows. Oracle pass@N is drawn as a ceiling | The agent-test selector becomes primary, the judge a sensitivity analysis. The paper says a realistic selector is weak for this model | SK | E0-JUDGE, G-JUDGE, E3-BoN |
| RK-17 | `compile()` is not finished before Stage 1 | M | H | G1 tests for `recovery.*` not green by the planned Stage-1 date; few fields that S\*1 changes are compiled | Build G1 in parallel with G-INFRA. Minimum compiled set, per-field CI tests, Table 2 code review | Narrow the typed-strategy claim in the pre-registration, logged, never silently. The E-T2 advised cell becomes "not applicable" if no changed field compiles | SK | G1, E-T2, G-T2, E4b |
| RK-18 | The cost metric is gameable or biased | M | M | The MCU gate fails for an arm; S\*'s saving comes mostly from failed trials | One cost function. Coefficients fitted on TB-Pro, frozen at Stage 1. Every call charged to its arm. Selection counts tasks; MCU only breaks ties. Raw tokens, dollars and medians reported, split by outcome | Add a context-length term, then match on processed tokens with MCU as a sensitivity analysis. Raw logs allow any unit to be recomputed | SK | E3-COST, G-MCU, E-N3, E11 |
| RK-19 | Results depend on hardware speed | M | M | Per-arm timeout rates differ; seconds per step far from the reference run | Binding limits in steps (60) and generated tokens (64k), identical for all arms. Wall-clock multiplier 2 for all arms as a backstop. Timeout rates reported per arm | If 1× censoring proves invalid, a 1× S0 run of 178 episodes from contingency | SK | E3-LB, E-P0, E-PORT |
| RK-20 | llama.cpp runs are not reproducible bit for bit | H | L | E0-AA: same-seed paired runs differ; low correlation rho | `pins.lock` holds the model file hash, llama.cpp commit and flags, GPU and driver, KV type, context, slots and sampling. Seeds logged. Analyses use per-task means | No variance reduction from shared seeds is claimed unless rho is measured. Reproducibility is stated as pass rates with CIs | SK | E-P0, E0-AA |
| RK-21 | Harbor or TB2 changes version during the project | H | M | A Harbor release or TB2 commit after our pin | Pin the Harbor tag and commit, the TB2 task commit and the image digests in `pins.lock` at Stage 1. Pull by digest and keep saved copies. E3-REF uses only the 82 unchanged tasks | No upgrade after Stage 1 without a logged amendment. Report the pinned versions | SK | E-P0, PREREG-1, E3-REF |
| RK-22 | Harness errors and timeouts count as agent failures | M | M | Harness errors in the 5-task TB-Pro smoke run; E0 infrastructure errors above 5% | G-INFRA: async adapter, one client per trial with a timeout at least the task timeout × multiplier, reward read from the Harbor result, per-step logs | Rerun infrastructure errors from contingency. Above 5% in E0 is a G0 fitness failure | SK | G-INFRA, E0, G0 |
| RK-23 | New harness-evolution papers pre-empt the contribution | H | M | A new paper compares adaptation of a small local model with test-time best-of-N or reflection at matched per-task compute on held-out Terminal-Bench tasks | No "first" claims. The contribution is a pre-registered, compute-matched test of typed, compiled strategy adaptation for a small local model on held-out Terminal-Bench tasks, against best-of-N and reflection-retry, with cost per task and mechanism evidence. E-N4 maps published edits onto our schema. Check arXiv every two weeks (proposed) | Update the closest-work table, cite the paper and state the differences. Keep the pre-registered analysis unchanged | SK | E-N4, PREREG-1 |
| RK-24 | Prof. Abdelrazek's readings of points 4 or 5 differ from the defaults | M | M | His answers to Q1 (point 4) and Q2 (point 5), due by the Stage-1 freeze | Keep both readings open: every index variant at 0 episodes; E4-SW under every answer; a 307-episode reserve for mid-task switching | Point 4 (b): the composite becomes a named model-choice table. Point 5 (b) or (c): E4b runs behind its gates. Later answers are logged deviations (see notes) | MA (decision), SK | E11, E4-SW, E4b, G-E4b |
| RK-25 | The timeline slips | H | H | G-INFRA or G1 not closed by the planned date; G0 later than planned | Run CPU-only work in parallel. Tier C only from headroom. Cut order fixed now. Short weekly update. Re-plan the timeline once the internship length and hours are agreed (plan item 1) | The G0 rule applies the cuts; below the floor, halt and ask for more GPU-days, a faster GPU or a narrower paper 1 | SK; MA (duration, plan item 1) | G-INFRA, G1, G0 |
| RK-26 | Licences of TB-Pro or Self-Harness code are unclear | M | H | No LICENSE file or written confirmation from the TB-Pro authors when P-M2 ends | Licence is GO condition (i) of P-M2. From Self-Harness, use the paper only and copy no code | TB-Pro unconfirmed: route failure, E-RESPLIT. Self-Harness: ask its authors before any reuse, else drop the 64-task comparison slice | SK | P-M2, G-ROUTE, E-RESPLIT, E-N4 |
| RK-27 | Disk space runs out | M | M | The P-M2 disk census leaves less than 20% headroom | Pull TB2 by digest, build TB-Pro once, no duplicate local registry. Request a 500 GB NVMe disk (1 TB recommended) | Build, run and prune by digest, logged. Ask for a larger disk | SK | P-M2, G-ROUTE (condition iv) |
| RK-28 | Model-written code escapes the B5 sandbox | L | H | The sandbox escape test fails | B5 runs only in a per-trial container whose only network route is the llama.cpp endpoint, killed on timeout, never in the host Harbor process | B5 moves to paper 2. The paper states that it makes no code-harness comparison | SK | E-B5, G-B5, E-INTERP |

### Highest-rated risks

These five risks matter most. Three are rated H for both likelihood and impact. The other two (RK-01, RK-03) decide when and whether budgeted runs can start.

1. **RK-05 floor effect** and **RK-14 single-loop variance**. Together they make a null or small result the most likely single outcome. The design accepts this and reports estimates with CIs.
2. **RK-25 timeline**. Engineering and about 45 GPU-days must fit an internship whose length is not yet agreed.
3. **RK-03 throughput** and **RK-01 no GPU**. The plan cannot start its budgeted episodes until both are known.

---

## Notes and sources

Facts below were checked against the cited source on or before 2026-10-20. "Simulation" means a planning simulation from the design review, not a measurement.

### RK-01 No GPU

- The compute asked for so far: a GPU with at least 24 GB, a Docker-capable Linux VM with about 100 GB of disk and 8 cores, and an API key with a budget. None had been granted as of 2026-10-20.
- The revised request in [EXPERIMENTS.md](EXPERIMENTS.md) and the design review: one NVIDIA GPU with at least 24 GB (32 GB or more recommended for two or more slots), 16 cores, 64 GB RAM, a 500 GB NVMe disk (1 TB recommended), dedicated during budgeted runs. It also asks for a consumer-class x86-64 machine (at least 8 GB VRAM, 32 GB RAM, Docker) for E-PORT.
- No model episode runs on the shared development machine. CPU-only work there runs in Docker within resource limits.
- API spend for paper-1 arms is $0. Point 6 of the meeting is read as "anyone can rerun the experiments without paying for an API" ([MEETING_2026-10-14.md](MEETING_2026-10-14.md)). Who provides the GPU is Q5 in [DECISIONS.md](DECISIONS.md#q5-compute-meeting-point-6).

### RK-02 Smaller GPU

- Qwen3.6-35B-A3B Q4_K_M weights are 20.61 GiB. f16 KV needs about 20 KiB per token. Estimated GPU memory: about 23.4 GiB for one 64k slot and 24.7 GiB for two (estimate). A 24 GB card therefore fits one slot at the 60-step context in f16. More slots need q8_0 KV or offload.
- Nemotron-Terminal-32B needs about 27.9 GiB with one 32k slot in f16 KV (24.2 GiB with q8_0), so it does not fit a 24 GB card. It is a fallback only on 32 GB or more.
- little-coder ran the same model on a laptop with 8 GB of VRAM and 32 GB of RAM, with MoE layers offloaded to the CPU, at about 44 tokens per second.
- Each fallback model costs at most 1,150 episodes, deducted from the available GPU-days. At most 2 fallbacks are tried on a 24 GB card and 3 on 32 GB or more.
- The floor is 6,224 episodes, 29.15 GPU-days at the planning rate.

### RK-03 Throughput

- The planning rate is 213.5 TB2 episodes per GPU-day: 86,400 s / 404.7 s, the mean over all 445 trials of little-coder's public Qwen3.6-35B-A3B run, which never ran two trials at once. It is a proxy with a ±30% band (149 to 278 per day).
- Trial time is heavy-tailed. The mean is 1.37 times the median of 296.4 s, and the longest trial took 4,589 s.
- The core plan is 9,653 episodes, 45.21 GPU-days at the planning rate, and 34.8 to 64.6 GPU-days across the band.
- An earlier figure of about 270 s per trial was wrong. It divided the time span of 287 resumed trials by all 445 trials. It is not used.
- A rate of about 500 per day at 4 slots is an unmeasured assumption and is not used.
- TB-Pro tasks have 3,600 s agent timeouts, against 900 s for 48 of the 89 TB2 tasks, so TB-Pro episodes may take longer. r is measured on TB-Pro at G0.

### RK-04 Model below the band

- In little-coder's run, Qwen3.6-35B-A3B solved 106 of 445 trials (23.8%). On the 82 TB2 tasks unchanged between its task commit and our pin, it solved 100 of 410 (24.39%). Both are inside the recorded 20 to 40% band.
- Our harness, sampling and budgets differ from that run, so our S0 score can differ. E3-REF compares the two descriptively only.
- Public figures for the fallbacks: Qwen3.5-35B-A3B 40.5% (vendor card) and 18.0% with Self-Harness's initial harness on a 64-task subset; TMax-9B 27.2 ± 1.5 (vendor, with its own harness). The order is **to confirm with Prof. Abdelrazek** (Q6 in [DECISIONS.md](DECISIONS.md#q6-fallback-models-meeting-point-6)).

### RK-05 Floor effect

- In little-coder's run, 54 of 89 TB2 tasks were never solved, 28 were contested and 7 were always solved. The committed held-out split of 37 tasks had only 11 contested tasks.
- Holding out all 89 TB2 tasks replaces the committed split, so it is **to confirm with Prof. Abdelrazek** (Q3). The default, if there is no answer by the Stage-1 freeze, is to hold out all 89.
- Planning MDEs (estimates): about 4.5 pp for S\* (10 runs) against S0 ×10, 5.8 to 5.9 pp for arms at 5 runs, and about 9.5 pp for the committed 37-task split at 5 runs.
- In simulation, the TB2 gain of one loop's chosen strategy has a between-loop mean of about 6.7 pp, close to these MDEs (see RK-13 and RK-14).
- Oracle best-of-2 headroom in the reference run is 7.9 pp (pass@2 31.7% against pass@1 23.8%). The gaps between S\* and BoN or B1 at matched compute may therefore be small.

### RK-06 Contested supply

- If TB-Pro's difficulty resembles TB2's (unverified), a task is contested at 5 runs with probability 0.308. With 120 survivors, 105 tasks enter E0, so C5 is about 32 (SD about 4.7), P(C5 ≥ 30) is about 0.7 and P(C5 < 20) is below 0.01. About 30% of the probability falls in the reduced-pool band 20 ≤ C5 < 30.
- At 3 runs the expected contested share is 22.6%.
- A TB2 re-split cannot cure a shortfall. Its 37 non-held-out tasks hold only about 12 contested tasks.

### RK-07 TB-Pro route

- TB-Pro has 200 tasks. No `task.toml` names a prebuilt image, and the repository has 201 Dockerfiles, so every image is built locally.
- The tasks use the older `version = "1.0"` schema. All set a 3,600 s agent timeout.
- Resources: 180 tasks ask for 1 CPU, 16 for 4, 2 for 2, and one each for 8 and 16. Memory is 2,048 MB for 180 tasks, 8,192 MB for 16, 16,384 MB for 2, and 4,096 and 8,092 MB for one task each. The provisional filter drops tasks above 4 CPUs or 8,192 MB.
- Harbor's Oracle agent runs a task's reference solution with no model, so the check costs no GPU time.

### RK-08 Leakage from TB-Pro

- In the committed TB2 split, all 9 known sibling pairs straddled the held-out set (5 siblings in A, 3 in M, 1 in V). Holding out all 89 TB2 tasks removes leakage inside TB2.
- Cross-source relatives exist. TB-Pro's `implement-tensor-parallel-matmul` and TB2's `torch-tensor-parallelism` cover the same topic with different specifications. They are related, not copies, which is why dedup uses owner review and not only an embedding threshold.

### RK-09 Notes and lessons

- The lint rejects exact task ids from the TB2 and TB-Pro lists, any URL, any command string over 40 characters, and any path that appears in a task's files or instructions.
- Notes and lessons are free text, so a lint cannot catch every paraphrase. The ablation arm with lessons_k = 0 and notes off measures how much of the gain flows through this channel.

### RK-10 Early TB2 contact

- Today the held-out guard in `evaluation/runner.py` is a boolean `final_evaluation` flag checked against the split name. It does not know task ids.
- Before Stage 2 the only allowed TB2 contact is pulling images by digest. Size simulations for the statistics use little-coder's public per-task rates, which are third-party data.

### RK-11 Internet access on TB2

- Every TB2 `task.toml` at commit `2fd12b8` sets `allow_internet = true`, and every task ships a public `solution/` directory. TB2 relies on a canary string only for contamination, with no private test set (see Terminal-Bench: Benchmarking Agents on Hard, Realistic Tasks in Command Line Interfaces ([Merrill et al., arXiv 2601.11868, Jan 2026](https://arxiv.org/abs/2601.11868))).
- Harbor's network modes are public, no-network and allowlist. There is no denylist, and rules match hosts, not paths ([Harbor network policies](https://github.com/harbor-framework/harbor/blob/main/docs-mintlify/tasks/network-policies.mdx)). Blocking only solution paths on github.com or huggingface.co would need a TLS-intercepting proxy.
- TB2 keeps its upstream setting so that our held-out numbers stay comparable with public TB2 results.
- The audit logs SNI (TLS server name) and DNS lookups per trial. It greps commands and observations for the canary GUID, "terminal-bench", "tbench", "harborframework", "laude-institute", "terminal-bench-pro" and "solution/".
- Residual risk: an agent that fetches and applies a fix without echoing a matching string leaves nothing to grep.
- If the run host cannot enforce the TB-Pro allowlist (no nftables for Harbor's egress sidecar), TB-Pro runs with public network and the full audit, logged as a deviation.

### RK-12 Memorisation

- TB-Pro was released by Alibaba with Let It Flow: Agentic Crafting on Rock and Roll, Building the ROME Model within an Open Agentic Learning Ecosystem ([Wang et al., arXiv 2512.24873, Dec 2025](https://arxiv.org/abs/2512.24873)). The Qwen models come from the same company. Shared provenance could inflate TB-Pro calibration scores. It cannot affect the TB2 held-out comparison directly.
- E0-MEM asks the model to complete the instruction from the task name on 20 TB-Pro tasks.

### RK-13 Selection overfitting

- In simulation, the plan's original rule accepted a null edit in about 52% of rounds, recording a fake gain of about +13.4 pp.
- A floating-point comparison in the original threshold (c/12 − p/12 ≥ 1/12) silently rejected about a third of one-task gains. CODE-FIX compares integer counts.
- In simulation, the adopted hybrid rule accepts about 4.4 edits per loop even when no edit helps. Under N(0, 0.3²) edit effects on the logit scale, the chosen version gains about 0.82 logit (about 6.6 pp on TB2) and ends worse than S0 in about 3.5% of loops. A second simulation of the same rule, summarised in pp per loop, gives a between-loop mean of 6.7 pp with 4.1% of loops below 0 (RK-14). The two figures are different summaries, not a conflict.
- Noise in selection biases the recorded edit deltas, not the held-out comparison, because TB2 is never used for selection.
- Per-loop cost is 1,365 episodes, with a cap of 1,575 by formula.

### RK-14 Single-loop variance

- In simulation, the chosen strategy's gain on TB2 has a mean of 6.7 pp and an SD of 4.7 pp between independent loops. In 35.5% of single loops the true gain is below the 4.5 pp MDE, 4.1% are below 0, and two independent loops differ by more than 5 pp 47% of the time.
- Two seeds at 5 runs each cost the same 890 TB2 episodes as one strategy at 10 runs. The extra cost is one adaptation loop on TB-Pro (1,365 episodes).
- "Diagnosis beats random search" is never claimed with fewer than 2 loops per arm. Gate G-H2 tests S\* against B4 only after the final run.

### RK-15 Weak baselines

- In the current code, the model client's temperature defaults to 0.0 (`llm/openai_compatible.py`), and its timeout is 120 s.
- B1 (`ReflectionRetry`) retries only when an own check explicitly fails. Own checks return None when no check applies, and Harbor uploads the task tests only at verification. As written, B1 therefore retries only when a strategy check returns an explicit failure.
- B2 (`BestOfN`) picks the first attempt whose own checks passed, or attempt 0. No judge selector exists yet.
- Sampling is pinned for all arms at temperature 0.6, top_p 0.95, top_k 20, the model card's setting for precise coding in thinking mode.

### RK-16 Judge

- The judge is the same local model. It scores each trajectory from the instruction, the trajectory and the outputs of agent-written tests.
- E0 gives about 600 TB-Pro trajectories with true labels, enough to estimate AUROC before Stage 2.

### RK-17 compile()

- Today only these fields act as controller behaviour: `exploration.probes` and `probe_budget_steps`, `tool_policy` (tools allowed, forbidden patterns, maximum observation length), `verification` (required, checks, maximum verify cycles) and the budget fields. Every other field reaches the agent only as prompt text.
- All `recovery.*` fields are text-only today. Recovery is in the minimum compiled set for that reason, and because it covers two of the four edit types that Self-Harness retained (command-retry discipline fully, loop breaking in part).
- Rollback values and `switch_to` are excluded from the paper-1 edit space, with unit tests.

### RK-18 Cost metric

- Three local-cost definitions conflict: [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md) section 4.3, [SMALL_MODELS.md](SMALL_MODELS.md) section 3.2 and `baselines/cost.py`. The code charges `model_s / 3600 × rate`, where `model_s` sums HTTP round-trip times. Under concurrency it also counts waiting for a free slot.
- A call-level fit can look good while one arm is biased, for example a strategy with longer contexts. The gate therefore checks each arm's mean episode residual (within ±3%, CI within ±5%, at least 40 TB-Pro episodes).
- Ways a strategy could look cheap without being better: giving up early on failed tasks, or moving work into diagnosis calls outside per-task cost. The outcome split (E-N3) shows the first. The payback T\* in E11 reports the second.
- Per-task matching treats the one-time adaptation cost as free. That choice is open to reading point 1 ("baseline cost : task") as total project cost per task.

### RK-19 Hardware dependence

- TB2 agent timeouts range from 600 to 12,000 s; 48 tasks use 900 s and 50 tasks are below 1,200 s.
- S0's committed wall-clock budget (`max_wall_s = 1200` in `strategy_schema/defaults.py`) is longer than the TB2 agent timeout on 50 of 89 tasks.
- In the reference run, 7 of 106 successful trials used more than half of their timeout, and 29 used more than a quarter. A slower machine would turn some of these into timeouts.
- Of the reference run's 8 timeouts, one still passed the verifier. Censoring at 1× therefore biases S0 downward by about 0.2 pp in that run.

### RK-20 llama.cpp reproducibility

- The llama.cpp server README says `cache_prompt` (default true) "can cause nondeterministic results", because logits are not guaranteed to be bit-for-bit identical across batch sizes ([llama.cpp server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)).
- The A/A run (60 episodes in E-P0) measures rho, the correlation between paired runs that share a seed.

### RK-21 Version drift

- As of 2026-10-20 the latest Harbor tag is v0.24.0. The plan proposes v0.23.0 (released 2026-09-12). The repository moved from `laude-institute/harbor` to `harbor-framework/harbor`.
- Our TB2 pin `2fd12b8` is 8 commits ahead of little-coder's task commit `69671fb`. The changes touch 7 tasks; one commit is titled "Various task fixes for TB2.1".
- TB2 images use the tag `alexgshaw/<task>:20251031`. A tag can be re-pushed, so images are pulled and recorded by digest.
- The evaluation study Rethinking the Evaluation of Harness Evolution for Agents ([Wang et al., arXiv 2607.12227, Jul 2026](https://arxiv.org/abs/2607.12227)) already reports on TB2.1.

### RK-22 Harness errors

- little-coder's result file records 8 AgentTimeoutError, 6 RuntimeError and 1 VerifierTimeoutError among 445 trials.
- Harbor v0.23.0 runs the agent inside an asyncio timeout and defaults to 4 concurrent trials. The current runner runs tasks one after another.
- The current client has a 120 s timeout. At about 44 tokens per second that allows at most about 5,280 generated tokens per call, so long reasoning calls would fail as errors.

### RK-23 Pre-emption by new papers

- Self-Harness: Harnesses That Improve Themselves ([Zhang et al., arXiv 2606.09498, Jun 2026](https://arxiv.org/abs/2606.09498)) evolves the harness of a frozen Qwen3.5-35B-A3B on TB2. On a 64-task subset, held-out pass rate rises from 23.8% to 38.1%. It has no best-of-N, reflection or cost-matched baseline.
- Rethinking the Evaluation of Harness Evolution for Agents ([Wang et al., arXiv 2607.12227, Jul 2026](https://arxiv.org/abs/2607.12227)) compares harness evolution with matched-budget best-of-N sampling and sequential refinement on TB2.1, with frontier API models only. It finds that harness evolution does not beat sampling on average. It is the closest precedent for our compute-matched framing. Among the harness-evolution methods we checked, none reports such a comparison.
- MetaRSI / RSI2: A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems Themselves ([Tan et al., arXiv 2609.06396, Sep 2026](https://arxiv.org/abs/2609.06396)) adapts a self-hosted Qwen3.5-35B-A3B on a sealed TB2.1 split, with equal budgets and five seeds. Its Harness-RSI-only condition edits a typed scaffold with the weights frozen and goes from 23.6 to 29.4. Its baselines are other improvement schedules. It has no test-time best-of-N or reflection baseline, so it does not fire the trigger as worded.
- ModularRSI: Modular and Generalizable Recursive Harness Self-Improvement ([Wu et al., arXiv 2609.14857, Sep 2026](https://arxiv.org/abs/2609.14857)) evolves on 2,000 tasks disjoint from TB2 and uses TB2 only for evaluation, with repeated runs and paired task-bootstrap CIs. Its main model is DeepSeek-V4-Flash-Preview, and it has no best-of-N baseline.
- Mixture of Self-Improving Branches For Agent Harness Optimization ([Dong et al., arXiv 2609.37834, Sep 2026](https://arxiv.org/abs/2609.37834)) routes each input to one evolved branch on TB2, which overlaps with E4-SW.
- At least 11 closely related papers appeared between March and September 2026 ([LITERATURE_MAP.md](LITERATURE_MAP.md)). The pace makes a new close paper likely before paper 1 is submitted (judgement).
- The Stage-1 tag, archived with a DOI, timestamps the design.

### RK-24 Readings of points 4 and 5

- Point 4, "intelligence index". Reading (a): one number for how efficiently the agent improves, after Chollet's skill-acquisition efficiency in On the Measure of Intelligence ([Chollet, arXiv 1911.01547, Nov 2019](https://arxiv.org/abs/1911.01547)). Reading (b): a composite over several benchmarks, for choosing models. Default if no answer by the Stage-1 freeze: (a), with the compute-equivalence ratio as the headline and the payback T\* as companion. **To confirm with Prof. Abdelrazek** (Q1 in [DECISIONS.md](DECISIONS.md#q1-intelligence-index-meeting-point-4)).
- Point 5, "strategy switching". Reading (a): a library of versions with a per-task selector. Reading (b): switching strategy mid-task when stuck. Default: (a) only, with mid-task switching in paper 2. **To confirm with Prof. Abdelrazek** (Q2 in [DECISIONS.md](DECISIONS.md#q2-strategy-switching-meeting-point-5)).
- An answer after the Stage-1 freeze: for point 4, a headline change is a logged deviation and all variants stay in the appendix. For point 5, E4b cannot meet its first gate, so mid-task switching moves to paper 2.
- Under reading (b) of point 4, if he wants our method scored across benchmarks, AppWorld returns as S0 against S\* at k=1, admitted only within the 12,500-episode absolute cap.

### RK-25 Timeline

- The internship's length, start date and weekly hours are still to be agreed. The default target is still about 24 weeks part-time ([DECISIONS.md](DECISIONS.md#plan-item-1-duration-start-date-hours-per-week-and-supervision-rhythm), plan item 1). The schedule in [EXECUTION_PLAN.md](EXECUTION_PLAN.md#how-the-plan-rescales) needs about 31 weeks at 20 hours per week. Finishing in 24 weeks needs about 28 hours per week, a later end date, or cuts (estimates).
- Engineering estimates (unverified): 2 to 3 weeks for G-INFRA, 1 to 1.5 weeks for P-M2, and 2 to 3 days for the TB-Pro allowlist fork.
- The core needs 45.21 GPU-days at the planning rate. On one GPU that is about 6.5 weeks of continuous, dedicated use (45.21 / 7, derived).

### RK-26 Licences

- TB-Pro: the Hugging Face dataset metadata says Apache-2.0. The GitHub repository `alibaba/terminal-bench-pro` has no LICENSE file at its root, and the GitHub API reports no licence (checked 2026-10-20).
- Self-Harness code (`github.com/qzzqzzb/Self-Harness`): the GitHub API reports no licence (checked 2026-10-20). We treat it as not reusable. E-N4 needs only the paper's description of its edits.

### RK-27 Disk space

- All 89 TB2 tasks use prebuilt amd64 images. Their compressed sizes on Docker Hub total 48.98 GB (median 0.149 GB, largest 8.82 GB for `mteb-leaderboard`).
- Unpacked on disk they may need about 100 to 150 GB (unverified estimate).
- The TB-Pro images are built locally; their footprint is unknown until P-M2 measures it.
- The disk originally requested was about 100 GB.

### RK-28 B5 sandbox

- B5 lets the proposer edit our controller code. That code then runs on every trial, so it must be isolated from the host.
- B5 is Tier C rank 4: 1,810 episodes, plus at most 5 engineering days for the sandbox. It also needs a 10-proposal smoke test (at least 5 apply cleanly and pass the controller unit tests).

---

## How this register is used

- It is reviewed at each gate: G-INFRA, G1, G0, Stage 1 and Stage 2. The other gates and their dates are in [EXECUTION_PLAN.md, section 4](EXECUTION_PLAN.md#4-gates).
- A risk that fires is logged in [DECISIONS.md](DECISIONS.md) with the contingency applied.
- Ratings are updated from measured values (r, C3 and C5, judge AUROC, MCU residuals) as they arrive.
- New risks get the next free id. Closed risks keep their id and are marked closed.
