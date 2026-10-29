"""Apply the project concurrency and timeout requirements to a Harbor job."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def configure_harbor_job(job: Mapping[str, Any], *, llama_cpp_slots: int) -> dict[str, Any]:
    """Copy a Harbor job mapping and set its concurrency and agent timeout.

    The caller supplies the remaining pinned Harbor job fields. This keeps the
    adapter independent of dataset/provider choices while preventing Harbor's
    default concurrency or timeout multiplier from silently taking effect.
    """
    if isinstance(llama_cpp_slots, bool) or not isinstance(llama_cpp_slots, int) or llama_cpp_slots < 1:
        raise ValueError("llama_cpp_slots must be a positive integer")
    configured = dict(job)
    configured["n_concurrent_trials"] = llama_cpp_slots
    configured["agent_timeout_multiplier"] = 2.0
    return configured


def main() -> None:
    """Resolve a JSON/YAML-compatible Harbor job for the pinned model-server slot count."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="source Harbor job config")
    parser.add_argument("--output", type=Path, required=True, help="resolved config path")
    parser.add_argument("--llama-cpp-slots", type=int, required=True)
    args = parser.parse_args()
    raw = args.input.read_text(encoding="utf-8")
    try:
        import yaml

        job = yaml.safe_load(raw)
    except ImportError:
        job = json.loads(raw)
    if not isinstance(job, dict):
        raise ValueError("Harbor job config must contain a mapping at its root")
    configured = configure_harbor_job(job, llama_cpp_slots=args.llama_cpp_slots)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        import yaml

        args.output.write_text(yaml.safe_dump(configured, sort_keys=False), encoding="utf-8")
    except ImportError:
        args.output.write_text(json.dumps(configured, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

\n