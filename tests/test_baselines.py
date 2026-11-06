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


class CountingToyTextEnvironment(ToyTextEnvironment):
    def __init__(self) -> None:
        super().__init__()
        self.reset_calls = 0

    def reset(self, task: Task) -> None:
        self.reset_calls += 1
        super().reset(task)


class FixedUsageModel:
    def __init__(self, replies: list[tuple[str, int]]) -> None:
        self.name = "fixed-usage"
        self.replies = iter(replies)
        self.limits: list[int | None] = []
        self.calls = []

    def complete(self, messages, *, seed=None, max_output_tokens=None):
        from llm import ChatResponse

        self.calls.append(list(messages))
        self.limits.append(max_output_tokens)
        text, output_tokens = next(self.replies)
        return ChatResponse(text, input_tokens=100, output_tokens=output_tokens, seed=seed)


class CountingExecuteEnvironment(CountingToyTextEnvironment):
    def __init__(self) -> None:
        super().__init__()
        self.execute_calls = 0

    def execute(self, action: Action) -> Observation:
        self.execute_calls += 1
        return super().execute(action)


def _sort_task(tasks: list[Task]) -> Task:
    task = next(t for t in tasks if t.payload["operation"] == "sort_words")
    assert task.payload["input"] != correct_answer(task)
    return task


def _no_checks_strategy(strategy: Strategy) -> Strategy:
    return strategy.model_copy(
        update={
            "exploration": strategy.exploration.model_copy(update={"probes": []}),
            "verification": strategy.verification.model_copy(update={"checks": [], "verification_required": False}),
        }
    )


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


def test_episode_token_limit_counts_generated_not_prompt_tokens(tasks: list[Task], strategy: Strategy) -> None:
    task = tasks[0].model_copy(update={"instruction": "Find the answer. " + "context " * 1000})
    no_probes = edited(strategy, ("replace", "/exploration/probes", []))
    no_checks = edited(
        no_probes,
        ("replace", "/verification/checks", []),
        ("replace", "/verification/verification_required", False),
    )
    tight = with_budget(no_checks, max_tokens=24)
    model = MockModel(["ACTION: file_view README", f"SUBMIT: {correct_answer(task)}"])

    attempt = run_episode(task, ToyTextEnvironment(), model, tight)

    assert attempt.success
    assert attempt.cost.input_tokens > tight.budget.max_tokens
    assert attempt.cost.output_tokens < tight.budget.max_tokens


def test_b1_shares_generated_token_budget_across_agent_judge_and_reflection(
    tasks: list[Task], strategy: Strategy
) -> None:
    task = tasks[0]
    no_checks = edited(
        _no_checks_strategy(strategy),
        ("replace", "/exploration/probes", []),
    )
    tight = with_budget(no_checks, max_tokens=14)
    model = FixedUsageModel(
        [
            (f"SUBMIT: {wrong_answer(task)}", 4),
            ('{"score": 0.1, "reason": "fail"}', 6),
            ("Try one clearer answer.", 4),
        ]
    )
    env = CountingToyTextEnvironment()

    outcome = ReflectionRetry(k=3).run(task, env, model, tight)

    assert len(outcome.attempts) == 1
    assert outcome.budget_stop_reason == "generated_token_limit"
    assert outcome.budget_overrun_tokens == 0
    assert model.limits == [14, 10, 4]
    assert outcome.attempts[0].cost.output_tokens == 4
    assert outcome.extra_cost.output_tokens == 10
    assert outcome.cost.output_tokens == 14
    assert env.reset_calls == 1


