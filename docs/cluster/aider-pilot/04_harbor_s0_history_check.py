"""Bounded, task-free S0/HarborStrategyAgent history check.

The real agent loop and model client are used. A mock environment discards all
commands and returns fixed synthetic probe/tool output; no command executor,
Harbor trial, benchmark task, or verifier is created.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import logging
import os
import statistics
import time
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from environments.harbor_agent import _TOOLS, HarborStrategyAgent
from strategy_schema.defaults import s0

_DIAG_PATH = Path(__file__).with_name("03_tool_schema_history_diagnostic.py")
_DIAG_SPEC = importlib.util.spec_from_file_location("_aas_protocol_diagnostic", _DIAG_PATH)
if _DIAG_SPEC is None or _DIAG_SPEC.loader is None:
    raise RuntimeError("protocol_diagnostic_helper_unavailable")
_DIAG_MODULE = importlib.util.module_from_spec(_DIAG_SPEC)
_DIAG_SPEC.loader.exec_module(_DIAG_MODULE)
CONTEXT_LIMIT = _DIAG_MODULE.CONTEXT_LIMIT
CONTEXT_MARGIN = _DIAG_MODULE.CONTEXT_MARGIN
MODEL = _DIAG_MODULE.MODEL
MemoryMonitor = _DIAG_MODULE.MemoryMonitor
check_tool_call = _DIAG_MODULE.check_tool_call
prompt_tokens = _DIAG_MODULE.prompt_tokens

OUTPUT_CAP = 1024
VRAM_HEADROOM_MIB = 1024
REQUEST_CEILING = 6
REPETITIONS = 3
SEED_ROOT = 20261124
S0_INSTRUCTION = (
    "This is a task-free interface check. Use the terminal tool once to describe "
    "a harmless synthetic action, then submit a brief completion. Do not access "
    "files, tests, credentials, networks, or external resources."
)
FILLER = "Synthetic README history marker; there is no real task, file, code, or user data. "
HISTORY_REPEATS = {"short": 80, "long": 260}


class ContextGuardStop(RuntimeError):
    def __init__(self, input_tokens: int, output_tokens: int):
        super().__init__("context_guard_stop")
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class RequestCeilingStop(RuntimeError):
    pass


class ProbeInvariantStop(RuntimeError):
    pass


@dataclass
class MockEnvironment:
    """Synthetic environment that drops command strings and never launches a process."""

    context_id: str
    environment_name: str
    readme: str
    exec_calls: int = 0
    workdir_probe_calls: int = 0
    readme_probe_calls: int = 0
    mock_terminal_calls: int = 0

    async def exec(self, command: str, *, timeout_sec: int) -> Any:
        # Deliberately discard `command` and `timeout_sec`; no shell/subprocess exists.
        self.exec_calls += 1
        if self.exec_calls == 1:
            self.workdir_probe_calls += 1
            stdout = "Synthetic workdir; no files or task data exist.\n"
        elif self.exec_calls == 2:
            self.readme_probe_calls += 1
            stdout = self.readme
        else:
            self.mock_terminal_calls += 1
            stdout = "Synthetic terminal result; no command was executed and no state exists.\n"
        return SimpleNamespace(stdout=stdout, stderr="", return_code=0)


def _safe_response_category(response: Any) -> tuple[str, str]:
    category = check_tool_call(response)
    calls = getattr(response, "tool_calls", None) or ()
    tool_name = calls[0].name if len(calls) == 1 and calls[0].name in {"terminal", "submit"} else "other"
    return category, tool_name


async def run_conversation(
    *,
    base: str,
    condition: str,
    repetition: int,
    monitor: MemoryMonitor,
    strategy_path: Path,
) -> dict[str, Any]:
    run_id = f"s0-history-pair-{repetition + 1:02d}"
    environment = MockEnvironment(
        context_id=f"synthetic-{condition}-{repetition + 1:02d}",
        environment_name="synthetic-history-check",
        readme=FILLER * HISTORY_REPEATS[condition],
    )
    log_dir = Path(".") / f"agent-logs-{condition}-{repetition + 1:02d}"
    log_dir.mkdir(parents=True, exist_ok=False)
    agent = HarborStrategyAgent(logs_dir=log_dir, model_name=MODEL)
    agent.extra_env = {
        "AAS_STRATEGY_PATH": str(strategy_path),
        "AAS_MODEL_BASE_URL": base + "/v1",
        "AAS_MODEL": MODEL,
        "AAS_RUN_ID": run_id,
        "AAS_PROVENANCE_TAG": "synthetic-engineering-check",
        "AAS_SEED_ROOT": str(SEED_ROOT),
        "AAS_MODEL_TIMEOUT_S": "180",
        # Explicitly empty: S0's optional visible-test hook cannot run a command.
        "AAS_CHECK_RUN_VISIBLE_TESTS": "",
    }
    context = SimpleNamespace(
        n_input_tokens=0,
        n_cache_tokens=0,
        n_output_tokens=0,
        metadata={},
    )
    aggregate: dict[str, Any] = {
        "condition": condition,
        "pair": repetition + 1,
        "mock_exec_calls": 0,
        "request_count": 0,
        "request_categories": Counter(),
        "tool_categories": Counter(),
        "step_categories": Counter(),
        "requests": [],
        "context_guard": None,
        "stop_reason": "agent_returned",
        "submit_step": None,
        "history_repeats": HISTORY_REPEATS[condition],
        "history_prompt_tokens_after_probes": None,
    }

    await agent.setup(environment)
    model = agent._model
    aggregate["effective_seed"] = model.seed
    aggregate["strategy_sha256"] = agent._strategy_hash
    aggregate["s0_max_steps"] = agent._strategy.budget.max_steps
    aggregate["s0_max_episode_tokens"] = agent._strategy.budget.max_tokens
    aggregate["s0_max_wall_seconds"] = agent._strategy.budget.max_wall_s

    def safe_write_step(
        response: Any,
        action: str,
        tool_call_id: str | None,
        observation: str,
        exit_code: int | None,
        action_args: Any = None,
        *,
        tripwire_flags: list[str] | None = None,
    ) -> None:
        # Aggregate labels only. Never serialize args, observations, reasoning, IDs, or content.
        safe_action = action if action in {
            "terminal", "submit", "invalid", "model_error", "terminal_error",
            "token_limit", "step_limit", "verify_failed", "verify",
            "probe:list_workdir", "probe:read_readme", "probe:check_toolchain_versions",
            "probe:check_installed_packages", "probe:check_services", "probe:git_status",
        } else "other"
        aggregate["step_categories"][safe_action] += 1
        if safe_action == "submit":
            aggregate["submit_step"] = agent._step_index
        for flag in tripwire_flags or []:
            if flag in {"url", "ipv4_address", "ipv6_address", "namespace_tool", "mount_tool"}:
                aggregate.setdefault("tripwire_flags", Counter())[flag] += 1

    # Replace the production writer before run() so no raw step JSONL is created.
    agent._write_step = safe_write_step

    original_complete = model.complete

    async def guarded_complete(
        messages: Any,
        *,
        seed: int | None = None,
        tools: Any = None,
        max_output_tokens: int | None = None,
    ) -> Any:
        monitor.assert_safe()
        if aggregate["request_count"] == 0 and environment.exec_calls != 2:
            raise ProbeInvariantStop("expected_two_s0_probes_before_inference")
        if aggregate["request_count"] >= REQUEST_CEILING:
            raise RequestCeilingStop("request_ceiling")
        request_cap = min(OUTPUT_CAP, max_output_tokens or OUTPUT_CAP)
        request_seed = seed if seed is not None else model.seed + model._request_count
        measured = prompt_tokens(base, model, messages, request_seed, request_cap)
        if aggregate["history_prompt_tokens_after_probes"] is None:
            aggregate["history_prompt_tokens_after_probes"] = measured
        if measured + request_cap + CONTEXT_MARGIN >= CONTEXT_LIMIT:
            aggregate["context_guard"] = {
                "input_tokens": measured,
                "output_cap": request_cap,
                "margin_tokens": CONTEXT_MARGIN,
                "context_limit": CONTEXT_LIMIT,
            }
            raise ContextGuardStop(measured, request_cap)
        aggregate["request_count"] += 1
        started = time.monotonic()
        response = await original_complete(
            messages,
            seed=seed,
            tools=tools or _TOOLS,
            max_output_tokens=request_cap,
        )
        monitor.assert_safe()
        category, tool_name = _safe_response_category(response)
        aggregate["request_categories"][category] += 1
        aggregate["tool_categories"][tool_name] += 1
        aggregate["requests"].append({
            "prompt_tokens_preflight": measured,
            "input_tokens_reported": response.input_tokens,
            "cached_tokens": response.cached_tokens,
            "output_tokens": response.output_tokens,
            "response_category": category,
            "tool_category": tool_name,
            "elapsed_seconds": round(time.monotonic() - started, 4),
            "model_elapsed_seconds": round(response.elapsed_s, 4),
            "prompt_ms": response.timings.prompt_ms,
            "generation_ms": response.timings.generated_ms,
        })
        return response

    model.complete = guarded_complete
    start = time.monotonic()
    try:
        await agent.run(S0_INSTRUCTION, environment, context)
    except ContextGuardStop:
        aggregate["stop_reason"] = "context_guard"
    except RequestCeilingStop:
        aggregate["stop_reason"] = "request_ceiling"
    except Exception as exc:
        # Do not print exception text: providers may include request details.
        aggregate["stop_reason"] = f"error:{type(exc).__name__}"
    aggregate["wall_seconds"] = round(time.monotonic() - start, 4)
    aggregate["mock_exec_calls"] = environment.exec_calls
    aggregate["raw_content_written"] = False
    aggregate["agent_step_log_created"] = (log_dir / "aas_steps.jsonl").exists()
    aggregate["submitted"] = aggregate["step_categories"].get("submit", 0) > 0
    aggregate["calls_to_submit"] = (
        aggregate["request_count"] if aggregate["submitted"] else None
    )
    aggregate["step_categories"] = dict(aggregate["step_categories"])
    aggregate["workdir_probe_calls"] = environment.workdir_probe_calls
    aggregate["readme_probe_calls"] = environment.readme_probe_calls
    aggregate["mock_terminal_calls"] = environment.mock_terminal_calls
    aggregate["s0_probes_intercepted_before_first_inference"] = (
        environment.workdir_probe_calls == 1
        and environment.readme_probe_calls == 1
    )
    aggregate["request_categories"] = dict(aggregate["request_categories"])
    aggregate["tool_categories"] = dict(aggregate["tool_categories"])
    aggregate["tripwire_flags"] = dict(aggregate.get("tripwire_flags", {}))
    aggregate["total_input_tokens"] = sum(row["input_tokens_reported"] for row in aggregate["requests"])
    aggregate["total_output_tokens"] = sum(row["output_tokens"] for row in aggregate["requests"])
    aggregate["mean_call_seconds"] = round(
        statistics.mean([row["model_elapsed_seconds"] for row in aggregate["requests"]]), 4
    ) if aggregate["requests"] else None
    if aggregate["mock_exec_calls"] < 2:
        aggregate["probe_invariant"] = "not_all_s0_probes_seen"
    else:
        aggregate["probe_invariant"] = "s0_probes_intercepted"
    if aggregate["agent_step_log_created"]:
        raise RuntimeError("raw_step_log_invariant_failed")
    return aggregate


async def run_experiment(base: str, output: Path, server_pid: int, hashes: dict[str, str]) -> dict[str, Any]:
    # Prevent inherited per-check commands from reaching the S0 verification hook.
    for key in list(os.environ):
        if key.startswith("AAS_CHECK_"):
            os.environ.pop(key, None)
    os.environ["HARBOR_TELEMETRY"] = "off"
    logging.disable(logging.CRITICAL)

    output.parent.mkdir(parents=True, exist_ok=True)
    strategy_path = output.parent / "s0-strategy.json"
    strategy_path.write_text(s0().to_json() + "\n", encoding="utf-8")
    strategy_hash = hashlib.sha256(strategy_path.read_bytes()).hexdigest()
    monitor = MemoryMonitor(server_pid)
    monitor.start()
    started = time.monotonic()
    runs: list[dict[str, Any]] = []
    status = "completed"
    try:
        for repetition in range(REPETITIONS):
            condition_order = ("short", "long") if repetition % 2 == 0 else ("long", "short")
            for condition in condition_order:
                monitor.assert_safe()
                row = await run_conversation(
                    base=base,
                    condition=condition,
                    repetition=repetition,
                    monitor=monitor,
                    strategy_path=strategy_path,
                )
                runs.append(row)
                if row["stop_reason"].startswith("error:"):
                    status = "aborted_model_or_protocol_error"
                    break
                if row["agent_step_log_created"]:
                    status = "aborted_safety_invariant"
                    break
            if status != "completed":
                break
    except Exception as exc:
        # Persist only the exception class, never its potentially sensitive message.
        status = f"aborted:{type(exc).__name__}"
    finally:
        monitor.stop()

    result = {
        "experiment": "synthetic_harbor_s0_history_check",
        "date_utc": datetime.now(UTC).date().isoformat(),
        "status": status,
        "interpretation": (
            "engineering evidence only; synthetic instructions and mock environment; "
            "not benchmark performance"
        ),
        "model": MODEL,
        "model_sha256": hashes["model"],
        "server_sif_sha256": hashes["server"],
        "source_commit": hashes["source_commit"],
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "strategy_id": "s0",
        "strategy_sha256": strategy_hash,
        "seed_root": SEED_ROOT,
        "paired_repetitions_per_condition": REPETITIONS,
        "planned_conversations": REPETITIONS * len(HISTORY_REPEATS),
        "started_conversations": len(runs),
        "bounded_loop_conversations_returned": sum(
            run.get("stop_reason") in {"agent_returned", "context_guard", "request_ceiling"}
            for run in runs
        ),
        "conditions": {key: HISTORY_REPEATS[key] for key in HISTORY_REPEATS},
        "context_limit_tokens": CONTEXT_LIMIT,
        "per_request_output_cap": OUTPUT_CAP,
        "required_context_margin_tokens": CONTEXT_MARGIN,
        "request_ceiling_per_conversation": REQUEST_CEILING,
        "tool_executor_created": False,
        "harbor_trial_created": False,
        "task_oracle_reference_solution_used": False,
        "real_harbor_environment_created": False,
        "task_command_executor_created": False,
        "s0_visible_test_check": "skipped_no_command_configured",
        "raw_prompt_completion_command_answer_or_reasoning_written": False,
        "harbor_uds_exercised": False,
        "runs": runs,
        "gpu_monitor": {
            "gpu_uuid": monitor.gpu_uuid,
            "peak_used_mib": monitor.peak_used_mib,
            "minimum_free_mib": monitor.minimum_free_mib,
            "samples": monitor.samples,
            "required_headroom_mib": VRAM_HEADROOM_MIB,
            "stop_reason": monitor.reason,
        },
        "total_wall_seconds": round(time.monotonic() - started, 3),
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="llama.cpp server root URL")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--server-pid", type=int, required=True)
    parser.add_argument("--model-sha256", required=True)
    parser.add_argument("--server-sif-sha256", required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    result = asyncio.run(run_experiment(
        args.base_url,
        args.output,
        args.server_pid,
        {"model": args.model_sha256, "server": args.server_sif_sha256, "source_commit": args.source_commit},
    ))
    print(json.dumps({
        "status": result["status"],
        "runs": len(result["runs"]),
        "submitted": sum(bool(run.get("submitted")) for run in result["runs"]),
        "gpu_minimum_free_mib": result["gpu_monitor"]["minimum_free_mib"],
        "artifact": str(args.output),
    }, sort_keys=True))
    return 0 if result["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
