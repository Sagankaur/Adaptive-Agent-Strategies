"""Async OpenAI-compatible client retaining llama.cpp's tool and timing fields."""

from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from threading import Lock
from typing import Any
from urllib.parse import urlparse

from llm.openai_compatible import MissingUsageError, ProviderError


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class ModelTimings:
    prompt_tokens: int
    cached_tokens: int
    generated_tokens: int
    prompt_ms: float
    generated_ms: float


@dataclass(frozen=True)
class AsyncChatResponse:
    content: str | None
    reasoning: str | None
    tool_calls: tuple[ToolCall, ...]
    input_tokens: int
    cached_tokens: int
    output_tokens: int
    timings: ModelTimings
    elapsed_s: float
    seed: int


@dataclass
class AsyncOpenAICompatibleModel:
    """Per-trial async client. HTTP runs in a worker thread to avoid extra dependencies."""

    base_url: str
    model: str
    api_key: str | None = field(default=None, repr=False)
    timeout_s: float = 120.0
    temperature: float = 0.6
    top_p: float = 0.95
    top_k: int = 20
    seed: int = 20261015
    max_tokens: int | None = None
    chat_template_kwargs: Mapping[str, Any] = field(default_factory=dict)
    headers: Mapping[str, str] = field(default_factory=dict)
    _request_count: int = field(default=0, init=False, repr=False)
    _seed_lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        if urlparse(self.base_url).scheme not in ("http", "https"):
            raise ValueError("base_url must use http or https")
        if not self.model:
            raise ValueError("model is required")
        if self.timeout_s <= 0 or not 0 < self.top_p <= 1 or self.top_k < 1:
            raise ValueError("timeout_s, top_p or top_k is out of range")
        if self.seed < 0:
            raise ValueError("seed must be non-negative")

    @property
    def endpoint(self) -> str:
        return self.base_url.rstrip("/") + "/chat/completions"

    def _request_body(
        self,
        messages: Sequence[Mapping[str, Any]],
        seed: int,
        tools: Sequence[Mapping[str, Any]] | None = None,
        max_output_tokens: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [dict(message) for message in messages],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "seed": seed,
            "stream": False,
        }
        request_max = self.max_tokens
        if max_output_tokens is not None:
            if isinstance(max_output_tokens, bool) or max_output_tokens < 1:
                raise ValueError("max_output_tokens must be a positive integer")
            request_max = max_output_tokens if request_max is None else min(request_max, max_output_tokens)
        if request_max is not None:
            body["max_tokens"] = request_max
        if self.chat_template_kwargs:
            body["chat_template_kwargs"] = dict(self.chat_template_kwargs)
        if tools:
            body["tools"] = [dict(tool) for tool in tools]
        return body

    def _next_seed(self, seed: int | None = None) -> int:
        with self._seed_lock:
            request_seed = (self.seed if seed is None else seed) + self._request_count
            self._request_count += 1
            return request_seed

    async def complete(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        seed: int | None = None,
        tools: Sequence[Mapping[str, Any]] | None = None,
        max_output_tokens: int | None = None,
    ) -> AsyncChatResponse:
        request_seed = self._next_seed(seed)
        return await asyncio.to_thread(self._complete_sync, messages, request_seed, tools, max_output_tokens)

    def _complete_sync(
        self,
        messages: Sequence[Mapping[str, Any]],
        seed: int,
        tools: Sequence[Mapping[str, Any]] | None,
        max_output_tokens: int | None,
    ) -> AsyncChatResponse:
        headers = {"Content-Type": "application/json", "Accept": "application/json", **self.headers}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(self._request_body(messages, seed, tools, max_output_tokens)).encode(),
            headers=headers,
            method="POST",
        )
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:500]
            raise ProviderError(f"{self.endpoint} returned HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            raise ProviderError(f"could not reach {self.endpoint}: {exc}") from exc
        elapsed = time.perf_counter() - start
        parsed = self._parse(raw)
        return AsyncChatResponse(**parsed, elapsed_s=elapsed, seed=seed)

    def _parse(self, raw: bytes) -> dict[str, Any]:
        try:
            data = json.loads(raw)
            message = data["choices"][0]["message"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"{self.endpoint} returned an invalid chat-completions response") from exc
        content = message.get("content")
        reasoning = message.get("reasoning_content")
        if content is not None and not isinstance(content, str):
            raise ProviderError("message.content must be text or null")
        if reasoning is not None and not isinstance(reasoning, str):
            raise ProviderError("message.reasoning_content must be text or null")
        calls: list[ToolCall] = []
        for call in message.get("tool_calls") or []:
            try:
                function = call["function"]
                calls.append(ToolCall(str(call["id"]), str(function["name"]), str(function["arguments"])))
            except (KeyError, TypeError) as exc:
                raise ProviderError("tool_calls contains a malformed function call") from exc
        usage = data.get("usage")
        if not isinstance(usage, dict):
            raise MissingUsageError(f"{self.endpoint} reply has no usage object")
        prompt = usage.get("prompt_tokens")
        generated = usage.get("completion_tokens")
        details = usage.get("prompt_tokens_details") or {}
        cached = details.get("cached_tokens", 0) if isinstance(details, dict) else 0
        values = (prompt, cached, generated)
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in values):
            raise MissingUsageError(f"{self.endpoint} reply has invalid prompt/completion/cached token counts")
        timing = data.get("timings") or {}

        def timing_value(key: str, fallback: int | float) -> float:
            value = timing.get(key, fallback)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                raise ProviderError(f"invalid timings.{key}")
            return float(value)

        timings = ModelTimings(
            int(timing_value("prompt_n", prompt)),
            int(timing_value("cache_n", cached)),
            int(timing_value("predicted_n", generated)),
            timing_value("prompt_ms", 0),
            timing_value("predicted_ms", 0),
        )
        return {
            "content": content,
            "reasoning": reasoning,
            "tool_calls": tuple(calls),
            "input_tokens": prompt,
            "cached_tokens": cached,
            "output_tokens": generated,
            "timings": timings,
        }
