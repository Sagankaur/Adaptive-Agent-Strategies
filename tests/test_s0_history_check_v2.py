"""Offline tests for the amended S0 history check (v2). No network, no model, no GPU."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from strategy_schema.defaults import s0

_RUNNER = Path(__file__).resolve().parents[1] / "docs" / "cluster" / "aider-pilot" / "05_s0_history_check_v2.py"
_spec = importlib.util.spec_from_file_location("_aas_s0_history_check_v2_under_test", _RUNNER)
assert _spec is not None and _spec.loader is not None
v2 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = v2
_spec.loader.exec_module(v2)


# ---------------------------------------------------------------- stubs
def _terminal(n: int) -> SimpleNamespace:
    return SimpleNamespace(id=f"c{n}", name="terminal", arguments=json.dumps({"command": "describe harmless step"}))


def _submit() -> SimpleNamespace:
    return SimpleNamespace(id="cs", name="submit", arguments=json.dumps({"answer": "done"}))


def _reply(calls: tuple[Any, ...], *, finish: str = "tool_calls", reasoning_tokens: int | None = 7,
           out: int = 20) -> SimpleNamespace:
    return SimpleNamespace(
        content=None, reasoning="r", tool_calls=calls, input_tokens=10, cached_tokens=0, output_tokens=out,
        timings=SimpleNamespace(prompt_ms=1.0, generated_ms=2.0), elapsed_s=0.01, seed=1,
        finish_reason=finish, reasoning_tokens=reasoning_tokens,
    )


class StubModel:
    """Replaces the HTTP client: scripted replies, same call surface."""

    def __init__(self, real: Any, script: list[Any], endless: Any = None) -> None:
        self.seed = real.seed
        self._request_count = 0
        self.timeout_s = 180.0
        self.script = list(script)
        self.endless = endless

    async def complete(self, messages: Any, *, seed: int | None = None, tools: Any = None,
                       max_output_tokens: int | None = None) -> Any:
        self._request_count += 1
        if self.script:
            return self.script.pop(0)
        if self.endless is not None:
            return _reply((self.endless,))
        raise RuntimeError("script exhausted")


class StubMonitor:
    def assert_safe(self) -> None:
        return None


def _count_tokens(base: str, model: Any, messages: Any, seed: int, cap: int) -> int:
    return 120 + sum(len(str(m.get("content") or "")) for m in messages) // 4


def _run(tmp_path: Path, condition: str, pair: int, script: list[Any], *, endless: Any = None, **kwargs: Any) -> dict:
    strategy_path = tmp_path / "s0.json"
    strategy_path.write_text(s0().to_json(), encoding="utf-8")
    log_root = tmp_path / f"logs-{condition}-{pair}"
    log_root.mkdir()
    return asyncio.run(v2.run_conversation(
        base="http://offline.invalid", condition=condition, repetition=pair, monitor=StubMonitor(),
        strategy_path=strategy_path, log_root=log_root, token_counter=_count_tokens,
        model_hook=lambda real: StubModel(real, script, endless), **kwargs,
    ))


# ---------------------------------------------------------------- category order / recovery
def test_category_order_finish_reason_and_recovery_are_recorded(tmp_path: Path) -> None:
    script = [
        _reply((), finish="stop", reasoning_tokens=3),
        _reply((_terminal(1),), finish="tool_calls", reasoning_tokens=5),
        _reply((), finish="length", reasoning_tokens=None, out=1024),
        _reply((_submit(),), finish="tool_calls"),
    ]
    row = _run(tmp_path, "short", 0, script)
    assert row["category_order"] == ["no_tool_call", "valid_schema_A", "no_tool_call", "valid_schema_B"]
    assert row["finish_reason_order"] == ["stop", "tool_calls", "length", "tool_calls"]
    assert row["reasoning_tokens_order"] == [3, 5, None, 7]
    assert row["completion_tokens_order"][2] == 1024
    assert row["requests"][2]["output_cap_reached"] is True
    assert row["requests"][2]["reasoning_tokens_source"] == "unavailable"
    assert row["recovery"]["no_tool_call_events"] == 2
    assert row["recovery"]["recovered"] == 2
    assert row["recovery"]["event_order"] == ["recovered", "recovered"]
    assert row["submitted"] is True
    assert row["stop_reason"] == "agent_returned"


def test_recovery_summary_distinguishes_all_three_outcomes() -> None:
    result = v2.recovery_summary(["no_tool_call", "no_tool_call", "invalid_json", "no_tool_call"])
    assert result["event_order"] == ["not_recovered", "not_recovered", "no_next_request"]
    assert result["recovered"] == 0 and result["not_recovered"] == 2 and result["no_next_request"] == 1


def test_no_raw_content_and_no_step_log_in_aggregate(tmp_path: Path) -> None:
    row = _run(tmp_path, "long", 0, [_reply((_terminal(1),)), _reply((_submit(),))])
    assert row["agent_step_log_created"] is False
    assert row["log_dir_new_log_files"] == 0 and row["raw_content_written"] is False
    assert v2.aggregate_only_violations(row) == []
    assert row["mock_exec_calls"] == 3  # two S0 probes + one discarded terminal command
    assert row["s0_probes_intercepted_before_first_inference"] is True
    assert row["s0_max_observation_chars"] == 4000


# ---------------------------------------------------------------- growth / pairing
def test_long_condition_grows_prompt_tokens_more_and_pair_is_identical_at_request_one(tmp_path: Path) -> None:
    def script() -> list[Any]:
        return [_reply((_terminal(i),)) for i in range(4)] + [_reply((_submit(),))]

    short = _run(tmp_path, "short", 0, script())
    long_ = _run(tmp_path, "long", 0, script())
    assert short["effective_seed"] == long_["effective_seed"]
    assert short["prompt_tokens_order"][0] == long_["prompt_tokens_order"][0]  # identical first request
    assert long_["prompt_tokens_order"][-1] > short["prompt_tokens_order"][-1] + 2000
    assert min(long_["terminal_turn_growth_deltas"]) > max(short["terminal_turn_growth_deltas"])
    assert all(c < 4000 for c in long_["terminal_output_chars"])  # never reaches S0 truncation
    assert len(set(long_["terminal_output_hash12"])) == len(long_["terminal_output_hash12"])  # differs per call
    # different pairs get different seeds
    assert _run(tmp_path, "short", 1, script())["effective_seed"] != short["effective_seed"]


def test_synthetic_outputs_are_distinct_inert_and_untruncated() -> None:
    info = v2.validate_synthetic_outputs()
    assert info["long"]["min_chars"] > info["short"]["max_chars"] * 10
    assert info["long"]["max_chars"] <= 3600 < v2.S0_MAX_OBSERVATION_CHARS
    assert v2.synthetic_terminal_output("long", 1) != v2.synthetic_terminal_output("long", 2)
    assert v2.synthetic_terminal_output("long", 3) == v2.synthetic_terminal_output("long", 3)  # fixed strings


# ---------------------------------------------------------------- guards
def test_request_ceiling_and_context_guard_stop_conversations(tmp_path: Path) -> None:
    ceiling = _run(tmp_path, "short", 0, [], endless=_terminal(0), request_ceiling=3)
    assert ceiling["stop_reason"] == "request_ceiling" and ceiling["request_count"] == 3
    guarded = _run(tmp_path, "long", 0, [], endless=_terminal(0), context_limit=3000)
    assert guarded["stop_reason"] == "context_guard"
    assert guarded["context_guard"]["context_limit"] == 3000
    assert guarded["context_guard"]["input_tokens"] + 1024 + 1024 >= 3000
    assert v2.CONTEXT_LIMIT == 32768 and v2.REQUEST_CEILING == 12


# ---------------------------------------------------------------- validity gate
def _fake_run(condition: str, pair: int, prompts: list[int], *, seed: int | None = None) -> dict[str, Any]:
    requests = [
        {"prompt_tokens_preflight": p, "response_category": "valid_schema_A"} for p in prompts[:-1]
    ] + [{"prompt_tokens_preflight": prompts[-1], "response_category": "valid_schema_B"}]
    return {
        "condition": condition, "pair": pair, "effective_seed": seed if seed is not None else 1000 + pair,
        "requests": requests, "request_count": len(requests), "stop_reason": "agent_returned",
        "agent_step_log_created": False, "log_dir_new_log_files": 0, "raw_content_written": False,
        "workdir_probe_calls": 1, "readme_probe_calls": 1, "mock_terminal_calls": len(requests) - 1,
        "mock_exec_calls": len(requests) + 1, "s0_probes_intercepted_before_first_inference": True,
        "terminal_output_chars": [90] * (len(requests) - 1),
    }


def _good_runs(long_step: int = 1500, short_step: int = 40) -> list[dict[str, Any]]:
    runs = []
    for pair in range(1, 5):
        order = ("short", "long") if pair % 2 == 1 else ("long", "short")
        for condition in order:
            step = short_step if condition == "short" else long_step
            runs.append(_fake_run(condition, pair, [1400 + step * i for i in range(4)]))
    return runs


def test_gate_valid_when_long_grows_materially_more() -> None:
    gate = v2.evaluate_validity(_good_runs())
    assert gate["verdict"] == "VALID", gate
    assert gate["growth"]["status"] == "long_grows_materially_more"
    assert gate["pairs_short_first"] == 2


@pytest.mark.parametrize("kwargs, reason", [
    ({"unexpected_process_spawns": 1}, "process_spawned_outside_gpu_monitor"),
    ({"new_harbor_modules": ["harbor.trial.trial"]}, "harbor_runtime_modules_loaded_during_run"),
    ({"output_violations": ["/runs[0]/x:long_string"]}, "raw_content_or_unbounded_string_in_output"),
])
def test_gate_invalid_on_executor_or_raw_content_signals(kwargs: dict[str, Any], reason: str) -> None:
    gate = v2.evaluate_validity(_good_runs(), **kwargs)
    assert gate["verdict"] == "INVALID" and reason in gate["invalid_reasons"]


def test_gate_invalid_when_growth_not_materially_different() -> None:
    gate = v2.evaluate_validity(_good_runs(long_step=150, short_step=40))
    assert gate["verdict"] == "INVALID"
    assert "growth_not_materially_different" in gate["invalid_reasons"]
    assert gate["growth"]["status"] == "growth_not_materially_different"


def test_gate_invalid_when_too_few_terminal_turns_to_assess_growth() -> None:
    runs = _good_runs()
    for run in runs:  # every conversation submits at request 2: one delta each, 4 per condition < 8 needed
        run["requests"] = run["requests"][:2]
    gate = v2.evaluate_validity(runs)  # default needs 8 deltas per condition
    assert gate["verdict"] == "INVALID"
    assert "growth_not_assessable_insufficient_terminal_turns" in gate["invalid_reasons"]


def test_gate_invalid_on_step_log_raw_content_nonmock_exec_seed_and_order() -> None:
    runs = _good_runs()
    runs[0]["agent_step_log_created"] = True
    runs[1]["raw_content_written"] = True
    runs[2]["mock_exec_calls"] += 1
    runs[3]["effective_seed"] = 5
    reasons = " ".join(v2.evaluate_validity(runs)["invalid_reasons"])
    for needle in ("step_log_or_log_file_created", "raw_content_written", "exec_calls_not_all_mock", "pair_seed_differs"):
        assert needle in reasons
    pooled = _good_runs()
    # every pair executed short-first: order is not balanced 2/2
    unbalanced = [r for p in range(1, 5) for r in sorted(
        (x for x in pooled if x["pair"] == p), key=lambda x: x["condition"] != "short")]
    assert "order_not_balanced" in v2.evaluate_validity(unbalanced)["invalid_reasons"]


def test_gate_invalid_when_first_request_prompts_differ_and_incomplete_is_separate() -> None:
    runs = _good_runs()
    runs[0]["requests"][0]["prompt_tokens_preflight"] += 5
    assert "first_request_prompt_differs:1" in v2.evaluate_validity(runs)["invalid_reasons"]
    partial = v2.evaluate_validity(_good_runs()[:6])
    assert partial["verdict"] == "INCOMPLETE" and "fewer_conversations_than_planned" in partial["incomplete_reasons"]


# ---------------------------------------------------------------- aggregate-only machinery
def test_aggregate_only_violation_detection() -> None:
    assert v2.aggregate_only_violations({"a": "x" * 65}) == ["/a:long_string"]
    assert v2.aggregate_only_violations({"command": "ls"}) == ["/command:forbidden_key"]
    assert v2.aggregate_only_violations({"reasoning_tokens": 3, "h": "a" * 64}) == []


def test_extract_raw_meta_returns_counts_only_and_hooks_real_parser() -> None:
    from llm.async_openai_compatible import AsyncOpenAICompatibleModel

    body = json.dumps({
        "choices": [{"finish_reason": "length", "message": {
            "content": "SECRET-COMPLETION", "reasoning_content": "SECRET-REASONING", "tool_calls": []}}],
        "usage": {"prompt_tokens": 50, "completion_tokens": 40,
                  "completion_tokens_details": {"reasoning_tokens": 33}},
    }).encode()
    meta = v2.extract_raw_meta(body)
    assert meta == {"finish_reason": "length", "reasoning_tokens": 33, "reasoning_chars": 16, "content_chars": 17}
    assert "SECRET" not in json.dumps(meta)
    model = AsyncOpenAICompatibleModel(base_url="http://offline.invalid/v1", model="m")
    box: dict[str, Any] = {}
    v2.install_meta_capture(model, box)
    parsed = model._parse(body)  # real parser, offline
    assert parsed["output_tokens"] == 40 and box["last"]["finish_reason"] == "length"
    assert v2.extract_raw_meta(b"not json") == {}
    odd = json.dumps({"choices": [{"finish_reason": "weird<script>", "message": {}}], "usage": {}}).encode()
    assert v2.extract_raw_meta(odd)["finish_reason"] == "other"


def test_process_spawn_audit_counts_non_gpu_monitor_launches_without_running_anything() -> None:
    import subprocess

    with v2.ProcessSpawnAudit() as audit:
        for name in ("aas-nonexistent-binary-1", "aas-nonexistent-binary-2", "nvidia-smi-not-installed-x"):
            with pytest.raises(OSError):
                subprocess.run([name], check=False)
    assert audit.unexpected == 3
    assert subprocess.Popen.__name__ == "Popen"  # restored


# ---------------------------------------------------------------- review amendments
def test_v2_instruction_requires_four_terminal_calls_and_s0_is_unmodified() -> None:
    assert "exactly four terminal calls" in v2.V2_INSTRUCTION
    assert v2.V2_INSTRUCTION != v2.V1_INSTRUCTION and v2.S0_INSTRUCTION == v2.V2_INSTRUCTION
    assert v2.GROWTH_MIN_TERMINAL_DELTAS == 8
    assert s0().tool_policy.max_observation_chars == 4000


def test_growth_reasons_are_not_reported_when_run_is_incomplete_or_errored() -> None:
    partial = v2.evaluate_validity(_good_runs(long_step=10, short_step=10)[:3])
    assert partial["verdict"] == "INCOMPLETE"
    assert partial["growth"]["status"] == "not_assessed_run_incomplete"
    assert not any("growth" in r for r in partial["invalid_reasons"])
    runs = _good_runs(long_step=10, short_step=10)
    runs[4]["stop_reason"] = "error:HarborAgentProtocolError"
    gate = v2.evaluate_validity(runs)
    assert gate["verdict"] == "INCOMPLETE"
    assert any(r.startswith("conversation_error") for r in gate["incomplete_reasons"])
    assert gate["invalid_reasons"] == []
    # a safety problem still wins over incompleteness
    runs[0]["raw_content_written"] = True
    assert v2.evaluate_validity(runs)["verdict"] == "INVALID"


def test_provider_error_is_recorded_as_class_only_and_safety_error_propagates(tmp_path: Path) -> None:
    row = _run(tmp_path, "short", 0, [])  # script exhausted -> RuntimeError inside the loop
    assert row["stop_reason"] == "error:RuntimeError"
    assert v2.aggregate_only_violations(row) == []

    class Boom(StubMonitor):
        def assert_safe(self) -> None:
            raise v2.SafeDiagnosticError("vram_headroom_below_1gib")

    strategy_path = tmp_path / "s0.json"
    strategy_path.write_text(s0().to_json(), encoding="utf-8")
    log_root = tmp_path / "boom"
    log_root.mkdir()
    with pytest.raises(v2.SafeDiagnosticError):
        asyncio.run(v2.run_conversation(
            base="http://offline.invalid", condition="short", repetition=0, monitor=Boom(),
            strategy_path=strategy_path, log_root=log_root, token_counter=_count_tokens,
            model_hook=lambda real: StubModel(real, []),
        ))


def test_step_log_detection_ignores_preexisting_entries_and_flags_new_step_logs(tmp_path: Path) -> None:
    before = {"aas_steps.jsonl", "config.json"}  # e.g. created by a base-class constructor
    assert v2.new_step_log_like_files(before, set(before)) == []
    assert v2.new_step_log_like_files(before, before | {"trial.lock", "agent.log"}) == []
    assert v2.new_step_log_like_files(before, before | {"other.jsonl"}) == ["other.jsonl"]

    class Writer(StubModel):
        async def complete(self, messages: Any, **kwargs: Any) -> Any:
            (tmp_path / "logs-short-0" / "agent-logs-short-01" / "aas_steps.jsonl").write_text("x", encoding="utf-8")
            return await super().complete(messages, **kwargs)

    strategy_path = tmp_path / "s0.json"
    strategy_path.write_text(s0().to_json(), encoding="utf-8")
    log_root = tmp_path / "logs-short-0"
    log_root.mkdir()
    row = asyncio.run(v2.run_conversation(
        base="http://offline.invalid", condition="short", repetition=0, monitor=StubMonitor(),
        strategy_path=strategy_path, log_root=log_root, token_counter=_count_tokens,
        model_hook=lambda real: Writer(real, [_reply((_submit(),))]),
    ))
    assert row["agent_step_log_created"] is True and row["log_dir_new_log_files"] == 1
    assert row["raw_content_written"] is True
    gate = v2.evaluate_validity([row])
    assert gate["verdict"] == "INVALID" and any(r.startswith("step_log_or_log_file") for r in gate["invalid_reasons"])
