"""Mock-model policies that play the toy environment, and a shorthand for editing strategies."""

from __future__ import annotations

import re
from collections.abc import Sequence

from environments import Task, apply_operation
from llm import Message, Policy
from strategy_schema import Edit, Strategy, apply_edits


def correct_answer(task: Task) -> str:
    return apply_operation(task.payload["operation"], task.payload["input"])


def wrong_answer(task: Task) -> str:
    """The correct answer with its last word dropped: fails the hidden test and the toy's own check."""
    return " ".join(correct_answer(task).split()[:-1])


def _operation(messages: Sequence[Message]) -> str:
    match = re.search(r"\(operation: (\w+)\)", messages[1].content)
    if match is None:
        raise AssertionError("the instruction must name the operation")
    return match.group(1)


def _input_text(messages: Sequence[Message]) -> str | None:
    prefix = "[file_view input.txt] exit=0\n"
    for m in messages:
        if m.role == "user" and m.content.startswith(prefix):
            return m.content[len(prefix) :]
    return None


def solver(*, sloppy_first: bool) -> Policy:
    """A policy that reads input.txt and submits; if ``sloppy_first``, its first answer drops a word.

    After a failed-check observation it submits the correct answer, so whether
    it succeeds depends on whether the strategy verifies before submitting.
    """

    def policy(messages: Sequence[Message]) -> str:
        text = _input_text(messages)
        if text is None:
            return "ACTION: file_view input.txt"
        correct = apply_operation(_operation(messages), text)
        told_to_fix = any("Checks failed" in m.content for m in messages if m.role == "user")
        if sloppy_first and not told_to_fix:
            return "SUBMIT: " + " ".join(correct.split()[:-1])
        return "SUBMIT: " + correct

    return policy


def edited(strategy: Strategy, *ops: tuple[str, str, object]) -> Strategy:
    """``strategy`` with the given (op, path, value) operations applied, as the next version."""
    edits = [Edit(op=op, path=path, value=value) for op, path, value in ops]
    return apply_edits(strategy, edits, version=strategy.version + 1)


def with_budget(strategy: Strategy, **budget: int) -> Strategy:
    """Budgets are not editable, so tests that need a different one build the strategy directly."""
    doc = strategy.model_dump(mode="json")
    doc["budget"].update(budget)
    return Strategy.model_validate(doc)
