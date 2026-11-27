"""AMENDED (v2) bounded, task-free S0/HarborStrategyAgent history check.

Protocol: docs/experiments/s0-history-check-v2-protocol-2026-11.md (frozen before any run).

Same safety design as the original check (04_harbor_s0_history_check.py, imported, not
modified): the real S0 agent loop and model client run against a mock environment that
discards every command. No command executor, Harbor trial, benchmark task or verifier is
created. Only aggregate labels, counts, token numbers and hashes are ever written.

Amendments relative to v1 (see the protocol for rationale):
  (a) per-request ORDER of categories, finish_reason, completion/reasoning token counts;
  (b) long condition = larger counter-based synthetic terminal outputs, so history grows
      over turns (S0 is untouched; outputs stay below S0 max_observation_chars);
  (c) server context 32768 (guard arithmetic unchanged), request ceiling 12;
  (d) explicit recovery record after every no_tool_call;
  (g) v2-specific instruction (four terminal calls) so conversations have several turns;
  (e) paired identical seeds, identical first request, 4 pairs with balanced order;
  (f) a validity gate that can mark the whole run INVALID.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import logging
import os
import re
import statistics
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

_HERE = Path(__file__).resolve().parent
_V1_PATH = _HERE / "04_harbor_s0_history_check.py"


def _load_v1() -> Any:
    """Import the original runner by path (its module name starts with a digit)."""
    name = "_aas_s0_history_check_v1"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _V1_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("v1_runner_unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # required: the v1 module defines a dataclass
    spec.loader.exec_module(module)
    return module


_V1 = _load_v1()
_TOOLS = _V1._TOOLS
HarborStrategyAgent = _V1.HarborStrategyAgent
s0 = _V1.s0
ContextGuardStop = _V1.ContextGuardStop
RequestCeilingStop = _V1.RequestCeilingStop
ProbeInvariantStop = _V1.ProbeInvariantStop
MemoryMonitor = _V1.MemoryMonitor
check_tool_call = _V1.check_tool_call
prompt_tokens = _V1.prompt_tokens
safe_response_category = _V1._safe_response_category
MODEL = _V1.MODEL
CONTEXT_MARGIN = _V1.CONTEXT_MARGIN
OUTPUT_CAP = _V1.OUTPUT_CAP
VRAM_HEADROOM_MIB = _V1.VRAM_HEADROOM_MIB
V1_INSTRUCTION = _V1.S0_INSTRUCTION  # the v1 task-free instruction (kept only to record its hash)
# v2-specific task-free instruction (amendment g). S0's system prompt/strategy are NOT modified;
# only the user instruction passed to agent.run differs, so conversations contain several turns.
V2_INSTRUCTION = (
    "This is a task-free interface check. Make exactly four terminal calls, each describing a "
    "different harmless synthetic action, then submit a brief completion. Do not access "
    "files, tests, credentials, networks, or external resources."
)
S0_INSTRUCTION = V2_INSTRUCTION
SafeDiagnosticError = _V1._DIAG_MODULE.SafeDiagnosticError
FILLER = _V1.FILLER

# ---- frozen v2 constants -------------------------------------------------------------
CONTEXT_LIMIT = 32768  # amendment (c); must equal the server's -c (checked in the sbatch)
REQUEST_CEILING = 12  # amendment (c)
PAIRS = 4  # amendment (e): order alternates short-first/long-first 2/2
CONDITIONS = ("short", "long")
SEED_ROOT = 20261127
README_REPEATS = 10  # identical README in BOTH conditions -> identical first request
LONG_OBSERVATION_CHARS = 3600  # < S0 max_observation_chars (4000): never truncated
S0_MAX_OBSERVATION_CHARS = 4000  # asserted against S0 at run time, never edited
GROWTH_MIN_TERMINAL_DELTAS = 8  # per condition (4 conversations x up to 4 terminal turns each)
GROWTH_MIN_DIFF_TOKENS = 400  # median per-terminal-turn prompt growth, long minus short
ALLOWED_PROCESS_NAMES = frozenset({"nvidia-smi"})
FORBIDDEN_KEYS = frozenset({
    "content", "prompt", "completion", "command", "commands", "reasoning", "arguments",
    "messages", "observation", "answer", "text",
})
MAX_STRING_LEAF = 64
FINISH_REASONS = frozenset({"stop", "length", "tool_calls", "function_call", "content_filter"})
VALID_CATEGORIES = frozenset({"valid_schema_A", "valid_schema_B"})
KNOWN_CATEGORIES = frozenset({
    "no_tool_call", "multiple_tool_calls", "wrong_tool_name", "invalid_json",
    "json_not_object", "invalid_schema", "valid_schema_A", "valid_schema_B",
})
SAFE_STEP_ACTIONS = frozenset({
    "terminal", "submit", "invalid", "model_error", "terminal_error",
    "token_limit", "step_limit", "verify_failed", "verify",
    "probe:list_workdir", "probe:read_readme", "probe:check_toolchain_versions",
    "probe:check_installed_packages", "probe:check_services", "probe:git_status",
})
HARBOR_RUNTIME_MODULE = re.compile(r"trial|verifier|orchestrat|docker|environments", re.IGNORECASE)


# ---- amendment (b): counter-based inert synthetic terminal outputs -------------------
def synthetic_terminal_output(condition: str, call_number: int) -> str:
    """Return a fixed, inert string determined only by (condition, call_number).

    Different for every call (counter-based) so the history is not one repeated blob.
    Contains no real data: record ids and digests are derived from the counters alone.
    """
    if condition == "short":
        return (
            f"Synthetic terminal result {call_number:02d}; "
            "no command was executed and no state exists.\n"
        )
    if condition != "long":
        raise ValueError("unknown condition")
    lines = [f"Synthetic terminal result {call_number:02d}; inert listing, no command was executed.\n"]
    total = len(lines[0])
    index = 0
    while True:
        digest = hashlib.sha256(f"{call_number}:{index}".encode()).hexdigest()[:16]
        line = f"synthetic-record {call_number:02d}-{index:03d} state=inert digest={digest}\n"
        if total + len(line) > LONG_OBSERVATION_CHARS:
            break
        lines.append(line)
        total += len(line)
        index += 1
    return "".join(lines)


def validate_synthetic_outputs(ceiling: int = REQUEST_CEILING) -> dict[str, Any]:
    """Offline construction checks: distinct per call, long > short, below S0 truncation."""
    out: dict[str, Any] = {}
    for condition in CONDITIONS:
        texts = [synthetic_terminal_output(condition, n) for n in range(1, ceiling + 1)]
        if len(set(texts)) != len(texts):
            raise RuntimeError("synthetic_outputs_not_distinct")
        if max(len(t) for t in texts) > S0_MAX_OBSERVATION_CHARS:
            raise RuntimeError("synthetic_output_exceeds_s0_truncation")
        out[condition] = {
            "min_chars": min(len(t) for t in texts),
            "max_chars": max(len(t) for t in texts),
        }
    if out["long"]["min_chars"] <= out["short"]["max_chars"]:
        raise RuntimeError("long_not_larger_than_short_by_construction")
    return out


@dataclass
class MockEnvironmentV2:
    """Synthetic environment that drops command strings and never launches a process."""

    context_id: str
    environment_name: str
    condition: str
    readme: str
    exec_calls: int = 0
    workdir_probe_calls: int = 0
    readme_probe_calls: int = 0
    mock_terminal_calls: int = 0
    terminal_output_chars: list[int] = field(default_factory=list)
    terminal_output_hash12: list[str] = field(default_factory=list)

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
            stdout = synthetic_terminal_output(self.condition, self.mock_terminal_calls)
            self.terminal_output_chars.append(len(stdout))
            self.terminal_output_hash12.append(hashlib.sha256(stdout.encode()).hexdigest()[:12])
        return SimpleNamespace(stdout=stdout, stderr="", return_code=0)


# ---- amendment (a): aggregate-only response metadata ---------------------------------
def extract_raw_meta(raw: bytes) -> dict[str, Any]:
    """Counts/labels only from a raw chat-completions body. Never returns text."""
    try:
        data = json.loads(raw)
        choice = data["choices"][0]
        message = choice.get("message") or {}
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        return {}
    finish = choice.get("finish_reason")
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    details = usage.get("completion_tokens_details")
    reasoning_tokens = details.get("reasoning_tokens") if isinstance(details, dict) else None
    if isinstance(reasoning_tokens, bool) or not isinstance(reasoning_tokens, int):
        reasoning_tokens = None
    reasoning = message.get("reasoning_content")
    content = message.get("content")
    return {
        "finish_reason": finish if finish in FINISH_REASONS else ("missing" if finish is None else "other"),
        "reasoning_tokens": reasoning_tokens,
        "reasoning_chars": len(reasoning) if isinstance(reasoning, str) else 0,
        "content_chars": len(content) if isinstance(content, str) else 0,
    }


def install_meta_capture(model: Any, box: dict[str, Any]) -> None:
    """Wrap the client's parser so response metadata is captured without touching the client."""
    original_parse = model._parse

    def parse(raw: bytes) -> Any:
        parsed = original_parse(raw)
        box["last"] = extract_raw_meta(raw)
        return parsed

    model._parse = parse


