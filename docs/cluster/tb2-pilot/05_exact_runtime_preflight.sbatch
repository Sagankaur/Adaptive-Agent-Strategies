#!/bin/bash -l
# Exact-image, no-model Harbor/UDS/network check using the pinned Python 3.13 runtime.
# This is a new model-free gate; it does not resume the stopped 2026-11-19 pilot.
#SBATCH --job-name=aas-tb2-runtime-check
#SBATCH --output=/scratch/%u/tb2-pilot/exact-runtime-%j.out
#SBATCH --error=/scratch/%u/tb2-pilot/exact-runtime-%j.err
#SBATCH --partition=cpu
#SBATCH --qos=short
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
set -eo pipefail
source /etc/profile
set -euo pipefail
module load apptainer/apptainer

SCR=/scratch/$USER
ROOT=$SCR/tb2-pilot
SNAPSHOT=$SCR/datasets/terminal-bench-2.0
TASK=$SNAPSHOT/cobol-modernization
IMAGE=$SNAPSHOT/images/cobol-modernization-593ab9df.sif
VENV=$SCR/venvs/harbor-0.23.0
SITE=$VENV/lib/python3.12/site-packages
STAGE=$SCR/harbor-smoke/egress-probe
SOURCE=$ROOT/source-exact-runtime-$SLURM_JOB_ID
OUT=$ROOT/exact-runtime-$SLURM_JOB_ID
OVERLAY=$OUT/overlay
APPTAINER=$(command -v apptainer)
RUNTIME_PREP_JOB_ID=${AAS_RUNTIME_PREP_JOB_ID:?Set AAS_RUNTIME_PREP_JOB_ID to a completed runtime prep job}
[[ "$RUNTIME_PREP_JOB_ID" =~ ^[0-9]+$ ]] || { echo "invalid runtime prep job id"; exit 5; }
PREP_STATE=$(sacct -X -j "$RUNTIME_PREP_JOB_ID" --noheader --format=State | awk 'NR==1 {print $1}')
[ "$PREP_STATE" = COMPLETED ] || { echo "runtime prep Slurm state is not COMPLETED: $PREP_STATE"; exit 5; }
RUNTIME_ROOT=$ROOT/runtime-prep-$RUNTIME_PREP_JOB_ID
RUNTIME_DEPS=$RUNTIME_ROOT/runtime-deps
RUNTIME_MANIFEST=$ROOT/runtime-manifest-$RUNTIME_PREP_JOB_ID.json
RUNTIME_LOCK=$RUNTIME_ROOT/requirements.lock
HELPER=$SOURCE/docs/cluster/tb2-pilot/03_task_workspace_path_preflight.py
BOOTSTRAP=$SOURCE/docs/cluster/tb2-pilot/bootstrap_harbor_python3.sh
PATCH_FILE=$SOURCE/docs/cluster/harbor-egress-safety/harbor-0.23.0-uds.patch
EXPECTED_SOURCE=$(cat "$ROOT/expected-source-commit.txt")
ARCHIVE_SHA=$(sha256sum "$ROOT/source.tar" | awk '{print $1}')
EXPECTED_ARCHIVE_SHA=$(cat "$ROOT/source-archive.sha256")

mkdir -p "$OUT" "$OUT/bin"
exec > >(tee "$OUT/exact-runtime-preflight.log") 2>&1
export HARBOR_TELEMETRY=off
[ -n "$EXPECTED_SOURCE" ] && [ "$ARCHIVE_SHA" = "$EXPECTED_ARCHIVE_SHA" ] || { echo "source archive pin mismatch"; exit 5; }
mkdir "$SOURCE"
tar -xf "$ROOT/source.tar" -C "$SOURCE"
chmod -R a-w "$SOURCE"

for required in "$TASK/task.toml" "$TASK/environment" "$IMAGE" "$RUNTIME_DEPS" "$RUNTIME_MANIFEST" "$RUNTIME_LOCK" \
  "$VENV/bin/activate" \
  "$HELPER" "$BOOTSTRAP" "$PATCH_FILE" "$SITE/harbor/environments/singularity/singularity.py"; do
  [ -e "$required" ] || { echo "missing required input: $required"; exit 2; }
done
THIS_SCRIPT_SHA=$(sha256sum "$0" | awk '{print $1}')
ARCHIVE_SCRIPT_SHA=$(sha256sum "$SOURCE/docs/cluster/tb2-pilot/05_exact_runtime_preflight.sbatch" | awk '{print $1}')
[ "$THIS_SCRIPT_SHA" = "$ARCHIVE_SCRIPT_SHA" ] || { echo "executed script differs from committed source archive"; exit 5; }
IMAGE_SHA=$(sha256sum "$IMAGE" | awk '{print $1}')
[ "$IMAGE_SHA" = e7fc37ce09d4ee50e4a71a6e2c9941c0cdacdeb979fcaf99182728b3d0e0dd49 ] || { echo "task SIF hash mismatch"; exit 5; }
python - "$RUNTIME_MANIFEST" "$IMAGE_SHA" <<'PY'
import json, sys
from pathlib import Path
manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert manifest.get("python") == "3.13.7"
assert manifest.get("task_sif_sha256") == sys.argv[2]
for name, version in {"fastapi": "0.162.0", "pydantic": "2.13.5", "uvicorn": "0.54.0"}.items():
    assert manifest["packages"].get(name) == version, name
