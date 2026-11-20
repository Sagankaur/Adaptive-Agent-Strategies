"""Run four predeclared Aider tasks and emit a summary without model text."""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from evaluation.harbor_results import reward_from_trial_result

DEFAULT_TASK_IDS = ("hangman", "poker", "rest-api", "variable-length-quantity")


def summarize_steps(step_log: Path) -> dict[str, Any]:
    rows = [
        json.loads(line)
        for line in step_log.read_text(encoding="utf-8").splitlines()
        if line
    ]
    actions: dict[str, int] = {}
    flags: set[str] = set()
    tokens = {"input": 0, "cached": 0, "output": 0}
    calls = 0
    prompt_tokens = generated_tokens = prompt_ms = generated_ms = 0.0
    for row in rows:
        action = str(row.get("action", "unknown"))
        actions[action] = actions.get(action, 0) + 1
        flags.update(row.get("tripwire_flags") or [])
        if isinstance(row.get("seed"), int):
            tokens["input"] += int(row.get("input_tokens", 0))
            tokens["cached"] += int(row.get("cached_tokens", 0))
            tokens["output"] += int(row.get("output_tokens", 0))
        timing = row.get("timings") or {}
        if timing:
            calls += 1
            prompt_tokens += float(timing.get("prompt_tokens", 0))
            generated_tokens += float(timing.get("generated_tokens", 0))
            prompt_ms += float(timing.get("prompt_ms", 0))
            generated_ms += float(timing.get("generated_ms", 0))
    return {
        "actions": actions,
        "tripwire_flags": sorted(flags),
        "agent_step_count": len(rows),
        "model_calls": calls,
        "tokens": tokens,
        "prompt_tokens_per_second_mean_call": (
            round(prompt_tokens * 1000 / prompt_ms, 2) if prompt_ms else None
        ),
        "generated_tokens_per_second_mean_call": (
            round(generated_tokens * 1000 / generated_ms, 2) if generated_ms else None
        ),
    }


