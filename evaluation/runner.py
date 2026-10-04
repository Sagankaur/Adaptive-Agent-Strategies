"""Evaluate one strategy with one baseline on one split, under a cost budget, writing JSONL records.

Each task produces one :class:`ResultRecord` line carrying the strategy
version, the baseline and its parameters, the outcome, the cost, and every
attempt's step table, so later diagnosis and attribution work from the
records alone. Tasks not started because the budget ran out are recorded as
``not_run_budget`` rather than dropped. The held-out split is refused unless
the call is explicitly marked as the final evaluation (TECHNICAL_PLAN.md,
section 7.1: H is never looked at during development).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from baselines.baselines import Baseline, TaskOutcome
from baselines.cost import Cost, PriceTable
from environments.base import Environment, Task
from evaluation.splits import HELD_OUT, Split
from llm import ChatModel
from strategy_schema.model import Strategy


class HeldOutAccessError(RuntimeError):
    """The held-out split was requested outside the final evaluation."""


@dataclass(frozen=True)
class RunBudget:
    """Caps on a whole run. Checked before each task starts, so the last task may overshoot."""

    max_calls: int | None = None
    max_tokens: int | None = None
    max_dollars: float | None = None
    prices: PriceTable | None = None

    def __post_init__(self) -> None:
        if self.max_dollars is not None and self.prices is None:
            raise ValueError("max_dollars needs a price table")

    def exhausted(self, spent: Cost) -> bool:
        return (
            (self.max_calls is not None and spent.calls >= self.max_calls)
            or (self.max_tokens is not None and spent.tokens >= self.max_tokens)
            or (
                self.max_dollars is not None
                and self.prices is not None
                and spent.dollars(self.prices) >= self.max_dollars
            )
        )


class ResultRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    benchmark: str
    environment: str
    split: str
    task_id: str
    baseline: str
    baseline_params: dict[str, Any]
    model: str
    strategy_id: str
    strategy_version: int
    status: Literal["completed", "not_run_budget"]
    success: bool | None = None
    oracle_success: bool | None = None
    own_check_passed: bool | None = None
    selected_attempt: int | None = None
    cost: dict[str, float] | None = None
    dollars: float | None = None
    attempts: list[dict[str, Any]] = []


def _attempt_dict(outcome: TaskOutcome) -> list[dict[str, Any]]:
    return [
        {
            "answer": a.answer,
            "stop_reason": a.stop_reason,
            "own_check_passed": a.own_check_passed,
            "success": a.success,
            "cost": a.cost.to_dict(),
            "steps": [asdict(s) for s in a.steps],
        }
        for a in outcome.attempts
    ]


def evaluate(
    *,
    run_id: str,
    baseline: Baseline,
    strategy: Strategy,
    model: ChatModel,
    env: Environment,
    tasks: Mapping[str, Task],
    split: Split,
    split_name: str,
    out_path: Path,
    budget: RunBudget | None = None,
    final_evaluation: bool = False,
) -> tuple[list[TaskOutcome], list[ResultRecord]]:
    """Run ``baseline`` with ``strategy`` on every task of ``split_name`` and append records to ``out_path``."""
    if split_name == HELD_OUT and not final_evaluation:
        raise HeldOutAccessError("the held-out split is only for the final evaluation")
    budget = budget or RunBudget()
    prices = budget.prices
    spent = Cost()
    outcomes: list[TaskOutcome] = []
    records: list[ResultRecord] = []
    common = dict(
        run_id=run_id,
        benchmark=split.benchmark,
        environment=env.name,
        split=split_name,
        baseline=baseline.name,
        baseline_params=baseline.params,
        model=model.name,
        strategy_id=strategy.strategy_id,
        strategy_version=strategy.version,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a") as out:
        for task_id in split.tasks(split_name):
            if budget.exhausted(spent):
                record = ResultRecord(**common, task_id=task_id, status="not_run_budget")
            else:
                outcome = baseline.run(tasks[task_id], env, model, strategy)
                cost = outcome.cost
                spent = spent + cost
                outcomes.append(outcome)
                record = ResultRecord(
                    **common,
                    task_id=task_id,
                    status="completed",
                    success=outcome.success,
                    oracle_success=outcome.oracle_success,
                    own_check_passed=outcome.attempts[outcome.selected].own_check_passed,
                    selected_attempt=outcome.selected,
                    cost=cost.to_dict(),
                    dollars=cost.dollars(prices) if prices else None,
                    attempts=_attempt_dict(outcome),
                )
            records.append(record)
            out.write(record.model_dump_json() + "\n")
            out.flush()
    return outcomes, records


@dataclass(frozen=True)
class Summary:
    completed: int
    not_run: int
    success_rate: float
    mean_calls: float
    mean_tokens: float
    mean_dollars: float | None


def summarise(records: Sequence[ResultRecord]) -> Summary:
    """Success rate and mean cost per completed task."""
    done = [r for r in records if r.status == "completed"]
    n = len(done)

    def mean(values: list[float]) -> float:
        return sum(values) / n if n else 0.0

    dollars = [r.dollars for r in done if r.dollars is not None]
    return Summary(
        completed=n,
        not_run=len(records) - n,
        success_rate=mean([1.0 if r.success else 0.0 for r in done]),
        mean_calls=mean([r.cost["calls"] for r in done if r.cost]),
        mean_tokens=mean([r.cost["input_tokens"] + r.cost["output_tokens"] for r in done if r.cost]),
        mean_dollars=mean(dollars) if n and len(dollars) == n else None,
    )
