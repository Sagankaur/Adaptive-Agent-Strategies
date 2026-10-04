from __future__ import annotations

import pytest

from environments import Task, make_toy_tasks
from strategy_schema import Strategy, s0


@pytest.fixture
def strategy() -> Strategy:
    return s0()


@pytest.fixture
def tasks() -> list[Task]:
    return make_toy_tasks(12, seed=0)
