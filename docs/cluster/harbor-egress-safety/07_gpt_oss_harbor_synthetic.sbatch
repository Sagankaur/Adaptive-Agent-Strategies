#!/bin/bash
# One gpt-oss-20b Harbor trial on a made-up file-write task with task egress
# blocked. Engineering smoke only; no Aider or other benchmark is run.
# Stage this script, its fixture, and a .env-free project source snapshot on Rohan.
#SBATCH --job-name=aas-gptoss-harbor
#SBATCH --output=/scratch/%u/harbor-smoke/egress-probe/gptoss-harbor-%j.out
#SBATCH --error=/scratch/%u/harbor-smoke/egress-probe/gptoss-harbor-%j.err
#SBATCH --partition=gpu
#SBATCH --qos=short
#SBATCH --gpus=rtxp6000:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00

set -eo pipefail
source /etc/profile
set -euo pipefail
log() { echo "[$(date -Is)] $*"; }

SCR=/scratch/$USER
ROOT=$SCR/harbor-smoke
STAGE=$ROOT/egress-probe
OUT=$ROOT/gptoss-harbor-smoke/${SLURM_JOB_ID}
SOURCE=$ROOT/aas-source-e094856
MODEL_FILE=gpt-oss-20b-MXFP4.gguf
MODEL=$SCR/models/$MODEL_FILE
MODEL_ID=/models/$MODEL_FILE
SERVER_IMAGE=/scratch/$USER/images/llama-server-cuda12-b11515.sif
TASK_IMAGE=$ROOT/images/aider-python311-buildpack-jammy.sif
HARBOR_PY=$SCR/venvs/harbor-0.23.0/bin/harbor
PATCH_FILE=$STAGE/harbor-0.23.0-uds.patch
BOOTSTRAP=$STAGE/04_aider_harbor_bootstrap.sh
FIXTURE=$STAGE/07_gpt_oss_harbor_fixture
VENV=$SCR/venvs/harbor-0.23.0
SITE=$VENV/lib/python3.12/site-packages
PORT=$((24000 + SLURM_JOB_ID % 20000))
TASK=$OUT/synthetic-gpt-oss-harbor
OVERLAY=$OUT/overlay
LOCAL_TMP=
SERVER_PID=

mkdir -p "$OUT" "$OUT/bin" "$TASK/app" "$TASK/tests" "$TASK/environment"
exec > >(tee "$OUT/slurm.log") 2>&1
export HARBOR_TELEMETRY=off
export APPTAINER_CACHEDIR=$ROOT/cache_apptainer
if [ ! -d /data ] || [ ! -w /data ]; then
  log "local /data scratch is unavailable; refusing slow shared-filesystem SIF conversion"
  exit 4
fi
mkdir -p "/data/$USER"
DATA_FREE_KB=$(df -Pk /data | awk 'NR == 2 {print $4}')
if [ -z "$DATA_FREE_KB" ] || [ "$DATA_FREE_KB" -lt 6291456 ]; then
  log "local /data scratch has less than 6 GiB free"
  df -h /data
  exit 4
fi
LOCAL_TMP=$(mktemp -d "/data/$USER/aas-gptoss-harbor-${SLURM_JOB_ID}.XXXXXX")
export TMPDIR=$LOCAL_TMP APPTAINER_TMPDIR=$LOCAL_TMP
trap 'if [ -n "${SERVER_PID:-}" ]; then kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true; fi; case "$LOCAL_TMP" in "/data/$USER/aas-gptoss-harbor-$SLURM_JOB_ID."*) rm -rf -- "$LOCAL_TMP";; esac' EXIT

for required in "$MODEL" "$SERVER_IMAGE" "$TASK_IMAGE" "$SOURCE/environments/harbor_agent.py" \
  "$PATCH_FILE" "$BOOTSTRAP" "$FIXTURE/instruction.md" "$FIXTURE/task.toml.in" \
  "$FIXTURE/tests/test.sh" "$FIXTURE/tests/test_gpt_oss_smoke.py" \
  "$SITE/harbor/environments/singularity/singularity.py" "$HARBOR_PY"; do
  [ -e "$required" ] || { log "missing required input: $required"; exit 2; }
done

module load apptainer/apptainer
source "$VENV/bin/activate"
cd "$ROOT"
export PYTHONPATH="$SOURCE"
export PYTHONDONTWRITEBYTECODE=1
log "job=$SLURM_JOB_ID host=$(hostname) source_commit=e094856"
log "architecture=$(uname -m) apptainer=$(apptainer --version)"
log "harbor=$(harbor --version) telemetry=$HARBOR_TELEMETRY task_tmp=local_nvme"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
df -h /data /scratch
sha256sum "$MODEL" "$SERVER_IMAGE" "$TASK_IMAGE" "$PATCH_FILE" > "$OUT/input-sha256sums.txt"

mkdir -p "$OVERLAY"
cp -a "$SITE/harbor" "$OVERLAY/harbor"
patch --batch --forward -p1 -d "$OVERLAY" < "$PATCH_FILE"
install -m 755 "$BOOTSTRAP" "$OVERLAY/harbor/environments/singularity/bootstrap.sh"
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

cp "$FIXTURE/instruction.md" "$TASK/instruction.md"
cp "$FIXTURE/tests/test.sh" "$TASK/tests/test.sh"
cp "$FIXTURE/tests/test_gpt_oss_smoke.py" "$TASK/tests/test_gpt_oss_smoke.py"
cp "$FIXTURE/environment/Dockerfile" "$TASK/environment/Dockerfile"
sed "s|@@IMAGE@@|$TASK_IMAGE|g" "$FIXTURE/task.toml.in" > "$TASK/task.toml"
chmod 755 "$TASK/tests/test.sh"

