#!/usr/bin/env python3
"""Audit one synthetic Harbor CLI trial and report a partial/full gate result."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def _read_json(path: Path | None) -> dict:
    if path is None:
        return {}
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--jobs-dir", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--pytest-version", required=True)
    parser.add_argument("--host-resource", type=Path, required=True)
    parser.add_argument("--provider-capabilities", type=Path, required=True)
    parser.add_argument("--harbor-exit-code", type=int, required=True)
    args = parser.parse_args()

    trial_logs = sorted(args.jobs_dir.rglob("trial.log"))
    trial_log = trial_logs[0] if len(trial_logs) == 1 else None
    result_path = trial_log.parent / "result.json" if trial_log else None
    has_trial_result = bool(result_path and result_path.is_file())
    trial_text = trial_log.read_text(errors="replace") if trial_log else ""
    result = _read_json(result_path)

    argv_lines = [line for line in trial_text.splitlines() if "Apptainer argv:" in line]
    argv = argv_lines[0] if len(argv_lines) == 1 else ""
    required_args = (
        "exec --net --network none",
        "--writable-tmpfs",
        "--containall",
        "--pid",
        "--no-mount home",
        "--no-mount tmp",
        "--no-mount bind-paths",
        "--uds /harbor-control/control.sock",
        "/harbor-control",
    )
    argv_pass = bool(argv) and all(token in argv for token in required_args)
    no_fakeroot_or_tcp = bool(argv) and "--fakeroot" not in argv and "--port" not in argv
    socket_dirs = re.findall(r"(/tmp/huds-[^:\s]+):/harbor-control", argv)
    uds_cleanup = len(socket_dirs) == 1 and not Path(socket_dirs[0]).exists()

    isolation_files = sorted(args.jobs_dir.rglob("isolation.json"))
    isolation = _read_json(isolation_files[0]) if len(isolation_files) == 1 else {}
    host_resource = _read_json(args.host_resource)
    provider_capabilities = _read_json(args.provider_capabilities)
    pip_logs = sorted(args.jobs_dir.rglob("pip-install.log"))
    pip_text = pip_logs[0].read_text(errors="replace") if len(pip_logs) == 1 else ""
    pytest_logs = sorted(args.jobs_dir.rglob("pytest.log"))
    pytest_text = pytest_logs[0].read_text(errors="replace") if len(pytest_logs) == 1 else ""

    verifier = result.get("verifier_result") or {}
    rewards = verifier.get("rewards") or {}
    reward = rewards.get("reward") if isinstance(rewards, dict) else None
    exception_info = result.get("exception_info")
    image_hash = hashlib.sha256(args.image.read_bytes()).hexdigest()

    checks = {
        "one_trial_log": len(trial_logs) == 1,
        "one_trial_result": has_trial_result,
        "harbor_cli_exit_zero": args.harbor_exit_code == 0,
        "harbor_trial_no_exception": exception_info is None,
        "synthetic_reward_one": reward == 1 or reward == 1.0,
        "isolated_argv_with_uds": argv_pass,
        "no_fakeroot_or_tcp_port": no_fakeroot_or_tcp,
        "private_uds_cleaned": uds_cleanup,
        "isolation_artifact_present": len(isolation_files) == 1,
        "read_only_wheel_and_runtime_mounts": (
            isolation.get("mount_audit", {}).get("checked_read_only_mounts")
            == {"/runtime-deps": "ro", "/wheels": "ro"}
            and not isolation.get("mount_audit", {}).get("writable_read_only_mounts")
        ),
        "offline_pytest_install": "Successfully installed" in pip_text
        and "Looking in links:" in pip_text
        and "Looking in indexes:" not in pip_text,
        "pytest_uses_pinned_version": f"pytest-{args.pytest_version}" in pip_text,
        "pytest_tests_pass": "1 passed" in pytest_text,
        "memory_watchdog_active": "Memory watchdog started: limit=2048MB" in trial_text,
    }
    core_names = [name for name, value in checks.items() if isinstance(value, bool)]
    core_pass = all(checks[name] for name in core_names)
    report = {
        "status": "PARTIAL" if core_pass else "FAIL",
        "core_synthetic_cli_gate": "PASS" if core_pass else "FAIL",
        "task_level_resource_limits": "NOT_VERIFIED",
        "harbor_cli_exit_code": args.harbor_exit_code,
        "synthetic_reward": reward,
        "image_sha256": image_hash,
        "isolation_checks": isolation,
        "host_resource_observation": host_resource,
        "provider_resource_capabilities": provider_capabilities,
        "checks": checks,
        "limitations": [
            "The synthetic reward is harness plumbing, not a benchmark result.",
            "A no-op agent was used; no model or agent behavior was evaluated.",
            "The synthetic task uses an Aider-compatible Python runtime image but contains no Aider benchmark task or task-specific workspace.",
            "The provider has a sampled software memory watchdog but advertises no hard CPU or memory resource capability.",
            "No resource stress test was run; task-level resource controls are inherited from the Slurm job allocation, not enforced by Harbor.",
        ],
    }
    output = args.output / "postflight.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if core_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
