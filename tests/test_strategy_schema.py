from __future__ import annotations

import pytest
from pydantic import ValidationError

from strategy_schema import DIMENSIONS, Edit, EditError, Strategy, apply_edits, s0
from tests.helpers import edited


def _with(strategy: Strategy, dimension: str, **fields: object) -> dict:
    doc = strategy.model_dump(mode="json")
    doc[dimension].update(fields)
    return doc


def test_s0_is_valid_and_round_trips_through_json(strategy: Strategy) -> None:
    restored = Strategy.from_json(strategy.to_json())
    assert restored == strategy
    assert restored.to_json() == strategy.to_json()


def test_set_fields_serialise_sorted_for_stable_json(strategy: Strategy) -> None:
    doc = strategy.model_dump(mode="json")
    assert doc["tool_policy"]["tools_allowed"] == sorted(doc["tool_policy"]["tools_allowed"])
    assert doc["recovery"]["retry_on"] == ["nonzero_exit", "timeout"]


@pytest.mark.parametrize(
    ("dimension", "fields"),
    [
        ("exploration", {"probe_budget_steps": 11}),
        ("exploration", {"probes": ["list_workdir", "list_workdir"]}),
        ("exploration", {"probes": ["not_a_probe"]}),
        ("planning", {"planning_depth": 13}),
        ("planning", {"replan_trigger": "every_k_steps", "replan_every_k": None}),
        ("tool_policy", {"command_timeout_s": 5}),
        ("tool_policy", {"max_observation_chars": 20001}),
        ("tool_policy", {"tools_allowed": ["bash", "browser"]}),
        ("memory", {"lessons_k": 6}),
        ("memory", {"window_or_summary_k": 0}),
        ("verification", {"max_verify_cycles": 6}),
        ("recovery", {"max_retries": 6}),
        ("recovery", {"max_rollbacks": 4}),
        ("budget", {"max_steps": 0}),
        ("budget", {"unknown_field": 1}),
    ],
)
def test_out_of_range_or_unknown_values_are_rejected(strategy: Strategy, dimension: str, fields: dict) -> None:
    with pytest.raises(ValidationError):
        Strategy.model_validate(_with(strategy, dimension, **fields))


def test_notes_are_limited_to_known_stages_and_300_chars(strategy: Strategy) -> None:
    doc = strategy.model_dump(mode="json")
    Strategy.model_validate({**doc, "notes": {"plan": "x" * 300}})
    with pytest.raises(ValidationError):
        Strategy.model_validate({**doc, "notes": {"plan": "x" * 301}})
    with pytest.raises(ValidationError):
        Strategy.model_validate({**doc, "notes": {"deploy": "x"}})


def test_parent_must_precede_version(strategy: Strategy) -> None:
    doc = strategy.model_dump(mode="json")
    with pytest.raises(ValidationError):
        Strategy.model_validate({**doc, "version": 2, "parent_version": 2})


def test_apply_edits_creates_child_version_with_changelog(strategy: Strategy) -> None:
    edit = Edit(
        op="add",
        path="/exploration/probes/-",
        value="check_installed_packages",
        rationale="missing dependency found late",
        diagnosis_ids=["d-1"],
        round=0,
    )
    child = apply_edits(strategy, [edit], version=1)
    assert (child.version, child.parent_version) == (1, 0)
    assert child.changelog == [edit]
    assert child.exploration.probes[-1] == "check_installed_packages"
    assert strategy.exploration.probes == ["list_workdir", "read_readme"]


def test_add_to_a_set_field_with_dash(strategy: Strategy) -> None:
    child = edited(strategy, ("add", "/tool_policy/tools_allowed/-", "python"))
    assert "python" in child.tool_policy.tools_allowed


@pytest.mark.parametrize(
    "edits",
    [
        [Edit(op="replace", path="/budget/max_steps", value=1000)],
        [Edit(op="replace", path="/version", value=9)],
        [Edit(op="replace", path="/exploration/no_such_field", value=1)],
        [Edit(op="replace", path="/verification/max_verify_cycles", value=1)] * 3,
        [],
    ],
)
def test_invalid_edits_are_refused(strategy: Strategy, edits: list[Edit]) -> None:
    with pytest.raises(EditError):
        apply_edits(strategy, edits, version=1)


def test_edit_producing_out_of_range_value_is_refused(strategy: Strategy) -> None:
    with pytest.raises(ValidationError):
        edited(strategy, ("replace", "/verification/max_verify_cycles", 9))


def test_diff_reports_changes_per_dimension(strategy: Strategy) -> None:
    child = edited(
        strategy,
        ("replace", "/verification/verification_required", False),
        ("add", "/notes/plan", "Read the Makefile first."),
    )
    diff = strategy.diff(child)
    assert set(diff) == {"verification", "notes"}
    assert [(c.path, c.before, c.after) for c in diff["verification"]] == [
        ("/verification/verification_required", True, False)
    ]
    assert [(c.path, c.before, c.after) for c in diff["notes"]] == [("/notes/plan", None, "Read the Makefile first.")]
    assert strategy.diff(strategy) == {}
    assert set(diff) <= set(DIMENSIONS)


def test_render_reflects_fields(strategy: Strategy) -> None:
    text = strategy.render()
    assert "list_workdir, read_readme" in text
    assert "run_visible_tests" in text
    assert "at most 40 steps" in text
    assert "Notes:" not in text

    child = edited(
        strategy,
        ("replace", "/verification/verification_required", False),
        ("add", "/notes/verify", "Compare output with the example."),
    )
    rendered = child.render()
    assert "Verification: none required." in rendered
    assert "- [verify] Compare output with the example." in rendered


def test_render_is_deterministic() -> None:
    assert s0().render() == s0().render()