def test_b1_budget_exhausted_by_attempt_skips_judge_and_retry(tasks: list[Task], strategy: Strategy) -> None:
    task = tasks[0]
    no_checks = edited(
        _no_checks_strategy(strategy),
        ("replace", "/exploration/probes", []),
    )
    tight = with_budget(no_checks, max_tokens=4)
    model = FixedUsageModel([(f"SUBMIT: {wrong_answer(task)}", 4)])
    env = CountingToyTextEnvironment()

    outcome = ReflectionRetry(k=3).run(task, env, model, tight)

    assert len(outcome.attempts) == 1
    assert model.limits == [4]
    assert outcome.attempts[0].judgments == [
        {"status": "skipped", "reason": "generated_token_limit", "cost": {"calls": 0}}
    ]
    assert outcome.budget_stop_reason == "generated_token_limit"
    assert outcome.cost.output_tokens == 4
    assert env.reset_calls == 1


def test_b1_provider_overrun_is_charged_without_executing_action(tasks: list[Task], strategy: Strategy) -> None:
    task = tasks[0]
    no_checks = edited(
        _no_checks_strategy(strategy),
        ("replace", "/exploration/probes", []),
    )
    tight = with_budget(no_checks, max_tokens=1)
    model = FixedUsageModel([("ACTION: file_view input.txt", 2)])
    env = CountingExecuteEnvironment()

    outcome = ReflectionRetry(k=1).run(task, env, model, tight)

    assert outcome.budget_stop_reason == "provider_output_overrun"
    assert outcome.budget_overrun_tokens == 1
    assert outcome.attempts[0].cost.output_tokens == 2
    assert outcome.cost.output_tokens == 2
    assert outcome.attempts[0].steps == []
    assert env.execute_calls == 0
    assert env.reset_calls == 1


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
    no_checks = _no_checks_strategy(strategy)
    reflection = "I should follow the requested transformation exactly."
    env = CountingToyTextEnvironment()
    class SeededMockModel(MockModel):
        def complete(self, messages, *, seed=None, max_output_tokens=None):
            return super().complete(
                messages, seed=500 + len(self.calls) + 1, max_output_tokens=max_output_tokens
            )

    model = SeededMockModel(
        [
            f"SUBMIT: {wrong_answer(task)}",
            '{"score": 0.1, "reason": "the answer does not follow the instruction"}',
            reflection,
            f"SUBMIT: {correct_answer(task)}",
            '{"score": 0.9, "reason": "the answer follows the instruction"}',
        ]
    )
    outcome = ReflectionRetry(k=2).run(task, env, model, no_checks)
    assert len(outcome.attempts) == 2 and outcome.selected == 1 and outcome.success
    assert outcome.reflections == [reflection]
    assert reflection in model.calls[3][1].content
    assert "own checks say" not in model.calls[2][0].content.lower()
    assert outcome.attempts[0].own_check_passed is None
    assert outcome.attempts[0].judgments[0]["score"] == 0.1
    assert env.reset_calls == 1
    assert outcome.extra_cost.calls == 3
    assert outcome.extra_calls[0]["kind"] == "reflection"
    assert outcome.extra_calls[0]["seed"] == 503
    assert outcome.cost.calls == 5


def test_b2_judge_time_is_in_aggregate_wall_cost(tasks: list[Task], strategy: Strategy, monkeypatch) -> None:
    from baselines import baselines as baseline_module
    from baselines.judge import JudgeResult

    task = tasks[0]
    model = MockModel([f"SUBMIT: {correct_answer(task)}"])
    timed_result = JudgeResult(0.9, "pass", ChatResponse("", 1, 1, elapsed_s=0.25, seed=9))
    monkeypatch.setattr(baseline_module, "judge_attempt", lambda *_args: timed_result)

    outcome = BestOfN(n=1).run(task, ToyTextEnvironment(), model, strategy)

    assert outcome.extra_cost.wall_s == pytest.approx(0.25)


