#!/bin/bash -l
# Prepare a hash-locked Harbor server runtime using Python in the pinned task SIF.
# This setup job downloads wheels only; it runs no task, model, Oracle, or verifier.
#SBATCH --job-name=aas-tb2-runtime
#SBATCH --output=/scratch/%u/tb2-pilot/runtime-prep-%j.out
#SBATCH --error=/scratch/%u/tb2-pilot/runtime-prep-%j.err
#SBATCH --partition=cpu
#SBATCH --qos=short
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
set -eo pipefail
source /etc/profile
set -euo pipefail
module load apptainer/apptainer

SCR=/scratch/$USER
ROOT=$SCR/tb2-pilot
SNAPSHOT=$SCR/datasets/terminal-bench-2.0
IMAGE=$SNAPSHOT/images/cobol-modernization-593ab9df.sif
OUT=$ROOT/runtime-prep-$SLURM_JOB_ID
WHEELHOUSE=$OUT/wheelhouse
RUNTIME_DEPS=$OUT/runtime-deps
LOCK=$OUT/requirements.lock
MANIFEST=$OUT/runtime-manifest.json
SOURCE=$ROOT/source-runtime-$SLURM_JOB_ID
EXPECTED_SOURCE=$(cat "$ROOT/expected-source-commit.txt")
ARCHIVE_SHA=$(sha256sum "$ROOT/source.tar" | awk '{print $1}')
EXPECTED_ARCHIVE_SHA=$(cat "$ROOT/source-archive.sha256")
PREP=$SOURCE/docs/cluster/tb2-pilot/04_prepare_harbor_runtime.py
THIS_SCRIPT_SHA=$(sha256sum "$0" | awk '{print $1}')

mkdir -p "$OUT" "$WHEELHOUSE" "$RUNTIME_DEPS"
exec > >(tee "$OUT/runtime-prep.log") 2>&1
[ -n "$EXPECTED_SOURCE" ] && [ "$ARCHIVE_SHA" = "$EXPECTED_ARCHIVE_SHA" ] || { echo "source archive pin mismatch"; exit 5; }
mkdir "$SOURCE"
tar -xf "$ROOT/source.tar" -C "$SOURCE"
chmod -R a-w "$SOURCE"
[ "$THIS_SCRIPT_SHA" = "$(sha256sum "$SOURCE/docs/cluster/tb2-pilot/04_prepare_harbor_runtime.sbatch" | awk '{print $1}')" ] || { echo "script differs from committed source archive"; exit 5; }
[ -s "$IMAGE" ] && [ -f "$PREP" ] || { echo "pinned image or helper is missing"; exit 2; }
IMAGE_SHA=$(sha256sum "$IMAGE" | awk '{print $1}')
[ "$IMAGE_SHA" = e7fc37ce09d4ee50e4a71a6e2c9941c0cdacdeb979fcaf99182728b3d0e0dd49 ] || { echo "task SIF digest changed"; exit 5; }

APPTAINER=$(command -v apptainer)
echo "job=$SLURM_JOB_ID host=$(hostname) source_commit=$EXPECTED_SOURCE"
"$APPTAINER" --version
sha256sum "$IMAGE"

# Network access is used only to fetch binary Python wheels. Nothing from the
# task workspace is executed and no task/model/Oracle/verifier is started.
"$APPTAINER" exec --bind "$WHEELHOUSE:/wheels" "$IMAGE" \
  /usr/local/bin/python3 -m pip download --disable-pip-version-check \
  --only-binary=:all: --no-cache-dir --dest /wheels \
  'fastapi==0.162.0' 'pydantic==2.13.5' 'uvicorn==0.54.0'

python3 "$PREP" --mode lock --wheelhouse "$WHEELHOUSE" --lock "$LOCK" \
  --runtime-deps "$RUNTIME_DEPS" --manifest "$MANIFEST" --task-sif-sha256 "$IMAGE_SHA"

# Install every pinned wheel offline into a dedicated directory. The task
# runtime later sees this directory only through a read-only bind mount.
"$APPTAINER" exec --net --network none --writable-tmpfs --containall \
  --bind "$WHEELHOUSE:/wheels:ro" --bind "$LOCK:/requirements.lock:ro" \
  --bind "$RUNTIME_DEPS:/runtime-deps" "$IMAGE" \
  /usr/local/bin/python3 -m pip install --disable-pip-version-check --no-cache-dir \
  --no-index --find-links=/wheels --require-hashes --target=/runtime-deps \
  -r /requirements.lock

"$APPTAINER" exec --net --network none --containall \
  --bind "$RUNTIME_DEPS:/runtime-deps:ro" "$IMAGE" /bin/sh -c '
  export PYTHONPATH=/runtime-deps
  /usr/local/bin/python3 -m pip check
  /usr/local/bin/python3 - <<"PY"
import importlib.metadata, importlib.util, sys
assert sys.version_info[:3] == (3, 13, 7), sys.version
for name, version in {"fastapi": "0.162.0", "pydantic": "2.13.5", "uvicorn": "0.54.0"}.items():
    spec = importlib.util.find_spec(name)
    assert spec and spec.origin and spec.origin.startswith("/runtime-deps/"), (name, spec)
    assert importlib.metadata.version(name) == version, name
print("task_python=3.13.7 runtime_dependencies=PASS read_only_mount=PASS")
PY
'

chmod -R a-w "$RUNTIME_DEPS" "$WHEELHOUSE"
python3 "$PREP" --mode manifest --wheelhouse "$WHEELHOUSE" --lock "$LOCK" \
  --runtime-deps "$RUNTIME_DEPS" --manifest "$MANIFEST" --task-sif-sha256 "$IMAGE_SHA"
cp "$MANIFEST" "$ROOT/runtime-manifest-$SLURM_JOB_ID.json"
echo "RUNTIME_PREP_STATUS=PASS output=$OUT manifest=$ROOT/runtime-manifest-$SLURM_JOB_ID.json"
