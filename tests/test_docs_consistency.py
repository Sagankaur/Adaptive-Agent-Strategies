"""Offline consistency checks between the docs and the data files they quote.

Standard library and pytest only. Nothing here touches the network or runs a model.

The constants (split sizes, seed, task counts, price-table model names) are read from
files in the repository; the checks assert that the docs state them consistently.
Assertions are written to survive reformatting: they look for numbers and names, not
for exact sentences.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
README = ROOT / "README.md"
SPLIT_FILE = ROOT / "splits" / "terminal-bench-2.0.json"
TASKS_FILE = ROOT / "evaluation" / "data" / "tb2_tasks.jsonl"
PRICE_FILE = ROOT / "evaluation" / "price_table.json"

# The planning throughput all GPU-day figures in the docs use (EXPERIMENTS.md, "Throughput").
PLANNING_RATE = 213.5


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _doc(name: str) -> str:
    return _read(DOCS / name)


def _normalise(text: str) -> str:
    """Drop Markdown emphasis and escapes so that `**A**` and `S\\*1` do not get in the way."""
    return text.replace("\\*", "*").replace("**", "").replace("`", "")


@pytest.fixture(scope="module")
def split() -> dict:
    return json.loads(_read(SPLIT_FILE))


@pytest.fixture(scope="module")
def tasks() -> list[dict]:
    return [json.loads(line) for line in _read(TASKS_FILE).splitlines() if line.strip()]


@pytest.fixture(scope="module")
def price_models() -> list[str]:
    return [row["model"] for row in json.loads(_read(PRICE_FILE))]


@pytest.fixture(scope="module")
def doc_files() -> list[Path]:
    files = sorted(DOCS.glob("*.md"))
    assert files, "docs/ has no Markdown files"
    return files


# ---------------------------------------------------------------------------
# The constants themselves must be self-consistent before docs are compared to them.
# ---------------------------------------------------------------------------


def test_split_file_is_self_consistent(split: dict, tasks: list[dict]) -> None:
    sizes = split["sizes"]
    assert {name: len(ids) for name, ids in split["splits"].items()} == sizes
    assert sum(sizes.values()) == len(tasks)
    all_ids = [t for ids in split["splits"].values() for t in ids]
    assert len(all_ids) == len(set(all_ids))
    assert set(all_ids) == {t["task_id"] for t in tasks}


# ---------------------------------------------------------------------------
# Split sizes and seed.
# ---------------------------------------------------------------------------


def _states_size(text: str, letter: str, size: int) -> bool:
    """True if the text says that split `letter` has `size` tasks.

    Accepts "H37", "H = 37", "H: 37", and a table row whose first cell starts with the
    letter and which has a cell equal to the size.
    """
    text = _normalise(text)
    if re.search(rf"(?<![A-Za-z0-9_]){letter}\s*[=:]?\s*{size}(?![0-9])", text):
        return True
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        if re.match(rf"{letter}(?![A-Za-z0-9])", cells[0]) and any(c == str(size) for c in cells[1:]):
            return True
    return False


def test_technical_plan_states_every_split_size_and_the_seed(split: dict) -> None:
    text = _doc("TECHNICAL_PLAN.md")
    missing = [f"{k}={n}" for k, n in split["sizes"].items() if not _states_size(text, k, n)]
    assert not missing, f"TECHNICAL_PLAN.md does not state split sizes {missing}"
    assert str(split["seed"]) in text, "TECHNICAL_PLAN.md does not state the split seed"


def test_experiments_states_held_out_size_and_the_seed(split: dict) -> None:
    text = _doc("EXPERIMENTS.md")
    held_out = split["sizes"]["H"]
    assert _states_size(text, "H", held_out), f"EXPERIMENTS.md does not state the held-out size H{held_out}"
    assert str(split["seed"]) in text, "EXPERIMENTS.md does not state the split seed"


def test_other_docs_that_quote_the_split_agree_with_the_file(split: dict, doc_files: list[Path]) -> None:
    sizes = split["sizes"]
    wrong: list[str] = []
    for path in doc_files:
        text = _normalise(_read(path))
        # "A25 / V12 / M15 / H37" written as a run of letter-number pairs.
        for run in re.finditer(r"(?:[AVMH]\s*[0-9]+\s*/\s*){3}[AVMH]\s*[0-9]+", text):
            for letter, number in re.findall(r"([AVMH])\s*([0-9]+)", run.group(0)):
                if sizes[letter] != int(number):
                    wrong.append(f"{path.name}: {letter}{number} (file says {sizes[letter]})")
    assert not wrong, "split sizes in docs differ from splits/terminal-bench-2.0.json: " + "; ".join(wrong)


def test_every_eight_digit_seed_in_docs_is_the_split_seed(split: dict, doc_files: list[Path]) -> None:
    seed = str(split["seed"])
    stray: list[str] = []
    for path in doc_files:
        for match in re.finditer(r"(?<![0-9A-Za-z])(2026[0-9]{4})(?![0-9])", _read(path)):
            if match.group(1) != seed:
                stray.append(f"{path.name}: {match.group(1)}")
    assert not stray, "seed-like numbers that differ from the split seed: " + ", ".join(stray)


# ---------------------------------------------------------------------------
# Task counts quoted in the docs.
# ---------------------------------------------------------------------------


def test_docs_state_the_tb2_task_count(tasks: list[dict]) -> None:
    n = len(tasks)
    for name in ("TECHNICAL_PLAN.md", "EXPERIMENTS.md", "OVERVIEW.md", "DECISIONS.md"):
        text = _normalise(_doc(name))
        assert re.search(rf"(?<![0-9,.]){n}(?![0-9,]) *(?:TB2 )?(?:tasks|task ids)|TB2-{n}", text), (
            f"{name} does not state the TB2 task count {n}"
        )


def test_glossary_category_counts_match_task_file(tasks: list[dict]) -> None:
    categories: dict[str, int] = {}
    for t in tasks:
        categories[t["category"]] = categories.get(t["category"], 0) + 1
    text = _normalise(_doc("GLOSSARY.md"))
    assert re.search(rf"{len(categories)} categories", text)
    singles = sum(1 for c in categories.values() if c == 1)
    assert re.search(rf"\b{singles} of them with a single task", text)


# ---------------------------------------------------------------------------
# Price table versus LOCAL_MODELS.md.
# ---------------------------------------------------------------------------


def test_every_price_table_model_is_named_in_local_models(price_models: list[str]) -> None:
    assert price_models, "price table is empty"
    text = _doc("LOCAL_MODELS.md")
    missing = [m for m in price_models if m not in text]
    assert not missing, f"LOCAL_MODELS.md does not name these price-table models: {missing}"


# ---------------------------------------------------------------------------
# README index.
# ---------------------------------------------------------------------------


def test_readme_lists_every_doc(doc_files: list[Path]) -> None:
    readme = _read(README)
    unlisted = [p.name for p in doc_files if f"docs/{p.name}" not in readme]
    assert not unlisted, f"README.md does not list: {unlisted}"


def test_readme_lists_only_docs_that_exist() -> None:
    readme = _read(README)
    linked = set(re.findall(r"docs/([A-Za-z0-9_.\-]+\.md)", readme))
    missing = sorted(name for name in linked if not (DOCS / name).exists())
    assert not missing, f"README.md links to docs that do not exist: {missing}"


# ---------------------------------------------------------------------------
# Public docs must not leak local file paths.
# ---------------------------------------------------------------------------

# Docs must use repo-relative paths only; an absolute home path means a local file leaked in.
FORBIDDEN = ("/home/",)


@pytest.mark.parametrize("needle", FORBIDDEN, ids=["home-path"])
def test_docs_do_not_contain_private_strings(needle: str, doc_files: list[Path]) -> None:
    hits = [
        f"{p.name}:{i}"
        for p in doc_files
        for i, line in enumerate(_read(p).splitlines(), start=1)
        if needle in line
    ]
    assert not hits, f"{needle!r} found in public docs at {hits}"


# ---------------------------------------------------------------------------
# GPU-day arithmetic: every "N episodes (X GPU-days)" pair equals N / 213.5, rounded to
# the number of decimals the doc itself uses.
# ---------------------------------------------------------------------------

_NUM = r"(?<![0-9.,/])([0-9][0-9,]*)"
_PAIR_WORDED = re.compile(
    _NUM + r"(?: episodes)?\s*(?:\(|=|\bis\b)\s*(?:about |~)?([0-9]+\.[0-9]+) GPU-days?"
)
_PAIR_TABLE = re.compile(r"\|\s*" + _NUM + r"\s*\(\s*([0-9]+\.[0-9]+)(?: GPU-days?)?\s*\)\s*\|")


def _gpu_day_pairs(text: str):
    for pattern in (_PAIR_WORDED, _PAIR_TABLE):
        for match in pattern.finditer(text):
            yield match.group(1), match.group(2), match.start()


def test_episode_and_gpu_day_pairs_agree_at_the_planning_rate(doc_files: list[Path]) -> None:
    bad: list[str] = []
    checked = 0
    for path in doc_files:
        text = _normalise(_read(path))
        for episodes_text, days_text, pos in _gpu_day_pairs(text):
            episodes = int(episodes_text.replace(",", ""))
            decimals = len(days_text.split(".")[1])
            expected = round(episodes / PLANNING_RATE, decimals)
            checked += 1
            if abs(expected - float(days_text)) > 10 ** -(decimals + 6):
                line = text.count("\n", 0, pos) + 1
                bad.append(f"{path.name}:{line}: {episodes_text} episodes -> {days_text} (expected {expected})")
    assert checked > 0, "no episode/GPU-day pairs found; the pattern no longer matches the docs"
    assert not bad, "GPU-day figures that do not equal episodes / 213.5:\n" + "\n".join(bad)


def test_cut_order_tables_agree_across_docs() -> None:
    """The plan size after each cut must be printed in every doc that prints the cut order."""
    expected = [9413, 9235, 8825, 7505, 6580, 6224]
    for name in ("TECHNICAL_PLAN.md", "EXPERIMENTS.md", "EXECUTION_PLAN.md", "DESIGN_REVIEW_2026-10.md"):
        text = _normalise(_doc(name))
        missing = [f"{n:,}" for n in expected if f"{n:,}" not in text]
        assert not missing, f"{name} does not print the cut-order totals {missing}"


def test_core_budget_is_stated_identically() -> None:
    for name in ("TECHNICAL_PLAN.md", "EXPERIMENTS.md", "EXECUTION_PLAN.md", "DECISIONS.md", "RISK_REGISTER.md"):
        text = _normalise(_doc(name))
        assert "9,653" in text, f"{name} does not state the core episode total 9,653"
        assert re.search(r"45\.2[01]?\b", text), f"{name} does not state the core GPU-days (45.21)"
