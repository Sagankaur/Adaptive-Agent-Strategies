"""Blind trajectory scoring and exact pooled best-of-N calculations."""

from __future__ import annotations

import itertools
import json
import math
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from baselines.agent_loop import Attempt
from llm import ChatModel, ChatResponse, Message


class JudgeOutputError(ValueError):
    """The judge did not return a valid score in [0, 1]."""


@dataclass(frozen=True)
class JudgeResult:
    score: float
    reason: str
    response: ChatResponse

    @property
    def passed(self) -> bool:
        """The default retry threshold; the judge-quality gate remains a separate decision."""
        return self.score >= 0.5


def judge_attempt(model: ChatModel, instruction: str, attempt: Attempt) -> JudgeResult:
    """Score one public trajectory; this function has no environment or filesystem handle."""
    transcript = {
        "answer": attempt.answer,
        "agent_check_passed": attempt.own_check_passed,
        "stop_reason": attempt.stop_reason,
        "steps": [
            {
                "kind": step.kind,
                "tool": step.tool,
                "argument": step.argument,
                "observation": step.observation,
                "exit_code": step.exit_code,
            }
            for step in attempt.steps
        ],
    }
    response = model.complete(
        [
            Message(
                "system",
                "You are a blind evaluator. Score how likely the recorded attempt is to satisfy the task, "
                "using only the instruction and visible trajectory. Return JSON with a numeric score from 0 to 1 "
                "and a short reason. Do not infer access to hidden tests or hidden reward.",
            ),
            Message("user", json.dumps({"instruction": instruction, "trajectory": transcript}, ensure_ascii=False)),
        ]
    )
    try:
        data = json.loads(response.text)
        score = data["score"]
        reason = data["reason"]
    except (ValueError, KeyError, TypeError) as exc:
        raise JudgeOutputError("judge reply must be JSON with score and reason") from exc
    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not math.isfinite(score)
        or not 0 <= score <= 1
    ):
        raise JudgeOutputError("judge score must be a finite number from 0 to 1")
    if not isinstance(reason, str) or not reason.strip():
        raise JudgeOutputError("judge reason must be a non-empty string")
    return JudgeResult(float(score), reason.strip(), response)


def select_best_index(scores: Sequence[float], *, seed: int) -> int:
    """Choose a maximum-score index, using a seeded uniform tie-break."""
    if not scores:
        raise ValueError("scores must not be empty")
    if any(isinstance(score, bool) or not math.isfinite(score) for score in scores):
        raise ValueError("scores must be finite numbers")
    best = max(scores)
    tied = [index for index, score in enumerate(scores) if score == best]
    return random.Random(seed).choice(tied)


def pooled_bon_frontier(
    records: Mapping[str, Sequence[tuple[float, bool]]], *, max_n: int | None = None
) -> dict[int, float]:
    """Expected selected success over every size-N subset, with analytic random tie-breaking.

    Each record is ``(judge_score, hidden_success)``. Hidden success is consumed
    only by this analysis function, never by :func:`judge_attempt` or a selector.
    All tasks must have the same non-zero number of S0 trajectories.
    """
    if not records or any(not rows for rows in records.values()):
        raise ValueError("records must contain at least one trajectory for each task")
    sizes = {len(rows) for rows in records.values()}
    if len(sizes) != 1:
        raise ValueError("every task must have the same S0 pool size")
    pool_size = sizes.pop()
    upper = pool_size if max_n is None else max_n
    if not 1 <= upper <= pool_size:
        raise ValueError("max_n must be between 1 and the S0 pool size")
    for rows in records.values():
        if any(
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not math.isfinite(score)
            or not 0 <= score <= 1
            or not isinstance(success, bool)
            for score, success in rows
        ):
            raise ValueError("each record must contain a score in [0, 1] and a boolean outcome")

    frontier: dict[int, float] = {}
    for n in range(1, upper + 1):
        task_rates: list[float] = []
        for rows in records.values():
            subset_rates: list[float] = []
            for subset in itertools.combinations(rows, n):
                top = max(score for score, _ in subset)
                tied_successes = [success for score, success in subset if score == top]
                subset_rates.append(sum(tied_successes) / len(tied_successes))
            task_rates.append(sum(subset_rates) / len(subset_rates))
        frontier[n] = sum(task_rates) / len(task_rates)
    return frontier
