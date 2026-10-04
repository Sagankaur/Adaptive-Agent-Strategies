from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from evaluation.splits import TERMINAL_BENCH_2_SIZES, TaskInfo, load_split, main, make_split, save_split


def _pool(n: int = 89) -> list[TaskInfo]:
    categories = ["build", "data", "security", "ml"]
    difficulties = ["easy", "medium", "hard"]
    return [TaskInfo(task_id=f"t{i:03d}", category=categories[i % 4], difficulty=difficulties[i % 3]) for i in range(n)]


def test_split_is_deterministic_for_a_seed() -> None:
    a = make_split(_pool(), TERMINAL_BENCH_2_SIZES, seed=7, benchmark="terminal-bench@2.0")
    b = make_split(list(reversed(_pool())), TERMINAL_BENCH_2_SIZES, seed=7, benchmark="terminal-bench@2.0")
    c = make_split(_pool(), TERMINAL_BENCH_2_SIZES, seed=8, benchmark="terminal-bench@2.0")
    assert a == b
    assert a.splits != c.splits


def test_split_has_exact_sizes_and_covers_every_task_once() -> None:
    split = make_split(_pool(), TERMINAL_BENCH_2_SIZES, seed=0, benchmark="terminal-bench@2.0")
    assert {name: len(ids) for name, ids in split.splits.items()} == TERMINAL_BENCH_2_SIZES
    all_ids = [t for ids in split.splits.values() for t in ids]
    assert sorted(all_ids) == sorted(t.task_id for t in _pool())


def test_split_is_stratified() -> None:
    pool = _pool()
    by_id = {t.task_id: t for t in pool}
    split = make_split(pool, TERMINAL_BENCH_2_SIZES, seed=0, benchmark="terminal-bench@2.0")
    for name, size in TERMINAL_BENCH_2_SIZES.items():
        counts = Counter(by_id[t].category for t in split.tasks(name))
        for category in ("build", "data", "security", "ml"):
            expected = size * sum(t.category == category for t in pool) / len(pool)
            assert abs(counts[category] - expected) <= 2, (name, category, counts)


def test_groups_stay_together() -> None:
    pool = [TaskInfo(task_id=f"s{g}-{i}", group=f"s{g}") for g in range(10) for i in range(3)]
    split = make_split(pool, {"A": 18, "V": 12}, seed=0, benchmark="appworld")
    for g in range(10):
        assert len({split.split_of(f"s{g}-{i}") for i in range(3)}) == 1


def test_sizes_must_match_the_pool() -> None:
    with pytest.raises(ValueError):
        make_split(_pool(10), TERMINAL_BENCH_2_SIZES, seed=0, benchmark="x")


def test_saved_split_round_trips_and_is_byte_stable(tmp_path: Path) -> None:
    path = tmp_path / "splits" / "tb2.json"
    split = make_split(_pool(), TERMINAL_BENCH_2_SIZES, seed=0, benchmark="terminal-bench@2.0")
    save_split(split, path)
    first = path.read_bytes()
    save_split(make_split(_pool(), TERMINAL_BENCH_2_SIZES, seed=0, benchmark="terminal-bench@2.0"), path)
    assert path.read_bytes() == first
    assert load_split(path) == split


def test_a_committed_split_is_not_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "tb2.json"
    save_split(make_split(_pool(), TERMINAL_BENCH_2_SIZES, seed=0, benchmark="terminal-bench@2.0"), path)
    with pytest.raises(FileExistsError):
        save_split(make_split(_pool(), TERMINAL_BENCH_2_SIZES, seed=1, benchmark="terminal-bench@2.0"), path)


def test_tampered_split_file_fails_validation(tmp_path: Path) -> None:
    path = tmp_path / "tb2.json"
    save_split(make_split(_pool(), TERMINAL_BENCH_2_SIZES, seed=0, benchmark="terminal-bench@2.0"), path)
    doc = json.loads(path.read_text())
    doc["splits"]["H"].append(doc["splits"]["A"][0])
    path.write_text(json.dumps(doc))
    with pytest.raises(ValueError):
        load_split(path)


def test_cli_writes_split_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text("\n".join(t.model_dump_json() for t in _pool(20)))
    out = tmp_path / "split.json"
    main(["--tasks", str(tasks), "--benchmark", "toy", "--seed", "3", "--sizes", "A=10,V=4,H=6", "--out", str(out)])
    assert {k: len(v) for k, v in load_split(out).splits.items()} == {"A": 10, "V": 4, "H": 6}
    assert "A=10" in capsys.readouterr().out
