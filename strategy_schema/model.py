"""The typed, versioned strategy object of TECHNICAL_PLAN.md, section 3.2.

Field names, types and ranges follow the table in section 3.2. Where the plan
leaves a type or range open, the simplest choice was taken and is stated on
the field's model:

- ``memory.window_or_summary_k`` (plan: ``int``) must be at least 1.
- ``budget.*`` (plan: ``int``) must be at least 1.
- ``planning.replan_every_k`` must be set when ``replan_trigger`` is
  ``every_k_steps``; it is ignored otherwise.
- ``probes`` and ``checks`` are lists without duplicates; ``tools_allowed`` and
  ``retry_on`` are sets, serialised as sorted lists so JSON output is stable.
- The meta fields (``strategy_id``, ``version``, ``parent_version``,
  ``changelog``) sit at the top level; every other dimension is a nested
  object, so edit paths look like ``/exploration/probes/-`` as in the plan.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_serializer, model_validator


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Probe(StrEnum):
    LIST_WORKDIR = "list_workdir"
    READ_README = "read_readme"
    INSPECT_TESTS = "inspect_tests"
    CHECK_TOOLCHAIN_VERSIONS = "check_toolchain_versions"
    CHECK_INSTALLED_PACKAGES = "check_installed_packages"
    CHECK_SERVICES = "check_services"
    GIT_STATUS = "git_status"


class PlanningMode(StrEnum):
    NONE = "none"
    UPFRONT = "upfront"
    UPFRONT_WITH_REPLAN = "upfront_with_replan"


class ReplanTrigger(StrEnum):
    NEVER = "never"
    ON_ERROR = "on_error"
    ON_VERIFY_FAIL = "on_verify_fail"
    EVERY_K_STEPS = "every_k_steps"


class Tool(StrEnum):
    BASH = "bash"
    FILE_VIEW = "file_view"
    FILE_EDIT = "file_edit"
    PYTHON = "python"


class ContextMode(StrEnum):
    FULL = "full"
    SLIDING_WINDOW = "sliding_window"
    SUMMARISE = "summarise"


class Check(StrEnum):
    RUN_VISIBLE_TESTS = "run_visible_tests"
    BUILD = "build"
    RUN_TASK_EXAMPLE = "run_task_example"
    REREAD_INSTRUCTIONS_CHECKLIST = "reread_instructions_checklist"
    CHECK_OUTPUT_ARTIFACTS = "check_output_artifacts"


class VerifyWhen(StrEnum):
    BEFORE_SUBMIT = "before_submit"
    AFTER_EACH_SUBGOAL = "after_each_subgoal"


class RetryOn(StrEnum):
    NONZERO_EXIT = "nonzero_exit"
    TIMEOUT = "timeout"
    VERIFY_FAIL = "verify_fail"


class OnRepeatedFailure(StrEnum):
    CONTINUE = "continue"
    REPLAN = "replan"
    ROLLBACK = "rollback"
    RESTART_TASK = "restart_task"


class CheckpointPolicy(StrEnum):
    NONE = "none"
    BEFORE_RISKY_COMMANDS = "before_risky_commands"
    AFTER_EACH_VERIFIED_SUBGOAL = "after_each_verified_subgoal"


class RollbackTarget(StrEnum):
    LAST_CHECKPOINT = "last_checkpoint"
    LAST_VERIFIED_SUBGOAL = "last_verified_subgoal"
    DIAGNOSED_STEP = "diagnosed_step"


class Stage(StrEnum):
    EXPLORE = "explore"
    PLAN = "plan"
    ACT = "act"
    VERIFY = "verify"
    RECOVER = "recover"


def _no_duplicates(items: list[Any], name: str) -> None:
    if len(set(items)) != len(items):
        raise ValueError(f"{name} must not contain duplicates")


class Exploration(_Frozen):
    """What the agent looks at before it plans."""

    probes: list[Probe]
    probe_budget_steps: int = Field(ge=0, le=10)
    read_tests_first: bool

    @model_validator(mode="after")
    def _unique(self) -> Exploration:
        _no_duplicates(self.probes, "probes")
        return self


class Planning(_Frozen):
    """Whether and how an explicit plan is written and revised."""

    mode: PlanningMode
    planning_depth: int = Field(ge=0, le=12)
    replan_trigger: ReplanTrigger
    replan_every_k: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _k_required(self) -> Planning:
        if self.replan_trigger == ReplanTrigger.EVERY_K_STEPS and self.replan_every_k is None:
            raise ValueError("replan_every_k is required when replan_trigger is every_k_steps")
        return self


class ToolPolicy(_Frozen):
    """Which tools the loop exposes and how their output reaches the model."""

    tools_allowed: frozenset[Tool]
    command_timeout_s: int = Field(ge=10, le=600)
    max_observation_chars: int = Field(ge=500, le=20000)
    forbidden_patterns: list[str]
    edit_via_tool_not_shell: bool

    @field_serializer("tools_allowed")
    def _sorted(self, value: frozenset[Tool]) -> list[str]:
        return sorted(value)


class Memory(_Frozen):
    """How past steps, environment state and cross-task lessons are kept."""

    context_mode: ContextMode
    window_or_summary_k: int = Field(ge=1)
    state_notes: bool
    lessons_k: int = Field(ge=0, le=5)
    lesson_store_version: str = Field(min_length=1)


class Verification(_Frozen):
    """What "checking my work" means and how often the agent may go back to fixing."""

    verification_required: bool
    checks: list[Check]
    when: VerifyWhen
    max_verify_cycles: int = Field(ge=0, le=5)

    @model_validator(mode="after")
    def _unique(self) -> Verification:
        _no_duplicates(self.checks, "checks")
        return self


class Recovery(_Frozen):
    """Retries, and what happens when they run out (including rollback)."""

    max_retries: int = Field(ge=0, le=5)
    retry_on: frozenset[RetryOn]
    on_repeated_failure: OnRepeatedFailure
    checkpoint_policy: CheckpointPolicy
    rollback_target: RollbackTarget
    max_rollbacks: int = Field(ge=0, le=3)

    @field_serializer("retry_on")
    def _sorted(self, value: frozenset[RetryOn]) -> list[str]:
        return sorted(value)


class Budget(_Frozen):
    """Per-episode caps fixed by the experimenter; edits may not change them."""

    max_steps: int = Field(ge=1)
    max_tokens: int = Field(ge=1)
    max_wall_s: int = Field(ge=1)


NoteText = Annotated[str, StringConstraints(max_length=300)]


class Edit(_Frozen):
    """One JSON-Patch-like operation with its rationale and evidence (section 3.2).

    ``measured_delta`` is not in the plan's example edit; it is where the
    selection step records the measured change in success rate, which
    section 3.1 requires every version to carry.
    """

    op: Literal["add", "remove", "replace"]
    path: str = Field(pattern=r"^/")
    value: Any = None
    rationale: str = ""
    diagnosis_ids: list[str] = Field(default_factory=list)
    round: int | None = Field(default=None, ge=0)
    measured_delta: float | None = None


class FieldChange(_Frozen):
    """One field that differs between two strategy versions."""

    path: str
    before: Any
    after: Any


DIMENSIONS: tuple[str, ...] = (
    "exploration",
    "planning",
    "tool_policy",
    "memory",
    "verification",
    "recovery",
    "notes",
    "budget",
)
EDITABLE_DIMENSIONS: tuple[str, ...] = tuple(d for d in DIMENSIONS if d != "budget")


class Strategy(_Frozen):
    """A complete, versioned agent strategy.

    Two versions can be compared with :meth:`diff`, which is what attributing a
    gain to a single dimension (RQ4) is built on. :meth:`render` produces the
    instruction text an agent receives; whether each field also changes the
    controller's actions is up to the agent loop that reads it.
    """

    strategy_id: str = Field(min_length=1)
    version: int = Field(ge=0)
    parent_version: int | None = Field(default=None, ge=0)
    changelog: list[Edit] = Field(default_factory=list)

    exploration: Exploration
    planning: Planning
    tool_policy: ToolPolicy
    memory: Memory
    verification: Verification
    recovery: Recovery
    notes: dict[Stage, NoteText] = Field(default_factory=dict)
    budget: Budget

    @model_validator(mode="after")
    def _lineage(self) -> Strategy:
        if self.parent_version is not None and self.parent_version >= self.version:
            raise ValueError("parent_version must be lower than version")
        return self

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, text: str) -> Strategy:
        return cls.model_validate_json(text)

    def diff(self, other: Strategy) -> dict[str, list[FieldChange]]:
        """Per-dimension field changes from ``self`` to ``other``; meta fields are ignored."""
        before = self.model_dump(mode="json")
        after = other.model_dump(mode="json")
        changes: dict[str, list[FieldChange]] = {}
        for dimension in DIMENSIONS:
            old, new = before[dimension], after[dimension]
            keys = sorted(set(old) | set(new))
            dim_changes = [
                FieldChange(path=f"/{dimension}/{key}", before=old.get(key), after=new.get(key))
                for key in keys
                if old.get(key) != new.get(key)
            ]
            if dim_changes:
                changes[dimension] = dim_changes
        return changes

    def render(self) -> str:
        """The instruction text an agent following this strategy is given."""
        e, p, t, m, v, r, b = (
            self.exploration,
            self.planning,
            self.tool_policy,
            self.memory,
            self.verification,
            self.recovery,
            self.budget,
        )
        lines = [f"Strategy {self.strategy_id} v{self.version}", ""]

        if e.probes and e.probe_budget_steps > 0:
            lines.append(
                f"Exploration: before planning, spend at most {e.probe_budget_steps} steps on these probes: "
                + ", ".join(e.probes)
                + "."
            )
        else:
            lines.append("Exploration: no probes before planning.")
        if e.read_tests_first:
            lines.append("Read any visible tests or examples before acting.")

        if p.mode == PlanningMode.NONE:
            lines.append("Planning: do not write an explicit plan.")
        else:
            trigger = {
                ReplanTrigger.NEVER: "do not revise it",
                ReplanTrigger.ON_ERROR: "revise it when a command fails",
                ReplanTrigger.ON_VERIFY_FAIL: "revise it when a check fails",
                ReplanTrigger.EVERY_K_STEPS: f"revise it every {p.replan_every_k} steps",
            }[p.replan_trigger]
            replan = trigger if p.mode == PlanningMode.UPFRONT_WITH_REPLAN else "do not revise it"
            lines.append(f"Planning: write a plan up front with at most {p.planning_depth} sub-goals; {replan}.")

        tools = ", ".join(sorted(t.tools_allowed)) or "none"
        lines.append(
            f"Tools: you may use {tools}. Commands time out after {t.command_timeout_s} s; "
            f"you will see at most {t.max_observation_chars} characters of output."
        )
        if t.forbidden_patterns:
            lines.append("Never run commands containing any of: " + ", ".join(repr(x) for x in t.forbidden_patterns))
        if t.edit_via_tool_not_shell:
            lines.append("Edit files with the edit tool, not with sed or echo.")

        context = {
            ContextMode.FULL: "you see the full history of this task",
            ContextMode.SLIDING_WINDOW: f"you see the last {m.window_or_summary_k} steps",
            ContextMode.SUMMARISE: f"older steps are summarised every {m.window_or_summary_k} steps",
        }[m.context_mode]
        lines.append(f"Memory: {context}.")
        if m.state_notes:
            lines.append(
                "Keep a running record of environment state: files created, packages installed, services started."
            )
        if m.lessons_k > 0:
            lines.append(f"Use up to {m.lessons_k} lessons from lesson store {m.lesson_store_version}.")

        if v.verification_required and v.checks:
            when = "before submitting" if v.when == VerifyWhen.BEFORE_SUBMIT else "after each sub-goal"
            lines.append(
                f"Verification: {when}, run these checks: " + ", ".join(v.checks) + ". "
                f"After a failed check you may go back to fixing at most {v.max_verify_cycles} times."
            )
        else:
            lines.append("Verification: none required.")

        retry_on = ", ".join(sorted(r.retry_on)) or "nothing"
        lines.append(
            f"Recovery: retry a failing action up to {r.max_retries} times on: {retry_on}. "
            f"When retries run out: {r.on_repeated_failure}."
        )
        if r.checkpoint_policy != CheckpointPolicy.NONE:
            lines.append(
                f"Take checkpoints {r.checkpoint_policy.replace('_', ' ')}; roll back to the "
                f"{r.rollback_target.replace('_', ' ')}, at most {r.max_rollbacks} times."
            )

        lines.append(f"Budget: at most {b.max_steps} steps, {b.max_tokens} tokens and {b.max_wall_s} s.")

        if self.notes:
            lines.append("")
            lines.append("Notes:")
            lines.extend(f"- [{stage}] {self.notes[stage]}" for stage in Stage if stage in self.notes)
        return "\n".join(lines)