STRATEGY=$OUT/strategy.json
python - "$STRATEGY" <<'PY'
import sys
from pathlib import Path
from strategy_schema.defaults import s0

Path(sys.argv[1]).write_text(s0().to_json() + "\n", encoding="utf-8")
PY
log "strategy_sha256=$(sha256sum "$STRATEGY" | awk '{print $1}')"

log "starting localhost-only gpt-oss server on port $PORT"
apptainer exec --nv --containall --bind "$SCR/models:/models:ro" "$SERVER_IMAGE" \
  env LD_LIBRARY_PATH="/app:/usr/local/cuda/lib64:/.singularity.d/libs" \
  /app/llama-server -m "$MODEL_ID" --host 127.0.0.1 --port "$PORT" \
  -c 8192 -np 1 -ngl 999 --jinja --metrics > "$OUT/server.log" 2>&1 &
SERVER_PID=$!

READY=0
for i in $(seq 1 90); do
  if curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    READY=1
    log "model server healthy after approximately $((i * 2)) seconds"
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    log "model server exited before becoming healthy"
    tail -60 "$OUT/server.log"
    exit 3
  fi
  sleep 2
done
[ "$READY" = 1 ] || { log "model server health timeout"; tail -60 "$OUT/server.log"; exit 3; }
nvidia-smi --query-gpu=memory.used,memory.total --format=csv | tee "$OUT/gpu-memory.csv"

cat > "$OUT/job.yaml" <<EOF
job_name: gptoss_isolated_synthetic_$SLURM_JOB_ID
jobs_dir: $OUT/harbor_jobs
n_attempts: 1
n_concurrent_trials: 1
agent_timeout_multiplier: 2.0
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
      source: "$STAGE/aider-py311-4801425/wheelhouse"
      target: /wheels
      read_only: true
    - type: bind
      source: "$STAGE/aider-py311-4801425/harbor-runtime-deps"
      target: /runtime-deps
      read_only: true
agents:
  - import_path: environments.harbor_agent:HarborStrategyAgent
    model_name: "$MODEL_ID"
    env:
      AAS_STRATEGY_PATH: "$STRATEGY"
      AAS_MODEL_BASE_URL: "http://127.0.0.1:$PORT/v1"
      AAS_MODEL_TIMEOUT_S: "180"
      AAS_RUN_ID: "gpt-oss-harbor-synthetic-$SLURM_JOB_ID"
      AAS_PROVENANCE_TAG: "gpt-oss-20b-synthetic-isolated-smoke"
      AAS_SEED_ROOT: "20261119"
tasks:
  - path: $TASK
EOF

set +e
harbor run --config "$OUT/job.yaml" --jobs-dir "$OUT/harbor_jobs" --n-concurrent 1 --quiet > "$OUT/harbor-run.log" 2>&1
HARBOR_RC=$?
set -e
echo "$HARBOR_RC" > "$OUT/harbor-cli-exit-code.txt"
cat "$OUT/harbor-run.log"

export AAS_SMOKE_JOB_DIR="$OUT/harbor_jobs/gptoss_isolated_synthetic_$SLURM_JOB_ID"
export AAS_SMOKE_OUT="$OUT/summary.json"
python - <<'PY' | tee "$OUT/evaluation.json"
import json
import os
from pathlib import Path

from evaluation.harbor_results import append_completed_trial

job_dir = Path(os.environ["AAS_SMOKE_JOB_DIR"])
summary = json.loads((job_dir / "result.json").read_text(encoding="utf-8"))
stats = summary.get("stats", {})
if summary.get("n_total_trials") != 1 or stats.get("n_completed_trials") != 1 or stats.get("n_errored_trials") != 0 or stats.get("n_retries") != 0:
    raise SystemExit(f"Harbor did not complete exactly one clean synthetic trial: {json.dumps(summary, sort_keys=True)}")
results = []
for path in job_dir.glob("*/result.json"):
    trial = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(trial, dict) and "verifier_result" in trial:
        results.append((path, trial))
if len(results) != 1:
    raise SystemExit(f"expected exactly one persisted trial result, found {len(results)}")
trial_path, trial = results[0]
step_logs = list(trial_path.parent.rglob("aas_steps.jsonl"))
if len(step_logs) != 1:
    raise SystemExit(f"expected one agent step log, found {len(step_logs)}")
steps = [json.loads(line) for line in step_logs[0].read_text(encoding="utf-8").splitlines() if line]
actions = [step.get("action") for step in steps]
if not any(action == "terminal" for action in actions) or not any(action == "submit" for action in actions):
    raise SystemExit(f"expected terminal and submit actions, got {actions}")
if any(step.get("tripwire_flags") for step in steps):
    raise SystemExit("command monitoring tripwire flagged the model's synthetic task commands")
record = append_completed_trial(trial, step_log_path=step_logs[0], output_path=Path(os.environ["AAS_SMOKE_OUT"]))
if record["reward"] != 1.0 or record["step_count"] < 2:
    raise SystemExit(f"synthetic agent smoke did not pass its verifier: {json.dumps(record, sort_keys=True)}")
print(json.dumps({
    "harbor_trial_id": record["harbor_trial_id"], "reward": record["reward"],
    "success": record["success"], "step_count": record["step_count"],
    "actions": actions, "input_tokens": record["input_tokens"],
    "cached_tokens": record["cached_tokens"], "output_tokens": record["output_tokens"],
    "tripwire_flags": [], "benchmark_task": False,
}, sort_keys=True))
PY

log "GPT_OSS_ISOLATED_SYNTHETIC_HARBOR_STATUS=PASS output_dir=$OUT"
