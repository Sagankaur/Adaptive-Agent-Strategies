#!/usr/bin/env python3
"""Start the exact task environment without a model and inspect only mounted path names."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
import shlex
import tomllib
from pathlib import Path

from harbor.environments.singularity.singularity import SingularityEnvironment


def _workdir(dockerfile: Path) -> str:
    result = "/app"
    if dockerfile.exists():
        for line in dockerfile.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.upper().startswith("WORKDIR "):
                result = line.split(None, 1)[1].strip()
    return result


def _make_environment(
    task_root: Path,
    task_environment: Path,
    task_config: Path,
    image: Path,
    work_root: Path,
) -> SingularityEnvironment:
    env = SingularityEnvironment.__new__(SingularityEnvironment)
    env.environment_dir = task_environment
    env._task_root = task_root.resolve()
    env.environment_name = "tb2-pilot-path-preflight"
    env.session_id = "tb2-pilot-path-preflight"
    env.logger = logging.getLogger("tb2-pilot-path-preflight")
    config = tomllib.loads(task_config.read_text(encoding="utf-8"))
    mounts = config.get("environment", {}).get("mounts", [])
    if mounts:
        raise RuntimeError("task declares extra mounts; stop before model execution")
    env._singularity_no_mount = "home,tmp,bind-paths"
    env._mounts = []
    env._workdir = _workdir(task_environment / "Dockerfile")
    env._sif_path = image
    env._server_process = None
    env._server_port = None
    env._control_dir = None
    env._server_socket_path = None
    env._staging_dir = None
    env._stream_task = None
    env._memory_watchdog_task = None
    env._http_client = None
    env._memory_limit_bytes = None
    env._memory_limit_exceeded = None
    env._merge_env = lambda values: values or {}
    env._resolve_user = lambda user: None
    if not task_environment.is_dir():
        raise FileNotFoundError("pinned task environment directory is missing")
    work_root.mkdir(parents=True, exist_ok=True)
    return env


async def _run(env: SingularityEnvironment) -> None:
    await env._start_server()
    try:
        assert env._server_port is None, "unexpected TCP control port"
        assert env._server_socket_path is not None and env._server_socket_path.is_socket(), "UDS unavailable"
        workdir = shlex.quote(env._workdir)
        command = (
            f"for root in {workdir} /staging/env_files; do "
            "if [ -d \"$root\" ]; then "
            f"find \"$root\" \\( -iname '*oracle*' -o -iname '*reference*' -o -iname '*solution*' "
            "-o -name tests -o -name test \\) -print; "
            "fi; done"
        )
        result = await env.exec(command, timeout_sec=30)
        if result.return_code != 0:
            raise RuntimeError("path-only scan did not complete")
        matches = [line for line in (result.stdout or "").splitlines() if line.strip()]
        if matches:
            raise RuntimeError("agent-visible workspace has denylisted path names; names withheld")
        mounts = await env.exec("cat /proc/self/mountinfo", timeout_sec=10)
        if mounts.return_code != 0:
            raise RuntimeError("could not inspect effective container mounts")
        task_root = str(env._task_root)
        allowed_source = str((env.environment_dir / "files").resolve())
        for line in (mounts.stdout or "").splitlines():
            fields = line.split(" - ", maxsplit=1)
            if len(fields) != 2:
                raise RuntimeError("container mount table has an unrecognized format")
            before_mount = fields[0].split()
            if len(before_mount) < 5:
                raise RuntimeError("container mount table is incomplete")
            mount_root = re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), before_mount[3])
            mount_point = re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), before_mount[4])
            post_mount = fields[1].split()
            if len(post_mount) < 2:
                raise RuntimeError("container mount table is incomplete")
            source = re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), post_mount[1])
            for host_path in (mount_root, source):
                if host_path == task_root or host_path.startswith(task_root + "/"):
                    if host_path != allowed_source:
                        raise RuntimeError("task-parent or verifier directory is mounted into the container")
            sensitive_mount_names = {"test", "tests", "solution", "oracle", "reference"}
            if sensitive_mount_names & set(mount_point.casefold().split("/")):
                raise RuntimeError("a verifier-like directory is mounted into the agent container")
        print("harbor_uds=PASS")
        print("agent_workdir_and_staged_files_sensitive_paths=0")
        print("task_parent_tests_solution_directories_mounted=NO")
    finally:
        await env._http_client.post("/shutdown")
        await env._server_process.wait()
        await env._cleanup_server_resources()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-environment", required=True, type=Path)
    parser.add_argument("--task-root", required=True, type=Path)
    parser.add_argument("--task-config", required=True, type=Path)
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)
    env = _make_environment(args.task_root, args.task_environment, args.task_config, args.image, args.output)
    asyncio.run(_run(env))


if __name__ == "__main__":
    if os.environ.get("HARBOR_TELEMETRY") != "off":
        raise SystemExit("HARBOR_TELEMETRY=off is required")
    main()
