# gpt-oss Tool-Contract Diagnostic Plan

> **Status:** Executing the user-approved synthetic serving diagnostic. No benchmark tasks or agent tools are involved.

**Goal:** Determine whether pinned gpt-oss produces valid native calls under the Aider pilot's 8K context and whether a larger context changes those interface outcomes.

**Architecture:** A single Slurm job runs a local llama.cpp server one context at a time on Rohan's RTX Pro 6000. A Python client generates inert synthetic multi-turn conversations, pre-counts exact prompt tokens, validates outputs without invoking tools, and persists only aggregate metrics.

**Tech Stack:** Python 3 standard library, Apptainer, llama.cpp server, Slurm.

**Spec:** `docs/experiments/gpt-oss-tool-context-diagnostic-2026-11-19.md`

## Global Constraints

- No tasks, benchmarks, Oracle, reference solutions, or agent command execution.
- Bind inference server to localhost; no tool executor exists.
- Retain no raw prompts, completions, tool names, or argument values.
- Stop if GPU headroom falls below 1 GiB; require exact input token counts before inference.
- Continue from HTTP 400 at 8K to 32K only if classified as a context error and server health/headroom are adequate.

## Review Focus

- VRAM drops during an in-flight request: terminate server and discard response.
- HTTP 400 vs transport/5xx: stop at the right scope and retain only a boolean context-error candidate.
- Malformed/unhashable tool arguments: classify without raising or persisting values.
- Partial cells: report planned, attempted, and HTTP 200 denominators explicitly.
- Hash provenance: record the pinned model, SIF, runner, and preregistration protocol hashes.

---

### Task 1: Freeze, review, and run the diagnostic

**Files:**
- Modify: `docs/cluster/serving-sweep/03_gpt_oss_tool_context_diagnostic.py`
- Modify: `docs/cluster/serving-sweep/03_gpt_oss_tool_context_diagnostic.sbatch`
- Modify: `docs/experiments/gpt-oss-tool-context-diagnostic-2026-11-19.md`
- Result: `docs/experiments/artifacts/gpt-oss-tool-context-diagnostic-2026-11-19.json`

- [x] Draft the protocol and runner.
- [x] Add cancellable inference, conservative stop behavior, explicit metric denominators, and protocol hash input.
- [x] Get independent review of the revised implementation and address blockers (VRAM monitor fail-closed; zero-attempt cells retained; JSON syntax rate independent of tool-name validity).
- [x] Run syntax/whitespace checks and inspect the staged diff.
- [x] Commit and push the preregistration/runner to the experiment branch.
- [x] Stage inputs on Rohan, verify pinned hashes, submit one short job, and collect only sanitized `results.json`.
- [x] Update the report with observed counts, resource evidence, deviations, and limitations; push the result record.
