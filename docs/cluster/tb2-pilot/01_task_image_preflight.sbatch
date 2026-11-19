#!/bin/bash -l
# Model-free, exact-image Harbor UDS and egress preflight for the TB2 pilot.
# Submit only after the preregistration and pilot-exclusion registry are committed.
#SBATCH --job-name=aas-tb2-preflight
#SBATCH --output=/scratch/%u/tb2-pilot/preflight-%j.out
#SBATCH --error=/scratch/%u/tb2-pilot/preflight-%j.err
#SBATCH --partition=cpu
#SBATCH --qos=short
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
set -euo pipefail

SCR=/scratch/$USER
ROOT=$SCR/tb2-pilot
SNAPSHOT=$SCR/datasets/terminal-bench-2.0
TASK=$SNAPSHOT/cobol-modernization
IMAGE_DIR=$SNAPSHOT/images
IMAGE=$IMAGE_DIR/cobol-modernization-593ab9df.sif
IMAGE_REF=docker://alexgshaw/cobol-modernization@sha256:593ab9df3d83f771e927888b2d9436b380cdf7ec4d0af2a9f0802d541edebba0
HARBOR_CACHE=$ROOT/apptainer-cache
MODEL=$SCR/models/gpt-oss-20b-MXFP4.gguf
SERVER_IMAGE=$SCR/images/llama-server-cuda12-b11515.sif
HF_PY=$SCR/.venvs/hf-download/bin/python
SOURCE=$ROOT/source-preflight-$SLURM_JOB_ID
VENV=$SCR/venvs/harbor-0.23.0
STAGE=$SCR/harbor-smoke/egress-probe
PATCH_FILE=$STAGE/harbor-0.23.0-uds.patch
HARNESS=$STAGE/02_harbor_uds_smoke.py
SITE=$VENV/lib/python3.12/site-packages
OUT=$ROOT/preflight-$SLURM_JOB_ID
OVERLAY=$OUT/overlay
APPTAINER=/sw/software/apptainer/apptainer-1.3.3/apptainer/apptainer

mkdir -p "$ROOT" "$IMAGE_DIR" "$HARBOR_CACHE" "$OUT" "$OUT/bin"
exec > >(tee "$OUT/preflight.log") 2>&1
export HARBOR_TELEMETRY=off
export APPTAINER_CACHEDIR="$ROOT/apptainer-cache"
printf 'status=RUNNING\njob_id=%s\n' "$SLURM_JOB_ID" > "$ROOT/latest-preflight.txt.tmp"
mv -f "$ROOT/latest-preflight.txt.tmp" "$ROOT/latest-preflight.txt"
EXPECTED_SOURCE=$(cat "$ROOT/expected-source-commit.txt")
ARCHIVE_SHA=$(sha256sum "$ROOT/source.tar" | awk '{print $1}')
EXPECTED_ARCHIVE_SHA=$(cat "$ROOT/source-archive.sha256")
[ -n "$EXPECTED_SOURCE" ] && [ "$ARCHIVE_SHA" = "$EXPECTED_ARCHIVE_SHA" ] || { echo "source archive or commit pin mismatch"; exit 6; }
mkdir "$SOURCE"
tar -xf "$ROOT/source.tar" -C "$SOURCE"
chmod -R a-w "$SOURCE"

for required in "$TASK/task.toml" "$PATCH_FILE" "$HARNESS" "$SITE/harbor/environments/singularity/singularity.py" \
  "$MODEL" "$SERVER_IMAGE" "$HF_PY" "$SOURCE/docs/cluster/tb2-pilot/verify_tb2_snapshot.py" \
  "$SOURCE/docs/cluster/tb2-pilot/03_task_workspace_path_preflight.py"; do
  [ -e "$required" ] || { echo "missing required artifact: $required"; exit 2; }
done
source "$VENV/bin/activate"
THIS_SCRIPT_SHA=$(sha256sum "$0" | awk '{print $1}')
ARCHIVE_SCRIPT_SHA=$(sha256sum "$SOURCE/docs/cluster/tb2-pilot/01_task_image_preflight.sbatch" | awk '{print $1}')
[ "$THIS_SCRIPT_SHA" = "$ARCHIVE_SCRIPT_SHA" ] || { echo "executed preflight script differs from verified archive"; exit 6; }
command -v patch >/dev/null || { echo "patch utility missing on compute node"; exit 3; }
python - "$TASK/task.toml" <<'PY'
import sys
import tomllib
from pathlib import Path

