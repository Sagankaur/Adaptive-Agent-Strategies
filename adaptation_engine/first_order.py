"""The interface of one first-order adaptation round (TECHNICAL_PLAN.md, section 5.1).

A round takes the current strategy S_r through: run on the adaptation split,
diagnose failures, aggregate diagnoses by (failure class, dimension), propose
candidate edits, evaluate each candidate and S_r on the selection split, and
accept the best candidate only if it improves success by at least a threshold
without going over a cost cap. Every candidate gets its own version number,
so rejected candidates stay traceable; the accepted one carries its measured
effect in its changelog, and the round record keeps its per-dimension diff
from S_r.

The diagnoser and proposer here are trivial rules so the loop can be
exercised offline. The LLM diagnoser and proposer, the staged evaluation on
half of V, stopping rules and the lesson store are Phase 2 work. The
second-order loop (section 6), which revises the mechanism itself, is not
implemented.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from baselines.baselines import TaskOutcome
from strategy_schema.edits import apply_edits
from strategy_schema.model import EDITABLE_DIMENSIONS, Check, Edit, FieldChange, PlanningMode, Probe, Strategy


class FailureClass(StrEnum):
    """Seed taxonomy: the Terminal-Bench paper's trajectory-level classes, plus one environment-setup class."""

    DISOBEYING_SPECIFICATION = "disobeying_specification"
    STEP_REPETITION = "step_repetition"
    UNAWARE_OF_TERMINATION = "unaware_of_termination"
    REASONING_ACTION_MISMATCH = "reasoning_action_mismatch"
    CONTEXT_LOSS = "context_loss"
    TASK_DERAILMENT = "task_derailment"
    PREMATURE_TERMINATION = "premature_termination"
    NO_OR_INCORRECT_VERIFICATION = "no_or_incorrect_verification"
    WEAK_VERIFICATION = "weak_verification"
    ACTED_BEFORE_CHECKING_ENVIRONMENT = "acted_before_checking_environment"


