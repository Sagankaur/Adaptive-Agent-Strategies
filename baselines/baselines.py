"""Baselines B0-B2 of TECHNICAL_PLAN.md, section 4.1, at measurable cost.

All three use the same model, agent loop and tools; they differ only in how
many episodes they run per task and how they pick the one that counts. None
of them looks at the hidden tests: retries (B1) and selection (B2) are driven
by the agent's own checks. B2 also reports oracle pass@N, the result of
picking with the hidden tests, as a separately labelled upper bound.

B3 (free-text adaptation) and B4 (random strategy search) adapt across tasks
and belong with the adaptation engine; they are not implemented yet.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from baselines.agent_loop import Attempt, run_episode
from baselines.cost import Cost
from environments.base import Environment, Task
from llm import ChatModel, Message
from strategy_schema.model import Strategy


@dataclass
class TaskOutcome:
    """Everything a baseline did on one task; ``success`` is the selected attempt's hidden verdict."""

    task_id: str
    baseline: str
    params: dict[str, Any]
    attempts: list[Attempt]
    selected: int
    reflections: list[str] = field(default_factory=list)
    extra_cost: Cost = field(default_factory=Cost)

    @property
    def success(self) -> bool:
        return self.attempts[self.selected].success

    @property
    def oracle_success(self) -> bool:
        """Whether any attempt passed the hidden tests: an upper bound, not a result."""
        return any(a.success for a in self.attempts)

    @property
    def cost(self) -> Cost:
        total = self.extra_cost
        for attempt in self.attempts:
            total = total + attempt.cost
        return total


class Baseline(Protocol):
    name: str

    @property
    def params(self) -> dict[str, Any]: ...

    def run(self, task: Task, env: Environment, model: ChatModel, strategy: Strategy) -> TaskOutcome: ...


class FixedStrategy:
    """B0: one episode under a fixed strategy."""

    name = "B0-fixed"

    @property
    def params(self) -> dict[str, Any]:
        return {}

    def run(self, task: Task, env: Environment, model: ChatModel, strategy: Strategy) -> TaskOutcome:
        attempt = run_episode(task, env, model, strategy)
        return TaskOutcome(task.task_id, self.name, self.params, [attempt], selected=0)


REFLECTION_PROMPT = (
    "Your own checks say the attempt below did not succeed. In at most three sentences, "
    "say what went wrong and what to do differently next time."
)


def _summarise_attempt(attempt: Attempt) -> str:
    rows = []
    for s in attempt.steps:
        first_line = s.observation.splitlines()[0] if s.observation else ""
        rows.append(f"{s.index}. {s.kind} {s.tool} {s.argument} -> exit {s.exit_code}: {first_line}")
    return "\n".join([*rows, f"stop reason: {attempt.stop_reason}"])


@dataclass
class ReflectionRetry:
    """B1: up to ``k`` attempts, with a written self-reflection between them (Reflexion-style).

    A new attempt starts only when the agent's own checks fail. The last
    attempt is the one that counts.
    """

    k: int
    name: str = "B1-reflection"

    def __post_init__(self) -> None:
        if self.k < 1:
            raise ValueError("k must be at least 1")

    @property
    def params(self) -> dict[str, Any]:
        return {"k": self.k}

    def run(self, task: Task, env: Environment, model: ChatModel, strategy: Strategy) -> TaskOutcome:
        outcome = TaskOutcome(task.task_id, self.name, self.params, [], selected=0)
        for i in range(self.k):
            context = [f"Reflection on an earlier attempt: {r}" for r in outcome.reflections]
            attempt = run_episode(task, env, model, strategy, extra_context=context)
            outcome.attempts.append(attempt)
            outcome.selected = i
            if attempt.own_check_passed is not False or i == self.k - 1:
                break
            start = time.perf_counter()
            reply = model.complete(
                [
                    Message("system", REFLECTION_PROMPT),
                    Message("user", task.instruction + "\n\n" + _summarise_attempt(attempt)),
                ]
            )
            outcome.extra_cost.record(reply)
            outcome.extra_cost.wall_s += time.perf_counter() - start
            outcome.reflections.append(reply.text.strip())
        return outcome


@dataclass
class BestOfN:
    """B2: ``n`` independent attempts; the first one that passes the agent's own checks is selected.

    If none passes, the first attempt is selected. Selection by an LLM judge,
    which the plan allows as an alternative, is not implemented.
    """

    n: int
    name: str = "B2-best-of-n"

    def __post_init__(self) -> None:
        if self.n < 1:
            raise ValueError("n must be at least 1")

    @property
    def params(self) -> dict[str, Any]:
        return {"n": self.n, "selector": "own_checks"}

    def run(self, task: Task, env: Environment, model: ChatModel, strategy: Strategy) -> TaskOutcome:
        attempts = [run_episode(task, env, model, strategy) for _ in range(self.n)]
        selected = next((i for i, a in enumerate(attempts) if a.own_check_passed), 0)
        return TaskOutcome(task.task_id, self.name, self.params, attempts, selected)
