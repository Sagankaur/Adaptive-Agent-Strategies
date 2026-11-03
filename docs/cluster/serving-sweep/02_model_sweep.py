#!/usr/bin/env python3
"""No-task llama.cpp serving characterization for the A2I2 Slurm cluster.

This runner screens model/server fit and synthetic request throughput only. It
never loads benchmark tasks or computes benchmark rewards.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODEL_SHA256 = "ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61"
MODEL_FILENAME = "Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"
TOKENS_PER_KIB = 1024
HEADROOM_REQUIRED_MIB = 1024
KV_TYPE_BYTES = {"q8_0": 1, "f16": 2}
SYNTHETIC_BLOCK = (
    "User request: inspect a fictional workspace and make a small change.\n"
    "Assistant: I will inspect the files, check the available tools, and plan a bounded edit.\n"
    "Tool call: cat /workspace/README.md\n"
    "Tool output: The fictional project contains a parser, a unit test, and a short build note.\n"
    "Assistant: The parser owns the requested behavior; I will change that file and run the visible check.\n"
    "Tool call: git status --short\n"
    "Tool output: M src/parser.py; no other files changed.\n"
)


class GracefulStop(Exception):
    """Raised on a Slurm warning signal so the active server can be stopped."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False))
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(command: list[str], timeout_s: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=timeout_s, check=False)


def apptainer_base_command(server_image: Path, model_dir: Path) -> list[str]:
    return [
        "apptainer", "exec", "--nv", "--containall", "--bind",
        f"{model_dir}:/models:ro", str(server_image),
    ]


def check_binary_capabilities(server_image: Path, model_dir: Path, output_dir: Path) -> str:
    command = apptainer_base_command(server_image, model_dir) + ["/app/llama-server", "--help"]
    result = run_command(command, timeout_s=90)
    help_path = output_dir / "llama-server-help.txt"
    help_path.write_text(result.stdout, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"pinned llama-server --help failed (exit {result.returncode}); see {help_path}")
    required = ["--ctx-size", "--parallel", "--cache-type-k", "--cache-type-v", "--metrics", "--jinja"]
    missing = [flag for flag in required if flag not in result.stdout]
    if missing:
        raise RuntimeError(f"pinned b11515 binary lacks required flags {missing}; see {help_path}")
    return result.stdout


def allocated_gpu_uuid() -> str:
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "").strip()
    devices = [device.strip() for device in visible.split(",") if device.strip()]
    if len(devices) != 1:
        raise RuntimeError(
            "expected Slurm to expose exactly one GPU in CUDA_VISIBLE_DEVICES; "
            f"got {visible!r}. Refusing to attribute VRAM to an ambiguous device."
        )
    rows = run_command([
        "nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader,nounits",
    ])
    if rows.returncode != 0:
        raise RuntimeError(f"nvidia-smi GPU mapping query failed: {rows.stdout.strip()}")
    for row in csv.reader(rows.stdout.splitlines(), skipinitialspace=True):
        if len(row) < 2:
            continue
        index, uuid = row[0].strip(), row[1].strip()
        if devices[0] in (index, uuid):
            return uuid
    raise RuntimeError(
        f"could not map CUDA_VISIBLE_DEVICES={devices[0]!r} to a physical GPU UUID; "
        "MIG identifiers and ambiguous mappings are rejected"
    )


def gpu_identity(gpu_uuid: str) -> dict[str, Any]:
    result = run_command([
        "nvidia-smi", f"--id={gpu_uuid}",
        "--query-gpu=name,memory.total,driver_version,uuid",
        "--format=csv,noheader,nounits",
    ])
    if result.returncode != 0:
        raise RuntimeError(f"nvidia-smi identity query failed: {result.stdout.strip()}")
    rows = list(csv.reader(result.stdout.splitlines(), skipinitialspace=True))
    if not rows:
        raise RuntimeError("nvidia-smi returned no GPU rows")
    row = rows[0]
    return {
        "name": row[0].strip(),
        "memory_total_mib": int(row[1].strip()),
        "driver_version": row[2].strip() if len(row) > 2 else None,
        "uuid": row[3].strip() if len(row) > 3 else gpu_uuid,
    }


