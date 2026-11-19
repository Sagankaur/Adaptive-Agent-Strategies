#!/bin/bash -l
# Exactly one exploratory TB2 Harbor episode after exact-image network preflight passes.
# Run from the committed pilot source snapshot on Rohan; never retry this job.
#SBATCH --job-name=aas-tb2-one-pilot
#SBATCH --output=/scratch/%u/tb2-pilot/model-%j.out
#SBATCH --error=/scratch/%u/tb2-pilot/model-%j.err
#SBATCH --partition=gpu
#SBATCH --qos=short
#SBATCH --gpus=rtxp6000:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
set -eo pipefail
source /etc/profile
set -euo pipefail

log() { echo "[$(date -Is)] $*"; }
SCR=/scratch/$USER
ROOT=$SCR/tb2-pilot
OUT=$ROOT/model-$SLURM_JOB_ID
SNAPSHOT=$SCR/datasets/terminal-bench-2.0
TASK=$SNAPSHOT/cobol-modernization
TASK_IMAGE=$SNAPSHOT/images/cobol-modernization-593ab9df.sif
MODEL_FILE=gpt-oss-20b-MXFP4.gguf
MODEL=$SCR/models/$MODEL_FILE
MODEL_ID=/models/$MODEL_FILE
SERVER_IMAGE=$SCR/images/llama-server-cuda12-b11515.sif
HARBOR_PY=$SCR/venvs/harbor-0.23.0/bin/harbor
VENV=$SCR/venvs/harbor-0.23.0
HF_PY=$SCR/.venvs/hf-download/bin/python
STAGE=$SCR/harbor-smoke/egress-probe
PATCH_FILE=$STAGE/harbor-0.23.0-uds.patch
SITE=$VENV/lib/python3.12/site-packages
EXPECTED_SOURCE=$(cat "$ROOT/expected-source-commit.txt")
SOURCE=$ROOT/source-model-$SLURM_JOB_ID
CACHE=$ROOT/apptainer-cache
PREFLIGHT_ID=${AAS_PREFLIGHT_JOB_ID:?Set AAS_PREFLIGHT_JOB_ID to the successful model-free preflight job ID}
[[ "$PREFLIGHT_ID" =~ ^[0-9]+$ ]] || { echo "invalid preflight job ID"; exit 5; }
PRECHECK=$ROOT/preflight-$PREFLIGHT_ID.txt
PORT=$((25000 + SLURM_JOB_ID % 20000))
JOB_NAME=tb2_gptoss_single_pilot_$SLURM_JOB_ID
OVERLAY=$OUT/overlay
LOCAL_TMP=
SERVER_PID=

mkdir -p "$OUT" "$OUT/bin"
exec > >(tee "$OUT/slurm.log") 2>&1
export HARBOR_TELEMETRY=off
export APPTAINER_CACHEDIR=$CACHE
ARCHIVE_SHA=$(sha256sum "$ROOT/source.tar" | awk '{print $1}')
EXPECTED_ARCHIVE_SHA=$(cat "$ROOT/source-archive.sha256")
[ -n "$EXPECTED_SOURCE" ] && [ "$ARCHIVE_SHA" = "$EXPECTED_ARCHIVE_SHA" ] || { log "source archive or commit pin mismatch"; exit 5; }
mkdir "$SOURCE"
tar -xf "$ROOT/source.tar" -C "$SOURCE"
chmod -R a-w "$SOURCE"
THIS_SCRIPT_SHA=$(sha256sum "$0" | awk '{print $1}')
ARCHIVE_SCRIPT_SHA=$(sha256sum "$SOURCE/docs/cluster/tb2-pilot/02_one_task_pilot.sbatch" | awk '{print $1}')
[ "$THIS_SCRIPT_SHA" = "$ARCHIVE_SCRIPT_SHA" ] || { log "executed model script differs from verified archive"; exit 5; }
if [ ! -d /data ] || [ ! -w /data ]; then
  log "local /data scratch is unavailable; refusing model episode"
  exit 4
fi
mkdir -p "/data/$USER"
DATA_FREE_KB=$(df -Pk /data | awk 'NR == 2 {print $4}')
if [ -z "$DATA_FREE_KB" ] || [ "$DATA_FREE_KB" -lt 6291456 ]; then
  log "local /data scratch has less than 6 GiB free; refusing model episode"
  df -h /data
  exit 4
