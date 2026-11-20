#!/bin/bash
# Build and inspect the pinned Aider-style Python runtime; no benchmark/model.
# Stage beside the existing Harbor egress fixtures under:
#   /scratch/$USER/harbor-smoke/egress-probe/
# Submit from Rohan with:
#   sbatch docs/cluster/harbor-egress-safety/06_build_aider_python_runtime.sbatch
# After it completes, run the normal synthetic CLI fixture with:
#   sbatch --export=ALL,AAS_TASK_IMAGE=/scratch/$USER/harbor-smoke/images/aider-python311-buildpack-jammy.sif \
#     docs/cluster/harbor-egress-safety/05_normal_cli_synthetic_trial.sbatch
# Fakeroot is used only for construction of the SIF; Harbor task execution
# below and in the follow-up job does not use fakeroot.
#SBATCH --job-name=aas-aider-image
#SBATCH --output=/scratch/%u/harbor-smoke/egress-probe/aider-image-%j.out
#SBATCH --error=/scratch/%u/harbor-smoke/egress-probe/aider-image-%j.err
#SBATCH --partition=cpu
#SBATCH --qos=short
#SBATCH --cpus-per-task=2
#SBATCH --mem=10G
#SBATCH --time=00:45:00

set -eo pipefail
source /etc/profile
set -euo pipefail
module load apptainer/apptainer

SCR=/scratch/$USER
ROOT=$SCR/harbor-smoke
STAGE=$ROOT/egress-probe
OUT=$STAGE/aider-runtime-${SLURM_JOB_ID}
DEF=$STAGE/aider-python311-buildpack.def
IMAGE=$ROOT/images/aider-python311-buildpack-jammy.sif
TMP_IMAGE=$OUT/aider-python311-buildpack-jammy.sif
APPTAINER=$(command -v apptainer)

mkdir -p "$OUT" "$ROOT/images"
exec > >(tee "$OUT/build-and-runtime.log") 2>&1
echo "job=$SLURM_JOB_ID host=$(hostname) date=$(date -Is)"
echo "architecture=$(uname -m)"
df -h /scratch
"$APPTAINER" --version
[ -s "$DEF" ] || { echo "missing definition file: $DEF"; exit 2; }

if [ ! -s "$IMAGE" ]; then
  rm -f "$TMP_IMAGE"
  echo "building Aider Python runtime SIF; fakeroot is build-only"
  "$APPTAINER" build --fakeroot "$TMP_IMAGE" "$DEF"
  mv "$TMP_IMAGE" "$IMAGE"
else
  echo "using previously built runtime SIF"
fi

"$APPTAINER" inspect --json "$IMAGE" > "$OUT/image-inspect.json"
"$APPTAINER" inspect --labels "$IMAGE" > "$OUT/image-labels.txt"
sha256sum "$DEF" "$IMAGE" | tee "$OUT/input-image-sha256sums.txt"

# Exercise the adapter's own Python test-dependency installation in an
# isolated task-like namespace. pytest is preinstalled, so pip must report it
# satisfied without reaching an index.
"$APPTAINER" exec --net --network none --writable-tmpfs --containall \
  --no-mount home,tmp,bind-paths "$IMAGE" /bin/bash -lc '
    set -euo pipefail
    test "$(id -u)" -ne 0
    python3 -c "import sys; assert sys.version_info[:2] == (3, 11), sys.version"
    python3 --version
    python3 -m pip --version
    python3 -m pytest --version
    for command in curl tmux asciinema git gcc make; do command -v "$command"; done
    pip3 install --disable-pip-version-check --no-cache-dir pytest \
      > /tmp/aider-pip-offline.log 2>&1
    cat /tmp/aider-pip-offline.log
    grep -q "Requirement already satisfied: pytest" /tmp/aider-pip-offline.log
    ! grep -q "Looking in indexes:" /tmp/aider-pip-offline.log
    echo "task_runtime=PASS fakeroot=no network=none pip_pytest=preinstalled"
  '

echo "image_and_runtime_status=PASS"
echo "artifact_dir=$OUT"
