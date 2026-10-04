from __future__ import annotations

import pytest

from baselines import BestOfN, Cost, FixedStrategy, PriceTable, ReflectionRetry, parse_reply, run_episode
from environments import Action, Observation, Task, ToyTextEnvironment
from llm import ChatResponse, Message, MockModel, MockScriptExhausted, ProviderModel, approx_tokens
from strategy_schema import Strategy
from tests.helpers import correct_answer, edited, solver, with_budget, wrong_answer


class LongOutputEnvironment(ToyTextEnvironment):
    def execute(self, action: Action) -> Observation:
        return Observation("y" * 2000, 0)


def _sort_task(tasks: list[Task]) -> Task:
    task = next(t for t in tasks if t.payload["operation"] == "sort_words")
    assert task.payload["input"] != correct_answer(task)
    return task


def test_parse_reply() -> None:
    assert parse_reply("thinking...\nACTION: file_view input.txt") == Action("file_view", "input.txt")
    assert parse_reply("SUBMIT: a b c") == Action("submit", "a b c")
    assert parse_reply("no action here") is None


def test_mock_model_scripts_and_counts_tokens() -> None:
    model = MockModel(["hello"])
    reply = model.complete([Message("user", "x" * 40)])
    assert reply == ChatResponse("hello", input_tokens=10, output_tokens=approx_tokens("hello"))
    with pytest.raises(MockScriptExhausted):
        model.complete([Message("user", "again")])


def test_provider_stub_refuses_to_run() -> None:
    with pytest.raises(NotImplementedError):
        ProviderModel("gpt-5-mini").complete([Message("user", "hi")])


def test_episode_runs_probes_then_solves(tasks: list[Task], strategy: Strategy) -> None:
    task = tasks[0]
    model = MockModel(["ACTION: file_view input.txt", f"SUBMIT: {correct_answer(task)}"])
    attempt = run_episode(task, ToyTextEnvironment(), model, strategy)
    assert [s.kind for s in attempt.steps] == ["probe", "probe", "action", "verify", "submit"]
    assert attempt.success and attempt.own_check_passed and attempt.stop_reason == "submitted"
    assert attempt.cost.calls == 2
    assert attempt.cost.input_tokens == sum(sum(approx_tokens(m.content) for m in call) for call in model.calls)
    assert attempt.cost.wall_s > 0
    assert strategy.render() in model.calls[0][0].content


def test_no_probes_means_no_probe_steps(tasks: list[Task], strategy: Strategy) -> None:
    no_probes = edited(strategy, ("replace", "/exploration/probes", []))
    attempt = run_episode(tasks[0], ToyTextEnvironment(), MockModel(solver(sloppy_first=False)), no_probes)
    assert attempt.success and "probe" not in [s.kind for s in attempt.steps]


def test_disallowed_tool_and_forbidden_pattern_are_refused(tasks: list[Task], strategy: Strategy) -> None:
    unverified = edited(strategy, ("replace", "/verification/verification_required", False))
    model = MockModel(["ACTION: python print(1)", "ACTION: bash rm -rf / --no-preserve-root", "SUBMIT: x"])
    attempt = run_episode(tasks[0], ToyTextEnvironment(), model, unverified)
    assert [s.exit_code for s in attempt.steps if s.kind == "action"] == [126, 126]


def test_observations_are_truncated(tasks: list[Task], strategy: Strategy) -> None:
    short = edited(
        strategy,
        ("replace", "/tool_policy/max_observation_chars", 500),
        ("replace", "/verification/verification_required", False),
    )
    attempt = run_episode(tasks[0], LongOutputEnvironment(), MockModel(["ACTION: bash ls", "SUBMIT: x"]), short)
    action = next(s for s in attempt.steps if s.kind == "action")
    assert action.observation.startswith("y" * 500)
    assert action.observation.endswith("[truncated 1500 chars]")


def test_step_limit_stops_the_episode(tasks: list[Task], strategy: Strategy) -> None:
    tight = with_budget(edited(strategy, ("replace", "/exploration/probes", [])), max_steps=3)
    attempt = run_episode(tasks[0], ToyTextEnvironment(), MockModel(["ACTION: file_view README"] * 3), tight)
    assert attempt.stop_reason == "step_limit"
    assert not attempt.success and attempt.own_check_passed is False and attempt.answer is None