fi
LOCAL_TMP=$(mktemp -d "/data/$USER/tb2-pilot-${SLURM_JOB_ID}.XXXXXX")
export TMPDIR=$LOCAL_TMP APPTAINER_TMPDIR=$LOCAL_TMP
cleanup() {
  if [ -n "${SERVER_PID:-}" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  case "$LOCAL_TMP" in "/data/$USER/tb2-pilot-$SLURM_JOB_ID."*) rm -rf -- "$LOCAL_TMP";; esac
}
trap cleanup EXIT

for required in "$PRECHECK" "$TASK/task.toml" "$TASK_IMAGE" "$MODEL" "$SERVER_IMAGE" \
  "$SOURCE/environments/harbor_agent.py" "$SOURCE/strategy_schema/defaults.py" \
  "$PATCH_FILE" "$SITE/harbor/environments/singularity/singularity.py" "$HARBOR_PY" "$HF_PY" \
  "$SOURCE/docs/cluster/tb2-pilot/verify_tb2_snapshot.py"; do
  [ -e "$required" ] || { log "missing required artifact: $required"; exit 2; }
done
grep -qx 'status=PASS' "$PRECHECK" || { log "exact-image preflight is not PASS"; exit 5; }
grep -qx "job_id=$PREFLIGHT_ID" "$PRECHECK" || { log "preflight job ID mismatch"; exit 5; }
grep -qx 'task_id=cobol-modernization' "$PRECHECK" || { log "preflight task mismatch"; exit 5; }
grep -qx "source_commit=$EXPECTED_SOURCE" "$PRECHECK" || { log "preflight source commit mismatch"; exit 5; }
grep -qx "source_archive_sha256=$ARCHIVE_SHA" "$PRECHECK" || { log "preflight source archive mismatch"; exit 5; }
grep -qx 'snapshot_revision=f2e8c75e23add71613117eecc9498f53bcd7e04e' "$PRECHECK" || { log "TB2 snapshot revision mismatch"; exit 5; }
grep -qx 'model_sha256=27cd6c432c7672cb812a92f611cf3ba7bbc35928262bb1e1253ff4ee6ae35901' "$PRECHECK" || { log "preflight model hash mismatch"; exit 5; }
grep -qx 'server_sif_sha256=dd8110164788b9deb354e06cb984214b2ef8b6b0598c2ef73dd0ab9828957d56' "$PRECHECK" || { log "preflight server image hash mismatch"; exit 5; }
PREFLIGHT_STATE=$(sacct -X -j "$PREFLIGHT_ID" --noheader --format=State | awk 'NR==1 {print $1}')
[ "$PREFLIGHT_STATE" = COMPLETED ] || { log "preflight Slurm job state is not COMPLETED: $PREFLIGHT_STATE"; exit 5; }
grep -qx 'source_manifest_sha256=593ab9df3d83f771e927888b2d9436b380cdf7ec4d0af2a9f0802d541edebba0' "$PRECHECK" || { log "preflight manifest mismatch"; exit 5; }
PRECHECK_HASH=$(awk -F= '$1=="task_sif_sha256" {print $2}' "$PRECHECK")
TASK_HASH=$(sha256sum "$TASK_IMAGE" | awk '{print $1}')
[ -n "$PRECHECK_HASH" ] && [ "$PRECHECK_HASH" = "$TASK_HASH" ] || { log "preflight SIF hash mismatch"; exit 5; }
PRECHECK_PATCH_HASH=$(awk -F= '$1=="harbor_uds_patch_sha256" {print $2}' "$PRECHECK")
PATCH_HASH=$(sha256sum "$PATCH_FILE" | awk '{print $1}')
[ -n "$PRECHECK_PATCH_HASH" ] && [ "$PRECHECK_PATCH_HASH" = "$PATCH_HASH" ] || { log "Harbor UDS patch differs from the tested preflight"; exit 5; }
MODEL_SHA=$(sha256sum "$MODEL" | awk '{print $1}')
SERVER_SHA=$(sha256sum "$SERVER_IMAGE" | awk '{print $1}')
[ "$MODEL_SHA" = 27cd6c432c7672cb812a92f611cf3ba7bbc35928262bb1e1253ff4ee6ae35901 ] || { log "pinned model SHA-256 mismatch"; exit 5; }
[ "$SERVER_SHA" = dd8110164788b9deb354e06cb984214b2ef8b6b0598c2ef73dd0ab9828957d56 ] || { log "pinned server image SHA-256 mismatch"; exit 5; }
grep -qx "model_sha256=$MODEL_SHA" "$PRECHECK" || { log "model differs from the preflight input"; exit 5; }
grep -qx "server_sif_sha256=$SERVER_SHA" "$PRECHECK" || { log "server image differs from the preflight input"; exit 5; }
SNAPSHOT_RESULT=$("$HF_PY" "$SOURCE/docs/cluster/tb2-pilot/verify_tb2_snapshot.py" "$SNAPSHOT")
SNAPSHOT_TREE=$(python -c 'import json,sys; print(json.loads(sys.argv[1])["tree_sha256"])' "$SNAPSHOT_RESULT")
grep -qx "snapshot_tree_sha256=$SNAPSHOT_TREE" "$PRECHECK" || { log "TB2 snapshot changed after preflight"; exit 5; }
ACTUAL_SOURCE=$EXPECTED_SOURCE
ln -sfn "$TASK_IMAGE" "$CACHE/alexgshaw_cobol-modernization_20251031.sif"

