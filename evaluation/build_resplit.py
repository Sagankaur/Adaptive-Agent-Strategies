"""Build a deterministic, exact-size TB2 re-split candidate.

The generator reads task metadata and the reviewed sibling-group manifest only.
It never reads task instructions or task environments.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Sequence

from evaluation.splits import Split, TaskInfo, _fingerprint


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASKS = ROOT / "evaluation/data/tb2_tasks.jsonl"
DEFAULT_GROUPS = ROOT / "evaluation/data/tb2_sibling_groups.json"
DEFAULT_OUT = ROOT / "splits/tb2-resplit-h52-seed20261015-v3.json"
SIZES = {"A": 15, "V": 12, "V2": 10, "H": 52}
GROUP_COUNTS = {"A": 2, "V": 1, "V2": 1, "H": 5}
TRIALS = 50_000
SEED = 20261015
TASK_COMMIT = "2fd12b88aafdd04a52c298e3940bcb189f9766d6"


def _save_split_lf(split: Split, path: Path) -> None:
    """Save canonical LF JSON while preserving the split immutability guard."""
    text = split.model_dump_json(indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise FileExistsError(f"{path} already holds a different split; splits are fixed once committed")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def _key(seed: int, trial: int, kind: str, value: str) -> str:
    payload = f"{seed}\0{trial}\0{kind}\0{value}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _read_tasks(path: Path, groups_path: Path) -> list[TaskInfo]:
    records = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected_source = f"laude-institute/terminal-bench-2@{TASK_COMMIT}"
    mismatched_sources = [
        row["task_id"]
        for row in records
        if expected_source not in row.get("source", "")
    ]
    if mismatched_sources:
        raise ValueError(
            "task metadata source does not match the pinned TB2 commit: "
            + ", ".join(sorted(mismatched_sources))
        )
    manifest = json.loads(groups_path.read_text(encoding="utf-8"))
    if manifest.get("benchmark") != "laude-institute/terminal-bench-2":
        raise ValueError("sibling manifest names a different benchmark")
    if manifest.get("commit") != TASK_COMMIT:
        raise ValueError("sibling manifest is not pinned to the expected TB2 commit")
    by_id = {row["task_id"]: row for row in records}
    if len(by_id) != len(records):
        raise ValueError("task inventory contains duplicate task IDs")

    group_by_id: dict[str, str] = {}
    group_ids: set[str] = set()
    for group in manifest["groups"]:
        group_id = group["group_id"]
        if group_id in group_ids:
            raise ValueError(f"duplicate sibling group ID: {group_id}")
        group_ids.add(group_id)
        members = group["task_ids"]
        if len(members) not in (2, 3) or len(set(members)) != len(members):
            raise ValueError(f"{group_id} must contain two or three distinct tasks")
        for task_id in members:
            if task_id not in by_id:
                raise ValueError(f"unknown task ID in {group_id}: {task_id}")
            if task_id in group_by_id:
                raise ValueError(f"task appears in multiple groups: {task_id}")
            group_by_id[task_id] = group_id

    tasks = [
        TaskInfo(
            task_id=row["task_id"],
            category=row.get("category", "uncategorised"),
            difficulty=row.get("difficulty", "unknown"),
            group=group_by_id.get(row["task_id"]),
        )
        for row in records
    ]
    group_sizes = Counter(len(group["task_ids"]) for group in manifest["groups"])
    if len(group_ids) != 9 or group_sizes != Counter({2: 7, 3: 2}) or len(group_by_id) != 20:
        raise ValueError(
            "expected 9 reviewed groups (seven pairs and two triplets; 20 task IDs), "
            f"got {len(group_ids)} groups, sizes={dict(group_sizes)}, members={len(group_by_id)}"
        )
    return tasks


def _objective(
    counts: dict[str, Counter[tuple[str, str]]],
    totals: Counter[tuple[str, str]],
    sizes: dict[str, int],
    total_tasks: int,
) -> float:
    score = 0.0
    for stratum, total in totals.items():
        for pool, pool_size in sizes.items():
            target = total * pool_size / total_tasks
            observed = counts[pool][stratum]
            score += (observed - target) ** 2 / max(target, 1.0)
    return score


def _marginal_cost(
    pool: str,
    stratum: tuple[str, str],
    counts: dict[str, Counter[tuple[str, str]]],
    totals: Counter[tuple[str, str]],
    sizes: dict[str, int],
    total_tasks: int,
) -> float:
    target = totals[stratum] * sizes[pool] / total_tasks
    current = counts[pool][stratum]
    return ((current + 1 - target) ** 2 - (current - target) ** 2) / max(target, 1.0)


def _allocate_trial(
    tasks: list[TaskInfo],
    sizes: dict[str, int],
    seed: int,
    trial: int,
) -> tuple[float, dict[str, list[str]]]:
    units: dict[str, list[TaskInfo]] = defaultdict(list)
    for task in tasks:
        units[task.group or f"task:{task.task_id}"].append(task)

    groups = [
        sorted(members, key=lambda task: task.task_id)
        for members in units.values()
        if len(members) > 1
    ]
    singles_by_stratum: dict[tuple[str, str], list[TaskInfo]] = defaultdict(list)
    for members in units.values():
        if len(members) == 1:
            task = members[0]
            singles_by_stratum[(task.category, task.difficulty)].append(task)
    if len(groups) != 9 or sum(map(len, singles_by_stratum.values())) != 69:
        raise ValueError("expected nine sibling groups and 69 singleton tasks")

    pool_names = list(sizes)
    counts: dict[str, Counter[tuple[str, str]]] = {
        pool: Counter() for pool in pool_names
    }
    assigned: dict[str, list[str]] = {pool: [] for pool in pool_names}
    remaining = dict(sizes)
    assigned_groups = Counter()
    totals: Counter[tuple[str, str]] = Counter(
        (task.category, task.difficulty) for task in tasks
    )

    groups.sort(key=lambda group: _key(seed, trial, "group-order", ",".join(sorted(t.task_id for t in group))))
    for group in groups:
        eligible = [
            pool
            for pool in pool_names
            if remaining[pool] >= len(group) and assigned_groups[pool] < GROUP_COUNTS[pool]
        ]
        if not eligible:
            raise RuntimeError("exact-size allocator cannot place a sibling group")
        pool_costs: list[tuple[float, str, str]] = []
        for pool in eligible:
            local = counts[pool].copy()
            cost = 0.0
            for task in group:
                stratum = (task.category, task.difficulty)
                cost += _marginal_cost(pool, stratum, {pool: local}, totals, sizes, len(tasks))
                local[stratum] += 1
            tie = _key(seed, trial, "group-tie", f"{','.join(sorted(t.task_id for t in group))}:{pool}")
            pool_costs.append((cost, tie, pool))
        _, _, chosen = min(pool_costs)
        for task in group:
            assigned[chosen].append(task.task_id)
            counts[chosen][(task.category, task.difficulty)] += 1
        remaining[chosen] -= len(group)
        assigned_groups[chosen] += 1

    if dict(assigned_groups) != GROUP_COUNTS:
        raise RuntimeError(f"sibling-group counts differ from target: {dict(assigned_groups)}")

    for stratum in sorted(singles_by_stratum):
        singles = singles_by_stratum[stratum]
        singles.sort(key=lambda task: _key(seed, trial, "single-order", task.task_id))
        for task in singles:
            eligible = [pool for pool in pool_names if remaining[pool] > 0]
            if not eligible:
                raise RuntimeError("exact-size allocator exhausted capacity early")
            candidates = [
                (
                    _marginal_cost(pool, stratum, counts, totals, sizes, len(tasks)),
                    _key(seed, trial, "single-tie", f"{task.task_id}:{pool}"),
                    pool,
                )
                for pool in eligible
            ]
            _, _, chosen = min(candidates)
            assigned[chosen].append(task.task_id)
            counts[chosen][stratum] += 1
            remaining[chosen] -= 1

    if any(remaining.values()):
        raise RuntimeError(f"unfilled split capacities: {remaining}")
    _validate_assignment(tasks, sizes, assigned)
    score = _objective(counts, totals, sizes, len(tasks))
    return score, {pool: sorted(ids) for pool, ids in assigned.items()}


def _validate_assignment(
    tasks: list[TaskInfo],
    sizes: dict[str, int],
    assigned: dict[str, list[str]],
) -> None:
    expected = {task.task_id for task in tasks}
    all_assigned = [task_id for ids in assigned.values() for task_id in ids]
    if len(all_assigned) != len(set(all_assigned)) or set(all_assigned) != expected:
        raise ValueError("assignment must cover every task exactly once")
    for pool, target_size in sizes.items():
        if len(assigned[pool]) != target_size:
            raise ValueError(f"{pool} has {len(assigned[pool])} tasks; expected {target_size}")
    pool_by_id = {
        task_id: pool for pool, ids in assigned.items() for task_id in ids
    }
    group_pools: dict[str, set[str]] = defaultdict(set)
    for task in tasks:
        if task.group:
            group_pools[task.group].add(pool_by_id[task.task_id])
    split_groups = [group_id for group_id, pools in group_pools.items() if len(pools) != 1]
    if split_groups:
        raise ValueError(f"sibling groups split across pools: {split_groups}")
    group_pool_counts = Counter()
    for group_id, pools in group_pools.items():
        if len(pools) == 1:
            group_pool_counts[next(iter(pools))] += 1
    group_pool_counts = Counter({pool: group_pool_counts[pool] for pool in sizes})
    if dict(group_pool_counts) != GROUP_COUNTS:
        raise ValueError(f"sibling-group pool counts differ from target: {dict(group_pool_counts)}")


def build(tasks: list[TaskInfo], sizes: dict[str, int], seed: int, trials: int):
    if sum(sizes.values()) != len(tasks):
        raise ValueError("target pool sizes must sum to the task count")
    if trials <= 0:
        raise ValueError("trials must be a positive integer")
    best: tuple[float, tuple[tuple[str, ...], ...], dict[str, list[str]]] | None = None
    for trial in range(trials):
        score, assignment = _allocate_trial(tasks, sizes, seed, trial)
        canonical = tuple(tuple(assignment[pool]) for pool in sizes)
        candidate = (score, canonical, assignment)
        if best is None or candidate[:2] < best[:2]:
            best = candidate
    assert best is not None
    return best[0], best[2]


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--groups", type=Path, default=DEFAULT_GROUPS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--trials", type=int, default=TRIALS)
    args = parser.parse_args(argv)

    tasks = _read_tasks(args.tasks, args.groups)
    score, assignments = build(tasks, SIZES, args.seed, args.trials)
    split = Split(
        benchmark="terminal-bench@2.0-resplit-h52",
        seed=args.seed,
        sizes=dict(SIZES),
        task_ids_sha256=_fingerprint([task.task_id for task in tasks]),
        splits=assignments,
    )
    _save_split_lf(split, args.out)
    counts: dict[str, Counter[tuple[str, str]]] = {
        pool: Counter() for pool in SIZES
    }
    by_id = {task.task_id: task for task in tasks}
    pool_by_id = {
        task_id: pool for pool, task_ids in assignments.items() for task_id in task_ids
    }
    group_distribution = Counter()
    for group in {task.group for task in tasks if task.group}:
        member = next(task for task in tasks if task.group == group)
        group_distribution[pool_by_id[member.task_id]] += 1
    group_distribution = Counter({pool: group_distribution[pool] for pool in SIZES})
    for pool, ids in assignments.items():
        for task_id in ids:
            task = by_id[task_id]
            counts[pool][(task.category, task.difficulty)] += 1
    print(f"wrote {args.out}: " + ", ".join(f"{pool}={len(assignments[pool])}" for pool in SIZES))
    print("sibling groups: " + ", ".join(f"{pool}={group_distribution[pool]}" for pool in SIZES))
    print(f"category-difficulty normalized squared-deviation objective={score:.8f}; trials={args.trials}")
    for pool in SIZES:
        detail = ", ".join(
            f"{category}/{difficulty}={count}"
            for (category, difficulty), count in sorted(counts[pool].items())
        )
        print(f"{pool}: {detail}")


if __name__ == "__main__":
    main()
