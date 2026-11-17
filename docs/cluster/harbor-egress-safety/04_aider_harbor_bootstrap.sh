#!/bin/bash
# Network-free Harbor execution-server bootstrap for the synthetic preflight.
set -euo pipefail

WORKDIR="${1:-/app}"
shift || true
export HARBOR_STAGING=/staging/env_files
export PYTHONPATH="/runtime-deps${PYTHONPATH:+:$PYTHONPATH}"
echo "aider_preflight_bootstrap=ready python=$(python3 --version 2>&1)"
python3 -c 'import fastapi, pydantic, uvicorn; print("harbor_server_dependencies=ready")'
mkdir -p "$WORKDIR"
exec python3 "$@"
