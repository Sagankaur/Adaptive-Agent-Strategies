"""Cost accounting, so that baselines can be compared at equal cost (TECHNICAL_PLAN.md, section 4.2).

Every model call is counted with its input and output tokens, and wall-clock
time is measured per episode. Dollars are derived from tokens with a price
table that is frozen at project start, so price changes during the project
do not move results.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from llm import ChatResponse


class PriceTable(BaseModel):
    """US dollars per million tokens for one model, with where and when the prices were seen."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model: str
    input_usd_per_m: float = Field(ge=0)
    output_usd_per_m: float = Field(ge=0)
    source: str
    seen_on: str


def load_price_tables(path: Path) -> dict[str, PriceTable]:
    entries = json.loads(path.read_text())
    return {entry["model"]: PriceTable.model_validate(entry) for entry in entries}


@dataclass
class Cost:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    wall_s: float = 0.0

    @property
    def tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def record(self, response: ChatResponse) -> None:
        self.calls += 1
        self.input_tokens += response.input_tokens
        self.output_tokens += response.output_tokens

    def __add__(self, other: Cost) -> Cost:
        return Cost(
            calls=self.calls + other.calls,
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            wall_s=self.wall_s + other.wall_s,
        )

    def dollars(self, prices: PriceTable) -> float:
        return (self.input_tokens * prices.input_usd_per_m + self.output_tokens * prices.output_usd_per_m) / 1e6

    def to_dict(self) -> dict[str, float]:
        return asdict(self)