class MemorySampler:
    def __init__(self, csv_path: Path, config_id: str, gpu_uuid: str,
                 interval_s: float = 1.0) -> None:
        self.csv_path = csv_path
        self.config_id = config_id
        self.gpu_uuid = gpu_uuid
        self.interval_s = interval_s
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.samples: list[dict[str, Any]] = []
        self.lock = threading.Lock()

    def start(self) -> None:
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.csv_path.exists():
            with self.csv_path.open("w", newline="", encoding="utf-8") as stream:
                csv.writer(stream).writerow([
                    "config_id", "timestamp", "memory_used_mib", "memory_total_mib", "gpu_util_percent"
                ])
        self.thread = threading.Thread(target=self._sample, name=f"gpu-memory-{self.config_id}", daemon=True)
        self.thread.start()

    def _sample(self) -> None:
        while not self.stop_event.is_set():
            result = run_command([
                "nvidia-smi", f"--id={self.gpu_uuid}",
                "--query-gpu=timestamp,memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",
            ], timeout_s=10)
            if result.returncode == 0:
                parsed = list(csv.reader(result.stdout.splitlines(), skipinitialspace=True))
                if parsed:
                    row = parsed[0]
                    try:
                        sample = {
                            "timestamp": row[0].strip(),
                            "memory_used_mib": int(row[1].strip()),
                            "memory_total_mib": int(row[2].strip()),
                            "gpu_util_percent": int(row[3].strip()),
                        }
                        with self.lock:
                            self.samples.append(sample)
                        with self.csv_path.open("a", newline="", encoding="utf-8") as stream:
                            csv.writer(stream).writerow([
                                self.config_id, sample["timestamp"], sample["memory_used_mib"],
                                sample["memory_total_mib"], sample["gpu_util_percent"],
                            ])
                            stream.flush()
                    except (IndexError, ValueError):
                        pass
            self.stop_event.wait(self.interval_s)

    def stop(self) -> dict[str, Any]:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=12)
        with self.lock:
            samples = list(self.samples)
        if not samples:
            return {
                "sample_interval_s": self.interval_s,
                "sample_count": 0,
                "peak_used_mib": None,
                "minimum_headroom_mib": None,
                "headroom_pass": False,
            }
        peak = max(row["memory_used_mib"] for row in samples)
        total = max(row["memory_total_mib"] for row in samples)
        headroom = total - peak
        return {
            "sample_interval_s": self.interval_s,
            "sample_count": len(samples),
            "peak_used_mib": peak,
            "memory_total_mib": total,
            "minimum_headroom_mib": headroom,
            "headroom_required_mib": HEADROOM_REQUIRED_MIB,
            "headroom_pass": headroom >= HEADROOM_REQUIRED_MIB,
        }


class LlamaClient:
    def __init__(self, base_url: str, timeout_s: int = 600) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {} if data is None else {"Content-Type": "application/json"}
        request = urllib.request.Request(self.base_url + path, data=data, headers=headers)
        with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
            return json.loads(response.read().decode("utf-8"))

    def tokenize(self, content: str) -> list[int]:
        response = self.request("/tokenize", {
            "content": content,
            "add_special": True,
            "parse_special": False,
            "with_pieces": False,
        })
        tokens = response.get("tokens")
        if not isinstance(tokens, list) or not tokens or not all(isinstance(token, int) for token in tokens):
            raise RuntimeError("pinned /tokenize response did not return a non-empty integer token array")
        return tokens