metadata = tomllib.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if metadata.get("environment", {}).get("docker_image") != "alexgshaw/cobol-modernization:20251031":
    raise SystemExit("task metadata image differs from the preregistered image tag")
print("task_image_metadata=PASS")
PY

MODEL_SHA_EXPECTED=27cd6c432c7672cb812a92f611cf3ba7bbc35928262bb1e1253ff4ee6ae35901
SERVER_SHA_EXPECTED=dd8110164788b9deb354e06cb984214b2ef8b6b0598c2ef73dd0ab9828957d56
MODEL_SHA=$(sha256sum "$MODEL" | awk '{print $1}')
SERVER_SHA=$(sha256sum "$SERVER_IMAGE" | awk '{print $1}')
[ "$MODEL_SHA" = "$MODEL_SHA_EXPECTED" ] || { echo "pinned model SHA-256 mismatch"; exit 6; }
[ "$SERVER_SHA" = "$SERVER_SHA_EXPECTED" ] || { echo "pinned server image SHA-256 mismatch"; exit 6; }
SNAPSHOT_RESULT=$("$HF_PY" "$SOURCE/docs/cluster/tb2-pilot/verify_tb2_snapshot.py" "$SNAPSHOT")
SNAPSHOT_REV=$(python -c 'import json,sys; print(json.loads(sys.argv[1])["revision"])' "$SNAPSHOT_RESULT")
SNAPSHOT_TREE=$(python -c 'import json,sys; print(json.loads(sys.argv[1])["tree_sha256"])' "$SNAPSHOT_RESULT")
[ "$SNAPSHOT_REV" = f2e8c75e23add71613117eecc9498f53bcd7e04e ] || { echo "TB2 snapshot revision mismatch"; exit 7; }
echo "snapshot_revision=$SNAPSHOT_REV snapshot_tree_sha256=$SNAPSHOT_TREE"

echo "job=$SLURM_JOB_ID host=$(hostname) date=$(date -Is)"
echo "snapshot_task_directory_present=yes"
"$APPTAINER" --version
python --version
"$VENV/bin/harbor" --version
echo "HARBOR_TELEMETRY=$HARBOR_TELEMETRY"

# Always pull the immutable manifest into a fresh job-specific file. Never trust a cache file.
IMAGE_TMP=$IMAGE_DIR/cobol-modernization-${SLURM_JOB_ID}.sif
rm -f -- "$IMAGE_TMP"
"$APPTAINER" pull "$IMAGE_TMP" "$IMAGE_REF"
SIF_SHA=$(sha256sum "$IMAGE_TMP" | awk '{print $1}')
mv -f "$IMAGE_TMP" "$IMAGE"
PATCH_SHA=$(sha256sum "$PATCH_FILE" | awk '{print $1}')
ln -sfn "$IMAGE" "$HARBOR_CACHE/alexgshaw_cobol-modernization_20251031.sif"
test "$(readlink -f "$HARBOR_CACHE/alexgshaw_cobol-modernization_20251031.sif")" = "$(readlink -f "$IMAGE")"
echo "source_manifest_sha256=593ab9df3d83f771e927888b2d9436b380cdf7ec4d0af2a9f0802d541edebba0"
echo "task_sif_sha256=$SIF_SHA"

WORKDIR=$(python - "$TASK/environment/Dockerfile" <<'PY'
import sys
from pathlib import Path

workdir = "/app"
path = Path(sys.argv[1])
if path.exists():
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.upper().startswith("WORKDIR "):
            workdir = line.split(None, 1)[1].strip()
print(workdir)
PY
)
TASK_MOUNTS=$(python - "$TASK/task.toml" <<'PY'
import sys
import tomllib
from pathlib import Path

config = tomllib.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if config.get("environment", {}).get("mounts", []):
    raise SystemExit("task declares extra environment mounts; stop for review")
print("0")
PY
)
SENSITIVE_PATHS=$("$APPTAINER" exec --net --network none --writable-tmpfs --containall --pwd "$WORKDIR" "$IMAGE" \
  /bin/sh -c 'find "$1" \( -iname "*oracle*" -o -iname "*reference*" -o -iname "*solution*" -o -name tests -o -name test \) -print 2>/dev/null' sh "$WORKDIR")
