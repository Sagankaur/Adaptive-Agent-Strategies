"""Synthetic Harbor task checks; no benchmark inputs or model calls."""

from __future__ import annotations

import json
import os
import re
import socket
import sys
from pathlib import Path


def _probe_connect(host: str, port: int) -> dict[str, object]:
    try:
        with socket.create_connection((host, port), timeout=3):
            return {"blocked": False, "error": None, "errno": None}
    except OSError as exc:
        blocked_errnos = {
            101,  # ENETUNREACH
            110,  # ETIMEDOUT
            113,  # EHOSTUNREACH
        }
        return {
            "blocked": exc.errno in blocked_errnos,
            "error": type(exc).__name__,
            "errno": exc.errno,
        }


def _probe_ipv6() -> dict[str, object]:
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.settimeout(3)
    try:
        sock.connect(("2606:4700:4700::1111", 443, 0, 0))
        return {"blocked": False, "error": None, "errno": None}
    except OSError as exc:
        blocked_errnos = {97, 101, 110, 113}  # unsupported, unreachable, timeout
        return {
            "blocked": exc.errno in blocked_errnos,
            "error": type(exc).__name__,
            "errno": exc.errno,
        }
    finally:
        sock.close()


def _probe_dns() -> dict[str, object]:
    try:
        socket.getaddrinfo("example.com", 443, type=socket.SOCK_STREAM)
        return {"blocked": False, "error": None, "errno": None}
    except socket.gaierror as exc:
        return {
            "blocked": exc.errno in {socket.EAI_AGAIN, socket.EAI_NONAME},
            "error": type(exc).__name__,
            "errno": exc.errno,
        }


def _mount_audit() -> dict[str, object]:
    mountpoints: set[str] = set()
    forbidden: set[str] = set()
    mount_modes: dict[str, str] = {}
    home_prefix = "/" + "home" + "/"
    sensitive_prefixes = (
        home_prefix,
        "/root/.ssh",
        "/root/.aws",
        "/run/secrets",
        "/var/run/secrets",
        "/var/tmp/xdg_runtime_dir_",
    )
    storage_prefixes = ("/scratch", "/vast", "/weka", "/data")
    expected_host_binds = {
        "/app",
        "/harbor-control",
        "/staging",
        "/wheels",
        "/runtime-deps",
        "/logs/agent",
        "/logs/verifier",
        "/logs/artifacts",
    }
    sensitive_exact = {
        "/run/docker.sock",
        "/var/run/docker.sock",
        "/.env",
    }
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        fields = line.split()
        if len(fields) < 6:
            continue
        mountpoint = fields[4].replace("\\040", " ")
        mount_root = fields[3].replace("\\040", " ")
        mountpoints.add(mountpoint)
        if mountpoint in {"/wheels", "/runtime-deps"}:
            mount_modes[mountpoint] = (
                "ro" if "ro" in fields[5].split(",") else "rw"
            )
        candidates = (mountpoint, mount_root)
        for candidate in candidates:
            if candidate in sensitive_exact or candidate.endswith("/docker.sock"):
                forbidden.add(mountpoint)
            if any(candidate.startswith(prefix) for prefix in storage_prefixes):
                if mountpoint.startswith(storage_prefixes) or mountpoint not in expected_host_binds:
                    forbidden.add(mountpoint)
            if any(
                candidate == prefix.rstrip("/") or candidate.startswith(prefix)
                for prefix in sensitive_prefixes
            ):
                forbidden.add(mountpoint)

    required = {
        "/app",
        "/harbor-control",
        "/staging",
        "/wheels",
        "/runtime-deps",
    }
    missing = sorted(required - mountpoints)
    read_only_required = {"/wheels", "/runtime-deps"}
    writable_read_only_mounts = sorted(
        mountpoint
        for mountpoint in read_only_required
        if mount_modes.get(mountpoint) != "ro"
    )
    credential_name = re.compile(
        r"(API_KEY|ACCESS_KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL|AUTH)", re.I
    )
    credential_env_names = sorted(
        key
        for key in os.environ
        if credential_name.search(key)
        or key in {"DOCKER_CONFIG", "SSH_AUTH_SOCK", "DOCKER_HOST"}
    )
    return {
        "checked_mount_targets": sorted(mountpoints),
        "forbidden_mount_targets": sorted(forbidden),
        "missing_required_mounts": missing,
        "checked_read_only_mounts": mount_modes,
        "writable_read_only_mounts": writable_read_only_mounts,
        "credential_environment_names": credential_env_names,
        "pass": (
            not forbidden
            and not missing
            and not writable_read_only_mounts
            and not credential_env_names
        ),
    }


