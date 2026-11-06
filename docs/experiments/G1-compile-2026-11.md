# G1 compile gate — feasibility note, 2026-11-06

## Status

**Open; implementation stopped before code changes. G1 is not green.** The P0-14/P0-15 implementation was paused under the project's stop rule because one required recovery value, `restart_task`, has no honest reset path in the current Harbor agent lifecycle.

## Evidence from the current interfaces

- `Strategy` exposes `recovery.on_repeated_failure = restart_task` in `strategy_schema/model.py`.
- The baseline `Environment` protocol has `reset(task)`, but `run_episode()` calls it only once at episode start. There is no restart transition in the controller.
- `HarborStrategyAgent.run()` receives the per-trial environment and uses its `exec()` interface. The adapter has no task reset, snapshot, or restore operation. A Harbor invocation is one trial over a mutable task environment.

Resetting only the model conversation would leave filesystem and process state from the failed attempt intact, so it would not be a task restart. Starting another Harbor trial would create another episode and change the registered budget and accounting. The adapter therefore cannot currently implement `restart_task` honestly.

## Consequence for P0-14/P0-15

The required compiled set includes all three `on_repeated_failure` values: `continue`, `replan`, and `restart_task`. Since that field cannot be compiled for the Harbor route as specified, I stopped before adding the compiler, field labels, generated Table 2, or tests. No G1 test IDs exist yet; the E-N4 audit has not been rerun against a changed controller. The prior audit describes the current repository snapshot only.

The typed-strategy claim must be narrowed in the pre-registration if this reset limitation remains. Before implementation resumes, the design needs either an explicitly supported, budget-preserving Harbor reset operation or an approved change to the paper-1 recovery values and claim. A conversation-only reset must not be called `restart_task`.

No TB2 task text was read for this feasibility check. No benchmark task, model, agent, Oracle, or reference solution was run.