module load apptainer/apptainer
source "$VENV/bin/activate"
export PYTHONPATH="$SOURCE"
export PYTHONDONTWRITEBYTECODE=1
log "job=$SLURM_JOB_ID host=$(hostname) source_commit=$ACTUAL_SOURCE task=cobol-modernization"
log "telemetry=$HARBOR_TELEMETRY preflight_job=$PREFLIGHT_ID preflight_state=$PREFLIGHT_STATE"
log "apptainer=$(apptainer --version) harbor=$(harbor --version)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
df -h /data /scratch
sha256sum "$MODEL" "$SERVER_IMAGE" "$TASK_IMAGE" "$PATCH_FILE" > "$OUT/input-sha256sums.txt"

mkdir -p "$OVERLAY"
cp -a "$SITE/harbor" "$OVERLAY/harbor"
patch --batch --forward -p1 -d "$OVERLAY" < "$PATCH_FILE"
python -m py_compile \
  "$OVERLAY/harbor/environments/singularity/singularity.py" \
  "$OVERLAY/harbor/environments/singularity/server.py"
cat > "$OUT/bin/singularity" <<SHIM
#!/bin/bash
exec "$(command -v apptainer)" "\$@"
SHIM
chmod 700 "$OUT/bin/singularity"
export PATH="$OUT/bin:$PATH"
export PYTHONPATH="$SOURCE:$OVERLAY"

STRATEGY=$OUT/strategy.json
python - "$STRATEGY" <<'PY'
import sys
from pathlib import Path
from strategy_schema.defaults import s0
from strategy_schema.model import Strategy

values = s0("s0-tb2-pilot").model_dump(mode="json")
# Keep the fixed S0 strategy but disable the optional visible-test self-check.
# Harbor's official verifier remains the only source of the pilot reward.
values["verification"] = {
    "verification_required": False,
    "checks": [],
    "when": "before_submit",
    "max_verify_cycles": 0,
}
Path(sys.argv[1]).write_text(Strategy.model_validate(values).to_json() + "\n", encoding="utf-8")
PY
log "strategy_sha256=$(sha256sum "$STRATEGY" | awk '{print $1}') own_visible_test_check=disabled"

log "starting localhost-only gpt-oss server on 127.0.0.1:$PORT"
apptainer exec --nv --containall --bind "$SCR/models:/models:ro" "$SERVER_IMAGE" \
  env LD_LIBRARY_PATH="/app:/usr/local/cuda/lib64:/.singularity.d/libs" \
  /app/llama-server -m "$MODEL_ID" --host 127.0.0.1 --port "$PORT" \
  -c 32768 -np 1 -ngl 999 --jinja --metrics --log-disable > "$OUT/server.log" 2>&1 &
