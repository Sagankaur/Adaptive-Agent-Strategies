"""A provider-agnostic chat interface, a scripted mock, and a client for OpenAI-compatible servers.

The tests run offline against :class:`MockModel` and a local stub server.
:class:`OpenAICompatibleModel` talks to a real model server, local (Ollama,
llama.cpp, vLLM, LM Studio) or hosted; see ``docs/LOCAL_MODELS.md``.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field

from llm.base import ChatModel, ChatResponse, Cost, Message, Pricing
from llm.openai_compatible import MissingUsageError, OpenAICompatibleModel, ProviderError


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
    receives is kept in ``calls`` for inspection, and ``usage`` is the running
    total of calls and tokens.
    """

    script: Sequence[str] | Policy
    name: str = "mock"
    calls: list[list[Message]] = field(default_factory=list)
    usage: Cost = field(default_factory=Cost, init=False)
    _replies: Iterator[str] | None = field(default=None, init=False, repr=False)

    def complete(self, messages: Sequence[Message], *, seed: int | None = None) -> ChatResponse:
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
        response = ChatResponse(
            text=text,
            input_tokens=sum(approx_tokens(m.content or "") for m in messages),
            output_tokens=approx_tokens(text),
            seed=seed,
        )
        self.usage.record(response)
        return response


class ProviderModel:
    """A named model that refuses to run, for code paths that must never call a model.

    Real endpoints, local or hosted, go through :class:`OpenAICompatibleModel`.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def complete(self, messages: Sequence[Message], *, seed: int | None = None) -> ChatResponse:
        raise NotImplementedError(
            f"{self.name!r} is a ProviderModel, which never calls a model; use OpenAICompatibleModel for a server"
        )


__all__ = [
    "ChatModel",
    "ChatResponse",
    "Cost",
    "Message",
    "MissingUsageError",
    "MockModel",
    "MockScriptExhausted",
    "OpenAICompatibleModel",
    "Policy",
    "Pricing",
    "ProviderError",
    "ProviderModel",
    "approx_tokens",
]
