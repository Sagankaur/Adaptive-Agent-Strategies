#!/bin/bash
# Scripted Harbor 0.23.0 UDS + egress smoke. No model, benchmark task, or oracle.
# Stage this file, 02_harbor_uds_smoke.py, and harbor-0.23.0-uds.patch at:
# /scratch/$USER/harbor-smoke/egress-probe/
#SBATCH --job-name=aas-harbor-uds
#SBATCH --output=/scratch/%u/harbor-smoke/egress-probe/uds-%j.out
#SBATCH --error=/scratch/%u/harbor-smoke/egress-probe/uds-%j.err
#SBATCH --partition=cpu
#SBATCH --qos=short
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:10:00
set -euo pipefail

SCR=/scratch/$USER
ROOT=$SCR/harbor-smoke
STAGE=$ROOT/egress-probe
OUT=$STAGE/uds-$SLURM_JOB_ID
VENV=$SCR/venvs/harbor-0.23.0
IMAGE=$ROOT/images/harbor-smoke-python312.sif
PATCH_FILE=$STAGE/harbor-0.23.0-uds.patch
HARNESS=$STAGE/02_harbor_uds_smoke.py
SITE=$VENV/lib/python3.12/site-packages
OVERLAY=$OUT/overlay
APPTAINER=/sw/software/apptainer/apptainer-1.3.3/apptainer/apptainer

mkdir -p "$OUT" "$OUT/bin"
exec > >(tee "$OUT/uds-smoke.log") 2>&1
export HARBOR_TELEMETRY=off

for required in "$IMAGE" "$PATCH_FILE" "$HARNESS" "$SITE/harbor/environments/singularity/singularity.py"; do
  [ -e "$required" ] || { echo "missing required artifact: $required"; exit 2; }
done
command -v patch >/dev/null || { echo "patch utility missing on compute node"; exit 3; }

echo "job=$SLURM_JOB_ID host=$(hostname) date=$(date -Is)"
"$APPTAINER" --version
source "$VENV/bin/activate"
python --version
"$VENV/bin/harbor" --version
echo "HARBOR_TELEMETRY=$HARBOR_TELEMETRY"
echo "source_singularity_sha256=$(sha256sum "$SITE/harbor/environments/singularity/singularity.py" | cut -d' ' -f1)"
echo "patch_sha256=$(sha256sum "$PATCH_FILE" | cut -d' ' -f1)"

mkdir -p "$OVERLAY"
cp -a "$SITE/harbor" "$OVERLAY/harbor"
patch --batch --forward -p1 -d "$OVERLAY" < "$PATCH_FILE"
python -m py_compile \
  "$OVERLAY/harbor/environments/singularity/singularity.py" \
  "$OVERLAY/harbor/environments/singularity/server.py"
echo "patched_singularity_sha256=$(sha256sum "$OVERLAY/harbor/environments/singularity/singularity.py" | cut -d' ' -f1)"
echo "patched_server_sha256=$(sha256sum "$OVERLAY/harbor/environments/singularity/server.py" | cut -d' ' -f1)"

cat > "$OUT/bin/singularity" <<SHIM
#!/bin/bash
exec "$APPTAINER" "\$@"
SHIM
chmod 700 "$OUT/bin/singularity"
export PATH="$OUT/bin:$PATH"
export PYTHONPATH="$OVERLAY"
export APPTAINER_CACHEDIR="$ROOT/cache_apptainer"

python "$HARNESS" --image "$IMAGE" --output "$OUT"