def main() -> int:
    taskroot = Path(os.environ["AAS_TASKROOT"])
    out = Path(os.environ["AAS_OUT"])
    port = int(os.environ["AAS_PORT"])
    strategy = os.environ["AAS_STRATEGY_PATH"]
    job_id = os.environ["SLURM_JOB_ID"]
    requested_ids = tuple(
        item.strip()
        for item in os.environ.get(
            "AAS_TASK_IDS", ",".join(DEFAULT_TASK_IDS)
        ).split(",")
        if item.strip()
    )
    if (
        not requested_ids
        or len(set(requested_ids)) != len(requested_ids)
        or any(item not in DEFAULT_TASK_IDS for item in requested_ids)
    ):
        raise SystemExit("AAS_TASK_IDS must be a nonempty, unique subset of the predeclared task IDs")
    scratch = taskroot.parents[2]
    cache = scratch / "harbor-smoke" / "cache_apptainer"
    wheelhouse = scratch / "harbor-smoke" / "egress-probe" / "aider-py311-4801425" / "wheelhouse"
    runtime_deps = scratch / "harbor-smoke" / "egress-probe" / "aider-py311-4801425" / "harbor-runtime-deps"
    results: list[dict[str, Any]] = []

    for task_id in requested_ids:
        task_path = taskroot / f"polyglot_python_{task_id}"
        workspace = task_path / "environment" / "workspace"
        jobs_dir = out / "harbor_jobs" / task_id
        config_path = out / f"{task_id}.yaml"
        lines = [
            f"job_name: gptoss_aider_{task_id}_{job_id}",
            f"jobs_dir: {jobs_dir}",
            "n_attempts: 1",
            "n_concurrent_trials: 1",
            "quiet: true",
            "environment:",
            "  type: singularity",
            "  kwargs:",
            '    singularity_no_mount: "home,tmp,bind-paths"',
            f'    singularity_image_cache_dir: "{cache}"',
            "  mounts:",
            "    - type: bind",
            f'      source: "{workspace}"',
            "      target: /app",
            "    - type: bind",
            f'      source: "{wheelhouse}"',
            "      target: /wheels",
            "      read_only: true",
            "    - type: bind",
            f'      source: "{runtime_deps}"',
            "      target: /runtime-deps",
            "      read_only: true",
            "agents:",
            "  - import_path: environments.harbor_agent:HarborStrategyAgent",
            '    model_name: "/models/gpt-oss-20b-MXFP4.gguf"',
            "    env:",
            f'      AAS_STRATEGY_PATH: "{strategy}"',
            f'      AAS_MODEL_BASE_URL: "http://127.0.0.1:{port}/v1"',
            '      AAS_MODEL_TIMEOUT_S: "180"',
            f'      AAS_RUN_ID: "gpt-oss-aider-pilot-{job_id}"',
            '      AAS_PROVENANCE_TAG: "gpt-oss-20b-aider-four-task-pilot"',
            '      AAS_SEED_ROOT: "20261119"',
            "tasks:",
            f"  - path: {task_path}",
            "",
        ]
        config_path.write_text("\n".join(lines), encoding="utf-8")
        proc = subprocess.run(
            ["harbor", "run", "--config", str(config_path), "--jobs-dir", str(jobs_dir), "--n-concurrent", "1", "--quiet"],
            check=False,
            capture_output=True,
            text=True,
        )
        (out / f"{task_id}.harbor-cli.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
        record: dict[str, Any] = {"task_id": f"polyglot_python_{task_id}", "harbor_exit_code": proc.returncode}
        job_roots = [path for path in jobs_dir.iterdir() if path.is_dir()] if jobs_dir.is_dir() else []
        if len(job_roots) != 1 or not (job_roots[0] / "result.json").is_file():
            record.update({"status": "infrastructure_or_harness_error", "reward": None})
            results.append(record)
            print(json.dumps(record, sort_keys=True), flush=True)
            if proc.returncode != 0:
                break
            continue

        job_root = job_roots[0]
        job_result = json.loads((job_root / "result.json").read_text(encoding="utf-8"))
        trial_files = list(job_root.glob("*/result.json"))
        if len(trial_files) != 1:
            record.update({"status": "infrastructure_or_harness_error", "reward": None})
            results.append(record)
            print(json.dumps(record, sort_keys=True), flush=True)
            continue

        trial_result = json.loads(trial_files[0].read_text(encoding="utf-8"))
        try:
            reward = reward_from_trial_result(trial_result)
        except ValueError:
            # Harbor may finish a failed trial without a verifier result. Record
            # the failure class only; never copy exception text or model output.
            exception = trial_result.get("exception_info") or {}
            message = str(exception.get("exception_message") or "")
            status = re.search(r"HTTP ([0-9]{3})", message)
            failure_type = str(exception.get("exception_type") or "UnknownError")
            error_origin = (
                "verifier"
                if "Verifier" in failure_type or "RewardFile" in failure_type
                else "agent_or_provider"
            )
            record.update({
                "status": f"{error_origin}_error_no_reward",
                "failure_type": failure_type,
                "provider_http_status": int(status.group(1)) if status else None,
                "context_related_error": bool(re.search(r"context|token", message, re.IGNORECASE)),
                "harbor_trial_id": trial_result.get("id"),
                "job_completed_trials": job_result.get("stats", {}).get("n_completed_trials"),
                "job_errored_trials": job_result.get("stats", {}).get("n_errored_trials"),
            })
            step_logs = list(trial_files[0].parent.rglob("aas_steps.jsonl"))
            if len(step_logs) == 1:
                record.update(summarize_steps(step_logs[0]))
            results.append(record)
            print(json.dumps(record, sort_keys=True), flush=True)
            continue
        step_logs = list(trial_files[0].parent.rglob("aas_steps.jsonl"))
        record.update({
            "status": "completed",
            "harbor_trial_id": reward.trial_id,
            "reward": reward.reward,
            "success": reward.success,
            "job_completed_trials": job_result.get("stats", {}).get("n_completed_trials"),
            "job_errored_trials": job_result.get("stats", {}).get("n_errored_trials"),
        })
        started = trial_result.get("started_at")
        finished = trial_result.get("finished_at")
        if isinstance(started, str) and isinstance(finished, str):
            try:
                record["wall_seconds"] = round(
                    (datetime.fromisoformat(finished) - datetime.fromisoformat(started)).total_seconds(),
                    3,
                )
            except ValueError:
                record["wall_seconds"] = None
        if len(step_logs) == 1:
            record.update(summarize_steps(step_logs[0]))
        else:
            record["status"] = "missing_step_log"
        results.append(record)
        print(json.dumps(record, sort_keys=True), flush=True)
        if {"namespace_tool", "mount_tool"} & set(record.get("tripwire_flags", [])):
            break

    summary = {
        "slurm_job_id": job_id,
        "original_denominator": 6,
        "attempted_ids": [entry["task_id"] for entry in results],
        "task_ids_requested_this_job": [f"polyglot_python_{item}" for item in requested_ids],
        "pre_run_safety_excluded_ids": ["polyglot_python_beer-song", "polyglot_python_food-chain"],
        "replacement_ids": [],
        "episodes": results,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if any({"namespace_tool", "mount_tool"} & set(entry.get("tripwire_flags", [])) for entry in results):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
