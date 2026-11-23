"""Synthetic tool-schema/history check; no task executor or benchmark is used."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import os
import signal
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

from environments.harbor_agent import _TOOLS, HarborStrategyAgent
from llm.async_openai_compatible import AsyncOpenAICompatibleModel
from strategy_schema.defaults import s0

MODEL = "gpt-oss-20b-MXFP4.gguf"
OUTPUT_CAPS = (192, 512)
PREFLIGHT_OUTPUT_TOKENS = max(OUTPUT_CAPS)
SEED_ROOT = 20261123
REPETITIONS = 8
CONTEXT_LIMIT = 8192
CONTEXT_MARGIN = 1024
VRAM_HEADROOM_MIB = 1024
TARGETS = (("short", 1024), ("medium", 4096), ("long", 6400))
FILLER = "Synthetic inert history marker; no task or environment exists. "
SYSTEM_SUFFIX = (
    "\n\nThis is a synthetic interface diagnostic, not a real task. Use the "
    "terminal tool only for inert descriptive text. Never request network, "
    "files, credentials, or hidden data. Tool calls are recorded as inert "
    "test data and are never executed. Use submit to end the simulation."
)
USER_REQUEST = (
    "Simulate two harmless tool turns by returning a terminal call containing "
    "a brief descriptive phrase, then submit a short completion sentence. "
    "Do not produce shell syntax or access any external resource."
)


class SafeDiagnosticError(RuntimeError):
    """A failure category with no request, completion, or argument content."""


class MemoryMonitor:
    """Fail-closed sampler for the single Slurm-visible GPU."""

    def __init__(self, server_pid: int):
        self.server_pid = server_pid
        self.stop_event = threading.Event()
        self.ready_event = threading.Event()
        self.failure_event = threading.Event()
        self.reason: str | None = None
        self.gpu_uuid: str | None = None
        self.peak_used_mib = 0
        self.minimum_free_mib: int | None = None
        self.samples = 0
        visible = os.environ.get("CUDA_VISIBLE_DEVICES", "").strip()
        self.device_id = visible.split(",", maxsplit=1)[0].strip() if visible else None
        self.thread = threading.Thread(target=self._sample, daemon=True)

    def start(self) -> None:
        self.thread.start()
        if not self.ready_event.wait(timeout=10):
            self._stop_server("vram_monitor_start_timeout")
        self.assert_safe()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=3)

    def assert_safe(self) -> None:
        if (
            self.thread.ident is not None
            and not self.thread.is_alive()
            and not self.stop_event.is_set()
            and not self.failure_event.is_set()
        ):
            self._stop_server("vram_monitor_stopped_unexpectedly")
        if self.failure_event.is_set():
            raise SafeDiagnosticError(self.reason or "vram_monitor_failed")

    def _stop_server(self, reason: str) -> None:
        self.reason = reason
        self.failure_event.set()
        try:
            os.kill(self.server_pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass

    def _sample(self) -> None:
        try:
            while not self.stop_event.is_set():
                command = ["nvidia-smi"]
                if self.device_id:
                    command.extend(["--id", self.device_id])
                command.extend([
                    "--query-gpu=uuid,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ])
                proc = subprocess.run(command, capture_output=True, text=True, timeout=5, check=True)
                rows = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
                if len(rows) != 1:
                    self.ready_event.set()
                    self._stop_server("vram_device_ambiguous")
                    return
                fields = [item.strip() for item in rows[0].split(",")]
                if len(fields) != 3 or not fields[1].isdigit() or not fields[2].isdigit():
                    self.ready_event.set()
                    self._stop_server("vram_telemetry_invalid")
                    return
                uuid, used_text, total_text = fields
                used_mib, total_mib = int(used_text), int(total_text)
                self.gpu_uuid = uuid
                self.peak_used_mib = max(self.peak_used_mib, used_mib)
                free_mib = total_mib - used_mib
                if self.minimum_free_mib is None:
                    self.minimum_free_mib = free_mib
                else:
                    self.minimum_free_mib = min(self.minimum_free_mib, free_mib)
                self.samples += 1
                self.ready_event.set()
                if free_mib < VRAM_HEADROOM_MIB:
                    self._stop_server("vram_headroom_below_1gib")
                    return
                self.stop_event.wait(0.5)
        except Exception:
            self.ready_event.set()
            self._stop_server("vram_telemetry_failed")


async def guarded_complete(
    model: AsyncOpenAICompatibleModel,
    messages: list[dict[str, Any]],
    monitor: MemoryMonitor,
    output_tokens: int,
) -> Any:
    monitor.assert_safe()
    request = asyncio.create_task(
        model.complete(messages, tools=_TOOLS, max_output_tokens=output_tokens)
    )
    while not request.done():
        await asyncio.sleep(0.1)
        if monitor.failure_event.is_set() or not monitor.thread.is_alive():
            request.cancel()
            monitor.assert_safe()
    response = await request
    monitor.assert_safe()
    return response


def post_json(base: str, route: str, payload: dict[str, Any]) -> tuple[int, Any]:
    req = urllib.request.Request(
        base + route,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        return status, None
    except Exception:
        return 0, None


def prompt_tokens(
    base: str,
    model: AsyncOpenAICompatibleModel,
    messages: list[dict[str, Any]],
    seed: int,
    output_tokens: int,
) -> int:
    body = model._request_body(messages, seed, _TOOLS, output_tokens)
    status, value = post_json(base, "/chat/completions/input_tokens", body)
    if status == 200 and isinstance(value, dict) and isinstance(value.get("input_tokens"), int):
        return value["input_tokens"]

    status, rendered = post_json(
        base,
        "/apply-template",
        {"messages": messages, "tools": _TOOLS},
    )
    if status != 200 or not isinstance(rendered, dict) or not isinstance(rendered.get("prompt"), str):
        raise SafeDiagnosticError("prompt_token_count_unavailable")
    status, tokenized = post_json(
        base,
        "/tokenize",
        {"content": rendered["prompt"], "add_special": False, "parse_special": True},
    )
    tokens = tokenized.get("tokens") if isinstance(tokenized, dict) else None
    if status != 200 or not isinstance(tokens, list):
        raise SafeDiagnosticError("prompt_token_count_unavailable")
    return len(tokens)


def messages_for_target(
    base: str,
    model: AsyncOpenAICompatibleModel,
    target: int,
    seed: int,
    output_tokens: int,
) -> tuple[list[dict[str, Any]], int]:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": s0().render() + SYSTEM_SUFFIX},
        {"role": "user", "content": USER_REQUEST},
    ]
    measured = prompt_tokens(base, model, messages, seed, output_tokens)
    if measured > target:
        raise SafeDiagnosticError("base_prompt_exceeds_target")

    low, high = 0, max(1, target // 8)
    best: tuple[list[dict[str, Any]], int] = (messages, measured)
    for _ in range(16):
        repeats = (low + high) // 2
        candidate = [dict(messages[0]), {"role": "user", "content": USER_REQUEST + "\n" + FILLER * repeats}]
        count = prompt_tokens(base, model, candidate, seed, output_tokens)
        if abs(count - target) < abs(best[1] - target):
            best = (candidate, count)
        if abs(count - target) <= 64:
            break
        if count < target:
            low = repeats + 1
        else:
            high = repeats - 1
        if low > high:
            break

    if abs(best[1] - target) > 256:
        raise SafeDiagnosticError("history_target_not_reached")
    if best[1] + output_tokens + CONTEXT_MARGIN >= CONTEXT_LIMIT:
        raise SafeDiagnosticError("context_headroom_preflight_failed")
    return best


def check_tool_call(response: Any) -> str:
    calls = getattr(response, "tool_calls", None)
    if not calls:
        return "no_tool_call"
    if len(calls) != 1:
        return "multiple_tool_calls"
    call = calls[0]
    if call.name not in {"terminal", "submit"}:
        return "wrong_tool_name"
    try:
        arguments = json.loads(call.arguments)
    except (TypeError, json.JSONDecodeError):
        return "invalid_json"
    if not isinstance(arguments, dict):
        return "json_not_object"
    expected_key = "command" if call.name == "terminal" else "answer"
    if set(arguments) != {expected_key} or not isinstance(arguments.get(expected_key), str):
        return "invalid_schema"
    if call.name == "terminal" and not arguments["command"].strip():
        return "invalid_schema"
    return "valid_schema_A" if call.name == "terminal" else "valid_schema_B"


async def run(
    base: str,
    output: Path,
    model_hash: str,
    server_hash: str,
    source_commit: str,
    server_pid: int,
) -> None:
    outcomes = {
        str(cap): {name: Counter() for name, _ in TARGETS} for cap in OUTPUT_CAPS
    }
    latencies = {str(cap): {name: [] for name, _ in TARGETS} for cap in OUTPUT_CAPS}
    input_tokens = {str(cap): {name: [] for name, _ in TARGETS} for cap in OUTPUT_CAPS}
    output_tokens = {str(cap): {name: [] for name, _ in TARGETS} for cap in OUTPUT_CAPS}
    cap_reached = {
        str(cap): {name: 0 for name, _ in TARGETS} for cap in OUTPUT_CAPS
    }
    attempted = 0
    monitor = MemoryMonitor(server_pid)
    monitor.start()

    try:
        for condition_index, (condition, target) in enumerate(TARGETS):
            for repetition in range(REPETITIONS):
                monitor.assert_safe()
                seed = SEED_ROOT + condition_index * 1000 + repetition * 10
                preflight_model = AsyncOpenAICompatibleModel(
                    base_url=base + "/v1",
                    model=MODEL,
                    timeout_s=120,
                    temperature=0.6,
                    top_p=0.95,
                    top_k=20,
                    seed=seed,
                    max_tokens=PREFLIGHT_OUTPUT_TOKENS,
                )
                try:
                    messages, measured = messages_for_target(
                        base,
                        preflight_model,
                        target,
                        seed,
                        PREFLIGHT_OUTPUT_TOKENS,
                    )
                except SafeDiagnosticError as exc:
                    for cap in OUTPUT_CAPS:
                        outcomes[str(cap)][condition][str(exc)] += 1
                    continue
                monitor.assert_safe()
                for cap in OUTPUT_CAPS:
                    cap_key = str(cap)
                    if measured + cap + CONTEXT_MARGIN >= CONTEXT_LIMIT:
                        outcomes[cap_key][condition]["context_headroom_preflight_failed"] += 1
                        continue
                    model = AsyncOpenAICompatibleModel(
                        base_url=base + "/v1",
                        model=MODEL,
                        timeout_s=120,
                        temperature=0.6,
                        top_p=0.95,
                        top_k=20,
                        seed=seed,
                        max_tokens=cap,
                    )
                    arm_messages = copy.deepcopy(messages)
                    # Matched cap arms share the exact synthetic prompt and seed.
                    for turn in range(2):
                        attempted += 1
                        started = time.monotonic()
                        try:
                            response = await guarded_complete(
                                model, arm_messages, monitor, cap
                            )
                        except Exception as exc:
                            if isinstance(exc, SafeDiagnosticError):
                                outcomes[cap_key][condition][str(exc)] += 1
                                break
                            outcomes[cap_key][condition][f"client_error:{type(exc).__name__}"] += 1
                            break
                        latencies[cap_key][condition].append(time.monotonic() - started)
                        input_tokens[cap_key][condition].append(response.input_tokens)
                        output_tokens[cap_key][condition].append(response.output_tokens)
                        if response.output_tokens >= cap:
                            cap_reached[cap_key][condition] += 1
                        category = check_tool_call(response)
                        outcomes[cap_key][condition][category] += 1
                        if category == "valid_schema_B":
                            break
                        if category != "valid_schema_A":
                            break

                        call = response.tool_calls[0]
                        arm_messages.append(HarborStrategyAgent._response_message(response))
                        arm_messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call.id,
                                "content": "exit=0\nSynthetic tool result; no command was executed.",
                            }
                        )
                        try:
                            current_tokens = prompt_tokens(
                                base, model, arm_messages, seed + turn + 1, cap
                            )
                        except SafeDiagnosticError as exc:
                            outcomes[cap_key][condition][str(exc)] += 1
                            break
                        monitor.assert_safe()
                        if current_tokens + cap + CONTEXT_MARGIN >= CONTEXT_LIMIT:
                            outcomes[cap_key][condition]["context_headroom_stop"] += 1
                            break

    finally:
        monitor.stop()

    result = {
        "experiment": "paired_synthetic_tool_schema_history_cap_sensitivity",
        "date": "2026-11-23",
        "task_oracle_reference_solution_used": False,
        "tool_executor_instantiated": False,
        "raw_prompt_completion_or_arguments_written": False,
        "model": MODEL,
        "model_sha256": model_hash,
        "server_sif_sha256": server_hash,
        "source_commit": source_commit,
        "strategy_id": "s0",
        "strategy_sha256": hashlib.sha256(s0().to_json().encode()).hexdigest(),
        "tools_sha256": hashlib.sha256(json.dumps(_TOOLS, sort_keys=True).encode()).hexdigest(),
        "client": "llm.async_openai_compatible.AsyncOpenAICompatibleModel",
        "history_targets": dict(TARGETS),
        "repetitions_per_target": REPETITIONS,
        "max_calls_per_conversation": 2,
        "output_token_caps": list(OUTPUT_CAPS),
        "seed_root": SEED_ROOT,
        "attempted_model_calls": attempted,
        "outcomes": {
            cap: {key: dict(value) for key, value in conditions.items()}
            for cap, conditions in outcomes.items()
        },
        "output_token_count_at_or_over_cap": cap_reached,
        "mean_latency_seconds": {
            cap: {
                key: round(statistics.mean(value), 4) if value else None
                for key, value in conditions.items()
            }
            for cap, conditions in latencies.items()
        },
        "mean_input_tokens": {
            cap: {
                key: round(statistics.mean(value), 1) if value else None
                for key, value in conditions.items()
            }
            for cap, conditions in input_tokens.items()
        },
        "mean_output_tokens": {
            cap: {
                key: round(statistics.mean(value), 1) if value else None
                for key, value in conditions.items()
            }
            for cap, conditions in output_tokens.items()
        },
        "finish_reason_captured": False,
        "gpu_monitor": {
            "gpu_uuid": monitor.gpu_uuid,
            "peak_used_mib": monitor.peak_used_mib,
            "minimum_free_mib": monitor.minimum_free_mib,
            "samples": monitor.samples,
            "headroom_mib": VRAM_HEADROOM_MIB,
            "stop_reason": monitor.reason,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"attempted_model_calls": attempted, "outcomes": result["outcomes"]},
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model-sha256", required=True)
    parser.add_argument("--server-sif-sha256", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--server-pid", required=True, type=int)
    args = parser.parse_args()
    asyncio.run(run(
        args.base_url.rstrip("/"), args.output, args.model_sha256,
        args.server_sif_sha256, args.source_commit, args.server_pid,
    ))


if __name__ == "__main__":
    main()
