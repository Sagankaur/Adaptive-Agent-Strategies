#!/bin/bash
# Offline Harbor execution-server bootstrap for the pinned task image's Python 3.13.
set -euo pipefail

WORKDIR="${1:-/app}"
shift || true
PYTHON=/usr/local/bin/python3
test -x "$PYTHON" || { echo "pinned image Python 3 not found" >&2; exit 70; }
test "$#" -gt 0 || { echo "Harbor server command is missing" >&2; exit 71; }
export WORKDIR HARBOR_STAGING=/staging/env_files
export HARBOR_PYTHON="$PYTHON"
export PYTHONPATH=/runtime-deps

"$PYTHON" - <<'PY'
import importlib.metadata
import importlib.util
import sys

expected = {"fastapi": "0.162.0", "pydantic": "2.13.5", "uvicorn": "0.54.0"}
if sys.version_info[:3] != (3, 13, 7):
    raise SystemExit(f"unexpected task Python version: {sys.version.split()[0]}")
for name, version in expected.items():
    module = importlib.util.find_spec(name)
    actual = importlib.metadata.version(name)
    if module is None or actual != version or not (module.origin or "").startswith("/runtime-deps/"):
        raise SystemExit(f"runtime dependency mismatch: {name}={actual} origin={getattr(module, 'origin', None)}")
print("harbor_server_dependencies=PINNED_FROM_READ_ONLY_RUNTIME")
PY

mkdir -p "$WORKDIR"
exec "$PYTHON" "$@"
