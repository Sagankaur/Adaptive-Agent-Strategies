"""Cost accounting, so that baselines can be compared at equal cost (TECHNICAL_PLAN.md, section 4.2).

Every model call is counted with its input and output tokens and its
wall-clock time, and wall-clock time is also measured per episode
(:class:`llm.Cost`, re-exported here). Dollars are derived with a price table
that is frozen at project start, so price changes during the project do not
move results.

A price entry has a per-token price and, for models run on our own or rented
hardware, an optional compute rate:

    dollars = input_tokens * input_usd_per_m / 1e6
            + output_tokens * output_usd_per_m / 1e6
            + model_s / 3600 * compute_usd_per_hour

``model_s`` is the time spent inside model calls, not the episode's
``wall_s``, which also covers environment time. A local model has zero token
prices and a compute rate (GPU rental, or hardware and electricity). Entries
marked ``placeholder`` do not have their rates filled in yet and refuse to
price anything.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from llm import Cost

__all__ = ["Cost", "PriceNotSetError", "PriceTable", "load_price_tables"]


class PriceNotSetError(ValueError):
    """A placeholder price entry was used to compute dollars."""


class PriceTable(BaseModel):
    """Prices for one model, with where and when they were seen.

    Token prices are US dollars per million tokens. ``compute_usd_per_hour``
    is charged per hour of model-call time; ``None`` means no compute charge
    applies, as for an API whose token price already covers it. ``hardware``
    names what the compute rate is for, since local wall-clock time depends on
    it (TECHNICAL_PLAN.md, section 4.3).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    model: str
    input_usd_per_m: float = Field(ge=0)
    output_usd_per_m: float = Field(ge=0)
    compute_usd_per_hour: float | None = Field(default=None, ge=0)
    hardware: str | None = None
    placeholder: bool = False
    source: str
    seen_on: str

    def dollars(self, cost: Cost) -> float:
        if self.placeholder:
            raise PriceNotSetError(f"the price entry for {self.model!r} is a placeholder: {self.source}")
        tokens = (cost.input_tokens * self.input_usd_per_m + cost.output_tokens * self.output_usd_per_m) / 1e6
        compute = cost.model_s / 3600 * self.compute_usd_per_hour if self.compute_usd_per_hour else 0.0
        return tokens + compute


def load_price_tables(path: Path) -> dict[str, PriceTable]:
    entries = json.loads(path.read_text())
    return {entry["model"]: PriceTable.model_validate(entry) for entry in entries}