def _response_meta(box: dict[str, Any], response: Any) -> dict[str, Any]:
    meta = box.pop("last", None) or {}
    finish = meta.get("finish_reason", getattr(response, "finish_reason", None))
    if finish is not None and finish not in FINISH_REASONS and finish not in {"missing", "other"}:
        finish = "other"
    reasoning_tokens = meta.get("reasoning_tokens", getattr(response, "reasoning_tokens", None))
    reasoning = getattr(response, "reasoning", None)
    content = getattr(response, "content", None)
    return {
        "finish_reason": finish if finish is not None else "unavailable",
        "reasoning_tokens": reasoning_tokens,
        "reasoning_tokens_source": "usage_details" if reasoning_tokens is not None else "unavailable",
        "reasoning_chars": meta.get("reasoning_chars", len(reasoning) if isinstance(reasoning, str) else 0),
        "content_chars": meta.get("content_chars", len(content) if isinstance(content, str) else 0),
    }


# ---- amendment (d): recovery after no_tool_call ---------------------------------------
def recovery_summary(categories: list[str]) -> dict[str, Any]:
    """For every no_tool_call, did the NEXT request produce a valid tool call?"""
    events: list[str] = []
    for index, category in enumerate(categories):
        if category != "no_tool_call":
            continue
        if index + 1 >= len(categories):
            events.append("no_next_request")
        elif categories[index + 1] in VALID_CATEGORIES:
            events.append("recovered")
        else:
            events.append("not_recovered")
    counts = Counter(events)
    return {
        "no_tool_call_events": len(events),
        "recovered": counts.get("recovered", 0),
        "not_recovered": counts.get("not_recovered", 0),
        "no_next_request": counts.get("no_next_request", 0),
        "event_order": events,
    }


