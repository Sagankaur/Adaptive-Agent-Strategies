"""One episode of a ReAct-style agent following a strategy: explore, act, verify, submit.

This loop is the stand-in for the plan's ``compile(strategy) -> AgentLoop``
(TECHNICAL_PLAN.md, section 3.3), which is Phase 1 work. It reads only these
strategy fields as controller behaviour:

- ``exploration.probes`` and ``probe_budget_steps``: probes run before the first model call;
- ``tool_policy.tools_allowed``, ``forbidden_patterns`` and ``max_observation_chars``;
- ``verification.verification_required``, ``checks`` and ``max_verify_cycles``;
- ``budget.max_steps``, ``max_tokens`` and ``max_wall_s``, applied per episode.

Every other field reaches the agent only through :meth:`Strategy.render`.
Making each field change the controller, with a test per field, is the
Phase 1 ``compile()`` work.

The model replies with ``ACTION: <tool> <argument>`` or ``SUBMIT: <answer>``.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Literal

from baselines.cost import Cost
from environments.base import Action, Environment, Observation, Task
from llm import ChatModel, Message
from strategy_schema.model import Strategy

ACTION_FORMAT = (
    "Reply with exactly one line of the form 'ACTION: <tool> <argument>' to use a tool, "
    "or 'SUBMIT: <answer>' when you are done."
)

_ACTION_RE = re.compile(r"^\s*ACTION:\s*(\S+)\s*(.*)$")
_SUBMIT_RE = re.compile(r"^\s*SUBMIT:\s*(.*)$")

StopReason = Literal["submitted", "step_limit", "token_limit", "time_limit"]
StepKind = Literal["probe", "action", "invalid", "verify", "submit"]


@dataclass(frozen=True)
class Step:
    """One row of the step table that trajectories are compressed into (section 5.1)."""

    index: int
    kind: StepKind
    tool: str
    argument: str
    observation: str
    exit_code: int
    elapsed_s: float


@dataclass
class Attempt:
    """One episode. ``success`` is the hidden-test verdict and is never shown to the agent."""

    task_id: str
    strategy_version: int
    steps: list[Step]
    answer: str | None
    stop_reason: StopReason
    own_check_passed: bool | None
    success: bool
    cost: Cost = field(default_factory=Cost)


def parse_reply(text: str) -> Action | None:
    for line in text.splitlines():
        if match := _SUBMIT_RE.match(line):
            return Action("submit", match.group(1).strip())
        if match := _ACTION_RE.match(line):
            return Action(match.group(1), match.group(2).strip())
    return None


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + f"\n[truncated {len(text) - limit} chars]"


def _own_checks(env: Environment, strategy: Strategy, answer: str) -> tuple[bool | None, str]:
    """Run the strategy's checks; None when none apply."""
    results = [env.own_check(answer, check) for check in strategy.verification.checks]
    applicable = [r for r in results if r.passed is not None]
    if not applicable:
        return None, "no applicable checks"
    passed = all(r.passed for r in applicable)
    return passed, "; ".join(f"{r.check}: {'pass' if r.passed else 'fail'} ({r.detail})" for r in applicable)


def run_episode(
    task: Task,
    env: Environment,
    model: ChatModel,
    strategy: Strategy,
    extra_context: list[str] | None = None,
) -> Attempt:
    """Run ``task`` once under ``strategy`` and return the trajectory, outcome and cost."""
    start = time.perf_counter()
    cost = Cost()
    steps: list[Step] = []
    tools, verification, budget = strategy.tool_policy, strategy.verification, strategy.budget

    def add_step(kind: StepKind, action: Action, obs: Observation) -> str:
        shown = _truncate(obs.text, tools.max_observation_chars)
        steps.append(
            Step(len(steps), kind, action.tool, action.argument, shown, obs.exit_code, time.perf_counter() - start)
        )
        return f"[{action.tool} {action.argument}] exit={obs.exit_code}\n{shown}"

    env.reset(task)
    user = task.instruction
    if extra_context:
        user += "\n\n" + "\n\n".join(extra_context)
    messages = [Message("system", strategy.render() + "\n\n" + ACTION_FORMAT), Message("user", user)]

    for probe in strategy.exploration.probes[: strategy.exploration.probe_budget_steps]:
        if len(steps) >= budget.max_steps:
            break
        messages.append(Message("user", add_step("probe", Action("probe", probe), env.probe(probe))))

    answer: str | None = None
    verify_cycles = 0
    stop: StopReason
    while True:
        if len(steps) >= budget.max_steps:
            stop = "step_limit"
            break
        if cost.tokens >= budget.max_tokens:
            stop = "token_limit"
            break
        if time.perf_counter() - start >= budget.max_wall_s:
            stop = "time_limit"
            break

        reply = model.complete(messages)
        cost.record(reply)
        messages.append(Message("assistant", reply.text))
        action = parse_reply(reply.text)

        if action is None:
            text = add_step("invalid", Action("none", ""), Observation("No action found. " + ACTION_FORMAT, 2))
        elif action.tool == "submit":
            if verification.verification_required and verification.checks:
                passed, detail = _own_checks(env, strategy, action.argument)
                if passed is False and verify_cycles < verification.max_verify_cycles:
                    verify_cycles += 1
                    text = add_step("verify", action, Observation("Checks failed: " + detail, 1))
                    messages.append(Message("user", text))
                    continue
                add_step("verify", action, Observation(detail, 0 if passed is not False else 1))
            add_step("submit", action, Observation("submitted", 0))
            answer = action.argument
            stop = "submitted"
            break
        elif action.tool not in tools.tools_allowed:
            text = add_step("action", action, Observation(f"tool {action.tool} is not allowed by the strategy", 126))
        elif any(p in action.argument for p in tools.forbidden_patterns):
            text = add_step("action", action, Observation("refused: command matches a forbidden pattern", 126))
        else:
            text = add_step("action", action, env.execute(action))
        messages.append(Message("user", text))

    own_check_passed: bool | None
    if answer is None:
        own_check_passed = False
    else:
        own_check_passed, _ = _own_checks(env, strategy, answer)
    success = answer is not None and env.grade(answer)
    cost.wall_s = time.perf_counter() - start
    return Attempt(task.task_id, strategy.version, steps, answer, stop, own_check_passed, success, cost)
