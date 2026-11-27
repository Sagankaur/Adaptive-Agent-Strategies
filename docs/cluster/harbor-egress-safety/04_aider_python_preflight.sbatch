#!/bin/bash
# No-model preflight for a Python 3.11 Aider-style task runtime.
# This is a synthetic pytest fixture, not an Aider benchmark task.
# Stage this script, the adjacent Python harness and test fixture, and the
# existing harbor-0.23.0-uds.patch under /scratch/$USER/harbor-smoke/egress-probe.
#SBATCH --job-name=aas-aider-py311
#SBATCH --output=/scratch/%u/harbor-smoke/egress-probe/aider-py311-%j.out
#SBATCH --error=/scratch/%u/harbor-smoke/egress-probe/aider-py311-%j.err
#SBATCH --partition=cpu
#SBATCH --qos=short
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
#SBATCH --time=00:20:00

set -eo pipefail
source /etc/profile
set -euo pipefail
module load apptainer/apptainer

SCR=/scratch/$USER
ROOT=$SCR/harbor-smoke
STAGE=$ROOT/egress-probe
OUT=$STAGE/aider-py311-${SLURM_JOB_ID}
VENV=$SCR/venvs/harbor-0.23.0
SITE=$VENV/lib/python3.12/site-packages
IMAGE=$ROOT/images/aider-python311-smoke.sif
WHEELHOUSE=$OUT/wheelhouse
FIXTURE=$STAGE/aider-python-fixture
PATCH_FILE=$STAGE/harbor-0.23.0-uds.patch
HARNESS=$STAGE/04_aider_python_preflight.py
BOOTSTRAP=$STAGE/04_aider_harbor_bootstrap.sh
APPTAINER=$(command -v apptainer)
OVERLAY=$OUT/overlay
RUNTIME_DEPS=$OUT/harbor-runtime-deps

mkdir -p "$OUT" "$ROOT/images" "$WHEELHOUSE" "$OUT/bin"
exec > >(tee "$OUT/preflight.log") 2>&1
export HARBOR_TELEMETRY=off

for required in "$PATCH_FILE" "$HARNESS" "$FIXTURE/test_synthetic.py" \
  "$FIXTURE/check_network.py" "$FIXTURE/check_mounts.py" \
  "$BOOTSTRAP" \
  "$SITE/harbor/environments/singularity/singularity.py" \
  "$VENV/bin/python"; do
  [ -e "$required" ] || { echo "missing required input: $required"; exit 2; }
done
command -v patch >/dev/null || { echo "patch utility missing on compute node"; exit 3; }

df -Pk /scratch
echo "job=$SLURM_JOB_ID host=$(hostname) date=$(date -Is)"
"$APPTAINER" --version

if [ ! -s "$IMAGE" ]; then
  echo "pulling docker://python:3.11-slim into a SIF"
  "$APPTAINER" pull "$IMAGE" docker://python:3.11-slim
fi
sha256sum "$IMAGE" | tee "$OUT/image.sha256"
"$APPTAINER" inspect --json "$IMAGE" > "$OUT/image-inspect.json"

"$APPTAINER" exec --bind "$WHEELHOUSE:/wheels" "$IMAGE" \
  python3 -m pip download --only-binary=:all: --no-cache-dir --dest /wheels \
  'pytest==8.3.4' 'fastapi==0.162.0' 'uvicorn==0.54.0'
sha256sum "$WHEELHOUSE"/* | tee "$OUT/wheels.sha256"

mkdir -p "$RUNTIME_DEPS"
"$APPTAINER" exec --net --network none --writable-tmpfs --containall \
  --bind "$WHEELHOUSE:/wheels:ro" --bind "$RUNTIME_DEPS:/runtime-deps" \
  "$IMAGE" python3 -m pip install --disable-pip-version-check --no-cache-dir \
  --no-index --find-links=/wheels --target=/runtime-deps \
  'fastapi==0.162.0' 'uvicorn==0.54.0'

mkdir -p "$OVERLAY"
cp -a "$SITE/harbor" "$OVERLAY/harbor"
patch --batch --forward -p1 -d "$OVERLAY" < "$PATCH_FILE"
install -m 755 "$BOOTSTRAP" \
  "$OVERLAY/harbor/environments/singularity/bootstrap.sh"
python -m py_compile \
  "$OVERLAY/harbor/environments/singularity/singularity.py" \
  "$OVERLAY/harbor/environments/singularity/server.py"
source "$VENV/bin/activate"
python --version

cat > "$OUT/bin/singularity" <<SHIM
#!/bin/bash
exec "$APPTAINER" "\$@"
SHIM
chmod 700 "$OUT/bin/singularity"
export PATH="$OUT/bin:$PATH"
export PYTHONPATH="$OVERLAY"
export APPTAINER_CACHEDIR="$ROOT/cache_apptainer"

python "$HARNESS" \
  --image "$IMAGE" \
  --wheelhouse "$WHEELHOUSE" \
  --fixture-dir "$FIXTURE" \
  --output "$OUT"
