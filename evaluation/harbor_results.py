"""Strict extraction of task reward from completed Harbor trial results."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class HarborResultError(ValueError):
    """A Harbor result lacks a valid trial identity or verifier reward."""


@dataclass(frozen=True)
class HarborReward:
    trial_id: str
    task_id: str
    reward: float

    @property
    def success(self) -> bool:
        return self.reward >= 1.0


def _mapping(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        result = value.model_dump()
        return result if isinstance(result, dict) else None
    return None


def reward_from_trial_result(result: Any) -> HarborReward:
    """Read ``verifier_result.rewards.reward`` from a completed Harbor result.

    This function is intended for the post-run evaluator. The Harbor agent
    never receives the verifier result and cannot use it to alter its actions.
    Missing reward is an error: it must not silently become a failed or passed
    episode.
    """
    trial = _mapping(result)
    if trial is None:
        raise HarborResultError("Harbor trial result must be a mapping or Pydantic model")
    trial_id = trial.get("id")
    task_id = trial.get("task_name") or trial.get("task_id")
    verifier = _mapping(trial.get("verifier_result"))
    rewards = verifier.get("rewards") if verifier else None
    raw_reward = rewards.get("reward") if isinstance(rewards, dict) else None
    if trial_id is None or isinstance(trial_id, bool) or not str(trial_id):
        raise HarborResultError("Harbor trial result has no usable id")
    if task_id is None or isinstance(task_id, bool) or not str(task_id):
        raise HarborResultError(f"Harbor trial {trial_id!r} has no usable task identity")
    if isinstance(raw_reward, bool) or not isinstance(raw_reward, (int, float)):
        raise HarborResultError(f"Harbor trial {trial_id!r} has no numeric verifier reward")
    reward = float(raw_reward)
    if not math.isfinite(reward) or not 0.0 <= reward <= 1.0:
        raise HarborResultError(f"Harbor trial {trial_id!r} has out-of-range reward {raw_reward!r}")
    return HarborReward(str(trial_id), str(task_id), reward)


def append_completed_trial(
    result: Any,
    *,
    step_log_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Join one completed Harbor result to its step log and append an episode JSONL record."""
    reward = reward_from_trial_result(result)
    try:
        steps = [json.loads(line) for line in step_log_path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, json.JSONDecodeError) as exc:
        raise HarborResultError(f"could not read valid step log {step_log_path}") from exc
    if not steps:
        raise HarborResultError(f"Harbor trial {reward.trial_id!r} has no step log records")
    if any(not isinstance(step, dict) for step in steps):
        raise HarborResultError(f"step log {step_log_path} must contain JSON objects")
    if any(step.get("harbor_trial_id") != reward.trial_id for step in steps):
        raise HarborResultError(f"step log {step_log_path} contains a different Harbor trial id")
    request_usage: dict[int, tuple[int, int, int]] = {}
    for step in steps:
        seed = step.get("seed")
        if isinstance(seed, int) and not isinstance(seed, bool):
            usage = (
                int(step.get("input_tokens", 0)),
                int(step.get("cached_tokens", 0)),
                int(step.get("output_tokens", 0)),
            )
            previous_usage = request_usage.get(seed)
            if previous_usage is not None and previous_usage != usage:
                raise HarborResultError(
                    f"Harbor trial {reward.trial_id!r} has conflicting token usage for seed {seed}"
                )
            request_usage[seed] = usage
    record = {
        "harbor_trial_id": reward.trial_id,
        "task_id": reward.task_id,
        "status": "completed",
        "reward": reward.reward,
        "success": reward.success,
        "run_id": steps[0].get("run_id"),
        "strategy_id": steps[0].get("strategy_id"),
        "strategy_version": steps[0].get("strategy_version"),
        "strategy_hash": steps[0].get("strategy_hash"),
        "provenance_tag": steps[0].get("provenance_tag"),
        "steps": steps,
        "step_count": len(steps),
        "input_tokens": sum(tokens[0] for tokens in request_usage.values()),
        "cached_tokens": sum(tokens[1] for tokens in request_usage.values()),
        "output_tokens": sum(tokens[2] for tokens in request_usage.values()),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        output.flush()
    return record
