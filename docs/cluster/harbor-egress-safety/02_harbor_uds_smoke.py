#!/usr/bin/env python3
"""Scripted Harbor 0.23.0 UDS/e2e egress check; no model or benchmark task."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import shlex
import shutil
from pathlib import Path

import httpx
import uvicorn
from harbor.environments.singularity.singularity import SingularityEnvironment


def make_environment(image: Path, work_root: Path) -> SingularityEnvironment:
    env = SingularityEnvironment.__new__(SingularityEnvironment)
    env.environment_dir = work_root / "environment"
    env.environment_dir.mkdir(parents=True, exist_ok=True)
    env.environment_name = "scripted-egress-probe"
    env.session_id = "scripted-uds-smoke"
    env.logger = logging.getLogger("harbor-uds-smoke")
    env._singularity_no_mount = "home,tmp,bind-paths"
    env._mounts = [
        {"type": "bind", "source": "/usr/bin/curl", "target": "/usr/local/bin/curl:ro"},
        {"type": "bind", "source": "/lib/x86_64-linux-gnu", "target": "/host-libs:ro"},
        {
            "type": "bind",
            "source": "/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2",
            "target": "/host-loader:ro",
        },
    ]
    env._workdir = "/app"
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
    return env


async def run_probe(env: SingularityEnvironment) -> None:
    await env._start_server()
    assert env._server_port is None, "unexpected TCP control port was assigned"
    assert env._control_dir is not None and env._server_socket_path is not None
    mode = env._control_dir.stat().st_mode & 0o777
    assert mode == 0o700, f"control socket parent mode is {mode:o}, expected 700"
    assert env._server_socket_path.is_socket(), "UDS control socket is missing"
    print(f"control_dir_mode={mode:o}")
    print(f"socket_path_length={len(str(env._server_socket_path).encode())}")
    print("harbor_health=PASS")

    nonce = f"aas-uds-control-{os.environ.get('SLURM_JOB_ID', 'local')}"
    result = await env.exec(
        f"printf '%s' {shlex.quote(nonce)} > /app/.uds-smoke && cat /app/.uds-smoke",
        timeout_sec=10,
    )
    assert result.return_code == 0 and result.stdout == nonce, result
    print(f"environment_exec_nonce={result.stdout}")

    task_net = await env.exec("cat /proc/net/dev; printf '\\nROUTES\\n'; cat /proc/net/route", timeout_sec=10)
    assert task_net.return_code == 0, task_net
    print("task_network_tables=" + (task_net.stdout or "").replace("\n", " | "))
    net_lines = (task_net.stdout or "").split("ROUTES", maxsplit=1)
    assert len(net_lines) == 2 and "lo:" in net_lines[0], task_net.stdout
    assert "eth" not in net_lines[0] and "ens" not in net_lines[0], task_net.stdout
    route_lines = [line for line in net_lines[1].splitlines() if line.strip()]
    assert len(route_lines) <= 1, f"unexpected task routes: {route_lines}"

    curl_prefix = "/host-loader --library-path /host-libs /usr/local/bin/curl"
    common = "--noproxy '*' -k -sS -o /dev/null --connect-timeout 3 --max-time 5"
    checks = {
        "external": f"{curl_prefix} {common} https://1.1.1.1/",
        "dns_external": f"{curl_prefix} {common} https://example.com/",
        "metadata": f"{curl_prefix} --noproxy '*' -sS -o /dev/null --connect-timeout 3 --max-time 5 http://169.254.169.254/latest/meta-data/",
    }
    for name, command in checks.items():
        result = await env.exec(command, timeout_sec=10)
        print(f"{name}_curl_rc={result.return_code}")
        print(f"{name}_curl_output={(result.stdout or '').strip()}")
        allowed_codes = {6, 7, 28} if name == "dns_external" else {7, 28}
        assert result.return_code in allowed_codes, f"{name} curl did not fail by network reachability: {result}"

    await env._http_client.post("/shutdown")
    await asyncio.wait_for(env._server_process.wait(), timeout=10)
    socket_path = env._server_socket_path
    control_dir = env._control_dir
    await env._cleanup_server_resources()
    assert socket_path is not None and not socket_path.exists(), "socket was not removed"
    assert control_dir is not None and not control_dir.exists(), "private control dir was not removed"
    print("shutdown_and_socket_cleanup=PASS")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
    print(f"httpx={httpx.__version__} uvicorn={uvicorn.__version__}")
    env = make_environment(args.image, args.output)
    try:
        await run_probe(env)
    finally:
        await env._cleanup_server_resources()
        shutil.rmtree(env.environment_dir, ignore_errors=True)


if __name__ == "__main__":
    if os.environ.get("HARBOR_TELEMETRY") != "off":
        raise SystemExit("HARBOR_TELEMETRY=off must be set before running this scripted smoke")
    asyncio.run(main())
