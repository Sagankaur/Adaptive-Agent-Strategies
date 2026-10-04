"""The task and environment interface that baselines and the evaluation harness run against.

The interface separates what the agent may see from how it is graded:
:meth:`Environment.own_check` is the agent's own verification and may be used
at test time; :meth:`Environment.grade` stands for the benchmark's hidden
tests and must only be used for scoring, or for diagnosis on the adaptation
split where hidden results are training data (TECHNICAL_PLAN.md, section 5.1).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from strategy_schema.model import Check, Probe


class Task(BaseModel):
    """One benchmark task. ``payload`` is environment-private data the agent never sees."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    task_id: str = Field(min_length=1)
    instruction: str
    category: str = "uncategorised"
    difficulty: str = "unknown"
    payload: dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True)
class Action:
    tool: str
    argument: str


@dataclass(frozen=True)
class Observation:
    text: str
    exit_code: int


@dataclass(frozen=True)
class CheckResult:
    """Outcome of one of the agent's own checks; ``passed`` is None when the check does not apply."""

    check: Check
    passed: bool | None
    detail: str


class Environment(ABC):
    """A benchmark environment that one task at a time is run in.

    For benchmarks graded on final state (Terminal-Bench), ``answer`` in
    :meth:`own_check` and :meth:`grade` may be empty and the environment
    inspects its own state instead.
    """

    name: str

    @abstractmethod
    def reset(self, task: Task) -> None:
        """Start a fresh episode of ``task``."""

    @abstractmethod
    def probe(self, probe: Probe) -> Observation:
        """Run one exploration probe."""

    @abstractmethod
    def execute(self, action: Action) -> Observation:
        """Run one tool call."""

    @abstractmethod
    def own_check(self, answer: str, check: Check) -> CheckResult:
        """Run one of the agent's own checks on the submitted work."""

    @abstractmethod
    def grade(self, answer: str) -> bool:
        """Hidden-test verdict on the submitted work."""
