"""Serving-only gpt-oss tool-contract diagnostic; never executes tool calls.

Only aggregate metrics are written. Prompts, completions, tool names and
argument values remain in memory and are not printed or persisted.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import signal
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


MODEL_FILE = "gpt-oss-20b-MXFP4.gguf"
MODEL_SHA256 = "27cd6c432c7672cb812a92f611cf3ba7bbc35928262bb1e1253ff4ee6ae35901"
SERVER_SIF_SHA256 = "dd8110164788b9deb354e06cb984214b2ef8b6b0598c2ef73dd0ab9828957d56"
SERVER_SIF = "/scratch/{user}/images/llama-server-cuda12-b11515.sif"
MODEL_PATH = "/scratch/{user}/models/" + MODEL_FILE
SEED_ROOT = 20261120
REPETITIONS = 10
OUTPUT_LIMIT = 256
CONTEXT_MARGIN = 768
VRAM_HEADROOM_MIB = 1024
TARGETS = (("shared_4k", 4096), ("shared_6_5k", 6656))
LONG_TARGET = ("long_24k", 24576)
FILLER_UNIT = (
    "Synthetic observation: status stable; action none; marker zero; "
    "this is inert diagnostic history and has no external effect. "
)
TOOL = {
    "type": "function",
    "function": {
        "name": "record_sample",
        "description": "Record a synthetic diagnostic label and count; perform no action.",
        "parameters": {
            "type": "object",
            "properties": {
                "stage": {
                    "type": "string",
                    "enum": ["baseline", "sample", "followup", "long_history"],
                },
                "count": {"type": "integer", "minimum": 0, "maximum": 3},
            },
            "required": ["stage", "count"],
            "additionalProperties": False,
        },
    },
}
SYSTEM_TEXT = (
    "This is a synthetic tool-call diagnostic. Use only the provided "
    "record_sample function when the user requests it. It records inert "
    "test metadata and has no side effects. Never propose shell commands."
)


class DiagnosticError(RuntimeError):
    """Safe error containing no request, completion, or argument text."""


def post_json(base: str, route: str, payload: dict[str, Any], timeout: float = 180.0) -> tuple[int, Any]:
    request = urllib.request.Request(
        base + route,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        return status, None
    except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError):
        return 0, None


def post_inference(
    base: str,
    payload: dict[str, Any],
    monitor: "MemoryMonitor",
    process: subprocess.Popen[Any],
) -> tuple[int, Any, bool]:
    """Run one inference request cancellably; retain only a context-error bit."""
    result: dict[str, Any] = {}

    def request() -> None:
        req = urllib.request.Request(
            base + "/v1/chat/completions",
            data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                result["status"] = response.status
                result["body"] = json.loads(response.read())
                result["context_error"] = False
        except urllib.error.HTTPError as exc:
            # Inspect at most 2 KiB in memory. Never print or persist the body.
            body = exc.read(2048).decode("utf-8", errors="ignore")
            result["status"] = exc.code
            result["body"] = None
            result["context_error"] = bool(
                re.search(r"context|n_ctx|prompt.{0,20}too long|too many tokens", body, re.I)
            )
            exc.close()
        except Exception:
            result["status"] = 0
            result["body"] = None
            result["context_error"] = False

    worker = threading.Thread(target=request, daemon=True)
    worker.start()
    while worker.is_alive():
        if monitor.limit_event.is_set():
            if process.poll() is None:
                process.terminate()
            return -1, None, False
        worker.join(timeout=0.2)
    if monitor.limit_event.is_set():
        if process.poll() is None:
            process.terminate()
        return -1, None, False
    return (
        int(result.get("status", 0)),
        result.get("body"),
        bool(result.get("context_error", False)),
    )


def request_body(messages: list[dict[str, Any]], seed: int) -> dict[str, Any]:
    return {
        "model": MODEL_FILE,
        "messages": messages,
        "tools": [TOOL],
        "temperature": 0.6,
        "top_p": 0.95,
        "top_k": 20,
        "seed": seed,
        "max_tokens": OUTPUT_LIMIT,
        "stream": False,
    }


def count_input_tokens(base: str, body: dict[str, Any], state: dict[str, str]) -> int:
    status, response = post_json(base, "/v1/chat/completions/input_tokens", body, timeout=30)
    if status == 200 and isinstance(response, dict):
        count = response.get("input_tokens")
        if isinstance(count, int) and not isinstance(count, bool) and count >= 0:
            state["token_count_method"] = "chat_completions_input_tokens"
            return count

    # Older pinned builds may not provide the chat token-count route. Fall
    # back only when the server can render the same chat template and tokenize
    # it; otherwise abort before sending any inference request.
    template_status, template = post_json(
        base,
        "/apply-template",
        {"messages": body["messages"], "tools": body["tools"]},
        timeout=30,
    )
    if template_status != 200 or not isinstance(template, dict) or not isinstance(template.get("prompt"), str):
        raise DiagnosticError("exact_prompt_token_count_unavailable")
    token_status, tokenized = post_json(
        base,
        "/tokenize",
        {"content": template["prompt"], "add_special": False, "parse_special": True},
        timeout=30,
    )
    tokens = tokenized.get("tokens") if isinstance(tokenized, dict) else None
    if token_status != 200 or not isinstance(tokens, list):
        raise DiagnosticError("exact_prompt_token_count_unavailable")
    state["token_count_method"] = "apply_template_plus_tokenize"
    return len(tokens)


def fake_assistant_tool_call(call_id: str, stage: str, count: int) -> dict[str, Any]:
    args = json.dumps({"stage": stage, "count": count}, separators=(",", ":"))
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": "record_sample", "arguments": args},
            }
        ],
    }


def prepare_stage_messages(
    base_messages: list[dict[str, Any]],
    *,
    base: str,
    context_size: int,
    target_tokens: int,
    stage: str,
    expected_count: int,
    seed: int,
    token_state: dict[str, str],
) -> tuple[list[dict[str, Any]], int]:
    if context_size not in (8192, 32768):
        raise DiagnosticError("unexpected_context_condition")

    def candidate(repetitions: int) -> list[dict[str, Any]]:
        messages = copy.deepcopy(base_messages)
        call_id = f"synthetic-history-{stage}"
        messages.append(fake_assistant_tool_call(call_id, "baseline", 0))
        observation = "Synthetic tool result only; executor invocation count remains zero. "
        if repetitions:
            observation += FILLER_UNIT * repetitions
        observation += (
            f" Next synthetic request: call record_sample with stage {stage!r} "
            f"and count {expected_count}. Do not perform any other action."
        )
        messages.append({"role": "user", "content": observation})
        return messages

    base_messages_count = count_input_tokens(
        base, request_body(candidate(0), seed), token_state
    )
    if base_messages_count >= target_tokens:
        raise DiagnosticError("base_history_exceeds_target")

    one_unit_count = count_input_tokens(
        base, request_body(candidate(1), seed), token_state
    )
    unit_tokens = max(1, one_unit_count - base_messages_count)
    repetitions = max(0, round((target_tokens - base_messages_count) / unit_tokens))
    best_messages: list[dict[str, Any]] | None = None
    best_count: int | None = None
    for _ in range(8):
        messages = candidate(repetitions)
        measured = count_input_tokens(base, request_body(messages, seed), token_state)
        if best_count is None or abs(measured - target_tokens) < abs(best_count - target_tokens):
            best_messages, best_count = messages, measured
        delta = target_tokens - measured
        if abs(delta) <= 64:
            break
        repetitions = max(0, repetitions + round(delta / unit_tokens))
    if best_messages is None or best_count is None or abs(best_count - target_tokens) > 256:
        raise DiagnosticError("history_target_not_reached")
    if best_count + OUTPUT_LIMIT + CONTEXT_MARGIN >= context_size:
        raise DiagnosticError("context_headroom_preflight_failed")
    return best_messages, best_count


def classify_response(response: Any, expected_stage: str, expected_count: int) -> tuple[str, dict[str, Any] | None]:
    if not isinstance(response, dict):
        return "response_not_object", None
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return "response_missing_choice", None
    message = choices[0].get("message")
    if not isinstance(message, dict):
        return "response_missing_message", None
    calls = message.get("tool_calls")
    if not isinstance(calls, list) or not calls:
        return "no_tool_call", message
    if len(calls) != 1:
        return "multiple_tool_calls", message
    call = calls[0]
    function = call.get("function") if isinstance(call, dict) else None
    if not isinstance(function, dict):
        return "malformed_tool_envelope", message
    if function.get("name") != "record_sample":
        return "wrong_tool_name", message
    raw_arguments = function.get("arguments")
    if not isinstance(raw_arguments, str):
        return "arguments_not_text", message
    try:
        arguments = json.loads(raw_arguments)
    except (TypeError, json.JSONDecodeError):
        return "invalid_json", message
    if not isinstance(arguments, dict):
        return "json_not_object", message
    if set(arguments) != {"stage", "count"}:
        return "schema_keys_invalid", message
    stage_value = arguments.get("stage")
    count_value = arguments.get("count")
    if (
        not isinstance(stage_value, str)
        or stage_value not in {"baseline", "sample", "followup", "long_history"}
        or isinstance(count_value, bool)
        or not isinstance(count_value, int)
        or not 0 <= count_value <= 3
    ):
        return "schema_values_invalid", message
    if stage_value != expected_stage or count_value != expected_count:
        return "schema_valid_request_mismatch", message
    return "schema_valid_request_match", message


def has_parseable_single_tool_arguments(response: Any) -> bool:
    """Return JSON syntax validity independent of tool name/schema validity."""
    try:
        calls = response["choices"][0]["message"]["tool_calls"]
        if not isinstance(calls, list) or len(calls) != 1:
            return False
        arguments = calls[0]["function"]["arguments"]
        if not isinstance(arguments, str):
            return False
        json.loads(arguments)
        return True
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return False


def assistant_message_only(message: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"role": "assistant", "content": message.get("content")}
    if isinstance(message.get("reasoning_content"), str):
        result["reasoning_content"] = message["reasoning_content"]
    if isinstance(message.get("tool_calls"), list):
        result["tool_calls"] = message["tool_calls"]
    return result


def gpu_memory_mib() -> tuple[int, int]:
    command = ["nvidia-smi"]
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "").strip()
    if visible:
        command.extend(["--id", visible.split(",", maxsplit=1)[0]])
    command.extend(
        ["--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"]
    )
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )
    first = result.stdout.splitlines()[0]
    used, total = (int(value.strip()) for value in first.split(",", maxsplit=1))
    return used, total


class MemoryMonitor:
    def __init__(self) -> None:
        self.stop_event = threading.Event()
        self.limit_event = threading.Event()
        self.monitor_failed = threading.Event()
        self.peak_used_mib = 0
        self.total_mib = 0
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=3)

    def _run(self) -> None:
        while not self.stop_event.is_set():
            try:
                used, total = gpu_memory_mib()
                self.peak_used_mib = max(self.peak_used_mib, used)
                self.total_mib = total
                if total - used < VRAM_HEADROOM_MIB:
                    self.limit_event.set()
                    return
            except Exception:
                # Fail closed: without telemetry we cannot enforce the VRAM
                # headroom stop rule.
                self.monitor_failed.set()
                self.limit_event.set()
                return
            self.stop_event.wait(1.0)


def get_json(base: str, route: str, timeout: float = 3.0) -> tuple[int, Any]:
    request = urllib.request.Request(base + route, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        return status, None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return 0, None


def start_server(context_size: int, out: Path, port: int, monitor: MemoryMonitor) -> tuple[subprocess.Popen[Any], float]:
    user = os.environ["USER"]
    model_path = MODEL_PATH.format(user=user)
    sif_path = SERVER_SIF.format(user=user)
    log_path = out / f"server-{context_size}.log"
    log_file = log_path.open("wb")
    command = [
        "apptainer",
        "exec",
        "--nv",
        "--containall",
        "--bind",
        f"/scratch/{user}/models:/models:ro",
        sif_path,
        "env",
        "LD_LIBRARY_PATH=/app:/usr/local/cuda/lib64:/.singularity.d/libs",
        "/app/llama-server",
        "-m",
        f"/models/{MODEL_FILE}",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "-c",
        str(context_size),
        "-np",
        "1",
        "-ngl",
        "999",
        "-t",
        "8",
        "-tb",
        "8",
        "--jinja",
        "--metrics",
        "--log-disable",
    ]
    started = time.monotonic()
    process = subprocess.Popen(command, stdout=log_file, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    for _ in range(180):
        if monitor.limit_event.is_set():
            process.terminate()
            raise DiagnosticError("vram_headroom_below_1gib_during_startup")
        if process.poll() is not None:
            raise DiagnosticError("model_server_exited_during_startup")
        status, _ = get_json(base, "/health")
        if status == 200:
            return process, round(time.monotonic() - started, 3)
        time.sleep(1)
    process.terminate()
    raise DiagnosticError("model_server_health_timeout")


def stop_server(process: subprocess.Popen[Any]) -> None:
    if process.poll() is None:
        process.send_signal(signal.SIGTERM)
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def verify_sha256(path: Path, expected: str, key: str) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected:
        raise DiagnosticError(f"{key}_sha256_mismatch")
    return actual


def cgroup_value(path: str) -> str | None:
    try:
        value = Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def run_context(context_size: int, port: int, out: Path, user: str) -> dict[str, Any]:
    monitor = MemoryMonitor()
    monitor.start()
    process: subprocess.Popen[Any] | None = None
    context_record: dict[str, Any] = {
        "context_tokens": context_size,
        "server_bind": "127.0.0.1",
        "parallel_slots": 1,
        "server_threads": 8,
        "status": "incomplete",
        "calls": [],
        "executor_invocations": 0,
    }
    try:
        process, startup_seconds = start_server(context_size, out, port, monitor)
        context_record["startup_seconds"] = startup_seconds
        used, total = gpu_memory_mib()
        context_record["gpu_memory_start_mib"] = used
        context_record["gpu_memory_total_mib"] = total
        if total - used < VRAM_HEADROOM_MIB:
            raise DiagnosticError("vram_headroom_below_1gib_after_startup")

        base = f"http://127.0.0.1:{port}"
        token_state: dict[str, str] = {}
        # Warm-up is deliberately unscored and the response is discarded.
        warm_body = request_body(
            [
                {"role": "system", "content": SYSTEM_TEXT},
                {"role": "user", "content": "Call record_sample with stage baseline and count 0."},
            ],
            SEED_ROOT,
        )
        warm_tokens = count_input_tokens(base, warm_body, token_state)
        if warm_tokens + OUTPUT_LIMIT + CONTEXT_MARGIN >= context_size:
            raise DiagnosticError("warmup_context_headroom_preflight_failed")
        if monitor.limit_event.is_set():
            raise DiagnosticError("vram_headroom_below_1gib_before_warmup")
        warm_status, warm_response, warm_context_error = post_inference(
            base, warm_body, monitor, process
        )
        if monitor.limit_event.is_set() or warm_status == -1:
            reason = "vram_monitor_failed" if monitor.monitor_failed.is_set() else "vram_headroom_below_1gib_during_warmup"
            raise DiagnosticError(reason)
        if warm_status != 200 or not isinstance(warm_response, dict):
            context_record["warmup_http_status"] = warm_status
            context_record["warmup_context_error_candidate"] = warm_context_error
            raise DiagnosticError("warmup_http_error")
        context_record["warmup_prompt_tokens"] = warm_tokens
        context_record["token_count_method"] = token_state.get("token_count_method")

        for repetition in range(REPETITIONS):
            seed_base = SEED_ROOT + repetition * 100
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": SYSTEM_TEXT},
                {
                    "role": "user",
                    "content": "Start a multi-turn synthetic conversation. No real task is present.",
                },
            ]
            stages = list(TARGETS)
            if context_size == 32768:
                stages.append(LONG_TARGET)
            repetition_ok = True
            for stage_index, (stage_name, target_tokens) in enumerate(stages):
                expected_stage = ("sample", "followup", "long_history")[stage_index]
                expected_count = stage_index + 1
                seed = seed_base + stage_index
                messages, measured_tokens = prepare_stage_messages(
                    messages,
                    base=base,
                    context_size=context_size,
                    target_tokens=target_tokens,
                    stage=expected_stage,
                    expected_count=expected_count,
                    seed=seed,
                    token_state=token_state,
                )
                if monitor.limit_event.is_set():
                    raise DiagnosticError("vram_headroom_below_1gib_during_requests")
                response_started = time.monotonic()
                status, result, context_error = post_inference(
                    base, request_body(messages, seed), monitor, process
                )
                wall_seconds = round(time.monotonic() - response_started, 3)
                record: dict[str, Any] = {
                    "repetition": repetition,
                    "stage": stage_name,
                    "planned_prompt_tokens": target_tokens,
                    "measured_prompt_tokens_before_generation": measured_tokens,
                    "http_status": status,
                    "context_error_candidate": context_error,
                    "wall_seconds": wall_seconds,
                }
                if monitor.limit_event.is_set() or status == -1:
                    record["outcome"] = "vram_headroom_stop"
                    context_record["calls"].append(record)
                    reason = "vram_monitor_failed" if monitor.monitor_failed.is_set() else "vram_headroom_below_1gib_during_inference"
                    raise DiagnosticError(reason)
                if status != 200 or not isinstance(result, dict):
                    record["outcome"] = "http_error"
                    context_record["calls"].append(record)
                    repetition_ok = False
                    if status == 400 and context_error:
                        context_record["status"] = "context_error"
                        context_record["stop_reason"] = "http_400_context_error_candidate"
                        health_status, _ = get_json(base, "/health")
                        used, total = gpu_memory_mib()
                        context_record["server_healthy_after_http400"] = health_status == 200
                        context_record["gpu_headroom_after_http400_mib"] = total - used
                        break
                    if status == 400:
                        context_record["status"] = "stopped"
                        context_record["stop_reason"] = "http_400_non_context_error"
                        break
                    if status != 400:
                        context_record["status"] = "stopped"
                        context_record["stop_reason"] = "server_or_transport_error"
                        break
                    break
                outcome, message = classify_response(result, expected_stage, expected_count)
                record["outcome"] = outcome
                record["parseable_single_tool_arguments"] = has_parseable_single_tool_arguments(result)
                choices = result.get("choices")
                if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                    finish_reason = choices[0].get("finish_reason")
                    if isinstance(finish_reason, str):
                        record["finish_reason"] = finish_reason
                    message_obj = choices[0].get("message")
                    tool_calls = message_obj.get("tool_calls") if isinstance(message_obj, dict) else None
                    record["tool_call_count"] = len(tool_calls) if isinstance(tool_calls, list) else 0
                usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}
                prompt_tokens = usage.get("prompt_tokens")
                completion_tokens = usage.get("completion_tokens")
                if isinstance(prompt_tokens, int):
                    record["prompt_tokens"] = prompt_tokens
                if isinstance(completion_tokens, int):
                    record["completion_tokens"] = completion_tokens
                timings = result.get("timings") if isinstance(result.get("timings"), dict) else {}
                prompt_ms = timings.get("prompt_ms")
                predicted_ms = timings.get("predicted_ms")
                if isinstance(prompt_tokens, int) and isinstance(prompt_ms, (int, float)) and prompt_ms > 0:
                    record["prompt_tokens_per_second"] = round(prompt_tokens * 1000 / prompt_ms, 2)
                if isinstance(completion_tokens, int) and isinstance(predicted_ms, (int, float)) and predicted_ms > 0:
                    record["completion_tokens_per_second"] = round(completion_tokens * 1000 / predicted_ms, 2)
                context_record["calls"].append(record)
                if outcome != "schema_valid_request_match" or not isinstance(message, dict):
                    repetition_ok = False
                    break

                # This synthetic tool result is fixture data only. No tool
                # executor exists in this script.
                messages.append(assistant_message_only(message))
                messages.append(
                    {
                        "role": "user",
                        "content": "Synthetic record_sample accepted. Executor invocation count remains zero.",
                    }
                )
            # Any invalid request ends that repetition; other predeclared
            # repetitions continue so the failure rate has a denominator.
            if not repetition_ok:
                if context_record.get("status") in {"stopped", "context_error"}:
                    break
                continue
        if context_record.get("status") == "incomplete":
            context_record["status"] = "completed"
    except DiagnosticError as exc:
        # These identifiers are fixed safe labels; exception text is never
        # copied from a server response or model output.
        context_record["status"] = "stopped"
        context_record["stop_reason"] = str(exc)
    finally:
        if process is not None:
            stop_server(process)
        monitor.stop()
        context_record["gpu_peak_used_mib"] = monitor.peak_used_mib
        context_record["gpu_memory_total_mib"] = monitor.total_mib or context_record.get("gpu_memory_total_mib")
    return context_record


def aggregate(contexts: list[dict[str, Any]]) -> dict[str, Any]:
    cells = {
        (8192, "shared_4k"), (8192, "shared_6_5k"),
        (32768, "shared_4k"), (32768, "shared_6_5k"), (32768, "long_24k"),
    }
    buckets: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    context_status = {item["context_tokens"]: item.get("status", "not_run") for item in contexts}
    for cell in cells:
        buckets[cell] = []
    for context in contexts:
        for call in context.get("calls", []):
            buckets[(context["context_tokens"], call["stage"])].append(call)
    summary: list[dict[str, Any]] = []
    def rate(numerator: int, denominator: int) -> float | None:
        return round(numerator / denominator, 4) if denominator else None

    for (context_size, stage), calls in sorted(buckets.items()):
        outcomes = Counter(call["outcome"] for call in calls)
        responses = [call for call in calls if call.get("http_status") == 200]
        exactly_one = sum(call.get("tool_call_count") == 1 for call in responses)
        single_tool_responses = [call for call in responses if call.get("tool_call_count") == 1]
        json_valid = sum(bool(call.get("parseable_single_tool_arguments")) for call in single_tool_responses)
        schema_valid = sum(call.get("outcome") in {
            "schema_valid_request_mismatch", "schema_valid_request_match"
        } for call in responses)
        def mean_metric(key: str) -> float | None:
            values = [call[key] for call in responses if isinstance(call.get(key), (int, float))]
            return round(sum(values) / len(values), 2) if values else None
        summary.append(
            {
                "context_tokens": context_size,
                "context_status": context_status.get(context_size, "not_run"),
                "history_condition": stage,
                "attempted_calls": len(calls),
                "planned_calls": REPETITIONS,
                "http_200_responses": len(responses),
                "outcomes": dict(sorted(outcomes.items())),
                "exactly_one_tool_calls": exactly_one,
                "exactly_one_tool_rate_among_http_200": rate(exactly_one, len(responses)),
                "parseable_single_tool_arguments": json_valid,
                "json_parse_rate_among_single_tool_calls": rate(json_valid, len(single_tool_responses)),
                "schema_valid_calls": schema_valid,
                "schema_valid_rate_among_http_200": rate(schema_valid, len(responses)),
                "request_match_calls": outcomes.get("schema_valid_request_match", 0),
                "request_match_rate_among_http_200": rate(outcomes.get("schema_valid_request_match", 0), len(responses)),
                "http_status_counts": dict(sorted(Counter(str(call.get("http_status")) for call in calls).items())),
                "context_error_candidate_count": sum(bool(call.get("context_error_candidate")) for call in calls),
                "mean_prompt_tokens": round(
                    sum(call.get("prompt_tokens", 0) for call in calls)
                    / max(1, sum("prompt_tokens" in call for call in calls)),
                    2,
                ),
                "mean_completion_tokens": round(
                    sum(call.get("completion_tokens", 0) for call in calls)
                    / max(1, sum("completion_tokens" in call for call in calls)),
                    2,
                ),
                "mean_prompt_tokens_per_second": mean_metric("prompt_tokens_per_second"),
                "mean_completion_tokens_per_second": mean_metric("completion_tokens_per_second"),
                "mean_wall_seconds": mean_metric("wall_seconds"),
            }
        )
    return {"conditions": summary}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--server-sif", type=Path, required=True)
    parser.add_argument("--protocol-file", type=Path, required=True)
    parser.add_argument("--job-id", default=os.environ.get("SLURM_JOB_ID", "unknown"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    model_hash = verify_sha256(args.model, MODEL_SHA256, "model")
    server_hash = verify_sha256(args.server_sif, SERVER_SIF_SHA256, "server_sif")
    host = socket.gethostname()
    initial_used, gpu_total = gpu_memory_mib()
    if gpu_total - initial_used < VRAM_HEADROOM_MIB:
        raise DiagnosticError("gpu_headroom_below_1gib_before_server_start")

    contexts = []
    for context_size in (8192, 32768):
        record = run_context(
            context_size,
            port=24000 + int(args.job_id[-4:]) % 20000 if args.job_id.isdigit() else 29000 + len(contexts),
            out=args.output_dir,
            user=os.environ["USER"],
        )
        contexts.append(record)
        if record.get("status") == "context_error":
            if not record.get("server_healthy_after_http400"):
                break
            if record.get("gpu_headroom_after_http400_mib", 0) < VRAM_HEADROOM_MIB:
                break
            continue
        if record.get("status") != "completed":
            break
        if context_size == 8192 and record.get("gpu_memory_total_mib", 0) - record.get("gpu_peak_used_mib", 0) < VRAM_HEADROOM_MIB:
            break

    output = {
        "experiment": "gpt-oss synthetic multi-turn tool-contract/context diagnostic",
        "slurm_job_id": args.job_id,
        "host": host,
        "model_file_sha256": model_hash,
        "server_sif_sha256": server_hash,
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(args.protocol_file.read_bytes()).hexdigest(),
        "experiment_commit": os.environ.get("AAS_DIAGNOSTIC_COMMIT", "unknown"),
        "contexts": contexts,
        **aggregate(contexts),
        "planned_repetitions": REPETITIONS,
        "tool_executor_invocations": 0,
        "task_or_benchmark_data_used": False,
        "raw_prompts_completions_and_arguments_retained": False,
        "tripwire_flags": [],
        "slurm_allocated_cpus": os.environ.get("SLURM_CPUS_PER_TASK"),
        "slurm_memory_per_node": os.environ.get("SLURM_MEM_PER_NODE"),
        "cgroup_cpu_max": cgroup_value("/sys/fs/cgroup/cpu.max"),
        "cgroup_memory_max": cgroup_value("/sys/fs/cgroup/memory.max"),
        "cgroup_cpuset": cgroup_value("/sys/fs/cgroup/cpuset.cpus.effective"),
        "gpu_initial_used_mib": initial_used,
        "gpu_total_mib": gpu_total,
    }
    output_path = args.output_dir / "results.json"
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    safe_summary = {
        "slurm_job_id": args.job_id,
        "model_sha256_verified": model_hash,
        "server_sif_sha256_verified": server_hash,
        "conditions": output["conditions"],
        "executor_invocations": 0,
        "task_or_benchmark_data_used": False,
    }
    print(json.dumps(safe_summary, sort_keys=True), flush=True)
    accepted_statuses = {"completed", "context_error"}
    return 0 if contexts and all(item.get("status") in accepted_statuses for item in contexts) else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DiagnosticError as exc:
        print(json.dumps({"status": "stopped", "reason": str(exc), "inference_output_logged": False}), flush=True)
        raise SystemExit(2)
    except Exception as exc:
        # Do not surface exception messages, request bodies, or local paths.
        print(
            json.dumps(
                {
                    "status": "unexpected_error",
                    "error_type": type(exc).__name__,
                    "inference_output_logged": False,
                }
            ),
            flush=True,
        )
        raise SystemExit(2)
