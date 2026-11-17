#!/usr/bin/env python3
"""No-model Python 3.11 + offline-pytest Harbor/Apptainer smoke."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import shlex
import shutil
from pathlib import Path

from harbor.environments.singularity.singularity import SingularityEnvironment


def make_environment(
    image: Path, work_root: Path, wheelhouse: Path, fixture_dir: Path
) -> SingularityEnvironment:
    env = SingularityEnvironment.__new__(SingularityEnvironment)
    env.environment_dir = work_root / "environment"
    env.environment_dir.mkdir(parents=True, exist_ok=True)
    env.environment_name = "aider-python311-preflight"
    env.session_id = "synthetic-python311-offline-pytest"
    env.logger = logging.getLogger("aider-python311-preflight")
    env._singularity_no_mount = "home,tmp,bind-paths"
    env._mounts = [
        {
            "type": "bind",
            "source": str(env.environment_dir),
            "target": "/app",
        },
        {
            "type": "bind",
            "source": str(work_root / "harbor-runtime-deps"),
            "target": "/runtime-deps:ro",
        },
        {"type": "bind", "source": str(wheelhouse), "target": "/wheels:ro"},
        {"type": "bind", "source": str(fixture_dir), "target": "/probe:ro"},
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
    env._merge_env = lambda values: {
        **(values or {}),
        "PIP_NO_INDEX": "1",
        "PIP_FIND_LINKS": "/wheels",
        "PIP_TARGET": "/tmp/aider-pytest",
        "PYTHONPATH": "/runtime-deps:/tmp/aider-pytest",
    }
    env._resolve_user = lambda user: None
    return env


async def run_probe(env: SingularityEnvironment) -> dict[str, object]:
    await env._start_server()
    assert env._server_port is None, "unexpected TCP control port was assigned"
    assert env._control_dir is not None and env._server_socket_path is not None
    assert env._server_socket_path.is_socket(), "UDS control socket is missing"
    assert env._control_dir.stat().st_mode & 0o777 == 0o700

    nonce = f"aider-py311-uds-{os.environ.get('SLURM_JOB_ID', 'local')}"
    control = await env.exec(
        f"printf '%s' {shlex.quote(nonce)} > /app/.preflight-write && "
        f"test -s /app/.preflight-write && "
        f"printf '%s ' {shlex.quote(nonce)} && python3 --version",
        timeout_sec=20,
    )
    assert control.return_code == 0 and nonce in control.stdout, control
    assert "Python 3.11." in control.stdout, control.stdout

    network = await env.exec("python3 /probe/check_network.py", timeout_sec=15)
    assert network.return_code == 0 and "network=PASS" in network.stdout, network
    mounts = await env.exec("python3 /probe/check_mounts.py", timeout_sec=15)
    assert mounts.return_code == 0 and "mounts=PASS" in mounts.stdout, mounts

    install_and_test = await env.exec(
        "PIP_NO_INDEX=1 PIP_FIND_LINKS=/wheels PIP_TARGET=/tmp/aider-pytest "
        "PYTHONPATH=/runtime-deps:/tmp/aider-pytest pip3 install --no-cache-dir pytest && "
        "cp /probe/test_synthetic.py /app/test_synthetic.py && "
        "PIP_NO_INDEX=1 PYTHONPATH=/runtime-deps:/tmp/aider-pytest "
        "python3 -m pytest -v --tb=short /app",
        timeout_sec=120,
    )
    assert install_and_test.return_code == 0, install_and_test
    assert "1 passed" in install_and_test.stdout, install_and_test.stdout
    assert "PytestCacheWarning" not in install_and_test.stdout, install_and_test.stdout

    report = {
        "provider_exec_server_health": "PASS",
        "uds_nonce_round_trip": "PASS",
        "tcp_control_port": None,
        "python_version": "3.11",
        "offline_pytest_install": "PASS",
        "synthetic_pytest": "PASS",
        "egress_fixed_ip_dns_metadata": "PASS_BLOCKED",
        "host_credentials_and_docker_sockets": "PASS_ABSENT_FOR_CHECKED_MOUNTS_AND_ENV_NAMES",
        "task_or_benchmark_run": False,
        "model_or_agent_run": False,
        "oracle_or_reference_solution_run": False,
        "limitations": [
            "This tests a generic Python 3.11 image, not the adapter-generated Aider task image.",
            "The harness constructs SingularityEnvironment directly and does not run Harbor's CLI trial lifecycle.",
            "It does not establish task-specific dependency completeness or resource limits.",
        ],
        "control_stdout": control.stdout,
        "network_stdout": network.stdout,
        "mount_stdout": mounts.stdout,
        "pytest_stdout": install_and_test.stdout,
        "pytest_stderr": install_and_test.stderr,
    }
    await env._http_client.post("/shutdown")
    await asyncio.wait_for(env._server_process.wait(), timeout=10)
    socket_path = env._server_socket_path
    control_dir = env._control_dir
    await env._cleanup_server_resources()
    assert socket_path is not None and not socket_path.exists()
    assert control_dir is not None and not control_dir.exists()
    report["uds_cleanup"] = "PASS"
    return report


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--wheelhouse", type=Path, required=True)
    parser.add_argument("--fixture-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    for path in (args.image, args.wheelhouse, args.fixture_dir):
        if not path.exists():
            raise SystemExit(f"required path missing: {path}")
    args.output.mkdir(parents=True, exist_ok=True)
    env = make_environment(args.image, args.output, args.wheelhouse, args.fixture_dir)
    completed = False
    try:
        report = await run_probe(env)
        report_path = args.output / "preflight.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2), flush=True)
        completed = True
    finally:
        if env._http_client is not None and env._server_process is not None:
            if env._server_process.returncode is None:
                try:
                    await env._http_client.post("/shutdown")
                    await asyncio.wait_for(env._server_process.wait(), timeout=10)
                except Exception:
                    env._server_process.terminate()
                    await env._server_process.wait()
        await env._cleanup_server_resources()
        if completed:
            shutil.rmtree(env.environment_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
