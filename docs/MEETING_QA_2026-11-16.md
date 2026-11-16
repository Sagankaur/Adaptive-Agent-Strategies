# Plain-language meeting Q&A and recommendations

Prepared for the 2026-11-16 discussion with Prof. Mohamed Abdelrazek. This note explains the project choices and records the recommended path. It does not authorize any benchmark run or change the current no-TB2 rule.

## 1. Why is Qwen3.6 the primary model?

It was selected as the most defensible starting point for this particular study, not because it is proven to be the best or safest model.

- The project needs a model that can be served locally so the main experiment is reproducible without API spending.
- Qwen3.6-35B-A3B has an independent public Terminal-Bench 2 result of 106/445 trials, or 23.8%, inside the plan's 20–40% starting range. This is another researcher's aggregate result, not our run.
- The model is a mixture-of-experts model with about 3B active parameters. Its quantized file and serving path work on the A2I2 L40S.
- We have already shown that the local server, client, and Harbor adapter can communicate on a small synthetic task.

That gives Qwen3.6 the strongest evidence and the lowest setup cost among the current local candidates. It does not make Qwen3.6 safe by default. The Qwen advisory discussed Qwen3.8-Flash-Next, not our pinned Qwen3.6; the advisory's cause and intent are unknown. A2I2 nevertheless recommends caution and using a different model where possible.

### Why not the other candidates?

The current fallback list contains more than two alternatives:

| Candidate | Why it is not the current primary | Practical note |
|---|---|---|
| Qwen3.5-35B-A3B | Public evidence conflicts: a vendor card reports 40.5%, while a paper reports 18.0% on an initial 64-task subset. No independent full run was found. It is also another Qwen model, so it does not clearly address a concern about Qwen-family models. | Similar size and likely convenient to serve, but its starting score is uncertain. |
| TMax-9B | Its 27.2% result is vendor-reported with TMax's own harness; no independent rerun was found. TMax-9B is fine-tuned from Qwen3.5-9B. | Small and easy to fit, but its published result may not transfer to our harness, and it is still Qwen-derived. |
| Nemotron-Terminal-32B | NVIDIA reports 27.4% with Terminus 2; trial count and independent rerun are unavailable. It is a Qwen3-32B fine-tune, and its action format may not transfer cleanly to our adapter. | Fits the 48 GB L40S at the planned context estimate, but it is dense and likely slower. It also remains Qwen-derived. |
| GPT-5-mini | API-hosted, so it changes the local-reproducibility and zero-API-spend design. | Use only if Prof. Abdelrazek explicitly approves an API arm and budget. |

**Recommendation:** Keep Qwen3.6 as the provisional primary candidate because it has the best independent evidence and the pipeline already serves it. Keep real-model task-command runs paused until Prof. Abdelrazek explicitly chooses the model and the benchmark route clears. If he wants to follow A2I2's recommendation strictly, qualify a genuinely non-Qwen-family local candidate; merely moving among Qwen3.5, TMax, and Nemotron may not answer a family-level safety concern. Every model still needs the same egress isolation.

## 2. Is TB-Pro the only possible benchmark?

No. It is the main benchmark chosen for this study, not the only benchmark that exists. TB-Pro was selected because its 200 terminal tasks can support the planned strategy-development pools and give the paper a second source of terminal tasks. Other benchmarks can be used, but switching changes what the experiment demonstrates.

An initial engineering test can use a made-up task, as the current smoke tests do. A real pilot on another benchmark is possible after choosing and approving that benchmark, checking its licence and task images, adapting the runner, defining its scoring and resource limits, checking overlap/contamination, and amending the protocol. Those episodes would not count as TB-Pro E-P0 results.

The current plan also names TB2 as the held-out benchmark for cross-source evaluation. **That conflicts with your standing rule that no model, agent, Oracle, or reference solution may touch TB2.** The prepared E-RESPLIT route also uses TB2-related material, so it is not usable under the current rule without an explicit change—which we should not assume. The clean recommendation is to choose a different non-TB2 holdout or narrow the cross-benchmark generalization claim before any such run.

### Why is TB-Pro important to this plan?

TB-Pro is important because the protocol was designed around it; it is not uniquely important in all research. Its task set has 200 pinned tasks, but 198 currently depend on two Alibaba-hosted base images that time out from our networks. A different benchmark would need a full route and licence review too.

The reporter on public issue #10 says the two public GHCR bases yielded 192/200 passes in a full Oracle sweep and 199/200 cumulative passes after targeted reruns and environment repairs. That is promising evidence from another user, not our result or maintainer approval. The repairs mean it does not establish that GHCR images are equivalent to TB-Pro's intended images.

### What if TB-Pro still cannot be run?