def exact_prompt_tokens(client: LlamaClient, target_tokens: int) -> list[int]:
    content = SYNTHETIC_BLOCK
    tokens: list[int] = []
    while len(tokens) < target_tokens:
        tokens = client.tokenize(content)
        if len(tokens) >= target_tokens:
            break
        content += content
        if len(content) > target_tokens * 256:
            raise RuntimeError(f"could not construct {target_tokens} tokens from synthetic history")
    exact = tokens[:target_tokens]
    if len(exact) != target_tokens:
        raise RuntimeError("tokenizer did not produce the requested exact input length")
    return exact


def post_completion(client: LlamaClient, prompt_tokens: list[int], n_predict: int,
                    seed: int, slot_id: int) -> dict[str, Any]:
    request_started = time.perf_counter()
    request_wall_start = time.time()
    try:
        response = client.request("/completion", {
            "prompt": prompt_tokens,
            "n_predict": n_predict,
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "seed": seed,
            "id_slot": slot_id,
            "cache_prompt": False,
            "timings_per_token": True,
            "stream": False,
        })
        timings = response.get("timings")
        if not isinstance(timings, dict):
            raise RuntimeError("pinned /completion response has no timings object")
        needed = ["prompt_n", "prompt_ms", "predicted_n", "predicted_ms"]
        missing = [key for key in needed if key not in timings]
        if missing:
            raise RuntimeError(f"pinned /completion timing fields missing: {missing}")
        actual_prompt_n = int(timings["prompt_n"]) + int(timings.get("cache_n", 0))
        if abs(actual_prompt_n - len(prompt_tokens)) > 1:
            raise RuntimeError(
                f"server processed {actual_prompt_n} prompt tokens; sent {len(prompt_tokens)} exact IDs"
            )
        return {
            "ok": True,
            "seed": seed,
            "slot_id": slot_id,
            "requested_prompt_tokens": len(prompt_tokens),
            "requested_output_cap": n_predict,
            "prompt_n": int(timings["prompt_n"]),
            "cache_n": int(timings.get("cache_n", 0)),
            "prompt_ms": float(timings["prompt_ms"]),
            "predicted_n": int(timings["predicted_n"]),
            "predicted_ms": float(timings["predicted_ms"]),
            "prompt_tokens_evaluated": actual_prompt_n,
            "total_context_tokens": actual_prompt_n + int(timings["predicted_n"]),
            "context_truncated": response.get("truncated"),
            "stop_type": response.get("stop_type"),
            "client_wall_s": time.perf_counter() - request_started,
            "client_start_unix_s": request_wall_start,
            "client_end_unix_s": time.time(),
            "prompt_tokens_per_second": (
                1000.0 * int(timings["prompt_n"]) / float(timings["prompt_ms"])
                if float(timings["prompt_ms"]) > 0 else None
            ),
            "generated_tokens_per_second": (
                1000.0 * int(timings["predicted_n"]) / float(timings["predicted_ms"])
                if float(timings["predicted_ms"]) > 0 else None
            ),
        }
    except (OSError, urllib.error.URLError, TimeoutError, ValueError, RuntimeError) as exc:
        return {
            "ok": False,
            "seed": seed,
            "slot_id": slot_id,
            "requested_prompt_tokens": len(prompt_tokens),
            "requested_output_cap": n_predict,
            "client_wall_s": time.perf_counter() - request_started,
            "error": f"{type(exc).__name__}: {exc}",
        }


