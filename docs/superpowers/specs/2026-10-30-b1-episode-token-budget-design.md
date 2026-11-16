# B1 episode token budget design

## Intent

Make the B1 reflection/retry arm obey the study-wide ceiling of 64,000 generated tokens for the complete task-level B1 run. Count every agent, blind-judge, and reflection completion against the same allowance, including reasoning tokens reported as output tokens.

## Why

The paper protocol sets a 64k generated-token limit per episode, but the B1 table currently grants 64k to each of up to three attempts. The synchronous agent loop also compares input plus output tokens to the budget, although the protocol defines generated tokens. Together these discrepancies make B1's resource contract ambiguous and can make the implemented cap differ from the reported one.

## Goals

- Enforce one shared 64,000 generated-token allowance across all B1 model calls for a task/run.
- Pass the remaining allowance to the OpenAI-compatible API as a per-request output-token cap.
- Stop cleanly when the budget prevents an agent, judge, or reflection call; never infer a judge result or trigger a retry from hidden reward.
- Record actual agent, judge, and reflection output-token usage once in the episode cost record, and make a provider overrun visible.
- Apply `budget.max_tokens` to generated output in the single-attempt loop, rather than input-plus-output tokens.
- Keep the predeclared B1 attempt cap `k` separate from the token cap; the token ceiling can end a B1 run before `k` attempts.

## Non-goals

- Do not change the `{1,2,3}` attempt-cap randomization or its Stage-2 compute-matching distribution in this change; that distribution must be frozen from the planned cost-matching evidence.
- Do not change B2's selection method or its post-trial judge accounting.
- Do not run TB-Pro tasks or use hidden reward to decide retries.

## Approaches considered

1. **Keep 64k per B1 attempt.** Smallest code change, but allows a three-attempt B1 run to consume up to 192k agent tokens plus judge/reflection output and conflicts with the global per-episode rule.
2. **Count output tokens after each call without limiting the request.** Simple accounting, but an individual response can exceed the remaining allowance, so it does not enforce the stated cap.
3. **Share one episode budget and pass remaining output tokens to each request (selected).** This matches the global protocol, includes B1 overhead, and prevents normal compliant servers from generating beyond the remaining budget. Provider-reported overruns remain explicitly visible.

## Decisions

- The B1 budget is 64,000 output/generated tokens for the complete B1 task/run, including agent replies, judge replies, and reflection replies. Input/prompt tokens remain costed but do not consume this cap.
- Each request receives `min(configured per-attempt remainder, B1 run remainder)` as its maximum completion-token allowance.
- If no budget remains before a judge call, record that the judge was skipped for budget exhaustion and stop with the most recent completed attempt selected. If the judge completes but leaves no allowance, do not request reflection or begin another attempt.
- If a provider reports more output tokens than requested, retain actual usage, mark the run as a budget overrun, and do not make further model calls.
- Never execute a tool action parsed from an over-limit agent response; retain its response usage for the record and terminate that attempt.
- If the per-attempt cap is reached while shared B1 allowance remains, finish judging that attempt and allow a retry if the normal trigger fires.
- The requested B1 attempt cap `k` remains recorded as planned; actual completed attempts and early budget stop are recorded separately.

## Constraints

- Preserve blind judging: the judge receives only the task instruction and public attempt record.
- Preserve the no-reset retry behavior and seeded model-call logging.
- Keep total cost accounting as agent attempts plus B1 extra calls; judgment details embedded in an attempt are audit metadata and must not be counted a second time.

## Builder decisions

- Use an optional per-call `max_output_tokens` parameter on the synchronous `ChatModel.complete` API. The effective request cap is the lower of the per-call limit and the configured client maximum, when one is set.
- Implement one budget wrapper for B1 and pass it to agent, judge, and reflection code. Keep the generic agent-loop cap as a separate per-attempt ceiling.
- Add focused offline tests for decreasing request caps, exhausted-budget stop behavior, and generated-token accounting. Run the complete offline acceptance suite after those tests pass.
