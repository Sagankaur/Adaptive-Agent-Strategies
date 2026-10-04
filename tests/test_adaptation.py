from __future__ import annotations

from pathlib import Path

from adaptation_engine import (
    Diagnosis,
    DiagnosisGroup,
    FailureClass,
    RuleBasedDiagnoser,
    RuleBasedProposer,
    Score,
    aggregate,
    run_round,
)
from baselines import FixedStrategy
from environments import Task, ToyTextEnvironment
from evaluation.runner import evaluate, summarise
from evaluation.splits import TaskInfo, make_split
from llm import MockModel
from strategy_schema import Strategy
from tests.helpers import edited, solver


def test_round_accepts_edit_that_fixes_diagnosed_failures(
    tasks: list[Task], strategy: Strategy, tmp_path: Path
) -> None:
    by_id = {t.task_id: t for t in tasks}
    infos = [TaskInfo(task_id=t.task_id, category=t.category, difficulty=t.difficulty) for t in tasks]
    split = make_split(infos, {"A": 6, "V": 6}, seed=0, benchmark="toy-text")
    start = edited(strategy, ("replace", "/verification/verification_required", False))

    def run(s: Strategy, split_name: str):
        return evaluate(
            run_id=f"{split_name}-v{s.version}",
            baseline=FixedStrategy(),
            strategy=s,
            model=MockModel(solver(sloppy_first=True)),
            env=ToyTextEnvironment(),
            tasks=by_id,
            split=split,
            split_name=split_name,
            out_path=tmp_path / "rounds.jsonl",
        )

    def run_adaptation(s: Strategy):
        return run(s, "A")[0]

    def evaluate_selection(s: Strategy) -> Score:
        summary = summarise(run(s, "V")[1])
        return Score(summary.success_rate, summary.mean_tokens)

    new, record = run_round(
        start,
        round_index=0,
        next_version=start.version + 1,
        run_adaptation=run_adaptation,
        evaluate_selection=evaluate_selection,
        diagnoser=RuleBasedDiagnoser(),
        proposer=RuleBasedProposer(),
        min_delta=0.1,
    )

    assert record.parent_score.success_rate == 0.0
    assert {d.failure_class for d in record.diagnoses} == {FailureClass.NO_OR_INCORRECT_VERIFICATION}
    assert len(record.diagnoses) == 6
    assert (new.version, new.parent_version) == (start.version + 1, start.version)
    assert record.accepted_version == new.version
    assert list(record.diff) == ["verification"]
    assert [(c.path, c.before, c.after) for c in record.diff["verification"]] == [
        ("/verification/verification_required", False, True)
    ]
    last = new.changelog[-1]
    assert last.measured_delta == 1.0 and last.round == 0 and len(last.diagnosis_ids) == 6
    assert evaluate_selection(new).success_rate == 1.0


def test_round_keeps_strategy_when_no_candidate_clears_threshold(strategy: Strategy) -> None:
    new, record = run_round(
        strategy,
        round_index=1,
        next_version=1,
        run_adaptation=lambda s: [],
        evaluate_selection=lambda s: Score(0.5, 100.0),
        diagnoser=RuleBasedDiagnoser(),
        proposer=RuleBasedProposer(),
        min_delta=0.05,
    )
    assert new is strategy and record.accepted_version is None and record.diff == {}


def test_cost_cap_blocks_an_otherwise_better_candidate(tasks: list[Task], strategy: Strategy) -> None:
    start = edited(strategy, ("replace", "/verification/verification_required", False))
    diagnosis_run = [FixedStrategy().run(tasks[0], ToyTextEnvironment(), MockModel(solver(sloppy_first=True)), start)]
    new, record = run_round(
        start,
        round_index=0,
        next_version=2,
        run_adaptation=lambda s: diagnosis_run,
        evaluate_selection=lambda s: Score(1.0, 500.0) if s.verification.verification_required else Score(0.0, 100.0),
        diagnoser=RuleBasedDiagnoser(),
        proposer=RuleBasedProposer(),
        min_delta=0.1,
        max_mean_cost=200.0,
    )
    assert new is start and len(record.candidates) == 1 and record.candidates[0].strategy.version == 2


def test_aggregate_ranks_groups_by_frequency() -> None:
    diagnoses = [
        Diagnosis(
            diagnosis_id=f"d{i}",
            task_id=f"t{i}",
            failure_class=cls,
            critical_step=0,
            evidence="",
            implicated_dimensions=dims,
        )
        for i, (cls, dims) in enumerate(
            [
                (FailureClass.WEAK_VERIFICATION, ["verification"]),
                (FailureClass.ACTED_BEFORE_CHECKING_ENVIRONMENT, ["exploration"]),
                (FailureClass.ACTED_BEFORE_CHECKING_ENVIRONMENT, ["exploration", "planning"]),
            ]
        )
    ]
    groups = aggregate(diagnoses)
    assert [(g.failure_class, g.dimension, g.count) for g in groups][0] == (
        FailureClass.ACTED_BEFORE_CHECKING_ENVIRONMENT,
        "exploration",
        2,
    )
    assert len(groups) == 3


def test_proposer_composes_two_operation_edit_for_exploration(strategy: Strategy) -> None:
    groups = [DiagnosisGroup(FailureClass.ACTED_BEFORE_CHECKING_ENVIRONMENT, "exploration", ["d1"])]
    (candidate,) = RuleBasedProposer().propose(strategy, groups, k=4, round_index=0)
    assert [(e.op, e.path, e.value) for e in candidate] == [("add", "/exploration/probes/-", "inspect_tests")]

    narrow = edited(strategy, ("replace", "/exploration/probe_budget_steps", 2))
    (candidate,) = RuleBasedProposer().propose(narrow, groups, k=4, round_index=0)
    assert [e.path for e in candidate] == ["/exploration/probes/-", "/exploration/probe_budget_steps"]