SERVER_PID=$!

READY=0
for i in $(seq 1 120); do
  if curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    READY=1
    log "model server healthy after approximately $((i * 2)) seconds"
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    log "model server exited before becoming healthy; raw server log remains on scratch"
    exit 3
  fi
  sleep 2
done
[ "$READY" = 1 ] || { log "model server health timeout; raw server log remains on scratch"; exit 3; }
nvidia-smi --query-gpu=memory.used,memory.total --format=csv > "$OUT/gpu-memory-before.csv"

cat > "$OUT/job.yaml" <<EOF
job_name: $JOB_NAME
jobs_dir: $OUT/harbor_jobs
n_attempts: 1
n_concurrent_trials: 1
agent_timeout_multiplier: 2.0
quiet: true
environment:
  type: singularity
  kwargs:
    singularity_no_mount: "home,tmp,bind-paths"
    singularity_image_cache_dir: "$CACHE"
agents:
  - import_path: environments.harbor_agent:HarborStrategyAgent
    model_name: "$MODEL_ID"
    env:
      AAS_STRATEGY_PATH: "$STRATEGY"
      AAS_MODEL_BASE_URL: "http://127.0.0.1:$PORT/v1"
      AAS_MODEL_TIMEOUT_S: "600"
      AAS_RUN_ID: "tb2-one-task-pilot-$SLURM_JOB_ID"
      AAS_PROVENANCE_TAG: "gpt-oss20b-tb2-one-task-exploratory"
      AAS_SEED_ROOT: "20261119"
tasks:
  - path: $TASK
EOF

set +e
harbor run --config "$OUT/job.yaml" --jobs-dir "$OUT/harbor_jobs" --n-concurrent 1 --quiet > "$OUT/harbor-run.log" 2>&1
HARBOR_RC=$?
set -e
echo "$HARBOR_RC" > "$OUT/harbor-cli-exit-code.txt"
if [ "$HARBOR_RC" -ne 0 ]; then
  log "Harbor returned nonzero rc=$HARBOR_RC; no retry or replacement will run"
  exit 30
fi

export AAS_PILOT_JOB_DIR="$OUT/harbor_jobs/$JOB_NAME"
export AAS_PILOT_OUT="$OUT/pilot-summary.jsonl"
python - <<'PY'
import json
import os
from pathlib import Path

from evaluation.harbor_results import append_completed_trial

job_dir = Path(os.environ["AAS_PILOT_JOB_DIR"])
summary = json.loads((job_dir / "result.json").read_text(encoding="utf-8"))
stats = summary.get("stats", {})
if (summary.get("n_total_trials") != 1 or stats.get("n_completed_trials") != 1
        or stats.get("n_errored_trials") != 0 or stats.get("n_retries") != 0):
    raise SystemExit("Harbor did not produce exactly one completed, unretried trial")
results = []
for path in job_dir.glob("*/result.json"):
    trial = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(trial, dict) and "verifier_result" in trial:
        results.append((path, trial))
if len(results) != 1:
    raise SystemExit(f"expected one Harbor verifier result, found {len(results)}")
trial_path, trial = results[0]
step_logs = list(trial_path.parent.rglob("aas_steps.jsonl"))
if len(step_logs) != 1:
    raise SystemExit(f"expected one private adapter log, found {len(step_logs)}")
record = append_completed_trial(trial, step_log_path=step_logs[0], output_path=Path(os.environ["AAS_PILOT_OUT"]))
if record["task_id"] != "cobol-modernization":
    raise SystemExit("Harbor result names a task other than the preregistered pilot task")
sanitized = {
    "task_id": record["task_id"],
    "status": record["status"],
    "reward": record["reward"],
    "success": record["success"],
    "step_count": record["step_count"],
    "input_tokens": record["input_tokens"],
    "cached_tokens": record["cached_tokens"],
    "output_tokens": record["output_tokens"],
    "strategy_hash": record["strategy_hash"],
    "provenance_tag": record["provenance_tag"],
}
print(json.dumps(sanitized, sort_keys=True))
PY

log "TB2_ONE_TASK_EXPLORATORY_PILOT=FINISHED output_dir=$OUT; raw logs remain on scratch"