def run_concurrent_batch(client: LlamaClient, prompts: list[list[int]], n_predict: int,
                         seed_base: int, repetition: int, purpose: str) -> dict[str, Any]:
    slots = len(prompts)
    barrier = threading.Barrier(slots)
    batch_start = time.perf_counter()

    def one_call(slot_id: int) -> dict[str, Any]:
        barrier.wait(timeout=120)
        return post_completion(client, prompts[slot_id], n_predict,
                               seed_base + repetition * 100 + slot_id, slot_id)

    calls: list[dict[str, Any]] = []
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=slots) as pool:
            futures = [pool.submit(one_call, index) for index in range(slots)]
            for future in concurrent.futures.as_completed(futures):
                calls.append(future.result())
    except Exception as exc:
        calls.append({"ok": False, "error": f"batch error: {type(exc).__name__}: {exc}"})
    batch_wall_s = max(0.0, time.perf_counter() - batch_start)
    good_calls = [call for call in calls if call.get("ok")]
    prompt_tokens = sum(call.get("prompt_n", 0) for call in good_calls)
    generated_tokens = sum(call.get("predicted_n", 0) for call in good_calls)
    total_tokens = prompt_tokens + sum(call.get("cache_n", 0) for call in good_calls) + generated_tokens
    return {
        "record_type": "batch",
        "purpose": purpose,
        "repetition": repetition,
        "slots": slots,
        "requested_output_cap": n_predict,
        "batch_wall_s": batch_wall_s,
        "successful_calls": len(good_calls),
        "failed_calls": len(calls) - len(good_calls),
        "aggregate_prompt_tokens": prompt_tokens,
        "aggregate_generated_tokens": generated_tokens,
        "aggregate_total_context_tokens": total_tokens,
        "aggregate_prompt_tokens_per_s": prompt_tokens / batch_wall_s if batch_wall_s else None,
        "aggregate_generated_tokens_per_s": generated_tokens / batch_wall_s if batch_wall_s else None,
        "aggregate_all_tokens_per_s": total_tokens / batch_wall_s if batch_wall_s else None,
        "calls": calls,
    }


def choose_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class ServerRun:
    def __init__(self, config: dict[str, Any], args: argparse.Namespace, output_dir: Path,
                 config_id: str, sampler: MemorySampler) -> None:
        self.config = config
        self.args = args
        self.output_dir = output_dir
        self.config_id = config_id
        self.sampler = sampler
        self.process: subprocess.Popen[bytes] | None = None
        self.log_path = output_dir / f"server-{config_id}.log"
        self.log_stream: Any = None
        self.client: LlamaClient | None = None
        self.startup_s: float | None = None
        self.port = choose_port()

    def start(self) -> None:
        total_context = int(self.config["slots"]) * int(self.config["context_per_slot"])
        command = apptainer_base_command(self.args.server_image, self.args.model.parent) + [
            "env", "LD_LIBRARY_PATH=/app:/usr/local/cuda/lib64:/.singularity.d/libs",
            "/app/llama-server", "-m", f"/models/{self.args.model.name}",
            "--host", "127.0.0.1", "--port", str(self.port),
            "-c", str(total_context), "-np", str(self.config["slots"]),
            "-ctk", str(self.config["kv_type"]), "-ctv", str(self.config["kv_type"]),
            "-ngl", "999", "--jinja", "--metrics",
        ]
        self.log_stream = self.log_path.open("wb")
        self.process = subprocess.Popen(command, stdout=self.log_stream, stderr=subprocess.STDOUT)
        self.client = LlamaClient(f"http://127.0.0.1:{self.port}", timeout_s=self.args.request_timeout_s)
        started = time.perf_counter()
        deadline = started + self.args.startup_timeout_s
        while time.perf_counter() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(f"llama-server exited with status {self.process.returncode}; see {self.log_path}")
            try:
                self.client.request("/health", payload=None)
                self.startup_s = time.perf_counter() - started
                return
            except (OSError, urllib.error.URLError, TimeoutError, ValueError):
                time.sleep(1.0)
        raise TimeoutError(f"llama-server did not become healthy in {self.args.startup_timeout_s}s; see {self.log_path}")

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)
        if self.log_stream is not None:
            self.log_stream.close()