print("runtime_manifest=PASS")
PY
RUNTIME_TREE_SHA=$(python - "$RUNTIME_DEPS" "$RUNTIME_MANIFEST" <<'PY'
import hashlib, json, sys
from pathlib import Path
root = Path(sys.argv[1])
manifest = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
digest = hashlib.sha256()
for path in sorted(item for item in root.rglob("*") if item.is_file()):
    child = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            child.update(block)
    digest.update(path.relative_to(root).as_posix().encode("utf-8") + b"\0" + child.digest() + b"\n")
actual = digest.hexdigest()
assert actual == manifest.get("runtime_tree_sha256"), "runtime dependency tree hash mismatch"
print(actual)
PY
)
RUNTIME_LOCK_SHA=$(python - "$RUNTIME_MANIFEST" <<'PY'
import json, sys
from pathlib import Path
print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["lock_sha256"])
PY
)
[ "$(sha256sum "$RUNTIME_LOCK" | awk '{print $1}')" = "$RUNTIME_LOCK_SHA" ] || { echo "runtime lock hash mismatch"; exit 5; }
PACKAGE_COUNT=$(python - "$RUNTIME_MANIFEST" <<'PY'
import json, sys
from pathlib import Path
print(len(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["packages"]))
PY
)
[ -z "$(find "$RUNTIME_DEPS" \( -type d -o -type f \) -perm /222 -print -quit)" ] || { echo "runtime dependency tree is writable on host"; exit 5; }

echo "job=$SLURM_JOB_ID host=$(hostname) source_commit=$EXPECTED_SOURCE runtime_prep_job=$RUNTIME_PREP_JOB_ID"
"$APPTAINER" --version
"$VENV/bin/harbor" --version
source "$VENV/bin/activate"
echo "HARBOR_TELEMETRY=$HARBOR_TELEMETRY"
sha256sum "$IMAGE" "$PATCH_FILE" "$RUNTIME_MANIFEST"

mkdir -p "$OVERLAY"
cp -a "$SITE/harbor" "$OVERLAY/harbor"
patch --batch --forward -p1 -d "$OVERLAY" < "$PATCH_FILE"
install -m 755 "$BOOTSTRAP" "$OVERLAY/harbor/environments/singularity/bootstrap.sh"
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
export APPTAINER_CACHEDIR="$ROOT/apptainer-cache"

set +e
python "$HELPER" \
  --task-environment "$TASK/environment" --task-root "$TASK" \
  --task-config "$TASK/task.toml" --image "$IMAGE" --output "$OUT/workspace" \
  --runtime-deps "$RUNTIME_DEPS" --runtime-manifest "$RUNTIME_MANIFEST" \
  > "$OUT/task-image-check.log" 2>&1
PROBE_RC=$?
set -e
cat "$OUT/task-image-check.log"
[ "$PROBE_RC" -eq 0 ] || { echo "EXACT_RUNTIME_PREFLIGHT=FAIL rc=$PROBE_RC"; exit 20; }

ARGV=$(grep -F "Apptainer argv:" "$OUT/task-image-check.log" | tail -1 || true)
for required in "--net" "--network none" "--writable-tmpfs" "--containall" \
  "--uds /harbor-control/control.sock" ":/runtime-deps:ro"; do
  [[ "$ARGV" == *"$required"* ]] || { echo "missing Apptainer argv requirement: $required"; exit 21; }
done
[[ "$ARGV" != *"--fakeroot"* ]] || { echo "fakeroot appeared in Apptainer argv"; exit 22; }

PATCH_SHA=$(sha256sum "$PATCH_FILE" | awk '{print $1}')
cp "$RUNTIME_MANIFEST" "$OUT/runtime-manifest.json"
cp "$RUNTIME_LOCK" "$OUT/requirements.lock"
cat > "$ROOT/exact-runtime-$SLURM_JOB_ID.txt.tmp" <<EOF
status=PASS
job_id=$SLURM_JOB_ID
task_id=cobol-modernization
source_commit=$EXPECTED_SOURCE
source_archive_sha256=$ARCHIVE_SHA
runtime_prep_job_id=$RUNTIME_PREP_JOB_ID
runtime_prep_state=$PREP_STATE
task_sif_sha256=$IMAGE_SHA
harbor_uds_patch_sha256=$PATCH_SHA
runtime_tree_sha256=$RUNTIME_TREE_SHA
runtime_lock_sha256=$RUNTIME_LOCK_SHA
runtime_package_count=$PACKAGE_COUNT
python_version=3.13.7
harbor_dependencies=PINNED_HASHED_READ_ONLY
harbor_telemetry=off
harbor_uds=PASS
environment_exec=PASS
network_none=PASS
external_dns_ip_metadata=BLOCKED
runtime_mount_read_only=PASS
fakeroot=absent
model_started=no
harbor_trial_count=0
oracle_reference_verifier=no
EOF
mv -f "$ROOT/exact-runtime-$SLURM_JOB_ID.txt.tmp" "$ROOT/exact-runtime-$SLURM_JOB_ID.txt"
echo "EXACT_RUNTIME_PREFLIGHT=PASS record=$ROOT/exact-runtime-$SLURM_JOB_ID.txt"