1. Wait for the maintainers and the already-sent licence/image request; the public issue reply so far is from another user, not a maintainer.
2. If there is no maintainer response by 20 November, ask Prof. Abdelrazek whether he approves *proposing* the GHCR fallback and changing the relevant P-M2 rules. Do not silently adopt it.
3. If an approved and licensed route still cannot meet P-M2's minimum of 120 eligible tasks, record a NO-GO and stop the TB-Pro route.
4. Select a different benchmark that obeys the no-TB2 rule, or narrow the paper's claims. Update the design, resource estimates, and preregistration before running it.

## 3. What are Harbor and GHCR?

**Harbor** is the task-running harness. It starts a task environment, lets the agent send terminal commands, runs the task's verifier when the trial finishes, and records the reward. It coordinates the task; it does not serve the language model.

**GHCR** means GitHub Container Registry. It stores downloadable container images. A benchmark task's Dockerfile starts from a base image (for example, Ubuntu or Python) and adds task-specific software. GHCR is being considered as an alternate source for base images because the intended Alibaba registry is unreachable. Using another base can change the task environment, so the GHCR route needs approval and per-task validation.

In this project, Apptainer runs the task containers on the HPC cluster. A private Unix socket lets Harbor exchange commands with a network-isolated task container. That keeps the tested Harbor control path working without giving the task container a normal external network route.

## 4. Where is the code to restart a task?

There is **no working restart-task implementation yet**.

- [`strategy_schema/model.py`](../strategy_schema/model.py#L89) declares the value `RESTART_TASK = "restart_task"`. That makes the value representable in the data schema; it does not implement its behavior.
- [`baselines/agent_loop.py`](../baselines/agent_loop.py#L121) calls `env.reset(task)` once at the start of a baseline episode. It does not reset the task after a failure.
- [`environments/harbor_agent.py`](../environments/harbor_agent.py#L251) contains the Harbor agent's `run()` loop, but Harbor currently exposes no task reset/snapshot API to this adapter.
- [`G1-compile-2026-11.md`](experiments/G1-compile-2026-11.md) records why G1 implementation stopped.

Clearing the model's chat would leave changed files and running processes in place. Starting a new Harbor trial would be another episode and alter the budget. Neither should be called “restart task.”

**Recommendation:** Unless Prof. Abdelrazek knows a real reset that preserves the trial and budget, remove `restart_task` from paper 1's edit space and narrow the typed-strategy claim in the preregistration. Keep the other recovery behaviors only if each can be implemented and tested honestly.

## 5. What is the five-task smoke?

It is the final small infrastructure check before budgeted experiments. Once the task images and licence route are approved, run one engineering trial on each of five selected TB-Pro tasks using the approved model, Harbor adapter, Apptainer configuration, and network restrictions.

The smoke checks that tasks start, the agent can issue commands, Harbor collects logs and verifier rewards, and the harness completes with **zero harness errors**. Its five episodes are recorded as infrastructure checks, charged to contingency, and excluded from research analysis. Five tasks are too few to estimate solve rate or compare methods. It is not E-P0.

The five-task smoke must remain paused until the P-M2 route and licence, network controls, and Q9 model choice are settled. After it passes, E-P0 measures actual episode throughput, timeout rate, and model-compute coefficients.

## 6. Recommended decisions for the meeting

| Topic | Recommendation to propose | Why |
|---|---|---|
| Model (Q9) | Keep Qwen3.6 as the provisional candidate under network isolation; get explicit approval before any model-driven task run. If Mohamed wants a different model for safety reasons, qualify a non-Qwen-family candidate before switching. | Preserves the best comparable evidence while taking A2I2's advice seriously; does not call Qwen safe. |
| TB-Pro fallback | If maintainers remain silent by 20 November, seek explicit approval for a bounded GHCR route proposal. Adopt nothing until licence, image, survivor-count, and protocol criteria are agreed. | GHCR looks feasible, but current evidence is external and repaired. |
| Failed TB-Pro route | Declare route NO-GO if P-M2 fails; choose a non-TB2 benchmark or narrow the claim, and revise the preregistration. | The prepared TB2 fallback conflicts with the standing no-TB2 instruction. |
| G1 `restart_task` | Remove the field and narrow the claim unless a genuine budget-preserving Harbor reset is identified. | Avoids a misleading “restart” that only resets the chat or starts a new episode. |
| Five-task smoke | Define it as five engineering trials, zero harness errors, no research-score claims; run only after approvals and gates. | Confirms integration before spending the Phase-0 episode budget. |

## Short explanation to say aloud

> “Qwen3.6 is our provisional primary because it has the strongest independent local benchmark evidence in the target range and already runs on the cluster. That is not a safety conclusion. TB-Pro is our chosen main task set, not the only possible benchmark. If its image and licence route fails, I recommend a formal switch to a different non-TB2 benchmark or a narrower claim. The restart-task option is only declared in the schema; no real Harbor restart exists. The five-task smoke is an infrastructure check, not a result.”

