"""Applying edits to a strategy to produce a new version (TECHNICAL_PLAN.md, sections 3.1-3.2).

An edit is one or two JSON-Patch-like operations. The result is validated
against the full schema, so an edit that would put a field out of range is
rejected rather than silently clipped. Budget and meta fields cannot be
edited: budgets are fixed by the experiment, and lineage is set here.
"""

from __future__ import annotations

from typing import Any

from strategy_schema.model import EDITABLE_DIMENSIONS, Edit, Strategy

MAX_EDIT_OPS = 2


class EditError(ValueError):
    """An edit that cannot be applied to the strategy."""


def _tokens(path: str) -> list[str]:
    return [t.replace("~1", "/").replace("~0", "~") for t in path.lstrip("/").split("/")]


def _apply_op(doc: dict[str, Any], edit: Edit) -> None:
    tokens = _tokens(edit.path)
    if tokens[0] not in EDITABLE_DIMENSIONS:
        raise EditError(f"{edit.path}: only {', '.join(EDITABLE_DIMENSIONS)} may be edited")
    parent: Any = doc
    for token in tokens[:-1]:
        try:
            parent = parent[int(token)] if isinstance(parent, list) else parent[token]
        except (KeyError, IndexError, ValueError) as exc:
            raise EditError(f"{edit.path}: no such location") from exc
    last = tokens[-1]

    if isinstance(parent, list):
        if edit.op == "add" and last == "-":
            parent.append(edit.value)
            return
        try:
            index = int(last)
        except ValueError as exc:
            raise EditError(f"{edit.path}: list index expected") from exc
        if edit.op == "add":
            if not 0 <= index <= len(parent):
                raise EditError(f"{edit.path}: index out of range")
            parent.insert(index, edit.value)
        elif not 0 <= index < len(parent):
            raise EditError(f"{edit.path}: index out of range")
        elif edit.op == "remove":
            del parent[index]
        else:
            parent[index] = edit.value
    elif isinstance(parent, dict):
        if edit.op == "add":
            parent[last] = edit.value
        elif last not in parent:
            raise EditError(f"{edit.path}: no such field")
        elif edit.op == "remove":
            del parent[last]
        else:
            parent[last] = edit.value
    else:
        raise EditError(f"{edit.path}: parent is not a container")


def apply_edits(strategy: Strategy, edits: list[Edit], *, version: int) -> Strategy:
    """Return a new strategy version derived from ``strategy`` by ``edits``.

    The new version records ``strategy`` as its parent and appends ``edits``
    to the changelog. ``version`` is supplied by the caller because candidate
    versions are numbered by whoever keeps the lineage (the adaptation loop).
    """
    if not 1 <= len(edits) <= MAX_EDIT_OPS:
        raise EditError(f"an edit has 1 to {MAX_EDIT_OPS} operations, got {len(edits)}")
    if version <= strategy.version:
        raise EditError("the new version must be higher than the parent's")
    doc = strategy.model_dump(mode="json")
    for edit in edits:
        _apply_op(doc, edit)
    doc["version"] = version
    doc["parent_version"] = strategy.version
    doc["changelog"] = [*doc["changelog"], *(e.model_dump(mode="json") for e in edits)]
    return Strategy.model_validate(doc)
