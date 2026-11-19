#!/bin/bash
# One no-model Harbor CLI trial on a synthetic task. No benchmark task, task
# text, hidden test, Oracle, or reference solution is used.
#SBATCH --job-name=aas-harbor-cli-probe
#SBATCH --output=/scratch/%u/harbor-smoke/egress-probe/harbor-cli-%j.out
#SBATCH --error=/scratch/%u/harbor-smoke/egress-probe/harbor-cli-%j.err
#SBATCH --partition=cpu
#SBATCH --qos=short
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:15:00

set -eo pipefail
source /etc/profile
set -euo pipefail
module load apptainer/apptainer

SCR=/scratch/$USER
ROOT=$SCR/harbor-smoke
STAGE=$ROOT/egress-probe
OUT=$STAGE/harbor-cli-${SLURM_JOB_ID}
VENV=$SCR/venvs/harbor-0.23.0
SITE=$VENV/lib/python3.12/site-packages
IMAGE=${AAS_TASK_IMAGE:-$ROOT/images/aider-python311-smoke.sif}
WHEELHOUSE=$STAGE/aider-py311-4801425/wheelhouse
RUNTIME_DEPS=$STAGE/aider-py311-4801425/harbor-runtime-deps
PATCH_FILE=$STAGE/harbor-0.23.0-uds.patch
BOOTSTRAP=$STAGE/04_aider_harbor_bootstrap.sh
FIXTURE=$STAGE/05_trial_fixture
TASK=$OUT/synthetic-python-isolation
OVERLAY=$OUT/overlay
APPTAINER=$(command -v apptainer)
LOCAL_TMP=

mkdir -p "$OUT" "$OUT/bin" "$TASK/tests" "$TASK/environment" "$TASK/app"
exec > >(tee "$OUT/slurm.log") 2>&1
export HARBOR_TELEMETRY=off
export APPTAINER_CACHEDIR=$ROOT/cache_apptainer
if [ ! -d /data ] || [ ! -w /data ]; then
  echo "local /data scratch is unavailable; refusing a slow shared-filesystem SIF conversion"
  exit 4
fi
mkdir -p "/data/$USER"
DATA_FREE_KB=$(df -Pk /data | awk 'NR == 2 {print $4}')
if [ -z "$DATA_FREE_KB" ] || [ "$DATA_FREE_KB" -lt 6291456 ]; then
  echo "local /data scratch has less than 6 GiB free; refusing SIF conversion"
  df -h /data
  exit 4
fi
LOCAL_TMP=$(mktemp -d "/data/$USER/aas-harbor-cli-${SLURM_JOB_ID}.XXXXXX")
TMPDIR=$LOCAL_TMP
export APPTAINER_TMPDIR=$LOCAL_TMP
export TMPDIR
trap 'case "$LOCAL_TMP" in "/data/$USER/aas-harbor-cli-$SLURM_JOB_ID."*) rm -rf -- "$LOCAL_TMP";; esac' EXIT
echo "container_tmp=local_nvme"
df -h /data
mkdir -p "$TMPDIR"

for required in "$IMAGE" "$WHEELHOUSE/pytest-8.3.4-py3-none-any.whl" \
  "$RUNTIME_DEPS/fastapi" "$PATCH_FILE" "$BOOTSTRAP" \
  "$FIXTURE/task.toml.in" "$FIXTURE/instruction.md" \
  "$FIXTURE/environment/Dockerfile" \
  "$FIXTURE/tests/test.sh" "$FIXTURE/tests/test_isolation.py" \
  "$FIXTURE/postflight.py" \
  "$SITE/harbor/environments/singularity/singularity.py" "$VENV/bin/harbor"; do
  [ -e "$required" ] || { echo "missing required input: $required"; exit 2; }
done
command -v patch >/dev/null || { echo "patch utility missing on compute node"; exit 3; }

