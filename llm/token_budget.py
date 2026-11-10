"""Shared output-token limits for multi-call episodes."""

from __future__ import annotations

from collections.abc import Sequence

from llm.base import ChatModel, ChatResponse, Message


class GeneratedTokenBudgetError(RuntimeError):
    """A generated-token budget prevented a call or the provider exceeded its request cap."""

    def __init__(self, reason: str, *, response: ChatResponse | None = None, overrun_tokens: int = 0) -> None:
        super().__init__(reason)
        self.response = response
        self.overrun_tokens = overrun_tokens


class GeneratedTokenBudget:
    """A model view that charges every reply's output tokens to one shared allowance."""

    def __init__(self, model: ChatModel, limit: int) -> None:
        if isinstance(limit, bool) or limit < 1:
            raise ValueError("generated-token limit must be a positive integer")
        self.model = model
        self.name = model.name
        self.limit = limit
        self.used = 0
        self.overrun_tokens = 0

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)

    def complete(
        self,
        messages: Sequence[Message],
        *,
        seed: int | None = None,
        max_output_tokens: int | None = None,
    ) -> ChatResponse:
        remaining = self.remaining
        if remaining == 0:
            raise GeneratedTokenBudgetError("generated-token budget exhausted")
        request_limit = remaining if max_output_tokens is None else min(remaining, max_output_tokens)
        response = self.model.complete(messages, seed=seed, max_output_tokens=request_limit)
        self.used += response.output_tokens
        if response.output_tokens > request_limit:
            overrun = response.output_tokens - request_limit
            self.overrun_tokens += overrun
            raise GeneratedTokenBudgetError(
                "provider output exceeded requested token limit", response=response, overrun_tokens=overrun
            )
        return response
