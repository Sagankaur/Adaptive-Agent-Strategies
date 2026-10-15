"""The OpenAI-compatible client against a stub server on 127.0.0.1, and pricing of local models.

The stub mimics a chat-completions endpoint (Ollama, llama.cpp, vLLM and
LM Studio all serve this shape), so the tests stay offline.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from baselines import FixedStrategy, PriceNotSetError, PriceTable, load_price_tables
from environments import Task, ToyTextEnvironment
from evaluation import PRICE_TABLE_PATH
from evaluation.runner import RunBudget, evaluate
from evaluation.splits import TaskInfo, make_split
from llm import (
    ChatResponse,
    Cost,
    Message,
    MissingUsageError,
    MockModel,
    OpenAICompatibleModel,
    ProviderError,
)
from strategy_schema import Strategy
from tests.helpers import solver

Reply = Callable[[dict[str, Any]], tuple[int, Any]]
"""Maps a request body to (HTTP status, JSON body)."""


def completion(text: str | None, usage: dict[str, Any] | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "id": "chatcmpl-stub",
        "object": "chat.completion",
        "model": "stub",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
    }
    if usage is not None:
        body["usage"] = usage
    return body


@dataclass
class StubServer:
    url: str
    requests: list[dict[str, Any]] = field(default_factory=list)
    reply: Reply = lambda body: (200, completion("hi", {"prompt_tokens": 7, "completion_tokens": 2}))


@pytest.fixture
def stub() -> Iterator[StubServer]:
    state: StubServer

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state.requests.append({"path": self.path, "headers": dict(self.headers), "body": body})
            status, payload = state.reply(body)
            data = payload.encode() if isinstance(payload, str) else json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    state = StubServer(url=f"http://127.0.0.1:{server.server_address[1]}/v1")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_successful_call_returns_reported_usage_and_time(stub: StubServer) -> None:
    model = OpenAICompatibleModel(
        base_url=stub.url + "/",
        model="qwen3-coder:30b",
        api_key="sk-test",
        max_tokens=64,
        headers={"X-Run": "test"},
    )
    reply = model.complete([Message("system", "be brief"), Message("user", "hello")])

    assert (reply.text, reply.input_tokens, reply.output_tokens) == ("hi", 7, 2)
    assert reply.elapsed_s > 0
    sent = stub.requests[0]
    assert sent["path"] == "/v1/chat/completions"
    assert sent["headers"]["Authorization"] == "Bearer sk-test"
    assert sent["headers"]["X-Run"] == "test"
    assert sent["body"] == {
        "model": "qwen3-coder:30b",
        "messages": [{"role": "system", "content": "be brief"}, {"role": "user", "content": "hello"}],
        "stream": False,
        "temperature": 0.0,
        "max_tokens": 64,
    }
    assert model.name == "qwen3-coder:30b"
    assert "sk-test" not in repr(model)

    model.complete([Message("user", "again")])
    assert (model.usage.calls, model.usage.input_tokens, model.usage.output_tokens) == (2, 14, 4)
    assert model.usage.model_s > reply.elapsed_s


def test_optional_fields_are_left_out_of_the_request(stub: StubServer) -> None:
    OpenAICompatibleModel(base_url=stub.url, model="m", temperature=None).complete([Message("user", "x")])
    sent = stub.requests[0]
    assert "Authorization" not in sent["headers"]
    assert set(sent["body"]) == {"model", "messages", "stream"}


@pytest.mark.parametrize(
    "usage",
    [None, {}, {"prompt_tokens": 3}, {"prompt_tokens": 3, "completion_tokens": None}],
    ids=["absent", "empty", "no-completion-tokens", "null-completion-tokens"],
)
def test_missing_usage_is_an_error_not_an_estimate(stub: StubServer, usage: dict[str, Any] | None) -> None:
    stub.reply = lambda body: (200, completion("hi", usage))
    model = OpenAICompatibleModel(base_url=stub.url, model="m")
    with pytest.raises(MissingUsageError, match="not estimated"):
        model.complete([Message("user", "x")])
    assert model.usage.calls == 0


@pytest.mark.parametrize("status", [400, 401, 404, 500, 503])
def test_non_200_reply_raises_with_status_and_body(stub: StubServer, status: int) -> None:
    stub.reply = lambda body: (status, {"error": {"message": "model 'm' not found"}})
    with pytest.raises(ProviderError, match=f"HTTP {status}.*not found"):
        OpenAICompatibleModel(base_url=stub.url, model="m").complete([Message("user", "x")])


def test_unusable_replies_raise(stub: StubServer) -> None:
    model = OpenAICompatibleModel(base_url=stub.url, model="m")
    for payload in ("not json", {"choices": []}, completion(None, {"prompt_tokens": 1, "completion_tokens": 0})):
        stub.reply = lambda body, payload=payload: (200, payload)
        with pytest.raises(ProviderError) as info:
            model.complete([Message("user", "x")])
        assert not isinstance(info.value, MissingUsageError)


def test_unreachable_server_raises() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
    port = server.server_address[1]
    server.server_close()
    with pytest.raises(ProviderError, match="could not reach"):
        OpenAICompatibleModel(base_url=f"http://127.0.0.1:{port}/v1", model="m", timeout_s=2).complete(
            [Message("user", "x")]
        )


def test_constructor_and_env_configuration() -> None:
    with pytest.raises(ValueError, match="http or https"):
        OpenAICompatibleModel(base_url="file:///etc/passwd", model="m")
    with pytest.raises(ValueError, match="LLM_MODEL"):
        OpenAICompatibleModel.from_env(environ={"LLM_BASE_URL": "http://localhost:11434/v1"})
    model = OpenAICompatibleModel.from_env(
        environ={
            "LLM_BASE_URL": "http://localhost:8080/v1",
            "LLM_MODEL": "qwen3-coder-30b-q4.gguf",
            "LLM_NAME": "qwen3-coder:30b",
            "LLM_TIMEOUT_S": "600",
            "LLM_MAX_TOKENS": "2048",
        }
    )
    assert (model.endpoint, model.name, model.timeout_s, model.max_tokens, model.api_key) == (
        "http://localhost:8080/v1/chat/completions",
        "qwen3-coder:30b",
        600.0,
        2048,
        None,
    )


def test_mock_model_keeps_a_running_total() -> None:
    model = MockModel(["a", "b"])
    model.complete([Message("user", "x" * 40)])
    model.complete([Message("user", "x" * 8)])
    assert (model.usage.calls, model.usage.input_tokens, model.usage.output_tokens, model.usage.model_s) == (
        2,
        12,
        2,
        0.0,
    )


def _prices(**kwargs: Any) -> PriceTable:
    return PriceTable.model_validate({"model": "m", "source": "test", "seen_on": "2026-10-15", **kwargs})


def test_dollars_add_compute_hours_for_model_call_time() -> None:
    cost = Cost()
    cost.record(ChatResponse("a", input_tokens=1_000_000, output_tokens=0, elapsed_s=1800.0))
    cost.record(ChatResponse("b", input_tokens=0, output_tokens=500_000, elapsed_s=1800.0))
    cost.wall_s = 10_000.0  # episode time is not what compute is charged on

    local = _prices(input_usd_per_m=0, output_usd_per_m=0, compute_usd_per_hour=1.5, hardware="1x L4")
    assert cost.dollars(local) == pytest.approx(1.5)
    mixed = _prices(input_usd_per_m=0.25, output_usd_per_m=2.0, compute_usd_per_hour=1.5)
    assert cost.dollars(mixed) == pytest.approx(0.25 + 1.0 + 1.5)
    api = _prices(input_usd_per_m=0.25, output_usd_per_m=2.0)
    assert api.compute_usd_per_hour is None and cost.dollars(api) == pytest.approx(0.25 + 1.0)
    with pytest.raises(ValueError):
        _prices(input_usd_per_m=0, output_usd_per_m=0, compute_usd_per_hour=-1)


def test_price_table_keeps_old_entries_and_marks_local_placeholders() -> None:
    tables = load_price_tables(PRICE_TABLE_PATH)
    assert tables["gpt-5-mini"].compute_usd_per_hour is None and not tables["gpt-5-mini"].placeholder
    local = [t for t in tables.values() if t.placeholder]
    assert local
    for entry in local:
        assert (entry.input_usd_per_m, entry.output_usd_per_m, entry.compute_usd_per_hour) == (0, 0, None)
        assert "SMALL_MODELS.md" in entry.source
        with pytest.raises(PriceNotSetError):
            Cost(calls=1, input_tokens=10, model_s=1.0).dollars(entry)
        with pytest.raises(PriceNotSetError):
            RunBudget(prices=entry)


def test_runner_with_a_served_model_records_tokens_time_and_compute_dollars(
    stub: StubServer, tasks: list[Task], strategy: Strategy, tmp_path: Path
) -> None:
    policy = solver(sloppy_first=False)

    def play(body: dict[str, Any]) -> tuple[int, Any]:
        messages = [Message(m["role"], m["content"]) for m in body["messages"]]
        return 200, completion(policy(messages), {"prompt_tokens": 100, "completion_tokens": 10})

    stub.reply = play
    model = OpenAICompatibleModel(base_url=stub.url, model="qwen3-coder:30b")
    infos = [TaskInfo(task_id=t.task_id, category=t.category, difficulty=t.difficulty) for t in tasks]
    split = make_split(infos, {"A": 4, "V": 4, "H": 4}, seed=0, benchmark="toy-text")
    prices = _prices(input_usd_per_m=0, output_usd_per_m=0, compute_usd_per_hour=3600.0)

    _, records = evaluate(
        run_id="served",
        baseline=FixedStrategy(),
        strategy=strategy,
        model=model,
        env=ToyTextEnvironment(),
        tasks={t.task_id: t for t in tasks},
        split=split,
        split_name="A",
        out_path=tmp_path / "r.jsonl",
        budget=RunBudget(prices=prices),
    )
    assert len(records) == 4 and all(r.success and r.model == "qwen3-coder:30b" for r in records)
    for record in records:
        assert record.cost is not None
        assert record.cost["input_tokens"] == 100 * record.cost["calls"]
        assert 0 < record.cost["model_s"] <= record.cost["wall_s"]
        assert record.dollars == pytest.approx(record.cost["model_s"])  # $3600/h is $1 per second
    assert model.usage.calls == sum(r.cost["calls"] for r in records if r.cost)
    assert len(stub.requests) == model.usage.calls