def screen_configs() -> list[dict[str, Any]]:
    rows = [
        {"slots": slots, "kv_type": kv, "context_per_slot": context}
        for slots in (1, 2, 4)
        for kv in ("q8_0", "f16")
        for context in (65536, 98304)
    ]
    return sorted(rows, key=lambda row: (
        row["slots"] * row["context_per_slot"] * KV_TYPE_BYTES[row["kv_type"]],
        row["slots"], row["context_per_slot"], row["kv_type"],
    ))


def run_one_configuration(config: dict[str, Any], config_index: int, args: argparse.Namespace,
                          output_dir: Path, jsonl_path: Path, metadata: dict[str, Any],
                          run_deadline: float, measure: bool, gpu_uuid: str) -> dict[str, Any]:
    config_id = f"s{config['slots']}-{config['kv_type']}-ctx{config['context_per_slot']}-i{config_index:02d}"
    start_record = {
        "record_type": "config_started",
        "timestamp_utc": utc_now(),
        "config_id": config_id,
        "mode": args.mode,
        "config": config,
        "total_context_pool_tokens": config["slots"] * config["context_per_slot"],
        "server_flags": ["-c", str(config["slots"] * config["context_per_slot"]),
                         "-np", str(config["slots"]), "-ctk", config["kv_type"],
                         "-ctv", config["kv_type"], "-ngl", "999", "--jinja", "--metrics"],
        "metadata": metadata,
    }
    append_jsonl(jsonl_path, start_record)
    remaining_s = run_deadline - time.monotonic()
    if remaining_s < 300:
        final = {"record_type": "config_finished", "timestamp_utc": utc_now(),
                 "config_id": config_id, "status": "skipped_time_budget", "reason": "less than 300s remain"}
        append_jsonl(jsonl_path, final)
        return final

    sampler = MemorySampler(output_dir / "gpu-memory.csv", config_id, gpu_uuid)
    sampler.start()
    server = ServerRun(config, args, output_dir, config_id, sampler)
    batch_records: list[dict[str, Any]] = []
    status = "failed_startup"
    error: str | None = None
    startup_s: float | None = None
    props: dict[str, Any] | None = None
    try:
        server.start()
        startup_s = server.startup_s
        assert server.client is not None
        try:
            props = server.client.request("/props")
        except Exception:
            props = None
        slots = server.client.request("/slots")
        if not isinstance(slots, list) or len(slots) != int(config["slots"]):
            raise RuntimeError(
                f"/slots reported {len(slots) if isinstance(slots, list) else type(slots).__name__}; "
                f"requested {config['slots']} slots"
            )
        effective_contexts = [int(slot.get("n_ctx", -1)) for slot in slots if isinstance(slot, dict)]
        if len(effective_contexts) != int(config["slots"]) or any(
            context != int(config["context_per_slot"]) for context in effective_contexts
        ):
            raise RuntimeError(
                f"effective per-slot contexts {effective_contexts} do not match "
                f"requested {config['context_per_slot']}"
            )
        if measure:
            warmup_prompt = exact_prompt_tokens(server.client, min(1024, config["context_per_slot"] - 512))
            warmup = run_concurrent_batch(
                server.client, [warmup_prompt] * config["slots"], 128,
                args.seed_base + config_index * 100000, 0, "warmup",
            )
            warmup["config_id"] = config_id
            batch_records.append(warmup)
            append_jsonl(jsonl_path, warmup)
            batches = measured_batches(server.client, config, args, config_id, config_index)
            batch_records.extend(batches)
            for batch in batches:
                append_jsonl(jsonl_path, batch)
            status = "measured" if all(batch["failed_calls"] == 0 for batch in batches) else "measured_with_errors"
        else:
            prompt = exact_prompt_tokens(server.client, min(8192, config["context_per_slot"] - 256))
            batch = run_concurrent_batch(
                server.client, [prompt] * config["slots"], 128,
                args.seed_base + config_index * 100000, 1, "fit_screen",
            )
            batch["config_id"] = config_id
            batch_records.append(batch)
            append_jsonl(jsonl_path, batch)
            status = "fit_probe_passed" if batch["failed_calls"] == 0 else "fit_probe_failed"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        if isinstance(exc, GracefulStop):
            status = "interrupted"
    finally:
        server.stop()
        memory = sampler.stop()

    headroom_pass = memory.get("headroom_pass", False)
    if status == "fit_probe_passed" and not headroom_pass:
        status = "headroom_failed"
    elif status == "measured" and not headroom_pass:
        status = "measured_headroom_failed"
    final = {
        "record_type": "config_finished",
        "timestamp_utc": utc_now(),
        "config_id": config_id,
        "mode": args.mode,
        "status": status,
        "error": error,
        "startup_seconds": startup_s,
        "gpu_memory": memory,
        "server_log": str(server.log_path),
        "server_props": props,
        "effective_context_per_slot": effective_contexts if "effective_contexts" in locals() else None,
        "effective_slot_count": len(slots) if "slots" in locals() and isinstance(slots, list) else None,
        "batch_count": len(batch_records),
        "config": config,
    }
    append_jsonl(jsonl_path, final)
    return final


