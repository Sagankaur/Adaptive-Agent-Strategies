"""Fixed, seeded task splits (TECHNICAL_PLAN.md, section 7.1).

The plan's Phase 0 rule is to fix the splits and commit the split file
before any agent run. :func:`make_split` is deterministic for a given task
list and seed, stratifies by category and difficulty, and can keep groups of
related tasks together (AppWorld tasks come three to a scenario and must be
split by scenario). The default sizes are the plan's suggestion for the 89
Terminal-Bench 2.0 tasks:

- ``A`` adaptation (25): run and diagnose in first-order rounds;
- ``V`` selection (12): accept or reject edits;
- ``M`` meta-training (15): score revised adaptation mechanisms;
- ``H`` held-out (37): the final evaluation only.

Transfer (section 7.3) is not a split of this pool: it uses a second
benchmark family, AppWorld, with its own built-in train/dev/test splits.
Its scenario-grouped split for mechanism transfer is made with the same
function and saved to its own file.

Run as a script to write a split file::

    python -m evaluation.splits --tasks tasks.jsonl --benchmark terminal-bench@2.0 --seed 0 --out splits/tb2.json

where each line of ``tasks.jsonl`` has ``task_id`` and optionally
``category``, ``difficulty`` and ``group``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator

TERMINAL_BENCH_2_SIZES: dict[str, int] = {"A": 25, "V": 12, "M": 15, "H": 37}
HELD_OUT = "H"


class TaskInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    task_id: str
    category: str = "uncategorised"
    difficulty: str = "unknown"
    group: str | None = None


class Split(BaseModel):
    """A committed assignment of task ids to named splits."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    benchmark: str
    seed: int
    sizes: dict[str, int]
    task_ids_sha256: str
    splits: dict[str, list[str]]

    @model_validator(mode="after")
    def _disjoint(self) -> Split:
        seen: set[str] = set()
        for ids in self.splits.values():
            if seen & set(ids):
                raise ValueError("splits overlap")
            seen |= set(ids)
        if _fingerprint(seen) != self.task_ids_sha256:
            raise ValueError("task ids do not match the recorded fingerprint")
        return self

    def tasks(self, name: str) -> list[str]:
        return self.splits[name]

    def split_of(self, task_id: str) -> str:
        for name, ids in self.splits.items():
            if task_id in ids:
                return name
        raise KeyError(task_id)


def _fingerprint(task_ids: set[str] | Sequence[str]) -> str:
    return hashlib.sha256("\n".join(sorted(task_ids)).encode()).hexdigest()


def make_split(
    tasks: Sequence[TaskInfo],
    sizes: Mapping[str, int],
    seed: int,
    benchmark: str,
) -> Split:
    """Assign tasks to splits of the given sizes, stratified by (category, difficulty).

    Tasks sharing a ``group`` are assigned together. Units (groups, or single
    tasks) are shuffled within each stratum with ``seed``, strata are walked
    in sorted order, and each unit goes to the split furthest below its
    target share, so every stratum is spread across splits in proportion to
    their sizes. With groups larger than one task the sizes can be missed by
    less than one group.
    """
    ids = [t.task_id for t in tasks]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate task ids")
    if sum(sizes.values()) != len(tasks):
        raise ValueError(f"split sizes sum to {sum(sizes.values())} but there are {len(tasks)} tasks")

    units: dict[str, list[TaskInfo]] = defaultdict(list)
    for t in tasks:
        units[t.group or f"task:{t.task_id}"].append(t)
    strata: dict[tuple[str, str], list[str]] = defaultdict(list)
    for key in sorted(units):
        first = units[key][0]
        strata[(first.category, first.difficulty)].append(key)

    rng = random.Random(seed)
    ordered: list[str] = []
    for stratum in sorted(strata):
        keys = strata[stratum]
        rng.shuffle(keys)
        ordered.extend(keys)

    total = len(tasks)
    names = list(sizes)
    assigned: dict[str, list[str]] = {name: [] for name in names}
    placed = 0
    for key in ordered:
        members = units[key]
        placed += len(members)
        open_names = [n for n in names if len(assigned[n]) + len(members) <= sizes[n]] or [
            max(names, key=lambda n: sizes[n] - len(assigned[n]))
        ]
        target = max(open_names, key=lambda n: (sizes[n] * placed / total - len(assigned[n]), -names.index(n)))
        assigned[target].extend(sorted(t.task_id for t in members))

    return Split(
        benchmark=benchmark,
        seed=seed,
        sizes=dict(sizes),
        task_ids_sha256=_fingerprint(ids),
        splits={name: sorted(assigned[name]) for name in names},
    )


def save_split(split: Split, path: Path) -> None:
    """Write the split file; refuses to overwrite a different split already committed there."""
    text = split.model_dump_json(indent=2) + "\n"
    if path.exists() and path.read_text() != text:
        raise FileExistsError(f"{path} already holds a different split; splits are fixed once committed")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def load_split(path: Path) -> Split:
    return Split.model_validate_json(path.read_text())


def _parse_sizes(text: str) -> dict[str, int]:
    return {name: int(size) for name, size in (part.split("=") for part in text.split(","))}


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Fix and save a seeded task split.")
    parser.add_argument("--tasks", type=Path, required=True, help="JSONL with task_id[, category, difficulty, group]")
    parser.add_argument("--benchmark", required=True, help="pinned benchmark id, e.g. terminal-bench@2.0")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--sizes", type=_parse_sizes, default=TERMINAL_BENCH_2_SIZES, help="e.g. A=25,V=12,M=15,H=37")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    lines = [line for line in args.tasks.read_text().splitlines() if line.strip()]
    tasks = [TaskInfo.model_validate(json.loads(line)) for line in lines]
    split = make_split(tasks, args.sizes, args.seed, args.benchmark)
    save_split(split, args.out)
    print(f"wrote {args.out}: " + ", ".join(f"{n}={len(ids)}" for n, ids in split.splits.items()))


if __name__ == "__main__":
    main()