def _resource_observation() -> dict[str, object]:
    proc_groups: dict[str, str] = {}
    for line in Path("/proc/self/cgroup").read_text().splitlines():
        hierarchy, controllers, group_path = line.split(":", maxsplit=2)
        proc_groups[controllers or "cgroup2"] = group_path

    mount_specs: list[tuple[Path, str, str, str]] = []
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        fields = line.split()
        if "-" not in fields:
            continue
        separator = fields.index("-")
        if len(fields) <= separator + 3:
            continue
        filesystem = fields[separator + 1]
        if filesystem not in {"cgroup", "cgroup2"}:
            continue
        mountpoint = Path(fields[4].replace("\\040", " "))
        root = fields[3].replace("\\040", " ")
        super_options = fields[separator + 3]
        mount_specs.append((mountpoint, root, filesystem, super_options))

    limit_files = {
        "cpu_v2": "cpu.max",
        "memory_v2": "memory.max",
        "cpuset_v2": "cpuset.cpus.effective",
        "cpu_v1_quota": "cpu.cfs_quota_us",
        "cpu_v1_period": "cpu.cfs_period_us",
        "memory_v1": "memory.limit_in_bytes",
        "cpuset_v1": "cpuset.cpus",
    }
    observed: dict[str, set[str]] = {name: set() for name in limit_files}
    mounted_controllers: set[str] = set()
    for mountpoint, root, filesystem, super_options in mount_specs:
        if filesystem == "cgroup2":
            group_path = proc_groups.get("cgroup2", "/")
            candidates = ["cpu_v2", "memory_v2", "cpuset_v2"]
        else:
            controllers = set(super_options.split(","))
            mounted_controllers.update(controllers)
            candidates = []
            if "cpu" in controllers or "cpuacct" in controllers:
                candidates.extend(["cpu_v1_quota", "cpu_v1_period"])
            if "memory" in controllers:
                candidates.append("memory_v1")
            if "cpuset" in controllers:
                candidates.append("cpuset_v1")
            group_path = next(
                (
                    path
                    for name, path in proc_groups.items()
                    if set(name.split(",")) & controllers
                ),
                "/",
            )

        relative = group_path.lstrip("/")
        if root != "/" and group_path.startswith(root.rstrip("/")):
            relative = group_path[len(root) :].lstrip("/")
        current = mountpoint / relative
        if not current.exists():
            current = mountpoint
        while True:
            for name in candidates:
                filename = limit_files[name]
                candidate = current / filename
                try:
                    if candidate.is_file():
                        observed[name].add(candidate.read_text().strip())
                except OSError:
                    pass
            if current == mountpoint or mountpoint not in current.parents:
                break
            current = current.parent

    status = Path("/proc/self/status").read_text()
    allowed = re.search(r"^Cpus_allowed_list:\s*(.+)$", status, re.M)
    affinity_count = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None
    return {
        "cgroup_filesystems": sorted({entry[2] for entry in mount_specs}),
        "proc_cgroup_controller_groups": sorted(proc_groups),
        "mounted_v1_controllers": sorted(mounted_controllers),
        "limits_visible_at_current_or_ancestor": {
            name: sorted(values) for name, values in observed.items()
        },
        "cpus_allowed_list": allowed.group(1).strip() if allowed else None,
        "process_affinity_cpu_count": affinity_count,
    }


def test_harbor_cli_task_is_isolated() -> None:
    interfaces = [
        line.split(":", maxsplit=1)[0].strip()
        for line in Path("/proc/net/dev").read_text().splitlines()[2:]
        if ":" in line
    ]
    route_lines = [
        line
        for line in Path("/proc/net/route").read_text().splitlines()[1:]
        if line.strip()
    ]
    ipv6_interfaces = sorted(
        {
            line.split()[-1]
            for line in Path("/proc/net/if_inet6").read_text().splitlines()
            if line.split()
        }
    )
    ipv6_routes = [
        line
        for line in Path("/proc/net/ipv6_route").read_text().splitlines()
        if line.strip()
    ]
    ipv6_route_interfaces = sorted(
        {line.split()[-1] for line in ipv6_routes if line.split()}
    )
    external = _probe_connect("1.1.1.1", 443)
    external_ipv6 = _probe_ipv6()
    metadata = _probe_connect("169.254.169.254", 80)
    dns = _probe_dns()
    mount_audit = _mount_audit()

    app_probe = Path("/app/.harbor-cli-isolation-probe")
    nonce = "synthetic-harbor-uds-task-control"
    app_probe.write_text(nonce)
    app_write_read = app_probe.read_text() == nonce
    app_probe.unlink(missing_ok=True)

    resource_limits = _resource_observation()
    report = {
        "python_version": sys.version.split()[0],
        "python_311": sys.version_info[:2] == (3, 11),
        "interfaces": interfaces,
        "route_count": len(route_lines),
        "ipv6_interfaces": ipv6_interfaces,
        "ipv6_route_count": len(ipv6_routes),
        "ipv6_route_interfaces": ipv6_route_interfaces,
        "external_ip": external,
        "external_ipv6": external_ipv6,
        "external_dns": dns,
        "metadata_address": metadata,
        "app_write_read": app_write_read,
        "mount_audit": mount_audit,
        "resource_observation": resource_limits,
        "task_level_cpu_memory_limit_enforcement": "not_asserted",
    }
    Path("/logs/verifier/isolation.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )

    assert report["python_311"], f"expected Python 3.11, got {report['python_version']}"
    assert interfaces == ["lo"], f"unexpected task interfaces: {interfaces}"
    assert not route_lines, f"unexpected task routes: {route_lines}"
    assert set(ipv6_interfaces) <= {"lo"}, f"unexpected IPv6 interfaces: {ipv6_interfaces}"
    assert set(ipv6_route_interfaces) <= {"lo"}, (
        f"unexpected IPv6 routes: {ipv6_route_interfaces}"
    )
    assert external["blocked"], f"external fixed-IP connection not blocked: {external}"
    assert external_ipv6["blocked"], f"external IPv6 connection not blocked: {external_ipv6}"
    assert dns["blocked"], f"external DNS lookup not blocked: {dns}"
    assert metadata["blocked"], f"metadata connection not blocked: {metadata}"
    assert app_write_read, "task workspace write/read through Harbor did not work"
    assert mount_audit["pass"], f"unsafe or missing mounts: {mount_audit}"


if __name__ == "__main__":
    print(json.dumps(_resource_observation(), sort_keys=True))
