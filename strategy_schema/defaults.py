"""The hand-written starting strategy S0 used by baseline B0 (TECHNICAL_PLAN.md, section 4.1).

S0 explores briefly, plans, acts and checks before submitting. The numbers
are starting values, not tuned ones; Phase 1 will revisit them once a real
model has been run on the adaptation and selection splits.
"""

from __future__ import annotations

from strategy_schema.model import (
    Budget,
    Check,
    CheckpointPolicy,
    ContextMode,
    Exploration,
    Memory,
    OnRepeatedFailure,
    Planning,
    PlanningMode,
    Probe,
    Recovery,
    ReplanTrigger,
    RetryOn,
    RollbackTarget,
    Strategy,
    Tool,
    ToolPolicy,
    Verification,
    VerifyWhen,
)


def s0(strategy_id: str = "s0") -> Strategy:
    return Strategy(
        strategy_id=strategy_id,
        version=0,
        exploration=Exploration(
            probes=[Probe.LIST_WORKDIR, Probe.READ_README],
            probe_budget_steps=3,
            read_tests_first=True,
        ),
        planning=Planning(
            mode=PlanningMode.UPFRONT_WITH_REPLAN,
            planning_depth=6,
            replan_trigger=ReplanTrigger.ON_VERIFY_FAIL,
        ),
        tool_policy=ToolPolicy(
            tools_allowed=frozenset({Tool.BASH, Tool.FILE_VIEW, Tool.FILE_EDIT}),
            command_timeout_s=120,
            max_observation_chars=4000,
            forbidden_patterns=["rm -rf /"],
            edit_via_tool_not_shell=True,
        ),
        memory=Memory(
            context_mode=ContextMode.FULL,
            window_or_summary_k=20,
            state_notes=False,
            lessons_k=0,
            lesson_store_version="none",
        ),
        verification=Verification(
            verification_required=True,
            checks=[Check.RUN_VISIBLE_TESTS],
            when=VerifyWhen.BEFORE_SUBMIT,
            max_verify_cycles=2,
        ),
        recovery=Recovery(
            max_retries=1,
            retry_on=frozenset({RetryOn.NONZERO_EXIT, RetryOn.TIMEOUT}),
            on_repeated_failure=OnRepeatedFailure.REPLAN,
            checkpoint_policy=CheckpointPolicy.NONE,
            rollback_target=RollbackTarget.LAST_CHECKPOINT,
            max_rollbacks=0,
        ),
        budget=Budget(max_steps=40, max_tokens=200_000, max_wall_s=1200),
    )