def test_b1_retry_trigger_is_own_checks_not_hidden_tests(tasks: list[Task], strategy: Strategy) -> None:
    task = _sort_task(tasks)
    no_fix_cycles = edited(strategy, ("replace", "/verification/max_verify_cycles", 0))
    model = MockModel(
        [
            "ACTION: file_view input.txt",
            f"SUBMIT: {task.payload['input']}",
            '{"score": 0.9, "reason": "the visible checks pass"}',
        ]
    )
    outcome = ReflectionRetry(k=1).run(task, ToyTextEnvironment(), model, no_fix_cycles)
    assert len(outcome.attempts) == 1
    assert outcome.attempts[0].own_check_passed and not outcome.success
    assert outcome.extra_cost.calls == 1


def test_b1_retries_on_failed_agent_check_even_when_judge_passes(
    tasks: list[Task], strategy: Strategy
) -> None:
    task = _sort_task(tasks)
    no_fix_cycles = edited(strategy, ("replace", "/verification/max_verify_cycles", 0))
    model = MockModel(
        [
            "ACTION: file_view input.txt",
            "SUBMIT: a completely unrelated answer",
            '{"score": 0.9, "reason": "the trajectory looks plausible"}',
            "The visible check failed, so compare every input word before submitting.",
            "ACTION: file_view input.txt",
            f"SUBMIT: {correct_answer(task)}",
            '{"score": 0.9, "reason": "the answer follows the task"}',
        ]
    )
    outcome = ReflectionRetry(k=2).run(task, ToyTextEnvironment(), model, no_fix_cycles)

    assert len(outcome.attempts) == 2
    assert outcome.attempts[0].own_check_passed is False
    assert outcome.attempts[0].judgments[0]["passed"] is True
    assert outcome.success


def test_b2_selects_by_own_checks(tasks: list[Task], strategy: Strategy) -> None:
    task = tasks[0]
    no_checks = _no_checks_strategy(strategy)
    model = MockModel(
        [
            f"SUBMIT: {wrong_answer(task)}",
            f"SUBMIT: {correct_answer(task)}",
            '{"score": 0.2, "reason": "the answer misses the requested operation"}',
            '{"score": 0.9, "reason": "the answer follows the instruction"}',
        ]
    )
    outcome = BestOfN(n=2, seed=31).run(task, ToyTextEnvironment(), model, no_checks)
    assert len(outcome.attempts) == 2 and outcome.selected == 1 and outcome.success
    assert outcome.cost.calls == 4
    assert outcome.extra_cost.calls == 2


def test_b2_reports_oracle_separately_from_selected_result(tasks: list[Task], strategy: Strategy) -> None:
    task = _sort_task(tasks)
    no_checks = _no_checks_strategy(strategy)
    script = [
        f"SUBMIT: {task.payload['input']}",
        f"SUBMIT: {correct_answer(task)}",
        '{"score": 0.9, "reason": "the answer is plausible"}',
        '{"score": 0.2, "reason": "the answer appears incomplete"}',
    ]
    outcome = BestOfN(n=2).run(task, ToyTextEnvironment(), MockModel(script), no_checks)
    assert outcome.selected == 0 and not outcome.success and outcome.oracle_success
    assert outcome.cost.calls == 4


def test_s0_does_not_call_the_judge(tasks: list[Task], strategy: Strategy) -> None:
    task = tasks[0]
    no_probes = edited(strategy, ("replace", "/exploration/probes", []))
    model = MockModel([f"SUBMIT: {correct_answer(task)}"])
    outcome = FixedStrategy().run(task, ToyTextEnvironment(), model, no_probes)
    assert outcome.success
    assert len(model.calls) == 1


def test_cost_arithmetic_and_dollars() -> None:
    total = Cost(calls=1, input_tokens=1_000_000, wall_s=1.0) + Cost(calls=2, output_tokens=500_000, wall_s=0.5)
    assert (total.calls, total.tokens, total.wall_s) == (3, 1_500_000, 1.5)
    prices = PriceTable(model="m", input_usd_per_m=0.25, output_usd_per_m=2.0, source="test", seen_on="2026-10-02")
    assert total.dollars(prices) == pytest.approx(0.25 + 1.0)
