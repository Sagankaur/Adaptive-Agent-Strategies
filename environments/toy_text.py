"""A toy text-manipulation environment so the whole loop runs offline.

This is not a benchmark and no result on it says anything about agents. It
exists so that baselines, cost accounting, the evaluation runner and the
adaptation loop can be exercised end to end with a mock model.

Each task asks for one word-level operation on the text in ``input.txt``. The
hidden grade is an exact match. The agent's own check (``run_visible_tests``)
is deliberately weaker: it only confirms the answer uses the same words as
the input, ignoring case and order, so a wrong answer can pass it, as weak
verification does on real benchmarks.
"""

from __future__ import annotations

import random

from environments.base import Action, CheckResult, Environment, Observation, Task
from strategy_schema.model import Check, Probe

OPERATIONS: dict[str, str] = {
    "reverse_words": "reverse the order of the words",
    "sort_words": "sort the words alphabetically",
    "uppercase": "convert every letter to upper case",
}

_WORDS = (
    "amber basil cedar delta ember fjord grove harbor island juniper kestrel lagoon "
    "meadow nectar orchid pebble quartz river saffron timber umber violet willow yarrow"
).split()

README = (
    "Toy text environment. The file input.txt holds one line of words. "
    "Tools: file_view <path>. Submit the transformed line with SUBMIT."
)


def apply_operation(operation: str, text: str) -> str:
    words = text.split()
    if operation == "reverse_words":
        return " ".join(reversed(words))
    if operation == "sort_words":
        return " ".join(sorted(words))
    if operation == "uppercase":
        return text.upper()
    raise ValueError(f"unknown operation {operation!r}")


def make_toy_tasks(n: int, seed: int = 0) -> list[Task]:
    """``n`` deterministic toy tasks, cycling through the operations; difficulty is set by word count."""
    rng = random.Random(seed)
    operations = sorted(OPERATIONS)
    tasks = []
    for i in range(n):
        operation = operations[i % len(operations)]
        difficulty = "easy" if rng.random() < 0.5 else "hard"
        count = rng.randint(3, 4) if difficulty == "easy" else rng.randint(6, 8)
        text = " ".join(rng.sample(_WORDS, count))
        tasks.append(
            Task(
                task_id=f"toy-{i:03d}",
                instruction=(
                    f"Toy task: {OPERATIONS[operation]} in input.txt "
                    f"(operation: {operation}) and submit the result as one line."
                ),
                category=operation,
                difficulty=difficulty,
                payload={"operation": operation, "input": text},
            )
        )
    return tasks


class ToyTextEnvironment(Environment):
    name = "toy-text"

    def __init__(self) -> None:
        self._task: Task | None = None

    @property
    def _input(self) -> str:
        if self._task is None:
            raise RuntimeError("reset() must be called before use")
        return self._task.payload["input"]

    def reset(self, task: Task) -> None:
        self._task = task

    def probe(self, probe: Probe) -> Observation:
        if probe == Probe.LIST_WORKDIR:
            return Observation("README\ninput.txt", 0)
        if probe == Probe.READ_README:
            return Observation(README, 0)
        if probe == Probe.INSPECT_TESTS:
            return Observation("The visible test checks the answer uses the same words as input.txt.", 0)
        return Observation(f"probe {probe} is not available in the toy environment", 127)

    def execute(self, action: Action) -> Observation:
        if action.tool != "file_view":
            return Observation(f"tool {action.tool} is not available in the toy environment", 127)
        path = action.argument.strip()
        if path == "input.txt":
            return Observation(self._input, 0)
        if path == "README":
            return Observation(README, 0)
        return Observation(f"{path}: no such file", 1)

    def own_check(self, answer: str, check: Check) -> CheckResult:
        if check != Check.RUN_VISIBLE_TESTS:
            return CheckResult(check, None, "not applicable in the toy environment")
        passed = sorted(answer.lower().split()) == sorted(self._input.lower().split())
        detail = "same words as input.txt" if passed else "words differ from input.txt"
        return CheckResult(check, passed, detail)

    def grade(self, answer: str) -> bool:
        text = self._input
        return answer.strip() == apply_operation(self._task.payload["operation"], text)
