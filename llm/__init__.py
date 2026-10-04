"""A provider-agnostic chat interface, a scripted mock, and the slot where a real client goes.

Nothing in this repository calls a model API yet. Everything runs offline
against :class:`MockModel`.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from typing import Literal, Protocol


@dataclass(frozen=True)
class Message:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class ChatResponse:
    """A model reply with the token counts used for cost accounting."""

    text: str
    input_tokens: int
    output_tokens: int


class ChatModel(Protocol):
    """Anything that turns a conversation into one reply.

    A real provider client implements this by sending ``messages`` to its API
    and returning the provider-reported token counts in the response.
    """

    name: str

    def complete(self, messages: Sequence[Message]) -> ChatResponse: ...


def approx_tokens(text: str) -> int:
    """Rough token count (four characters per token) for offline accounting only."""
    return max(1, math.ceil(len(text) / 4))


class MockScriptExhausted(RuntimeError):
    """The mock was called more times than its script has replies."""


Policy = Callable[[Sequence[Message]], str]


@dataclass
class MockModel:
    """Returns scripted replies, either from a fixed list or from a function of the conversation.

    Token counts are approximated with :func:`approx_tokens`, so cost
    accounting can be tested without a provider. Every conversation it
    receives is kept in ``calls`` for inspection.
    """

    script: Sequence[str] | Policy
    name: str = "mock"
    calls: list[list[Message]] = field(default_factory=list)
    _replies: Iterator[str] | None = field(default=None, init=False, repr=False)

    def complete(self, messages: Sequence[Message]) -> ChatResponse:
        self.calls.append(list(messages))
        if callable(self.script):
            text = self.script(messages)
        else:
            if self._replies is None:
                self._replies = iter(self.script)
            try:
                text = next(self._replies)
            except StopIteration as exc:
                raise MockScriptExhausted(f"script has {len(self.script)} replies") from exc
        return ChatResponse(
            text=text,
            input_tokens=sum(approx_tokens(m.content) for m in messages),
            output_tokens=approx_tokens(text),
        )


class ProviderModel:
    """Where a real provider client plugs in once the model is chosen in Phase 0.

    It must implement :class:`ChatModel` and report the provider's own token
    counts; until then it refuses to run so that no code path can spend money
    by accident.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def complete(self, messages: Sequence[Message]) -> ChatResponse:
        raise NotImplementedError(
            f"no provider client is wired up for {self.name!r}; tests and the toy environment use MockModel"
        )


__all__ = [
    "ChatModel",
    "ChatResponse",
    "Message",
    "MockModel",
    "MockScriptExhausted",
    "Policy",
    "ProviderModel",
    "approx_tokens",
]