def test_verification_sends_the_agent_back_to_fix(tasks: list[Task], strategy: Strategy) -> None:
    attempt = run_episode(tasks[0], ToyTextEnvironment(), MockModel(solver(sloppy_first=True)), strategy)
    assert attempt.success
    assert [s.exit_code for s in attempt.steps if s.kind == "verify"] == [1, 0]

    unverified = edited(strategy, ("replace", "/verification/verification_required", False))
    attempt = run_episode(tasks[0], ToyTextEnvironment(), MockModel(solver(sloppy_first=True)), unverified)
    assert not attempt.success and "verify" not in [s.kind for s in attempt.steps]


def test_b0_runs_one_attempt(tasks: list[Task], strategy: Strategy) -> None:
    outcome = FixedStrategy().run(tasks[0], ToyTextEnvironment(), MockModel(solver(sloppy_first=False)), strategy)
    assert len(outcome.attempts) == 1 and outcome.success and outcome.cost.calls == 2


def test_b1_reflects_and_retries_when_own_checks_fail(tasks: list[Task], strategy: Strategy) -> None:
    task = tasks[0]
    no_fix_cycles = edited(strategy, ("replace", "/verification/max_verify_cycles", 0))
    reflection = "I dropped a word; copy all words next time."
    model = MockModel(
        [
            "ACTION: file_view input.txt",
            f"SUBMIT: {wrong_answer(task)}",
            reflection,
            "ACTION: file_view input.txt",
            f"SUBMIT: {correct_answer(task)}",
        ]
    )
    outcome = ReflectionRetry(k=3).run(task, ToyTextEnvironment(), model, no_fix_cycles)
    assert len(outcome.attempts) == 2 and outcome.selected == 1 and outcome.success
    assert outcome.reflections == [reflection]
    assert reflection in model.calls[3][1].content
    assert outcome.cost.calls == 5 and outcome.extra_cost.calls == 1


def test_b1_retry_trigger_is_own_checks_not_hidden_tests(tasks: list[Task], strategy: Strategy) -> None:
    task = _sort_task(tasks)
    model = MockModel(["ACTION: file_view input.txt", f"SUBMIT: {task.payload['input']}"])
    outcome = ReflectionRetry(k=3).run(task, ToyTextEnvironment(), model, strategy)
    assert len(outcome.attempts) == 1
    assert outcome.attempts[0].own_check_passed and not outcome.success


def test_b2_selects_by_own_checks(tasks: list[Task], strategy: Strategy) -> None:
    task = tasks[0]
    no_fix_cycles = edited(strategy, ("replace", "/verification/max_verify_cycles", 0))
    script = []
    for answer in (wrong_answer(task), correct_answer(task), wrong_answer(task)):
        script += ["ACTION: file_view input.txt", f"SUBMIT: {answer}"]
    outcome = BestOfN(n=3).run(task, ToyTextEnvironment(), MockModel(script), no_fix_cycles)
    assert len(outcome.attempts) == 3 and outcome.selected == 1 and outcome.success
    assert outcome.cost.calls == 6


def test_b2_reports_oracle_separately_from_selected_result(tasks: list[Task], strategy: Strategy) -> None:
    task = _sort_task(tasks)
    script = ["ACTION: file_view input.txt", f"SUBMIT: {task.payload['input']}"]
    script += ["ACTION: file_view input.txt", f"SUBMIT: {correct_answer(task)}"]
    outcome = BestOfN(n=2).run(task, ToyTextEnvironment(), MockModel(script), strategy)
    assert outcome.selected == 0 and not outcome.success and outcome.oracle_success


def test_cost_arithmetic_and_dollars() -> None:
    total = Cost(calls=1, input_tokens=1_000_000, wall_s=1.0) + Cost(calls=2, output_tokens=500_000, wall_s=0.5)
    assert (total.calls, total.tokens, total.wall_s) == (3, 1_500_000, 1.5)
    prices = PriceTable(model="m", input_usd_per_m=0.25, output_usd_per_m=2.0, source="test", seen_on="2026-10-02")
    assert total.dollars(prices) == pytest.approx(0.25 + 1.0)