[ "$TASK_MOUNTS" = 0 ] && [ -z "$SENSITIVE_PATHS" ] || { echo "agent workdir contains task mounts or sensitive paths; path names withheld"; exit 8; }
echo "agent_workdir_sensitive_path_count=0 task_declared_mount_count=$TASK_MOUNTS"

mkdir -p "$OVERLAY"
cp -a "$SITE/harbor" "$OVERLAY/harbor"
patch --batch --forward -p1 -d "$OVERLAY" < "$PATCH_FILE"
python -m py_compile \
  "$OVERLAY/harbor/environments/singularity/singularity.py" \
  "$OVERLAY/harbor/environments/singularity/server.py"

cat > "$OUT/bin/singularity" <<SHIM
#!/bin/bash
exec "$APPTAINER" "\$@"
SHIM
chmod 700 "$OUT/bin/singularity"
export PATH="$OUT/bin:$PATH"
export PYTHONPATH="$OVERLAY"

# Reuse the previously validated scripted Harbor probe, pointed at this exact SIF.
set +e
python "$HARNESS" --image "$IMAGE" --output "$OUT" > "$OUT/uds-egress.log" 2>&1
PROBE_RC=$?
set -e
cat "$OUT/uds-egress.log"
[ "$PROBE_RC" -eq 0 ] || { echo "PREFLIGHT_FAIL rc=$PROBE_RC"; exit 20; }

set +e
python "$SOURCE/docs/cluster/tb2-pilot/03_task_workspace_path_preflight.py" \
  --task-root "$TASK" --task-environment "$TASK/environment" --task-config "$TASK/task.toml" \
  --image "$IMAGE" --output "$OUT/task-workspace" > "$OUT/task-workspace-guard.log" 2>&1
WORKSPACE_RC=$?
set -e
[ "$WORKSPACE_RC" -eq 0 ] || { echo "PREFLIGHT_FAIL task workspace path-only guard rc=$WORKSPACE_RC; details remain on scratch"; exit 23; }
grep -E '^(harbor_uds=PASS|agent_workdir_and_staged_files_sensitive_paths=0|task_parent_tests_solution_directories_mounted=NO)$' "$OUT/task-workspace-guard.log"

ARGV=$(grep -F "Apptainer argv:" "$OUT/uds-egress.log" | tail -1 || true)
for required in "--net" "--network none" "--writable-tmpfs" "--containall" "--uds /harbor-control/control.sock"; do
  [[ "$ARGV" == *"$required"* ]] || { echo "PREFLIGHT_FAIL missing argv fragment: $required"; exit 21; }
done
[[ "$ARGV" != *"--fakeroot"* ]] || { echo "PREFLIGHT_FAIL fakeroot present"; exit 22; }

cat > "$ROOT/preflight-$SLURM_JOB_ID.txt.tmp" <<EOF
status=PASS
job_id=$SLURM_JOB_ID
task_id=cobol-modernization
source_commit=$EXPECTED_SOURCE
source_archive_sha256=$ARCHIVE_SHA
snapshot_revision=$SNAPSHOT_REV
snapshot_tree_sha256=$SNAPSHOT_TREE
model_sha256=$MODEL_SHA
server_sif_sha256=$SERVER_SHA
source_manifest_sha256=593ab9df3d83f771e927888b2d9436b380cdf7ec4d0af2a9f0802d541edebba0
task_sif_sha256=$SIF_SHA
harbor_uds_patch_sha256=$PATCH_SHA
harbor_cache_alias=alexgshaw_cobol-modernization_20251031.sif
harbor_telemetry=off
network_none=PASS
harbor_uds=PASS
agent_workspace_path_guard=PASS
external_dns_and_ip_blocked=PASS
metadata_ip_blocked=PASS
writable_tmpfs=PASS
fakeroot=absent
EOF
mv -f "$ROOT/preflight-$SLURM_JOB_ID.txt.tmp" "$ROOT/preflight-$SLURM_JOB_ID.txt"
cp "$ROOT/preflight-$SLURM_JOB_ID.txt" "$ROOT/latest-preflight.txt.tmp"
mv -f "$ROOT/latest-preflight.txt.tmp" "$ROOT/latest-preflight.txt"
echo "PREFLIGHT_STATUS=PASS record=$ROOT/latest-preflight.txt"