class Diagnosis(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    diagnosis_id: str
    task_id: str
    failure_class: FailureClass
    critical_step: int | None
    evidence: str
    implicated_dimensions: list[str] = Field(min_length=1)

    @field_validator("implicated_dimensions")
    @classmethod
    def _known(cls, value: list[str]) -> list[str]:
        unknown = set(value) - set(EDITABLE_DIMENSIONS)
        if unknown:
            raise ValueError(f"not editable dimensions: {sorted(unknown)}")
        return value


@dataclass(frozen=True)
class DiagnosisGroup:
    failure_class: FailureClass
    dimension: str
    diagnosis_ids: list[str]

    @property
    def count(self) -> int:
        return len(self.diagnosis_ids)


class Diagnoser(Protocol):
    def diagnose(self, outcomes: Sequence[TaskOutcome]) -> list[Diagnosis]: ...


class Proposer(Protocol):
    def propose(
        self, strategy: Strategy, groups: Sequence[DiagnosisGroup], k: int, round_index: int
    ) -> list[list[Edit]]:
        """Up to ``k`` candidate edits, each of one or two operations."""
        ...


@dataclass(frozen=True)
class Score:
    """A strategy's result on the selection split; ``mean_cost`` is in whatever unit the evaluator uses."""

    success_rate: float
    mean_cost: float


Runner = Callable[[Strategy], Sequence[TaskOutcome]]
Evaluator = Callable[[Strategy], Score]


@dataclass
class CandidateResult:
    strategy: Strategy
    edits: list[Edit]
    score: Score
    delta: float


@dataclass
class RoundRecord:
    round_index: int
    parent_version: int
    parent_score: Score
    diagnoses: list[Diagnosis]
    groups: list[DiagnosisGroup]
    candidates: list[CandidateResult] = field(default_factory=list)
    accepted_version: int | None = None
    diff: dict[str, list[FieldChange]] = field(default_factory=dict)


def aggregate(diagnoses: Sequence[Diagnosis]) -> list[DiagnosisGroup]:
    """Group diagnoses by (failure class, dimension), most frequent first."""
    groups: dict[tuple[FailureClass, str], list[str]] = defaultdict(list)
    for d in diagnoses:
        for dimension in d.implicated_dimensions:
            groups[(d.failure_class, dimension)].append(d.diagnosis_id)
    ranked = sorted(groups.items(), key=lambda item: (-len(item[1]), item[0][0], item[0][1]))
    return [DiagnosisGroup(cls, dim, ids) for (cls, dim), ids in ranked]


def run_round(
    strategy: Strategy,
    *,
    round_index: int,
    next_version: int,
    run_adaptation: Runner,
    evaluate_selection: Evaluator,
    diagnoser: Diagnoser,
    proposer: Proposer,
    min_delta: float,
    max_mean_cost: float | None = None,
    k: int = 4,
) -> tuple[Strategy, RoundRecord]:
    """One round from S_r; returns the strategy to continue with (S_r if nothing is accepted)."""
    outcomes = run_adaptation(strategy)
    diagnoses = diagnoser.diagnose(outcomes)
    groups = aggregate(diagnoses)
    parent_score = evaluate_selection(strategy)
    record = RoundRecord(round_index, strategy.version, parent_score, diagnoses, groups)

    for offset, edits in enumerate(proposer.propose(strategy, groups, k, round_index)[:k]):
        candidate = apply_edits(strategy, edits, version=next_version + offset)
        score = evaluate_selection(candidate)
        record.candidates.append(
            CandidateResult(candidate, edits, score, score.success_rate - parent_score.success_rate)
        )

    eligible = [
        c
        for c in record.candidates
        if c.delta > 0 and c.delta >= min_delta and (max_mean_cost is None or c.score.mean_cost <= max_mean_cost)
    ]
    if not eligible:
        return strategy, record

    best = max(eligible, key=lambda c: (c.delta, -c.score.mean_cost, -c.strategy.version))
    measured = [e.model_copy(update={"measured_delta": best.delta}) for e in best.edits]
    accepted = apply_edits(strategy, measured, version=best.strategy.version)
    record.accepted_version = accepted.version
    record.diff = strategy.diff(accepted)
    return accepted, record


class RuleBasedDiagnoser:
    """Labels each failed outcome with the first matching rule, from its selected attempt's step table.

    It reads hidden-test results, which is allowed only on the adaptation split.
    """

    def diagnose(self, outcomes: Sequence[TaskOutcome]) -> list[Diagnosis]:
        diagnoses = []
        for outcome in outcomes:
            if outcome.success:
                continue
            attempt = outcome.attempts[outcome.selected]
            kinds = [s.kind for s in attempt.steps]
            last = attempt.steps[-1] if attempt.steps else None
            evidence = last.observation.splitlines()[0] if last and last.observation else ""
            critical = last.index if last else None
            if attempt.stop_reason == "step_limit":
                cls, dims = FailureClass.UNAWARE_OF_TERMINATION, ["planning"]
            elif "verify" not in kinds:
                cls, dims = FailureClass.NO_OR_INCORRECT_VERIFICATION, ["verification"]
            elif attempt.own_check_passed:
                cls, dims = FailureClass.WEAK_VERIFICATION, ["verification"]
            elif "probe" not in kinds:
                cls, dims = FailureClass.ACTED_BEFORE_CHECKING_ENVIRONMENT, ["exploration"]
            else:
                cls, dims = FailureClass.PREMATURE_TERMINATION, ["verification"]
            diagnoses.append(
                Diagnosis(
                    diagnosis_id=f"d-{outcome.task_id}-v{attempt.strategy_version}",
                    task_id=outcome.task_id,
                    failure_class=cls,
                    critical_step=critical,
                    evidence=evidence,
                    implicated_dimensions=dims,
                )
            )
        return diagnoses


class RuleBasedProposer:
    """Maps each top (class, dimension) group to one fixed edit for that dimension, if one applies."""

    def propose(
        self, strategy: Strategy, groups: Sequence[DiagnosisGroup], k: int, round_index: int
    ) -> list[list[Edit]]:
        candidates: list[list[Edit]] = []
        used: set[str] = set()
        for group in groups:
            if len(candidates) >= k:
                break
            ops = self._ops_for(strategy, group.dimension)
            if not ops or group.dimension in used:
                continue
            used.add(group.dimension)
            rationale = f"rule: {group.failure_class} implicates {group.dimension} in {group.count} failures"
            candidates.append(
                [
                    Edit(
                        op=op,
                        path=path,
                        value=value,
                        rationale=rationale,
                        diagnosis_ids=group.diagnosis_ids,
                        round=round_index,
                    )
                    for op, path, value in ops
                ]
            )
        return candidates

    @staticmethod
    def _ops_for(strategy: Strategy, dimension: str) -> list[tuple[str, str, object]]:
        v, e, p = strategy.verification, strategy.exploration, strategy.planning
        if dimension == "verification":
            if not v.verification_required:
                ops: list[tuple[str, str, object]] = [("replace", "/verification/verification_required", True)]
                if not v.checks:
                    ops.append(("add", "/verification/checks/-", Check.RUN_VISIBLE_TESTS.value))
                return ops
            if Check.RUN_VISIBLE_TESTS not in v.checks:
                return [("add", "/verification/checks/-", Check.RUN_VISIBLE_TESTS.value)]
            if v.max_verify_cycles < 5:
                return [("replace", "/verification/max_verify_cycles", v.max_verify_cycles + 1)]
        if dimension == "exploration":
            missing = [probe for probe in Probe if probe not in e.probes]
            if missing:
                ops = [("add", "/exploration/probes/-", missing[0].value)]
                if e.probe_budget_steps < min(10, len(e.probes) + 1):
                    ops.append(("replace", "/exploration/probe_budget_steps", len(e.probes) + 1))
                return ops
        if dimension == "planning" and p.mode == PlanningMode.NONE:
            return [("replace", "/planning/mode", PlanningMode.UPFRONT.value)]
        return []