# ---- safety audits ---------------------------------------------------------------------
class ProcessSpawnAudit:
    """Count subprocess launches other than the GPU monitor's nvidia-smi."""

    def __init__(self) -> None:
        self.unexpected = 0
        self._original: Any = None

    def __enter__(self) -> ProcessSpawnAudit:
        audit = self
        original = subprocess.Popen
        self._original = original

        class CountingPopen(original):  # type: ignore[valid-type, misc]
            def __init__(self, args: Any, *a: Any, **k: Any) -> None:
                first = args if isinstance(args, str) else (list(args)[0] if args else "")
                name = Path(str(first).split()[0] if isinstance(first, str) and first else str(first)).stem
                if name not in ALLOWED_PROCESS_NAMES:
                    audit.unexpected += 1
                super().__init__(args, *a, **k)

        subprocess.Popen = CountingPopen  # type: ignore[misc]
        return self

    def __exit__(self, *exc: object) -> None:
        subprocess.Popen = self._original  # type: ignore[misc]


def new_step_log_like_files(before: set[str], after: set[str]) -> list[str]:
    """Entries created during the run that look like step logs (ignores pre-existing entries)."""
    return sorted(
        name for name in after - before
        if name.lower().endswith((".jsonl", ".ndjson")) or "step" in name.lower() or name.startswith("aas_")
    )


