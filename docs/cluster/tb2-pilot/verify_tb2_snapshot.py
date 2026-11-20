#!/usr/bin/env python3
"""Verify a local TB2 snapshot against pinned Hugging Face metadata without printing task contents."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from huggingface_hub import HfApi

REPO_ID = "harborframework/terminal-bench-2.0"
REVISION = "f2e8c75e23add71613117eecc9498f53bcd7e04e"


def _local_git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def verify_snapshot(root: Path) -> dict[str, object]:
    api = HfApi()
    info = api.repo_info(REPO_ID, repo_type="dataset", revision=REVISION)
    if info.sha != REVISION:
        raise ValueError("Hub did not resolve the requested immutable TB2 revision")

    remote = {
        entry.path: entry
        for entry in api.list_repo_tree(REPO_ID, repo_type="dataset", revision=REVISION, recursive=True)
        if hasattr(entry, "size")
    }
    local: dict[str, Path] = {}
    for path in root.rglob("*"):
        if ".cache" in path.relative_to(root).parts:
            continue
        if path.is_file():
            local[path.relative_to(root).as_posix()] = path

    if local.keys() != remote.keys():
        raise ValueError("local TB2 file inventory differs from the pinned Hub revision")

    content_hashes: list[tuple[str, str]] = []
    total_bytes = 0
    for relative, path in sorted(local.items()):
        entry = remote[relative]
        size = path.stat().st_size
        if size != entry.size:
            raise ValueError("local TB2 file sizes differ from the pinned Hub revision")
        total_bytes += size
        lfs = getattr(entry, "lfs", None)
        if lfs is not None:
            lfs_sha256 = (
                lfs.get("sha256") or lfs.get("oid")
                if isinstance(lfs, dict)
                else getattr(lfs, "sha256", None) or getattr(lfs, "oid", None)
            )
            if lfs_sha256 and lfs_sha256.startswith("sha256:"):
                lfs_sha256 = lfs_sha256.split(":", maxsplit=1)[1]
            if not lfs_sha256 or len(lfs_sha256) != 64:
                raise ValueError("Hub returned an unsupported LFS object identifier")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != lfs_sha256:
                raise ValueError("local TB2 file content differs from the pinned Hub LFS object")
        else:
            digest = _local_git_blob_sha1(path)
            if digest != entry.blob_id:
                raise ValueError("local TB2 file content differs from the pinned Hub Git object")
        content_hashes.append((relative, digest))

    tree = hashlib.sha256()
    for relative, digest in content_hashes:
        tree.update(relative.encode("utf-8"))
        tree.update(b"\0")
        tree.update(digest.encode("ascii"))
        tree.update(b"\n")
    return {
        "revision": REVISION,
        "files": len(local),
        "bytes": total_bytes,
        "tree_sha256": tree.hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    result = verify_snapshot(args.snapshot)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
