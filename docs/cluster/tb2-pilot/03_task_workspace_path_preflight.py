#!/usr/bin/env python3
"""Start the exact task environment without a model and inspect only mounted path names."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
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
    runtime_deps: Path,
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
    if not runtime_deps.is_dir():
        raise FileNotFoundError("pinned Harbor runtime dependency directory is missing")
    env._mounts = [
        {
            "type": "bind",
            "source": str(runtime_deps.resolve()),
            "target": "/runtime-deps",
            "read_only": True,
        }
    ]
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
        runtime_check = """import importlib.metadata, importlib.util, sys
assert sys.version_info[:3] == (3, 13, 7), sys.version
for name, version in {"fastapi": "0.162.0", "pydantic": "2.13.5", "uvicorn": "0.54.0"}.items():
    spec = importlib.util.find_spec(name)
    assert spec and spec.origin and spec.origin.startswith("/runtime-deps/"), (name, spec)
    assert importlib.metadata.version(name) == version, name
print("runtime_imports=PASS")
"""
        dependency_check = await env.exec(
            "/usr/local/bin/python3 -c " + shlex.quote(runtime_check), timeout_sec=15
        )
        if dependency_check.return_code != 0 or "runtime_imports=PASS" not in (dependency_check.stdout or ""):
            raise RuntimeError("pinned Harbor dependencies are not loaded from the runtime mount")
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
        runtime_mount_found = False
        for line in (mounts.stdout or "").splitlines():
            fields = line.split(" - ", maxsplit=1)
            if len(fields) != 2:
                raise RuntimeError("container mount table has an unrecognized format")
            before_mount = fields[0].split()
            if len(before_mount) < 5:
                raise RuntimeError("container mount table is incomplete")
            mount_root = re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), before_mount[3])
            mount_point = re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), before_mount[4])
            mount_options = set(before_mount[5].split(",")) if len(before_mount) > 5 else set()
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
            if mount_point == "/runtime-deps":
                if "ro" not in mount_options:
                    raise RuntimeError("Harbor dependency mount is not read-only")
                runtime_mount_found = True
        if not runtime_mount_found:
            raise RuntimeError("read-only Harbor dependency mount is missing")

        nonce = f"aas-task-image-uds-{os.environ.get('SLURM_JOB_ID', 'local')}"
        control = await env.exec(
            f"printf '%s' {shlex.quote(nonce)} > /app/.aas-runtime-preflight && "
            f"test \"$(cat /app/.aas-runtime-preflight)\" = {shlex.quote(nonce)} && "
            "/usr/local/bin/python3 --version",
            timeout_sec=20,
        )
        if control.return_code != 0 or "Python 3.13.7" not in (control.stdout or ""):
            raise RuntimeError("Harbor UDS environment.exec or pinned Python check failed")

        network_code = """import socket
interfaces = {line.split(":", 1)[0].strip() for line in open("/proc/net/dev").read().splitlines()[2:] if ":" in line}
routes = open("/proc/net/route").read().splitlines()[1:]
blocked = []
if interfaces - {"lo"} or routes:
    blocked.append("route_or_interface")
for host, port in (("1.1.1.1", 443), ("169.254.169.254", 80)):
    try:
        socket.create_connection((host, port), timeout=2).close()
    except OSError:
        pass
    else:
        blocked.append("external_tcp")
try:
    socket.getaddrinfo("example.com", 443)
except OSError:
    pass
else:
    blocked.append("external_dns")
if blocked:
    raise SystemExit("egress probe failed: " + ",".join(blocked))
print("egress=BLOCKED routes=LOOPBACK_ONLY fixed_ip=BLOCKED dns=BLOCKED metadata=BLOCKED")
"""
        network = await env.exec(
            "/usr/local/bin/python3 -c " + shlex.quote(network_code), timeout_sec=15
        )
        if network.return_code != 0 or "egress=BLOCKED" not in (network.stdout or ""):
            raise RuntimeError("exact task image egress probe failed")

        readonly = await env.exec(
            "if touch /runtime-deps/.aas-readonly-probe 2>/dev/null; then "
            "rm -f /runtime-deps/.aas-readonly-probe; exit 1; else exit 0; fi",
            timeout_sec=10,
        )
        if readonly.return_code != 0:
            raise RuntimeError("Harbor runtime dependency mount accepted a write")
        print("harbor_uds=PASS")
        print("harbor_uds_exec_round_trip=PASS")
        print("task_image_python=3.13.7")
        print("harbor_runtime_mount=READ_ONLY")
        print("task_image_egress=BLOCKED")
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
    parser.add_argument("--runtime-deps", required=True, type=Path)
    parser.add_argument("--runtime-manifest", required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.runtime_manifest.read_text(encoding="utf-8"))
    if manifest.get("task_sif_sha256") != hashlib.sha256(args.image.read_bytes()).hexdigest():
        raise SystemExit("runtime dependency manifest is for a different task SIF")
    if manifest.get("python") != "3.13.7":
        raise SystemExit("runtime dependency manifest has an unexpected Python version")
    if args.runtime_deps.stat().st_mode & 0o222:
        raise SystemExit("runtime dependency directory is writable on the host")
    logging.basicConfig(level=logging.INFO)
    env = _make_environment(
        args.task_root,
        args.task_environment,
        args.task_config,
        args.image,
        args.output,
        args.runtime_deps,
    )
    asyncio.run(_run(env))


if __name__ == "__main__":
    if os.environ.get("HARBOR_TELEMETRY") != "off":
        raise SystemExit("HARBOR_TELEMETRY=off is required")
    main()