def aggregate_only_violations(value: Any, path: str = "") -> list[str]:
    """Return paths of anything that could be raw content (long strings or content keys)."""
    problems: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in FORBIDDEN_KEYS:
                problems.append(f"{path}/{key}:forbidden_key")
            problems.extend(aggregate_only_violations(item, f"{path}/{key}"))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            problems.extend(aggregate_only_violations(item, f"{path}[{index}]"))
    elif isinstance(value, str) and len(value) > MAX_STRING_LEAF:
        problems.append(f"{path}:long_string")
    return problems


# ---- amendment (f): validity gate --------------------------------------------------------
def growth_deltas(requests: list[dict[str, Any]]) -> list[int]:
    """Prompt-token growth across each request that followed a valid terminal call."""
    deltas: list[int] = []
    for before, after in zip(requests, requests[1:], strict=False):
        if before.get("response_category") == "valid_schema_A":
            deltas.append(after["prompt_tokens_preflight"] - before["prompt_tokens_preflight"])
    return deltas


def evaluate_validity(
    runs: list[dict[str, Any]],
    *,
    planned: int = PAIRS * len(CONDITIONS),
    min_deltas: int = GROWTH_MIN_TERMINAL_DELTAS,
    min_diff: int = GROWTH_MIN_DIFF_TOKENS,
    new_harbor_modules: list[str] | None = None,
    unexpected_process_spawns: int = 0,
    output_violations: list[str] | None = None,
) -> dict[str, Any]:
    """Pure function over aggregates. verdict in {VALID, INVALID, INCOMPLETE}."""
    invalid: list[str] = []
    incomplete: list[str] = []

    # --- safety: any real executor / Harbor trial / raw content => INVALID
    if unexpected_process_spawns:
        invalid.append("process_spawned_outside_gpu_monitor")
    if new_harbor_modules:
        invalid.append("harbor_runtime_modules_loaded_during_run")
    if output_violations:
        invalid.append("raw_content_or_unbounded_string_in_output")
    for run in runs:
        tag = f"{run.get('condition')}-{run.get('pair')}"
        if run.get("agent_step_log_created") or run.get("log_dir_new_log_files"):
            invalid.append(f"step_log_or_log_file_created:{tag}")
        if run.get("raw_content_written"):
            invalid.append(f"raw_content_written:{tag}")
        expected_exec = (
            run.get("workdir_probe_calls", 0) + run.get("readme_probe_calls", 0) + run.get("mock_terminal_calls", 0)
        )
        if run.get("mock_exec_calls") != expected_exec:
            invalid.append(f"exec_calls_not_all_mock:{tag}")
        if not run.get("s0_probes_intercepted_before_first_inference"):
            invalid.append(f"s0_probes_not_intercepted:{tag}")
        if run.get("terminal_output_chars") and max(run["terminal_output_chars"]) > S0_MAX_OBSERVATION_CHARS:
            invalid.append(f"observation_exceeds_s0_truncation:{tag}")

    # --- completeness
    if len(runs) < planned:
        incomplete.append("fewer_conversations_than_planned")
    for run in runs:
        if str(run.get("stop_reason", "")).startswith("error:"):
            incomplete.append(f"conversation_error:{run.get('condition')}-{run.get('pair')}")
        elif run.get("request_count", 0) < 1:
            incomplete.append(f"no_request:{run.get('condition')}-{run.get('pair')}")

    # --- pairing: identical seed, identical first request, balanced order
    by_pair: dict[int, dict[str, dict[str, Any]]] = {}
    order_by_pair: dict[int, list[str]] = {}
    for run in runs:
        by_pair.setdefault(run["pair"], {})[run["condition"]] = run
        order_by_pair.setdefault(run["pair"], []).append(run["condition"])
    first_agreement = []
    for pair, conds in sorted(by_pair.items()):
        if set(conds) != set(CONDITIONS):
            continue
        short, long_ = conds["short"], conds["long"]
        if short.get("effective_seed") != long_.get("effective_seed"):
            invalid.append(f"pair_seed_differs:{pair}")
        if short.get("requests") and long_.get("requests"):
            if short["requests"][0]["prompt_tokens_preflight"] != long_["requests"][0]["prompt_tokens_preflight"]:
                invalid.append(f"first_request_prompt_differs:{pair}")
            first_agreement.append(
                short["requests"][0]["response_category"] == long_["requests"][0]["response_category"]
            )
    complete_pairs = [p for p, c in by_pair.items() if set(c) == set(CONDITIONS)]
    if len(complete_pairs) == PAIRS:
        short_first = sum(order_by_pair[p][0] == "short" for p in complete_pairs)
        if short_first != PAIRS // 2:
            invalid.append("order_not_balanced")
    else:
        short_first = None

    # --- growth: long history must be materially larger than short
    deltas = {c: [] for c in CONDITIONS}
    for run in runs:
        deltas[run["condition"]].extend(growth_deltas(run.get("requests", [])))
    medians = {c: (statistics.median(v) if v else None) for c, v in deltas.items()}
    growth: dict[str, Any] = {
        "terminal_turn_deltas": {c: len(v) for c, v in deltas.items()},
        "median_growth_tokens_per_terminal_turn": medians,
        "required_min_deltas_per_condition": min_deltas,
        "required_min_median_difference_tokens": min_diff,
        "max_prompt_tokens": {
            c: max((r["prompt_tokens_preflight"] for run in runs if run["condition"] == c for r in run.get("requests", [])),
                   default=None)
            for c in CONDITIONS
        },
    }
    if incomplete:
        # A setup/provider abort or error must not be reported as a growth failure.
        growth["status"] = "not_assessed_run_incomplete"
    elif any(len(v) < min_deltas for v in deltas.values()):
        growth["status"] = "insufficient_growth_observations"
        invalid.append("growth_not_assessable_insufficient_terminal_turns")
    elif medians["long"] - medians["short"] < min_diff:
        growth["status"] = "growth_not_materially_different"
        invalid.append("growth_not_materially_different")
    else:
        growth["status"] = "long_grows_materially_more"

    verdict = "INVALID" if invalid else ("INCOMPLETE" if incomplete else "VALID")
    return {
        "verdict": verdict,
        "invalid_reasons": sorted(set(invalid)),
        "incomplete_reasons": sorted(set(incomplete)),
        "growth": growth,
        "first_request_category_agreement_in_pairs": first_agreement,
        "pairs_short_first": short_first,
        "unexpected_process_spawns": unexpected_process_spawns,
        "new_harbor_runtime_modules": sorted(new_harbor_modules or []),
    }


