from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from environments import harbor_agent
from environments.harbor_agent import HarborStrategyAgent
from evaluation.harbor_job import configure_harbor_job
from evaluation.harbor_results import (
    HarborResultError,
    append_completed_trial,
    reward_from_trial_result,
)
from strategy_schema import s0


def _response(call_id: str, name: str, arguments: dict[str, Any], seed: int) -> SimpleNamespace:
    return SimpleNamespace(
        content=None,
        reasoning="Follow the task instruction.",
        tool_calls=(SimpleNamespace(id=call_id, name=name, arguments=json.dumps(arguments)),),
        input_tokens=12,
        cached_tokens=3,
        output_tokens=4,
        timings=SimpleNamespace(prompt_tokens=12, cached_tokens=3, generated_tokens=4, prompt_ms=2.0, generated_ms=1.0),
        elapsed_s=0.1,
        seed=seed,
    )


class _ScriptedModel:
    def __init__(self, responses: list[SimpleNamespace]):
        self.responses = responses
        self.requests: list[list[dict[str, Any]]] = []
        self.tools: list[dict[str, Any]] | None = None
        self.timeout_s = 30.0
        self.output_limits: list[int | None] = []

    async def complete(
        self, messages: list[dict[str, Any]], *, tools: list[dict[str, Any]], max_output_tokens: int | None = None
    ):
        self.requests.append([dict(message) for message in messages])
        self.tools = tools
        self.output_limits.append(max_output_tokens)
        return self.responses.pop(0)


class _ToyEnvironment:
    context_id = "harbor-trial-17"
    environment_name = "toy-file-task"

    def __init__(self):
        self.commands: list[tuple[str, int]] = []

    async def exec(self, command: str, *, timeout_sec: int):
        self.commands.append((command, timeout_sec))
        return SimpleNamespace(stdout="created output\n", stderr="", return_code=0)


def _strategy_file(path: Path) -> Path:
    strategy = s0()
    strategy = strategy.model_copy(
        update={
            "exploration": strategy.exploration.model_copy(update={"probes": [], "probe_budget_steps": 0}),
            "verification": strategy.verification.model_copy(update={"checks": []}),
            "budget": strategy.budget.model_copy(update={"max_steps": 8, "max_tokens": 1000, "max_wall_s": 90}),
        }
    )
    path.write_text(strategy.to_json(), encoding="utf-8")
    return path


def _configured_agent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, model: _ScriptedModel):
    strategy_path = _strategy_file(tmp_path / "strategy.json")
    agent = HarborStrategyAgent(logs_dir=tmp_path / "agent-logs", model_name="scripted")
    agent.extra_env = {
        "AAS_STRATEGY_PATH": str(strategy_path),
        "AAS_MODEL_BASE_URL": "http://127.0.0.1:8080/v1",
        "AAS_RUN_ID": "fixture-run",
        "AAS_PROVENANCE_TAG": "fixture",
        "AAS_SEED_ROOT": "1234",
    }
    monkeypatch.setattr(harbor_agent, "AsyncOpenAICompatibleModel", lambda **kwargs: model)
    return agent


def test_agent_executes_terminal_then_submits_with_tool_result_and_telemetry(tmp_path, monkeypatch):
    model = _ScriptedModel(
        [
            _response("call-terminal", "terminal", {"command": "printf smoke"}, 501),
            _response("call-submit", "submit", {"answer": "done"}, 502),
        ]
    )
    agent = _configured_agent(tmp_path, monkeypatch, model)
    environment = _ToyEnvironment()
    context = SimpleNamespace(n_input_tokens=0, n_cache_tokens=0, n_output_tokens=0, metadata={})

    async def run_agent():
        await agent.setup(environment)
        await agent.run("Create the requested output.", environment, context)

    asyncio.run(run_agent())

    assert len(environment.commands) == 1
    assert model.output_limits == [1000, 996]
    assert environment.commands[0][0] == "printf smoke"
    assert 1 <= environment.commands[0][1] <= 90
    assert model.requests[1][-1] == {
        "role": "tool",
        "tool_call_id": "call-terminal",
        "content": "exit=0\ncreated output\n",
    }
    assert {tool["function"]["name"] for tool in model.tools or []} == {"terminal", "submit"}
    assert (context.n_input_tokens, context.n_cache_tokens, context.n_output_tokens) == (24, 6, 8)
    assert context.metadata["harbor_trial_id"] == "harbor-trial-17"
    assert context.metadata["provenance_tag"] == "fixture"

    rows = [json.loads(line) for line in (tmp_path / "agent-logs" / "aas_steps.jsonl").read_text().splitlines()]
    assert [row["action"] for row in rows] == ["terminal", "submit"]
    assert all(row["harbor_trial_id"] == "harbor-trial-17" for row in rows)
    assert rows[0]["seed"] == 501
    assert rows[0]["strategy_hash"] == context.metadata["strategy_hash"]
    assert rows[0]["input_tokens"] == 12
    assert rows[0]["timings"]["prompt_ms"] == 2.0


