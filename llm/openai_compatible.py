"""A client for any server that implements the OpenAI chat-completions API.

That covers local servers for open-weight models (Ollama, the llama.cpp
server, vLLM, LM Studio) and hosted APIs (OpenAI, Together) alike: the only
differences are the base URL, the model id and whether an API key is needed.
See ``docs/LOCAL_MODELS.md``.

It uses only the standard library, sends one non-streaming request per call,
and returns the token counts the server reports in ``usage``. If the server
reports none, the call fails with :class:`MissingUsageError` instead of
estimating, because cost results must rest on counted tokens.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from threading import Lock
from typing import Any
from urllib.parse import urlparse

from llm.base import ChatResponse, Cost, Message

_ERROR_BODY_CHARS = 500


class ProviderError(RuntimeError):
    """The model server could not be reached, refused the request, or sent an unusable reply."""


class MissingUsageError(ProviderError):
    """The reply had no provider-reported token counts."""


@dataclass
class OpenAICompatibleModel:
    """Sends conversations to ``{base_url}/chat/completions`` and returns the reply.

    - ``base_url``: the API root including its version path, for example
      ``http://localhost:11434/v1`` (Ollama) or ``https://api.openai.com/v1``.
    - ``model``: the id the server knows the model by.
    - ``api_key``: sent as a bearer token when given; local servers usually need none.
    - ``name``: the name used in result records and to look up the price
      table; defaults to ``model``.
    - ``temperature``, ``top_p``, ``top_k`` and ``max_tokens``: sent when not ``None``.
      Some hosted reasoning APIs reject sampling controls, so callers can omit them explicitly.
    - ``seed``: root for deterministic, unique per-request seeds. Each call uses
      ``seed + request_index``; use a task/run-specific root for isolated trials.
    - ``headers``: extra HTTP headers, sent with every request.

    Each reply's ``elapsed_s`` is the wall-clock time of the HTTP round trip.
    ``usage`` is the running total of calls, tokens and seconds over the
    model's lifetime. The client is not thread-safe.
    """

    base_url: str
    model: str
    api_key: str | None = field(default=None, repr=False)
    name: str = ""
    timeout_s: float = 120.0
    temperature: float | None = 0.6
    top_p: float | None = 0.95
    top_k: int | None = 20
    seed: int = 20261015
    max_tokens: int | None = None
    headers: Mapping[str, str] = field(default_factory=dict)
    usage: Cost = field(default_factory=Cost, init=False)
    _request_count: int = field(default=0, init=False, repr=False)
    _seed_lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        if urlparse(self.base_url).scheme not in ("http", "https"):
            raise ValueError(f"base_url must be an http or https URL, got {self.base_url!r}")
        if not self.model:
            raise ValueError("model must be the id the server knows the model by")
        if self.timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError("seed must be a non-negative integer")
        if self.top_p is not None and not 0 < self.top_p <= 1:
            raise ValueError("top_p must be in (0, 1]")
        if self.top_k is not None and self.top_k < 1:
            raise ValueError("top_k must be positive")
        if not self.name:
            self.name = self.model

    @classmethod
    def from_env(cls, prefix: str = "LLM_", environ: Mapping[str, str] | None = None) -> OpenAICompatibleModel:
        """Build a client from ``{prefix}BASE_URL`` and ``{prefix}MODEL``.

        Optional: ``{prefix}API_KEY``, ``{prefix}NAME``, ``{prefix}TIMEOUT_S``,
        ``{prefix}MAX_TOKENS``, ``{prefix}TOP_P``, ``{prefix}TOP_K`` and ``{prefix}SEED``.
        ``environ`` defaults to ``os.environ``.
        """
        env = os.environ if environ is None else environ
        missing = [prefix + key for key in ("BASE_URL", "MODEL") if not env.get(prefix + key)]
        if missing:
            raise ValueError(f"set {' and '.join(missing)} to use a model server")
        max_tokens = env.get(prefix + "MAX_TOKENS")
        return cls(
            base_url=env[prefix + "BASE_URL"],
            model=env[prefix + "MODEL"],
            api_key=env.get(prefix + "API_KEY") or None,
            name=env.get(prefix + "NAME", ""),
            timeout_s=float(env.get(prefix + "TIMEOUT_S", "120")),
            max_tokens=int(max_tokens) if max_tokens else None,
            temperature=float(env.get(prefix + "TEMPERATURE", "0.6")),
            top_p=float(env.get(prefix + "TOP_P", "0.95")),
            top_k=int(env.get(prefix + "TOP_K", "20")),
            seed=int(env.get(prefix + "SEED", "20261015")),
        )

    @property
    def endpoint(self) -> str:
        return self.base_url.rstrip("/") + "/chat/completions"

    def _request_body(
        self, messages: Sequence[Message], seed: int, max_output_tokens: int | None = None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    **{"role": message.role, "content": message.content},
                    **({"tool_call_id": message.tool_call_id} if message.tool_call_id is not None else {}),
                    **({"tool_calls": message.tool_calls} if message.tool_calls is not None else {}),
                }
                for message in messages
            ],
            "stream": False,
        }
        if self.temperature is not None:
            body["temperature"] = self.temperature
        if self.top_p is not None:
            body["top_p"] = self.top_p
        if self.top_k is not None:
            body["top_k"] = self.top_k
        request_max = self.max_tokens
        if max_output_tokens is not None:
            if isinstance(max_output_tokens, bool) or max_output_tokens < 1:
                raise ValueError("max_output_tokens must be a positive integer")
            request_max = max_output_tokens if request_max is None else min(request_max, max_output_tokens)
        if request_max is not None:
            body["max_tokens"] = request_max
        body["seed"] = seed
        return body

    def complete(
        self, messages: Sequence[Message], *, seed: int | None = None, max_output_tokens: int | None = None
    ) -> ChatResponse:
        with self._seed_lock:
            request_seed = self.seed + self._request_count if seed is None else seed
            self._request_count += 1
        headers = {"Content-Type": "application/json", "Accept": "application/json", **self.headers}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(self._request_body(messages, request_seed, max_output_tokens)).encode(),
            headers=headers,
            method="POST",
        )
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as reply:
                raw = reply.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:_ERROR_BODY_CHARS]
            raise ProviderError(f"{self.endpoint} returned HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            raise ProviderError(f"could not reach {self.endpoint}: {exc}") from exc
        elapsed = time.perf_counter() - start

        response = ChatResponse(*self._parse(raw), elapsed_s=elapsed, seed=request_seed)
        self.usage.record(response)
        return response

    def _parse(self, raw: bytes) -> tuple[str, int, int]:
        """The reply text and the provider-reported input and output tokens."""
        try:
            data = json.loads(raw)
        except ValueError as exc:
            raise ProviderError(f"{self.endpoint} did not return JSON: {raw[:_ERROR_BODY_CHARS]!r}") from exc
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"{self.endpoint} returned no choices[0].message.content") from exc
        if not isinstance(text, str):
            raise ProviderError(f"{self.endpoint} returned no text content (content is {text!r})")

        usage = data.get("usage")
        tokens = [usage.get(key) if isinstance(usage, dict) else None for key in ("prompt_tokens", "completion_tokens")]
        if not all(isinstance(t, int) and not isinstance(t, bool) and t >= 0 for t in tokens):
            raise MissingUsageError(
                f"{self.endpoint} reply for model {self.model!r} has no usage.prompt_tokens and "
                f"usage.completion_tokens (usage is {usage!r}); token counts are not estimated"
            )
        return text, tokens[0], tokens[1]