# ---- one conversation --------------------------------------------------------------------
async def run_conversation(
    *,
    base: str,
    condition: str,
    repetition: int,
    monitor: Any,
    strategy_path: Path,
    log_root: Path,
    token_counter: Any = None,
    model_hook: Any = None,
    request_ceiling: int = REQUEST_CEILING,
    context_limit: int = CONTEXT_LIMIT,
) -> dict[str, Any]:
    count_tokens = token_counter or prompt_tokens
    # run_id depends on the pair only: both conditions of a pair get the same effective seed.
    run_id = f"s0-history-v2-pair-{repetition + 1:02d}"
    environment = MockEnvironmentV2(
        context_id=f"synthetic-v2-{condition}-{repetition + 1:02d}",
        environment_name="synthetic-history-check-v2",
        condition=condition,
        readme=FILLER * README_REPEATS,
    )
    log_dir = log_root / f"agent-logs-{condition}-{repetition + 1:02d}"
    log_dir.mkdir(parents=True, exist_ok=False)
    agent_env = {
        "AAS_STRATEGY_PATH": str(strategy_path),
        "AAS_MODEL_BASE_URL": base + "/v1",
        "AAS_MODEL": MODEL,
        "AAS_RUN_ID": run_id,
        "AAS_PROVENANCE_TAG": "synthetic-engineering-check",
        "AAS_SEED_ROOT": str(SEED_ROOT),
        "AAS_MODEL_TIMEOUT_S": "180",
        "AAS_CHECK_RUN_VISIBLE_TESTS": "",
    }
    agent = HarborStrategyAgent(logs_dir=log_dir, model_name=MODEL, extra_env=agent_env)
    if not getattr(agent, "extra_env", None):  # fallback BaseAgent (no Harbor installed) drops kwargs
        agent.extra_env = dict(agent_env)
    context = SimpleNamespace(n_input_tokens=0, n_cache_tokens=0, n_output_tokens=0, metadata={})
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
        "history_prompt_tokens_after_probes": None,
    }

    await agent.setup(environment)
    if agent._strategy.tool_policy.max_observation_chars != S0_MAX_OBSERVATION_CHARS:
        raise ProbeInvariantStop("s0_max_observation_chars_changed")
    model = agent._model
    meta_box: dict[str, Any] = {}
    if model_hook is not None:
        model = model_hook(model)
        agent._model = model
    else:
        install_meta_capture(model, meta_box)
    aggregate["effective_seed"] = model.seed
    aggregate["strategy_sha256"] = agent._strategy_hash
    aggregate["s0_max_steps"] = agent._strategy.budget.max_steps
    aggregate["s0_max_episode_tokens"] = agent._strategy.budget.max_tokens
    aggregate["s0_max_wall_seconds"] = agent._strategy.budget.max_wall_s
    aggregate["s0_max_observation_chars"] = agent._strategy.tool_policy.max_observation_chars

    def safe_write_step(
        response: Any, action: str, tool_call_id: str | None, observation: str,
        exit_code: int | None, action_args: Any = None, *, tripwire_flags: list[str] | None = None,
    ) -> None:
        # Aggregate labels only. Never serialize args, observations, reasoning, IDs or content.
        safe_action = action if action in SAFE_STEP_ACTIONS else "other"
        aggregate["step_categories"][safe_action] += 1
        if safe_action == "submit":
            aggregate["submit_step"] = agent._step_index
        for flag in tripwire_flags or []:
            if flag in {"url", "ipv4_address", "ipv6_address", "namespace_tool", "mount_tool"}:
                aggregate.setdefault("tripwire_flags", Counter())[flag] += 1

    agent._write_step = safe_write_step  # no raw step JSONL is ever created
    # Entries Harbor's BaseAgent may have created itself are not violations: only NEW ones count.
    log_entries_before = {p.name for p in log_dir.iterdir()}
    original_complete = model.complete

    async def guarded_complete(
        messages: Any, *, seed: int | None = None, tools: Any = None, max_output_tokens: int | None = None,
    ) -> Any:
        monitor.assert_safe()
        if aggregate["request_count"] == 0 and environment.exec_calls != 2:
            raise ProbeInvariantStop("expected_two_s0_probes_before_inference")
        if aggregate["request_count"] >= request_ceiling:
            raise RequestCeilingStop("request_ceiling")
        request_cap = min(OUTPUT_CAP, max_output_tokens or OUTPUT_CAP)
        request_seed = seed if seed is not None else model.seed + model._request_count
        measured = count_tokens(base, model, messages, request_seed, request_cap)
        if aggregate["history_prompt_tokens_after_probes"] is None:
            aggregate["history_prompt_tokens_after_probes"] = measured
        if measured + request_cap + CONTEXT_MARGIN >= context_limit:  # guard arithmetic unchanged
            aggregate["context_guard"] = {
                "input_tokens": measured, "output_cap": request_cap,
                "margin_tokens": CONTEXT_MARGIN, "context_limit": context_limit,
            }
            raise ContextGuardStop(measured, request_cap)
        aggregate["request_count"] += 1
        started = time.monotonic()
        meta_box.pop("last", None)
        response = await original_complete(
            messages, seed=seed, tools=tools or _TOOLS, max_output_tokens=request_cap,
        )
        monitor.assert_safe()
        category, tool_name = safe_response_category(response)
        if category not in KNOWN_CATEGORIES:
            category = "other"
        meta = _response_meta(meta_box, response)
        aggregate["request_categories"][category] += 1
        aggregate["tool_categories"][tool_name] += 1
        aggregate["requests"].append({
            "index": aggregate["request_count"],
            "response_category": category,
            "tool_category": tool_name,
            "finish_reason": meta["finish_reason"],
            "prompt_tokens_preflight": measured,
            "input_tokens_reported": response.input_tokens,
            "cached_tokens": response.cached_tokens,
            "completion_tokens": response.output_tokens,
            "reasoning_tokens": meta["reasoning_tokens"],
            "reasoning_tokens_source": meta["reasoning_tokens_source"],
            "reasoning_chars": meta["reasoning_chars"],
            "content_chars": meta["content_chars"],
            "output_cap": request_cap,
            "output_cap_reached": response.output_tokens >= request_cap,
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
    except SafeDiagnosticError:
        raise  # VRAM-monitor / safety-invariant failure: hard abort of the whole run
    except Exception as exc:
        # Do not record exception text: providers may include request details.
        aggregate["stop_reason"] = f"error:{type(exc).__name__}"
    aggregate["wall_seconds"] = round(time.monotonic() - start, 4)

    requests = aggregate["requests"]
    categories = [row["response_category"] for row in requests]
    aggregate["category_order"] = categories
    aggregate["tool_order"] = [row["tool_category"] for row in requests]
    aggregate["finish_reason_order"] = [row["finish_reason"] for row in requests]
    aggregate["completion_tokens_order"] = [row["completion_tokens"] for row in requests]
    aggregate["reasoning_tokens_order"] = [row["reasoning_tokens"] for row in requests]
    aggregate["prompt_tokens_order"] = [row["prompt_tokens_preflight"] for row in requests]
    aggregate["recovery"] = recovery_summary(categories)
    aggregate["terminal_turn_growth_deltas"] = growth_deltas(requests)
    aggregate["mock_exec_calls"] = environment.exec_calls
    aggregate["workdir_probe_calls"] = environment.workdir_probe_calls
    aggregate["readme_probe_calls"] = environment.readme_probe_calls
    aggregate["mock_terminal_calls"] = environment.mock_terminal_calls
    aggregate["terminal_output_chars"] = list(environment.terminal_output_chars)
    aggregate["terminal_output_hash12"] = list(environment.terminal_output_hash12)
    new_logs = new_step_log_like_files(log_entries_before, {p.name for p in log_dir.iterdir()})
    aggregate["agent_step_log_created"] = (log_dir / "aas_steps.jsonl").exists()
    aggregate["log_dir_new_log_files"] = len(new_logs)
    aggregate["raw_content_written"] = bool(new_logs)
    aggregate["submitted"] = aggregate["step_categories"].get("submit", 0) > 0
    aggregate["calls_to_submit"] = aggregate["request_count"] if aggregate["submitted"] else None
    aggregate["step_categories"] = dict(aggregate["step_categories"])
    aggregate["request_categories"] = dict(aggregate["request_categories"])
    aggregate["tool_categories"] = dict(aggregate["tool_categories"])
    aggregate["tripwire_flags"] = dict(aggregate.get("tripwire_flags", {}))
    aggregate["s0_probes_intercepted_before_first_inference"] = (
        environment.workdir_probe_calls == 1 and environment.readme_probe_calls == 1
    )
    aggregate["probe_invariant"] = (
        "s0_probes_intercepted" if environment.exec_calls >= 2 else "not_all_s0_probes_seen"
    )
    aggregate["total_input_tokens"] = sum(r["input_tokens_reported"] for r in requests)
    aggregate["total_output_tokens"] = sum(r["completion_tokens"] for r in requests)
    aggregate["mean_call_seconds"] = (
        round(statistics.mean(r["model_elapsed_seconds"] for r in requests), 4) if requests else None
    )
    return aggregate


async def run_experiment(base: str, output: Path, server_pid: int, hashes: dict[str, str]) -> dict[str, Any]:
    for key in list(os.environ):
        if key.startswith("AAS_CHECK_"):
            os.environ.pop(key, None)
    os.environ["HARBOR_TELEMETRY"] = "off"
    logging.disable(logging.CRITICAL)

    construction = validate_synthetic_outputs()
    output.parent.mkdir(parents=True, exist_ok=True)
    strategy_path = output.parent / "s0-strategy.json"
    strategy_path.write_text(s0().to_json() + "\n", encoding="utf-8")
    strategy_hash = hashlib.sha256(strategy_path.read_bytes()).hexdigest()
    log_root = output.parent / "agent-logs-v2"
    log_root.mkdir(parents=True, exist_ok=True)
    monitor = MemoryMonitor(server_pid)
    monitor.start()
    modules_before = {name for name in sys.modules if name == "harbor" or name.startswith("harbor.")}
    started = time.monotonic()
    runs: list[dict[str, Any]] = []
    status = "completed"
    audit = ProcessSpawnAudit()
    try:
        with audit:
            for repetition in range(PAIRS):
                order = ("short", "long") if repetition % 2 == 0 else ("long", "short")
                for condition in order:
                    monitor.assert_safe()
                    row = await run_conversation(
                        base=base, condition=condition, repetition=repetition,
                        monitor=monitor, strategy_path=strategy_path, log_root=log_root,
                    )
                    runs.append(row)
                    if row["stop_reason"].startswith("error:"):
                        # Record (class only) and continue with the next conversation;
                        # the verdict becomes INCOMPLETE. Hard aborts: safety/VRAM only.
                        status = "completed_with_conversation_errors"
                        continue
                    if row["agent_step_log_created"] or row["log_dir_new_log_files"]:
                        status = "aborted_safety_invariant"
                        break
                if status.startswith("aborted"):
                    break
    except Exception as exc:
        status = f"aborted:{type(exc).__name__}"  # class only, never the message
    finally:
        monitor.stop()

    modules_after = {name for name in sys.modules if name == "harbor" or name.startswith("harbor.")}
    new_harbor = sorted(name for name in modules_after - modules_before if HARBOR_RUNTIME_MODULE.search(name))
    violations = aggregate_only_violations(runs, "/runs")
    validity = evaluate_validity(
        runs, new_harbor_modules=new_harbor,
        unexpected_process_spawns=audit.unexpected, output_violations=violations,
    )
    result = {
        "experiment": "synthetic_harbor_s0_history_check_v2",
        "protocol": "docs/experiments/s0-history-check-v2-protocol-2026-11.md",
        "date_utc": datetime.now(UTC).date().isoformat(),
        "status": status,
        "validity": validity,
        "interpretation": (
            "engineering evidence only; synthetic instructions and mock environment; "
            "not benchmark performance"
        ),
        "model": MODEL,
        "model_sha256": hashes["model"],
        "server_sif_sha256": hashes["server"],
        "source_commit": hashes["source_commit"],
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "v1_runner_sha256": hashlib.sha256(_V1_PATH.read_bytes()).hexdigest(),
        "strategy_id": "s0",
        "strategy_sha256": strategy_hash,
        "seed_root": SEED_ROOT,
        "pairs": PAIRS,
        "planned_conversations": PAIRS * len(CONDITIONS),
        "started_conversations": len(runs),
        "conditions": {
            "short": {"readme_repeats": README_REPEATS, "terminal_output": "short_counter_based"},
            "long": {
                "readme_repeats": README_REPEATS,
                "terminal_output": "long_counter_based",
                "terminal_output_target_chars": LONG_OBSERVATION_CHARS,
            },
        },
        "synthetic_output_construction": construction,
        "context_limit_tokens": CONTEXT_LIMIT,
        "per_request_output_cap": OUTPUT_CAP,
        "required_context_margin_tokens": CONTEXT_MARGIN,
        "request_ceiling_per_conversation": REQUEST_CEILING,
        "growth_gate": {"min_deltas": GROWTH_MIN_TERMINAL_DELTAS, "min_median_diff_tokens": GROWTH_MIN_DIFF_TOKENS},
        "instruction_label": "v2_specific_four_terminal_calls_instruction",
        "instruction_sha256": hashlib.sha256(V2_INSTRUCTION.encode()).hexdigest(),
        "v1_instruction_sha256": hashlib.sha256(V1_INSTRUCTION.encode()).hexdigest(),
        "unexpected_process_spawns": audit.unexpected,
        "aggregate_only_violations": violations,
        "raw_prompt_completion_command_answer_or_reasoning_written": bool(violations)
        or any(run.get("raw_content_written") for run in runs),
        "s0_visible_test_check": "skipped_no_command_configured",
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
        args.base_url, args.output, args.server_pid,
        {"model": args.model_sha256, "server": args.server_sif_sha256, "source_commit": args.source_commit},
    ))
    print(json.dumps({
        "status": result["status"],
        "validity_verdict": result["validity"]["verdict"],
        "runs": len(result["runs"]),
        "gpu_minimum_free_mib": result["gpu_monitor"]["minimum_free_mib"],
        "artifact": str(args.output),
    }, sort_keys=True))
    return 0 if result["status"] == "completed" and result["validity"]["verdict"] == "VALID" else 2


if __name__ == "__main__":
    raise SystemExit(main())
