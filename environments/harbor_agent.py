"""Harbor v0.23 adapter for the project's typed strategy and async model client.

The agent sees only the task instruction and its execution environment. It never
receives the verifier result; reward is joined from Harbor's persisted trial
result by :mod:`evaluation.harbor_results` after Harbor completes grading.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

try:
    from harbor.agents.base import BaseAgent
except ImportError:  # Keep project modules importable without the optional Harbor package.
    class BaseAgent:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.logs_dir = Path(kwargs.get("logs_dir", "."))
            self.model_name = kwargs.get("model_name")
            self.context_id = None
            self.extra_env = {}

        @staticmethod
        def name() -> str:
            return "adaptive-agent-strategies"

        def version(self) -> str:
            return "0.1.0"

from llm.async_openai_compatible import AsyncChatResponse, AsyncOpenAICompatibleModel
from strategy_schema.model import Check, Probe, Strategy

_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "terminal",
            "description": "Run one shell command in the task environment.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit",
            "description": "Finish the task when the requested work is complete.",
            "parameters": {
                "type": "object",
                "properties": {"answer": {"type": "string"}},
                "required": ["answer"],
                "additionalProperties": False,
            },
        },
    },
]
_HIDDEN_PATH_MARKERS = ("tests/", "tests\\", "solution/", "solution\\", "/logs/verifier", "reward.txt")
_PATH_TOKEN = re.compile(r"(?:^|[\s./])(?:tests|solution)(?:$|[\s/\\.])", re.IGNORECASE)


class HarborAgentConfigurationError(ValueError):
    """The Harbor agent is missing a required, non-secret configuration value."""


class HarborAgentProtocolError(RuntimeError):
    """The model produced an unusable tool call or no action."""


def _json_object(arguments: str, *, call_id: str) -> dict[str, Any]:
    try:
        value = json.loads(arguments)
    except json.JSONDecodeError as exc:
        raise HarborAgentProtocolError(f"tool call {call_id!r} has invalid JSON arguments") from exc
    if not isinstance(value, dict):
        raise HarborAgentProtocolError(f"tool call {call_id!r} arguments must be a JSON object")
    return value


def _seed_for_trial(seed_root: int, trial_id: str) -> int:
    """Derive a stable trial seed while avoiding Python's process-randomized hash."""
    digest = hashlib.sha256(f"{seed_root}:{trial_id}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


class HarborStrategyAgent(BaseAgent):
    """Async Harbor agent that executes strategy-directed terminal actions."""

    @staticmethod
    def name() -> str:
        return "adaptive-agent-strategies"

    def version(self) -> str:
        return "0.1.0"

    def _setting(self, key: str, default: str | None = None) -> str | None:
        configured = getattr(self, "extra_env", {}) or {}
        return configured.get(key, os.environ.get(key, default))

    @staticmethod
    def _references_hidden_path(command: str) -> bool:
        normalized = command.casefold()
        return any(marker in normalized for marker in _HIDDEN_PATH_MARKERS) or bool(_PATH_TOKEN.search(command))

    def _command_timeout(self, strategy: Strategy) -> int:
        remaining = strategy.budget.max_wall_s - (time.monotonic() - self._started)
        if remaining <= 0:
            raise TimeoutError("strategy wall-clock budget exhausted")
        return max(1, min(strategy.tool_policy.command_timeout_s, int(remaining)))

    def _load_strategy(self) -> Strategy:
        path_value = self._setting("AAS_STRATEGY_PATH")
        if not path_value:
            raise HarborAgentConfigurationError("AAS_STRATEGY_PATH must point to a strategy JSON file")
        path = Path(path_value).expanduser()
        try:
            return Strategy.from_json(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise HarborAgentConfigurationError(f"could not read strategy file {path}") from exc

    def _new_model(self, trial_id: str) -> AsyncOpenAICompatibleModel:
        base_url = self._setting("AAS_MODEL_BASE_URL")
        model = self.model_name or self._setting("AAS_MODEL")
        if not base_url or not model:
            raise HarborAgentConfigurationError("Harbor requires AAS_MODEL_BASE_URL and a model name")
        seed_raw = self._setting("AAS_SEED_ROOT", "20261015")
        try:
            seed_root = int(seed_raw or "20261015")
        except ValueError as exc:
            raise HarborAgentConfigurationError("AAS_SEED_ROOT must be an integer") from exc
        timeout_raw = self._setting("AAS_MODEL_TIMEOUT_S", "7200")
        try:
            timeout_s = float(timeout_raw or "7200")
        except ValueError as exc:
            raise HarborAgentConfigurationError("AAS_MODEL_TIMEOUT_S must be numeric") from exc
        if timeout_s <= 0:
            raise HarborAgentConfigurationError("AAS_MODEL_TIMEOUT_S must be positive")
        attempt_raw = self._setting("AAS_ATTEMPT_INDEX", "0")
        try:
            attempt_index = int(attempt_raw or "0")
        except ValueError as exc:
            raise HarborAgentConfigurationError("AAS_ATTEMPT_INDEX must be an integer") from exc
        if attempt_index < 0:
            raise HarborAgentConfigurationError("AAS_ATTEMPT_INDEX must be non-negative")
        return AsyncOpenAICompatibleModel(
            base_url=base_url,
            model=model,
            api_key=self._setting("AAS_MODEL_API_KEY"),
            timeout_s=timeout_s,
            seed=_seed_for_trial(seed_root, f"{trial_id}:{attempt_index}"),
        )

    @staticmethod
    def _append_log(path: Path, row: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")
            output.flush()

    @staticmethod
    def _response_message(response: AsyncChatResponse) -> dict[str, Any]:
        message: dict[str, Any] = {"role": "assistant", "content": response.content}
        if response.reasoning is not None:
            message["reasoning_content"] = response.reasoning
        if response.tool_calls:
            message["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {"name": call.name, "arguments": call.arguments},
                }
                for call in response.tool_calls
            ]
        return message

    async def setup(self, environment: Any) -> None:
        """Validate configuration before the first model request."""
        self._strategy = self._load_strategy()
        trial_id = str(getattr(self, "context_id", None) or getattr(environment, "context_id", None) or "")
        if not trial_id:
            raise HarborAgentConfigurationError("Harbor did not provide a trial context_id")
        self._trial_id = trial_id
        self._strategy_hash = hashlib.sha256(self._strategy.to_json().encode()).hexdigest()
        task_id = str(getattr(environment, "environment_name", "unknown-task"))
        self._task_id = task_id
        self._run_id = self._setting("AAS_RUN_ID", "unspecified") or "unspecified"
        self._provenance = self._setting("AAS_PROVENANCE_TAG", "unregistered") or "unregistered"
        self._model = self._new_model(f"{self._run_id}:{task_id}")
        self._step_log = Path(self.logs_dir) / "aas_steps.jsonl"
        self._step_index = 0
        self._tokens = 0
        self._verify_cycles = 0
        self._started = time.monotonic()

    async def run(self, instruction: str, environment: Any, context: Any) -> None:
        strategy = self._strategy
        model = self._model
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    strategy.render()
                    + "\n\nUse the terminal tool for task work. Never inspect hidden tests, verifier files, "
                    "or reward data. "
                    "Call submit only when finished."
                ),
            },
            {"role": "user", "content": instruction},
        ]
        allowed_tools = {str(tool) for tool in strategy.tool_policy.tools_allowed}
        for probe_result in await self._run_probes(environment, strategy):
            messages.append({"role": "user", "content": probe_result})
        max_steps = strategy.budget.max_steps
        while self._step_index < max_steps:
            elapsed = time.monotonic() - self._started
            if elapsed >= strategy.budget.max_wall_s or self._tokens >= strategy.budget.max_tokens:
                break
            model.timeout_s = min(model.timeout_s, strategy.budget.max_wall_s - elapsed)
            try:
                response = await model.complete(messages, tools=_TOOLS)
            except Exception as exc:
                self._write_step(None, "model_error", None, f"{type(exc).__name__}: {exc}", None)
                raise
            self._tokens += response.output_tokens
            if hasattr(context, "n_input_tokens"):
                context.n_input_tokens = (context.n_input_tokens or 0) + response.input_tokens
                context.n_cache_tokens = (context.n_cache_tokens or 0) + response.cached_tokens
                context.n_output_tokens = (context.n_output_tokens or 0) + response.output_tokens
                context.metadata = {
                    **(context.metadata or {}),
                    "harbor_trial_id": self._trial_id,
                    "strategy_hash": self._strategy_hash,
                    "provenance_tag": self._provenance,
                }
            messages.append(self._response_message(response))
            if self._tokens > strategy.budget.max_tokens:
                self._write_step(response, "token_limit", None, "Response exceeded the episode token budget.", 126)
                return
            if not response.tool_calls:
                observation = "Protocol error: return a terminal or submit tool call."
                self._write_step(response, "invalid", None, observation, None)
                messages.append({"role": "user", "content": observation})
                self._step_index += 1
                continue
            for call in response.tool_calls:
                args = _json_object(call.arguments, call_id=call.id)
                if call.name == "submit":
                    if not isinstance(args.get("answer"), str):
                        raise HarborAgentProtocolError(f"submit call {call.id!r} requires a string answer")
                    check_budget = (
                        len(strategy.verification.checks)
                        if strategy.verification.verification_required
                        else 0
                    )
                    if self._step_index + check_budget + 1 > max_steps:
                        self._write_step(
                            response,
                            "step_limit",
                            call.id,
                            "Insufficient steps remain for configured checks and submission.",
                            126,
                            args,
                        )
                        return
                    check_passed, check_detail = True, ""
                    if strategy.verification.verification_required and strategy.verification.checks:
                        check_passed, check_detail = await self._run_own_checks(environment, strategy)
                    if strategy.verification.verification_required and not check_passed:
                        if self._verify_cycles < strategy.verification.max_verify_cycles:
                            self._verify_cycles += 1
                            observation = "Configured own checks failed. Continue fixing the task before submitting.\n"
                            observation += check_detail
                            self._write_step(response, "verify_failed", call.id, observation, 1, args)
                            messages.append(
                                {"role": "tool", "tool_call_id": call.id, "content": f"exit=1\n{observation}"}
                            )
                            self._step_index += 1
                            continue
                    self._write_step(response, "submit", call.id, "submitted", 0, args)
                    self._step_index += 1
                    return
                if call.name != "terminal" or "bash" not in allowed_tools:
                    observation, return_code = "Tool is not allowed by the strategy.", 126
                else:
                    command = args.get("command")
                    if not isinstance(command, str) or not command.strip():
                        raise HarborAgentProtocolError(f"terminal call {call.id!r} requires a non-empty command")
                    if self._references_hidden_path(command):
                        observation = "Command refused because it references verifier or solution paths."
                        return_code = 126
                        self._write_step(response, call.name, call.id, observation, return_code, args)
                        messages.append(
                            {"role": "tool", "tool_call_id": call.id, "content": f"exit={return_code}\n{observation}"}
                        )
                        self._step_index += 1
                        continue
                    folded_command = command.casefold()
                    forbidden = [
                        pattern
                        for pattern in strategy.tool_policy.forbidden_patterns
                        if pattern.casefold() in folded_command
                    ]
                    if forbidden:
                        observation, return_code = "Command refused by the strategy's forbidden-pattern policy.", 126
                        self._write_step(response, call.name, call.id, observation, return_code, args)
                        messages.append(
                            {"role": "tool", "tool_call_id": call.id, "content": f"exit={return_code}\n{observation}"}
                        )
                        self._step_index += 1
                        continue
                    try:
                        result = await environment.exec(
                            command,
                            timeout_sec=self._command_timeout(strategy),
                        )
                    except Exception as exc:
                        self._write_step(
                            response,
                            "terminal_error",
                            call.id,
                            f"{type(exc).__name__}: {exc}",
                            None,
                            args,
                        )
                        raise
                    observation = (result.stdout or "") + (result.stderr or "")
                    return_code = result.return_code
                    observation = observation[: strategy.tool_policy.max_observation_chars]
                self._write_step(response, call.name, call.id, observation, return_code, args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": f"exit={return_code}\n{observation}",
                    }
                )
                self._step_index += 1
                if self._step_index >= max_steps:
                    return

    async def _run_probes(self, environment: Any, strategy: Strategy) -> list[str]:
        """Run only safe, configured probes; never enumerate or execute hidden tests."""
        results: list[str] = []
        commands = {
            Probe.LIST_WORKDIR: "pwd && ls -la",
            Probe.READ_README: "if [ -f README.md ]; then cat README.md; else echo 'README.md not present'; fi",
            Probe.CHECK_TOOLCHAIN_VERSIONS: "python --version 2>&1; git --version 2>&1",
            Probe.CHECK_INSTALLED_PACKAGES: "python -m pip list --format=columns 2>&1",
            Probe.CHECK_SERVICES: "ps -ef 2>&1 | head -40",
            Probe.GIT_STATUS: "git status --short 2>&1",
        }
        shell_allowed = "bash" in {str(tool) for tool in strategy.tool_policy.tools_allowed}
        for probe in strategy.exploration.probes[: strategy.exploration.probe_budget_steps]:
            if self._step_index >= strategy.budget.max_steps:
                break
            command = commands.get(probe)
            if not shell_allowed:
                observation, code = "Skipped: strategy does not allow shell probes.", 0
            elif probe == Probe.INSPECT_TESTS:
                observation, code = "Skipped: Harbor keeps verifier tests unavailable during agent execution.", 0
            elif command is None:
                observation, code = "Probe is not implemented by this Harbor adapter.", 127
            else:
                result = await environment.exec(command, timeout_sec=self._command_timeout(strategy))
                observation = (result.stdout or "") + (result.stderr or "")
                code = result.return_code
                observation = observation[: strategy.tool_policy.max_observation_chars]
            self._write_step(None, f"probe:{probe}", None, observation, code, {"command": command})
            results.append(f"Probe {probe}: exit={code}\n{observation}")
            self._step_index += 1
        return results

    async def _run_own_checks(self, environment: Any, strategy: Strategy) -> tuple[bool, str]:
        """Run only experimenter-provided checks, never the Harbor verifier tests."""
        outcomes: list[bool] = []
        details: list[str] = []
        shell_allowed = "bash" in {str(tool) for tool in strategy.tool_policy.tools_allowed}
        for check in strategy.verification.checks:
            if self._step_index >= strategy.budget.max_steps:
                break
            variable = f"AAS_CHECK_{check.value.upper()}"
            command = self._setting(variable)
            if not shell_allowed:
                result_text, code = "Skipped: strategy does not allow shell checks.", 0
            elif check == Check.RUN_VISIBLE_TESTS and not command:
                result_text, code = "Skipped: visible-test command is not configured before verification.", 0
            elif not command:
                result_text, code = f"Skipped: {variable} is not configured.", 0
            elif self._references_hidden_path(command):
                result_text, code = "Skipped: configured check references verifier or solution paths.", 126
            else:
                result = await environment.exec(command, timeout_sec=self._command_timeout(strategy))
                result_text = (result.stdout or "") + (result.stderr or "")
                code = result.return_code
                result_text = result_text[: strategy.tool_policy.max_observation_chars]
            self._write_step(None, f"check:{check}", None, result_text, code, {"command": command})
            details.append(f"{check}: exit={code}\n{result_text}")
            if command:
                outcomes.append(code == 0)
            self._step_index += 1
        return all(outcomes), "\n".join(details)

    def _write_step(
        self,
        response: AsyncChatResponse | None,
        action: str,
        tool_call_id: str | None,
        observation: str,
        exit_code: int | None,
        action_args: Mapping[str, Any] | None = None,
    ) -> None:
        self._append_log(
            self._step_log,
            {
                "run_id": self._run_id,
                "harbor_trial_id": self._trial_id,
                "step": self._step_index,
                "task_id": self._task_id,
                "strategy_id": self._strategy.strategy_id,
                "strategy_version": self._strategy.version,
                "strategy_hash": self._strategy_hash,
                "provenance_tag": self._provenance,
                "seed": response.seed if response else None,
                "action": action,
                "tool_call_id": tool_call_id,
                "action_args": action_args,
                "reasoning": response.reasoning if response else None,
                "observation": observation,
                "exit_code": exit_code,
                "input_tokens": response.input_tokens if response else 0,
                "cached_tokens": response.cached_tokens if response else 0,
                "output_tokens": response.output_tokens if response else 0,
                "timings": response.timings.__dict__ if response else None,
                "model_elapsed_s": response.elapsed_s if response else 0.0,
                "elapsed_s": time.monotonic() - self._started,
            },
        )

\n