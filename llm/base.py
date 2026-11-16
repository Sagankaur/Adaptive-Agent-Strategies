"""Messages, replies, the chat-model interface and the usage counter shared by every model.

These live in their own module so that model clients (``llm.openai_compatible``)
and cost accounting (``baselines.cost``) can both use them without importing
each other.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


@dataclass(frozen=True)
class ChatResponse:
    """A model reply with the token counts and time used for cost accounting.

    ``elapsed_s`` is the wall-clock time of the call as measured by the client.
    The mock does no inference and reports 0.
    """

    text: str
    input_tokens: int
    output_tokens: int
    elapsed_s: float = 0.0
    seed: int | None = None


class ChatModel(Protocol):
    """Anything that turns a conversation into one reply.

    A real provider client implements this by sending ``messages`` to its API
    and returning the provider-reported token counts in the response.
    """

    name: str

    def complete(
        self, messages: Sequence[Message], *, seed: int | None = None, max_output_tokens: int | None = None
    ) -> ChatResponse: ...


class Pricing(Protocol):
    """Anything that turns a :class:`Cost` into dollars; ``baselines.cost.PriceTable`` is the implementation."""

    def dollars(self, cost: Cost) -> float: ...


@dataclass
class Cost:
    """Calls, tokens and time, summed over model replies.

    :meth:`record` adds one reply: a call, its tokens, and its ``elapsed_s``
    into ``model_s``. ``wall_s`` is set by whoever times a whole episode
    (``baselines.agent_loop``) and also covers environment time, so it is at
    least ``model_s`` there. Models keep one of these as a running total in
    their ``usage`` attribute, where ``wall_s`` stays 0.
    """

    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    model_s: float = 0.0
    wall_s: float = 0.0

    @property
    def tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def record(self, response: ChatResponse) -> None:
        self.calls += 1
        self.input_tokens += response.input_tokens
        self.output_tokens += response.output_tokens
        self.model_s += response.elapsed_s

    def __add__(self, other: Cost) -> Cost:
        return Cost(
            calls=self.calls + other.calls,
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            model_s=self.model_s + other.model_s,
            wall_s=self.wall_s + other.wall_s,
        )

    def dollars(self, prices: Pricing) -> float:
        return prices.dollars(self)

    def to_dict(self) -> dict[str, float]:
        return asdict(self)
