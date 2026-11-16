from __future__ import annotations

import itertools

import pytest

from baselines.agent_loop import Attempt, Step
from baselines.judge import JudgeOutputError, judge_attempt, pooled_bon_frontier, select_best_index
from llm import MockModel


def _attempt(*, success: bool = False) -> Attempt:
    return Attempt(
        task_id="toy-000",
        strategy_version=0,
        steps=[Step(0, "action", "bash", "echo hi", "hi", 0, 0.1)],
        answer="hi",
        stop_reason="submitted",
        own_check_passed=None,
        success=success,
    )


def test_judge_scores_only_instruction_and_public_trajectory() -> None:
    model = MockModel(['{"score": 0.25, "reason": "output is incomplete"}'])
    result = judge_attempt(model, "Write hi to output.txt", _attempt(success=True))

    assert result.score == 0.25
    assert not result.passed
    serialized = "\n".join(message.content for message in model.calls[0])
    assert "Write hi to output.txt" in serialized
    assert "echo hi" in serialized
    assert '"success"' not in serialized
    assert "tests/" not in serialized


def test_judge_rejects_malformed_scores() -> None:
    with pytest.raises(JudgeOutputError, match="score"):
        judge_attempt(MockModel(["not json"]), "task", _attempt())


def test_tie_breaking_is_randomized_but_reproducible() -> None:
    assert select_best_index([0.8, 0.8, 0.2], seed=11) == select_best_index([0.8, 0.8, 0.2], seed=11)
    assert select_best_index([0.2, 0.9, 0.1], seed=11) == 1


def test_pooled_bon_frontier_matches_explicit_subset_and_tie_average() -> None:
    records = {"task-a": [(0.8, True), (0.8, False), (0.2, True)]}
    frontier = pooled_bon_frontier(records, max_n=3)
    assert frontier == {1: pytest.approx(2 / 3), 2: pytest.approx(0.5), 3: pytest.approx(0.5)}

    # Independent exhaustive check for every subset size and uniform tie-breaking.
    for n, expected in frontier.items():
        values = []
        for subset in itertools.combinations(records["task-a"], n):
            best = max(score for score, _ in subset)
            successes = sum(success for score, success in subset if score == best)
            top_count = sum(score == best for score, _ in subset)
            values.append(successes / top_count)
        assert expected == pytest.approx(sum(values) / len(values))