echo "job=$SLURM_JOB_ID date=$(date -Is)"
echo "task_image=$IMAGE"
df -h /scratch
"$APPTAINER" --version
source "$VENV/bin/activate"
python --version
harbor --version
sha256sum "$IMAGE" "$PATCH_FILE" "$WHEELHOUSE"/*.whl > "$OUT/input-sha256sums.txt"
echo "harbor_telemetry=$HARBOR_TELEMETRY"

mkdir -p "$OVERLAY"
cp -a "$SITE/harbor" "$OVERLAY/harbor"
patch --batch --forward -p1 -d "$OVERLAY" < "$PATCH_FILE"
python -m py_compile \
  "$OVERLAY/harbor/environments/singularity/singularity.py" \
  "$OVERLAY/harbor/environments/singularity/server.py"
install -m 755 "$BOOTSTRAP" \
  "$OVERLAY/harbor/environments/singularity/bootstrap.sh"
python "$FIXTURE/tests/test_isolation.py" > "$OUT/host-resource-observation.json"
python - <<'PY' > "$OUT/provider-resource-capabilities.json"
import json
from harbor.environments.singularity.singularity import SingularityEnvironment

print(json.dumps(SingularityEnvironment.resource_capabilities().model_dump(), sort_keys=True))
PY
sha256sum \
  "$SITE/harbor/environments/singularity/singularity.py" \
  "$OVERLAY/harbor/environments/singularity/singularity.py" \
  "$OVERLAY/harbor/environments/singularity/server.py" > "$OUT/provider-sha256sums.txt"

cat > "$OUT/bin/singularity" <<SHIM
#!/bin/bash
exec "$APPTAINER" "\$@"
SHIM
chmod 700 "$OUT/bin/singularity"
export PATH="$OUT/bin:$PATH"
export PYTHONPATH="$OVERLAY"

sed "s|@@IMAGE@@|$IMAGE|g" "$FIXTURE/task.toml.in" > "$TASK/task.toml"
cp "$FIXTURE/instruction.md" "$TASK/instruction.md"
cp "$FIXTURE/environment/Dockerfile" "$TASK/environment/Dockerfile"
cp "$FIXTURE/tests/test.sh" "$TASK/tests/test.sh"
cp "$FIXTURE/tests/test_isolation.py" "$TASK/tests/test_isolation.py"
chmod 755 "$TASK/tests/test.sh"

cat > "$OUT/job.yaml" <<EOF
job_name: harbor_cli_synthetic_isolation_$SLURM_JOB_ID
jobs_dir: $OUT/harbor_jobs
n_attempts: 1
n_concurrent_trials: 1
quiet: true
environment:
  type: singularity
  kwargs:
    singularity_no_mount: "home,tmp,bind-paths"
    singularity_image_cache_dir: "$ROOT/cache_apptainer"
  mounts:
    - type: bind
      source: "$TASK/app"
      target: /app
    - type: bind
      source: "$WHEELHOUSE"
      target: /wheels
      read_only: true
    - type: bind
      source: "$RUNTIME_DEPS"
      target: /runtime-deps
      read_only: true
agents:
  - name: nop
tasks:
  - path: $TASK
EOF

set +e
harbor run --config "$OUT/job.yaml" --jobs-dir "$OUT/harbor_jobs" \
  --n-concurrent 1 --quiet > "$OUT/harbor-run.log" 2>&1
HARBOR_RC=$?
set -e
echo "$HARBOR_RC" > "$OUT/harbor-cli-exit-code.txt"
cat "$OUT/harbor-run.log"

python "$FIXTURE/postflight.py" \
  --output "$OUT" \
  --jobs-dir "$OUT/harbor_jobs" \
  --image "$IMAGE" \
  --pytest-version 8.3.4 \
  --host-resource "$OUT/host-resource-observation.json" \
  --provider-capabilities "$OUT/provider-resource-capabilities.json" \
  --harbor-exit-code "$HARBOR_RC"
