#!/usr/bin/env python3
"""Compare candidate TB-Pro base images without starting their containers."""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


IMAGES = {
    "python_3_13": {
        "tbpro": "skylensage-registry.cn-hangzhou.cr.aliyuncs.com/instances/1124:t-bench-python-3-13",
        "ghcr": "ghcr.io/laude-institute/t-bench/python-3-13:20250620@sha256:10dd0648b5339468ba39b2df90c1a28745faf8622e7552f85446611e2e992110",
    },
    "ubuntu_24_04": {
        "tbpro": "skylensage-registry.cn-hangzhou.cr.aliyuncs.com/instances/1124:t-bench-ubuntu-24-04",
        "ghcr": "ghcr.io/laude-institute/t-bench/ubuntu-24-04:20250624@sha256:9ae5033b4f62fbffd63896353f2c8e02939764fac81311608e4e731f0b4a8db5",
    },
}


def run(command: list[str], *, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def inspect_image(ref: str) -> dict[str, Any]:
    image = json.loads(run(["docker", "image", "inspect", ref]).stdout)[0]
    config = image.get("Config") or {}
    return {
        "requested_ref": ref,
        "image_id": image.get("Id"),
        "repo_digests": sorted(image.get("RepoDigests") or []),
        "os": image.get("Os"),
        "architecture": image.get("Architecture"),
        "rootfs_diff_ids": image.get("RootFS", {}).get("Layers", []),
        "config_sha256": canonical_hash(config),
        "config_summary": {
            "env_keys": sorted(
                entry.split("=", 1)[0] for entry in config.get("Env", [])
            ),
            "cmd": config.get("Cmd"),
            "entrypoint": config.get("Entrypoint"),
            "working_dir": config.get("WorkingDir"),
            "user": config.get("User"),
            "labels": config.get("Labels"),
            "volumes": sorted((config.get("Volumes") or {}).keys()),
            "healthcheck": config.get("Healthcheck"),
            "stop_signal": config.get("StopSignal"),
        },
    }


def hash_member(stream: Any) -> str:
    digest = hashlib.sha256()
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest()


def normalize_tar_path(name: str) -> str:
    while name.startswith("./"):
        name = name[2:]
    name = name.rstrip("/")
    if name in ("", "."):
        return "/"
    return "/" + str(PurePosixPath(name))


def rootfs_inventory(ref: str) -> tuple[list[dict[str, Any]], str]:
    """Export (but never run) an image and hash its visible merged rootfs."""
    created = run(["docker", "create", ref]).stdout.strip()
    try:
        with tempfile.NamedTemporaryFile(suffix=".tar") as archive:
            exported = subprocess.run(
                ["docker", "export", created],
                check=True,
                stdout=archive,
                stderr=subprocess.PIPE,
                text=True,
                timeout=900,
            )
            del exported
            archive.flush()
            archive.seek(0)
            entries: list[dict[str, Any]] = []
            with tarfile.open(fileobj=archive, mode="r:") as tar:
                for member in tar:
                    path = normalize_tar_path(member.name)
                    entry: dict[str, Any] = {
                        "path": path,
                        "mode": member.mode,
                        "uid": member.uid,
                        "gid": member.gid,
                        "type": member.type.decode("ascii", errors="replace")
                        if isinstance(member.type, bytes)
                        else str(member.type),
                        "size": member.size,
                        "pax_xattrs": {
                            key: value
                            for key, value in sorted(member.pax_headers.items())
                            if key.startswith("SCHILY.xattr.")
                        },
                    }
                    if member.isfile():
                        content = tar.extractfile(member)
                        if content is None:
                            raise RuntimeError(f"cannot read exported file {path}")
                        entry["sha256"] = hash_member(content)
                    elif member.issym() or member.islnk():
                        entry["link"] = member.linkname
                    entries.append(entry)
            entries.sort(key=lambda entry: entry["path"])
            manifest_digest = canonical_hash(entries)
            return entries, manifest_digest
    finally:
        subprocess.run(
            ["docker", "rm", created],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )


def compare_pair(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_by_path = {item["path"]: item for item in left["inventory"]}
    right_by_path = {item["path"]: item for item in right["inventory"]}
    all_paths = sorted(left_by_path.keys() | right_by_path.keys())
    differences = [
        {
            "path": path,
            "tbpro": left_by_path.get(path),
            "ghcr": right_by_path.get(path),
        }
        for path in all_paths
        if left_by_path.get(path) != right_by_path.get(path)
    ]
    left_config = left["image"]["config_sha256"]
    right_config = right["image"]["config_sha256"]
    left_layers = left["image"]["rootfs_diff_ids"]
    right_layers = right["image"]["rootfs_diff_ids"]
    rootfs_equal = left["rootfs_manifest_sha256"] == right["rootfs_manifest_sha256"]
    config_equal = left_config == right_config
    layers_equal = left_layers == right_layers
    platform_equal = (
        left["image"]["os"], left["image"]["architecture"]
    ) == (right["image"]["os"], right["image"]["architecture"])
    return {
        "platform_equal": platform_equal,
        "config_equal": config_equal,
        "layer_diff_ids_equal": layers_equal,
        "exported_rootfs_inventory_equal": rootfs_equal,
        "tbpro_entries": len(left_by_path),
        "ghcr_entries": len(right_by_path),
        "different_paths_count": len(differences),
        "first_100_differences": differences[:100],
        "all_checks_equal": platform_equal and config_equal and layers_equal and rootfs_equal,
        "interpretation": (
            "The platform, image config, uncompressed layer IDs, and exported merged-rootfs inventory match. "
            "This is strong evidence of content equivalence for the pulled references, but not proof "
            "that the GHCR image was the historical source of the TB-Pro tag."
            if platform_equal and config_equal and layers_equal and rootfs_equal
            else "At least one compared platform, config, layer-ID, or exported-rootfs check differs."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "schema_version": 1,
        "run_metadata": {
            "utc_started": dt.datetime.now(dt.timezone.utc).isoformat(),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_ref": os.environ.get("GITHUB_REF"),
            "runner_os": os.environ.get("RUNNER_OS"),
            "runner_arch": os.environ.get("RUNNER_ARCH"),
        },
        "safety": "Images were pulled, inspected, and exported only. No container was started.",
        "comparison_scope": (
            "GHCR references are digest-pinned; TB-Pro references are the mutable tags currently "
            "named in the pinned task Dockerfiles. Resolved repo digests and config IDs are recorded. "
            "The rootfs inventory hashes exported path/type/mode/owner/content/symlink metadata."
        ),
        "pairs": {},
    }
    inventory_path = args.output_dir / "rootfs-inventories.jsonl.gz"
    with gzip.open(inventory_path, "wt", encoding="utf-8") as inventories:
        for name, refs in IMAGES.items():
            pair: dict[str, Any] = {"references": refs, "images": {}, "comparison": None}
            errors: dict[str, str] = {}
            for side, ref in refs.items():
                try:
                    run(["docker", "pull", ref], timeout=1200)
                    image = inspect_image(ref)
                    pair["images"][side] = {"image": image}
                    entries, rootfs_hash = rootfs_inventory(ref)
                    image_result = {
                        "image": image,
                        "rootfs_manifest_sha256": rootfs_hash,
                        "inventory": entries,
                    }
                    pair["images"][side] = {
                        "image": image,
                        "rootfs_manifest_sha256": rootfs_hash,
                        "rootfs_entry_count": len(entries),
                    }
                    inventories.write(
                        json.dumps(
                            {"pair": name, "side": side, "entries": entries},
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        + "\n"
                    )
                    pair.setdefault("_results", {})[side] = image_result
                except Exception as exc:  # preserve partial evidence for failed pulls
                    detail = str(exc)
                    if isinstance(exc, subprocess.CalledProcessError):
                        detail += f"; stderr={exc.stderr!r}; stdout={exc.stdout!r}"
                    errors[side] = f"{type(exc).__name__}: {detail}"
            if "tbpro" in pair.get("_results", {}) and "ghcr" in pair.get("_results", {}):
                pair["comparison"] = compare_pair(
                    pair["_results"]["tbpro"], pair["_results"]["ghcr"]
                )
            pair.pop("_results", None)
            pair["errors"] = errors
            report["pairs"][name] = pair

    report_path = args.output_dir / "comparison-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if any(pair["errors"] for pair in report["pairs"].values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