def test_agent_refuses_hidden_test_paths_without_executing_them(tmp_path, monkeypatch):
    model = _ScriptedModel(
        [
            _response("call-hidden", "terminal", {"command": "cat /tests/test.sh"}, 601),
            _response("call-submit", "submit", {"answer": "done"}, 602),
        ]
    )
    agent = _configured_agent(tmp_path, monkeypatch, model)
    environment = _ToyEnvironment()
    context = SimpleNamespace(n_input_tokens=0, n_cache_tokens=0, n_output_tokens=0, metadata={})

    async def run_agent():
        await agent.setup(environment)
        await agent.run("Inspect the task.", environment, context)

    asyncio.run(run_agent())

    assert environment.commands == []
    rows = [json.loads(line) for line in (tmp_path / "agent-logs" / "aas_steps.jsonl").read_text().splitlines()]
    assert rows[0]["exit_code"] == 126
    assert "refused" in rows[0]["observation"].lower()


def test_reward_reader_uses_harbor_verifier_result():
    result = {
        "id": "trial-42",
        "task_name": "toy-task",
        "verifier_result": {"rewards": {"reward": 0.5}},
    }

    reward = reward_from_trial_result(result)

    assert (reward.trial_id, reward.task_id, reward.reward, reward.success) == ("trial-42", "toy-task", 0.5, False)


@pytest.mark.parametrize(
    "result",
    [
        {"id": "trial-42", "task_name": "toy-task", "verifier_result": None},
        {"id": "trial-42", "task_name": "toy-task", "verifier_result": {"rewards": {}}},
        {"id": "trial-42", "task_name": "toy-task", "verifier_result": {"rewards": {"reward": True}}},
        {"id": "trial-42", "task_name": "toy-task", "verifier_result": {"rewards": {"reward": float("nan")}}},
        {"id": "trial-42", "task_name": "toy-task", "verifier_result": {"rewards": {"reward": 1.1}}},
    ],
)
def test_reward_reader_rejects_missing_or_invalid_harbor_reward(result):
    with pytest.raises(HarborResultError):
        reward_from_trial_result(result)


def test_episode_record_deduplicates_repeated_tool_rows_for_one_request_seed(tmp_path):
    trial_result = {
        "id": "trial-42",
        "task_name": "toy-task",
        "verifier_result": {"rewards": {"reward": 1.0}},
    }
    step_log = tmp_path / "steps.jsonl"
    output = tmp_path / "episodes.jsonl"
    rows = [
        {"harbor_trial_id": "trial-42", "seed": 700, "input_tokens": 10, "cached_tokens": 2, "output_tokens": 3},
        {"harbor_trial_id": "trial-42", "seed": 700, "input_tokens": 10, "cached_tokens": 2, "output_tokens": 3},
        {"harbor_trial_id": "trial-42", "seed": 701, "input_tokens": 8, "cached_tokens": 1, "output_tokens": 4},
    ]
    step_log.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    record = append_completed_trial(trial_result, step_log_path=step_log, output_path=output)

    assert (record["reward"], record["success"], record["step_count"]) == (1.0, True, 3)
    assert (record["input_tokens"], record["cached_tokens"], record["output_tokens"]) == (18, 3, 7)
    assert json.loads(output.read_text(encoding="utf-8"))["harbor_trial_id"] == "trial-42"


def test_episode_record_rejects_conflicting_usage_for_reused_request_seed(tmp_path):
    trial_result = {
        "id": "trial-42",
        "task_name": "toy-task",
        "verifier_result": {"rewards": {"reward": 1.0}},
    }
    step_log = tmp_path / "steps.jsonl"
    output = tmp_path / "episodes.jsonl"
    rows = [
        {"harbor_trial_id": "trial-42", "seed": 700, "input_tokens": 10, "cached_tokens": 2, "output_tokens": 3},
        {"harbor_trial_id": "trial-42", "seed": 700, "input_tokens": 11, "cached_tokens": 2, "output_tokens": 3},
    ]
    step_log.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    with pytest.raises(HarborResultError, match="conflicting token usage"):
        append_completed_trial(trial_result, step_log_path=step_log, output_path=output)

    assert not output.exists()


def test_harbor_job_config_sets_slot_concurrency_without_mutating_input():
    original = {"n_concurrent_trials": 8, "agent_timeout_multiplier": 1.0, "tasks": [{"name": "toy"}]}

    resolved = configure_harbor_job(original, llama_cpp_slots=3)

    assert resolved["n_concurrent_trials"] == 3
    assert resolved["agent_timeout_multiplier"] == 2.0
    assert resolved["tasks"] == [{"name": "toy"}]
    assert original["n_concurrent_trials"] == 8
    assert original["agent_timeout_multiplier"] == 1.0


@pytest.mark.parametrize("slots", [0, -1, True, 1.5])
def test_harbor_job_config_rejects_invalid_slot_counts(slots):
    with pytest.raises(ValueError, match="positive integer"):
        configure_harbor_job({}, llama_cpp_slots=slots)
