#!/usr/bin/env python3
"""Create a hash-locked offline Harbor server runtime from downloaded wheels."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from email.parser import Parser
from pathlib import Path

EXPECTED = {"fastapi": "0.162.0", "pydantic": "2.13.5", "uvicorn": "0.54.0"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _wheel_metadata(path: Path) -> tuple[str, str]:
    with zipfile.ZipFile(path) as archive:
        metadata_paths = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(metadata_paths) != 1:
            raise ValueError(f"wheel must contain exactly one METADATA: {path.name}")
        metadata = Parser().parsestr(archive.read(metadata_paths[0]).decode("utf-8"))
    name = metadata.get("Name")
    version = metadata.get("Version")
    if not name or not version or not re.fullmatch(r"[A-Za-z0-9_.+-]+", name + version):
        raise ValueError(f"invalid wheel metadata: {path.name}")
    return name, version


def _write_lock(wheelhouse: Path, output: Path) -> dict[str, str]:
    wheels = sorted(wheelhouse.glob("*.whl"))
    if not wheels:
        raise ValueError("wheelhouse is empty")
    packages: dict[str, tuple[str, str, str]] = {}
    for wheel in wheels:
        name, version = _wheel_metadata(wheel)
        key = re.sub(r"[-_.]+", "-", name).lower()
        record = (name, version, _sha256(wheel))
        if key in packages and packages[key] != record:
            raise ValueError(f"multiple versions of {name} in wheelhouse")
        packages[key] = record
    for name, version in EXPECTED.items():
        if packages.get(name, (None, None, None))[1] != version:
            raise ValueError(f"expected {name}=={version} in wheelhouse")
    lines = [f"{name}=={version} --hash=sha256:{digest}" for name, version, digest in sorted(packages.values())]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {name: version for name, version, _ in sorted(packages.values())}


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative + b"\0" + bytes.fromhex(_sha256(path)) + b"\n")
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheelhouse", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--runtime-deps", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--task-sif-sha256", required=True)
    parser.add_argument("--mode", choices=("lock", "manifest"), required=True)
    args = parser.parse_args()
    if args.mode == "lock":
        versions = _write_lock(args.wheelhouse, args.lock)
        print(f"wheel_lock_packages={len(versions)}")
        print(f"wheel_lock_sha256={_sha256(args.lock)}")
        return
    versions = {}
    for path in sorted(args.runtime_deps.glob("*.dist-info/METADATA")):
        metadata = Parser().parsestr(path.read_text(encoding="utf-8"))
        key = re.sub(r"[-_.]+", "-", metadata["Name"]).lower()
        versions[key] = metadata["Version"]
    if not versions:
        raise ValueError("installed runtime has no package metadata")
    manifest = {
        "python": "3.13.7",
        "task_sif_sha256": args.task_sif_sha256,
        "lock_sha256": _sha256(args.lock),
        "wheelhouse_sha256": _tree_sha256(args.wheelhouse),
        "runtime_tree_sha256": _tree_sha256(args.runtime_deps),
        "packages": dict(sorted(versions.items(), key=lambda item: item[0].lower())),
    }
    if any(versions.get(name) != version for name, version in EXPECTED.items()):
        raise ValueError("runtime manifest does not contain the expected direct dependency versions")
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"runtime_tree_sha256={manifest['runtime_tree_sha256']}")
    print(f"runtime_lock_sha256={manifest['lock_sha256']}")
    print(f"runtime_package_count={len(versions)}")


if __name__ == "__main__":
    main()
