from __future__ import annotations

import json
from pathlib import Path

import pytest

from baselines import BestOfN, FixedStrategy, ReflectionRetry, load_price_tables
from environments import Task, ToyTextEnvironment
from evaluation import PRICE_TABLE_PATH
from evaluation.runner import HeldOutAccessError, ResultRecord, RunBudget, evaluate, summarise
from evaluation.splits import Split, TaskInfo, make_split
from llm import MockModel
from strategy_schema import Strategy
from tests.helpers import solver


def _split(tasks: list[Task]) -> Split:
    infos = [TaskInfo(task_id=t.task_id, category=t.category, difficulty=t.difficulty) for t in tasks]
    return make_split(infos, {"A": 4, "V": 4, "H": 4}, seed=0, benchmark="toy-text")


@pytest.mark.parametrize("baseline", [FixedStrategy(), ReflectionRetry(k=2), BestOfN(n=2)], ids=lambda b: b.name)
def test_each_baseline_runs_a_split_and_writes_records(
    baseline, tasks: list[Task], strategy: Strategy, tmp_path: Path
) -> None:
    out = tmp_path / "results.jsonl"
    prices = load_price_tables(PRICE_TABLE_PATH)["gpt-5-mini"]
    outcomes, records = evaluate(
        run_id="test",
        baseline=baseline,
        strategy=strategy,
        model=MockModel(solver(sloppy_first=False)),
        env=ToyTextEnvironment(),
        tasks={t.task_id: t for t in tasks},
        split=_split(tasks),
        split_name="A",
        out_path=out,
        budget=RunBudget(prices=prices),
    )
    lines = [ResultRecord.model_validate_json(line) for line in out.read_text().splitlines()]
    assert lines == records and len(records) == 4 and len(outcomes) == 4
    for record in records:
        assert record.status == "completed" and record.success
        assert (record.strategy_id, record.strategy_version) == ("s0", 0)
        assert record.baseline == baseline.name and record.baseline_params == baseline.params
        assert record.cost and record.cost["calls"] >= 2 and record.dollars and record.dollars > 0
        assert record.attempts[0]["steps"][0]["kind"] == "probe"
    expected_attempts = 2 if isinstance(baseline, BestOfN) else 1
    assert all(len(r.attempts) == expected_attempts for r in records)
    summary = summarise(records)
    assert summary.success_rate == 1.0 and summary.completed == 4 and summary.mean_dollars


def test_budget_stops_new_tasks_and_records_them(tasks: list[Task], strategy: Strategy, tmp_path: Path) -> None:
    _, records = evaluate(
        run_id="budget",
        baseline=FixedStrategy(),
        strategy=strategy,
        model=MockModel(solver(sloppy_first=False)),
        env=ToyTextEnvironment(),
        tasks={t.task_id: t for t in tasks},
        split=_split(tasks),
        split_name="A",
        out_path=tmp_path / "r.jsonl",
        budget=RunBudget(max_calls=3),
    )
    assert [r.status for r in records] == ["completed", "completed", "not_run_budget", "not_run_budget"]
    summary = summarise(records)
    assert (summary.completed, summary.not_run) == (2, 2)


def test_held_out_split_is_refused_outside_final_evaluation(
    tasks: list[Task], strategy: Strategy, tmp_path: Path
) -> None:
    kwargs = dict(
        run_id="h",
        baseline=FixedStrategy(),
        strategy=strategy,
        model=MockModel(solver(sloppy_first=False)),
        env=ToyTextEnvironment(),
        tasks={t.task_id: t for t in tasks},
        split=_split(tasks),
        split_name="H",
        out_path=tmp_path / "h.jsonl",
    )
    with pytest.raises(HeldOutAccessError):
        evaluate(**kwargs)
    _, records = evaluate(**kwargs, final_evaluation=True)
    assert len(records) == 4


def test_records_append_across_runs(tasks: list[Task], strategy: Strategy, tmp_path: Path) -> None:
    out = tmp_path / "r.jsonl"
    for run_id in ("one", "two"):
        evaluate(
            run_id=run_id,
            baseline=FixedStrategy(),
            strategy=strategy,
            model=MockModel(solver(sloppy_first=False)),
            env=ToyTextEnvironment(),
            tasks={t.task_id: t for t in tasks},
            split=_split(tasks),
            split_name="V",
            out_path=out,
        )
    assert [json.loads(line)["run_id"] for line in out.read_text().splitlines()] == ["one"] * 4 + ["two"] * 4