def measured_batches(client: LlamaClient, config: dict[str, Any], args: argparse.Namespace,
                     config_id: str, config_index: int) -> list[dict[str, Any]]:
    context = int(config["context_per_slot"])
    prompt_lengths: set[int] = set()
    for output_cap in (512, 2048):
        near_limit = context - output_cap - 128
        for target in (8192, 32768, 65536, near_limit):
            if target >= 8192 and target + output_cap + 128 <= context:
                prompt_lengths.add(target)
    results: list[dict[str, Any]] = []
    token_cache: dict[int, list[int]] = {}
    for prompt_length in sorted(prompt_lengths):
        token_cache[prompt_length] = exact_prompt_tokens(client, prompt_length)
    for output_cap in (512, 2048):
        valid_lengths = [
            length for length in sorted(prompt_lengths)
            if length + output_cap + 128 <= context
        ]
        for prompt_length in valid_lengths:
            prompts = [token_cache[prompt_length]] * config["slots"]
            for repetition in range(1, args.repetitions + 1):
                record = run_concurrent_batch(
                    client, prompts, output_cap,
                    args.seed_base + config_index * 100000 + prompt_length * 2 + output_cap,
                    repetition, "measured",
                )
                record.update({
                    "config_id": config_id,
                    "prompt_target_tokens": prompt_length,
                    "output_cap_tokens": output_cap,
                    "per_slot_context_tokens": context,
                    "repetition": repetition,
                })
                results.append(record)
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("screen", "measure"), required=True)
    parser.add_argument("--server-image", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--gpu-label", default="unspecified")
    parser.add_argument("--slots", type=int, choices=(1, 2, 4))
    parser.add_argument("--kv-type", choices=("f16", "q8_0"))
    parser.add_argument("--context-per-slot", type=int, choices=(65536, 98304))
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--seed-base", type=int, default=20261103)
    parser.add_argument("--startup-timeout-s", type=int, default=180)
    parser.add_argument("--request-timeout-s", type=int, default=900)
    parser.add_argument("--run-budget-s", type=int, default=3300)
    args = parser.parse_args()
    if args.mode == "measure" and (args.slots is None or args.kv_type is None or args.context_per_slot is None):
        parser.error("measure mode requires --slots, --kv-type, and --context-per-slot")
    if args.repetitions < 1 or args.repetitions > 5:
        parser.error("--repetitions must be between 1 and 5")
    return args


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / ("screen.jsonl" if args.mode == "screen" else "measure.jsonl")
    args.model = args.model.resolve()
    args.server_image = args.server_image.resolve()
    append_jsonl(jsonl_path, {
        "record_type": "run_preflight_started",
        "timestamp_utc": utc_now(),
        "mode": args.mode,
        "model_path": str(args.model),
        "server_image_path": str(args.server_image),
        "task_data_used": False,
        "benchmark_episodes": 0,
    })
    try:
        if args.model.name != MODEL_FILENAME:
            raise RuntimeError(f"unexpected model filename: {args.model.name}")
        for required_path in (args.model, args.server_image):
            if not required_path.is_file():
                raise RuntimeError(f"required file is missing: {required_path}")

        model_hash = sha256_file(args.model)
        if model_hash != MODEL_SHA256:
            raise RuntimeError(f"model SHA-256 mismatch: expected {MODEL_SHA256}, got {model_hash}")
        image_hash = sha256_file(args.server_image)
        gpu_uuid = allocated_gpu_uuid()
        gpu = gpu_identity(gpu_uuid)
        help_text = check_binary_capabilities(args.server_image, args.model.parent, output_dir)
    except Exception as exc:
        append_jsonl(jsonl_path, {
            "record_type": "run_preflight_failed",
            "timestamp_utc": utc_now(),
            "mode": args.mode,
            "error": f"{type(exc).__name__}: {exc}",
        })
        raise
    metadata = {
        "timestamp_utc": utc_now(),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "host": os.uname().nodename,
        "gpu_label_requested": args.gpu_label,
        "gpu": gpu,
        "model_path": str(args.model),
        "model_sha256": model_hash,
        "server_image_path": str(args.server_image),
        "server_image_sha256": image_hash,
        "server_image_reference": "ghcr.io/ggml-org/llama.cpp:server-cuda12-b11515 (existing cluster SIF)",
        "sampling": {"temperature": 0.6, "top_p": 0.95, "top_k": 20},
        "server_help_sha256": hashlib.sha256(help_text.encode("utf-8")).hexdigest(),
        "task_data_used": False,
        "benchmark_episodes": 0,
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    append_jsonl(jsonl_path, {"record_type": "run_started", **metadata, "mode": args.mode})
    run_deadline = time.monotonic() + args.run_budget_s

    if args.mode == "screen":
        configs = screen_configs()
    else:
        configs = [{"slots": args.slots, "kv_type": args.kv_type,
                    "context_per_slot": args.context_per_slot}]

    summaries: list[dict[str, Any]] = []
    for index, config in enumerate(configs, start=1):
        if time.monotonic() >= run_deadline - 300:
            append_jsonl(jsonl_path, {
                "record_type": "run_stopped_for_time_budget",
                "timestamp_utc": utc_now(),
                "completed_configurations": len(summaries),
                "remaining_configurations": len(configs) - len(summaries),
            })
            break
        summary = run_one_configuration(
            config, index, args, output_dir, jsonl_path, metadata, run_deadline,
            measure=args.mode == "measure", gpu_uuid=gpu_uuid,
        )
        summaries.append(summary)
        if summary.get("status") == "interrupted":
            break
    summary = {
        "record_type": "run_finished",
        "timestamp_utc": utc_now(),
        "mode": args.mode,
        "configurations_recorded": len(summaries),
        "statuses": [row.get("status") for row in summaries],
        "result_file": str(jsonl_path),
        "metadata_file": str(output_dir / "metadata.json"),
    }
    append_jsonl(jsonl_path, summary)
    print(json.dumps(summary, sort_keys=True))
    failures = {
        "failed_startup", "fit_probe_failed", "headroom_failed", "measured_headroom_failed",
        "measured_with_errors", "interrupted",
    }
    return 0 if all(row.get("status") not in failures for row in summaries) else 2


if __name__ == "__main__":
    def stop_on_slurm_signal(signum: int, _frame: Any) -> None:
        raise GracefulStop(f"received signal {signum}")

    signal.signal(signal.SIGTERM, stop_on_slurm_signal)
    signal.signal(signal.SIGINT, stop_on_slurm_signal)
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted; completed JSONL records are retained.", file=sys.stderr)
        raise SystemExit(130)
