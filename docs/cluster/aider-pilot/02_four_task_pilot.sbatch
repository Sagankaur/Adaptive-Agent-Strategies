#!/bin/bash
# Frozen Aider Python subset runner. Two lyric-generation tasks from the
# original sample are safety-excluded; no replacements selected. AAS_TASK_IDS
# can select a predeclared subset for a continuation after an infrastructure error.
# Generated task data and raw logs stay on scratch.
#SBATCH --job-name=aas-aider4-gptoss
#SBATCH --output=/scratch/%u/aider-pilot/20261119/aider4-%j.out
#SBATCH --error=/scratch/%u/aider-pilot/20261119/aider4-%j.err
#SBATCH --partition=gpu
#SBATCH --qos=short
#SBATCH --gpus=rtxp6000:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00

set -eo pipefail
source /etc/profile
set -euo pipefail
log() { echo "[$(date -Is)] $*"; }

SCR=/scratch/$USER
ROOT=$SCR/harbor-smoke
STAGE=$ROOT/egress-probe
PILOT=$SCR/aider-pilot/20261119
TASKROOT=$PILOT/tasks_no_oracle_4_strict
OUT=$PILOT/runs/${SLURM_JOB_ID}
SOURCE=$ROOT/aas-source-e094856
MODEL=$SCR/models/gpt-oss-20b-MXFP4.gguf
MODEL_ID=/models/gpt-oss-20b-MXFP4.gguf
SERVER_IMAGE=/scratch/$USER/images/llama-server-cuda12-b11515.sif
TASK_IMAGE=$ROOT/images/aider-python311-buildpack-jammy.sif
HARBOR_PY=$SCR/venvs/harbor-0.23.0/bin/harbor
PATCH_FILE=$STAGE/harbor-0.23.0-uds.patch
BOOTSTRAP=$STAGE/04_aider_harbor_bootstrap.sh
VENV=$SCR/venvs/harbor-0.23.0
SITE=$VENV/lib/python3.12/site-packages
RUNNER=$STAGE/02_run_four_tasks.py
PORT=$((28000 + SLURM_JOB_ID % 20000))
LOCAL_TMP=
SERVER_PID=

mkdir -p "$OUT" "$OUT/bin"
exec > >(tee "$OUT/slurm.log") 2>&1
export HARBOR_TELEMETRY=off
export APPTAINER_CACHEDIR=$ROOT/cache_apptainer
if [ ! -d /data ] || [ ! -w /data ]; then
  log "local /data scratch unavailable"
  exit 4
fi
mkdir -p "/data/$USER"
DATA_FREE_KB=$(df -Pk /data | awk 'NR == 2 {print $4}')
if [ -z "$DATA_FREE_KB" ] || [ "$DATA_FREE_KB" -lt 6291456 ]; then
  log "local /data scratch has less than 6 GiB free"
  df -h /data
  exit 4
fi
LOCAL_TMP=$(mktemp -d "/data/$USER/aas-aider4-${SLURM_JOB_ID}.XXXXXX")
export TMPDIR=$LOCAL_TMP APPTAINER_TMPDIR=$LOCAL_TMP
trap 'if [ -n "${SERVER_PID:-}" ]; then kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true; fi; case "$LOCAL_TMP" in "/data/$USER/aas-aider4-$SLURM_JOB_ID."*) rm -rf -- "$LOCAL_TMP";; esac' EXIT

for required in "$MODEL" "$SERVER_IMAGE" "$TASK_IMAGE" "$RUNNER" \
  "$TASKROOT/generation-manifest.json" "$TASKROOT/polyglot_python_hangman/task.toml" \
  "$TASKROOT/polyglot_python_poker/task.toml" "$TASKROOT/polyglot_python_rest-api/task.toml" \
  "$TASKROOT/polyglot_python_variable-length-quantity/task.toml" \
  "$SOURCE/environments/harbor_agent.py" "$PATCH_FILE" "$BOOTSTRAP" \
  "$SITE/harbor/environments/singularity/singularity.py" "$HARBOR_PY"; do
  [ -e "$required" ] || { log "missing required input: $required"; exit 2; }
done

if find "$TASKROOT" \( -iname .oracle -o -iname solution.enc -o -path '*/solution/solve.sh' -o -path '*/.meta/example*' \) -print -quit | grep -q .; then
  log "Oracle/reference artifact path detected; refusing model execution"
  exit 5
fi

module load apptainer/apptainer
source "$VENV/bin/activate"
cd "$ROOT"
export PYTHONPATH="$SOURCE"
export PYTHONDONTWRITEBYTECODE=1
log "job=$SLURM_JOB_ID host=$(hostname) source_commit=e094856"
log "arch=$(uname -m) apptainer=$(apptainer --version) harbor=$(harbor --version) telemetry=$HARBOR_TELEMETRY"
log "cgroup_cpu_max=$(cat /sys/fs/cgroup/cpu.max 2>/dev/null || true)"
log "cgroup_memory_max=$(cat /sys/fs/cgroup/memory.max 2>/dev/null || true)"
log "cgroup_cpuset=$(cat /sys/fs/cgroup/cpuset.cpus.effective 2>/dev/null || true)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
df -h /data /scratch
sha256sum "$MODEL" "$SERVER_IMAGE" "$TASK_IMAGE" "$PATCH_FILE" \
  "$TASKROOT/generation-manifest.json" > "$OUT/input-sha256sums.txt"

OVERLAY=$OUT/overlay
mkdir -p "$OVERLAY"
cp -a "$SITE/harbor" "$OVERLAY/harbor"
patch --batch --forward -p1 -d "$OVERLAY" < "$PATCH_FILE"
python -m py_compile "$OVERLAY/harbor/environments/singularity/singularity.py" \
  "$OVERLAY/harbor/environments/singularity/server.py"
install -m 755 "$BOOTSTRAP" "$OVERLAY/harbor/environments/singularity/bootstrap.sh"
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
Path(sys.argv[1]).write_text(s0().to_json() + "\n", encoding="utf-8")
PY
log "strategy_sha256=$(sha256sum "$STRATEGY" | awk '{print $1}')"

log "starting localhost-only gpt-oss model server on port $PORT"
apptainer exec --nv --containall --bind "$SCR/models:/models:ro" "$SERVER_IMAGE" \
  env LD_LIBRARY_PATH="/app:/usr/local/cuda/lib64:/.singularity.d/libs" \
  /app/llama-server -m "$MODEL_ID" --host 127.0.0.1 --port "$PORT" \
  -c 8192 -np 1 -ngl 999 -t 8 -tb 8 --jinja --metrics > "$OUT/server.log" 2>&1 &
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
nvidia-smi --query-gpu=memory.used,memory.total --format=csv | tee "$OUT/gpu-memory-start.csv"

export AAS_TASKROOT=$TASKROOT AAS_OUT=$OUT AAS_PORT=$PORT AAS_STRATEGY_PATH=$STRATEGY
export AAS_TASK_IDS=${AAS_TASK_IDS:-hangman,poker,rest-api,variable-length-quantity}
set +e
python "$RUNNER" | tee "$OUT/episode-summary-lines.jsonl"
RUNNER_RC=${PIPESTATUS[0]}
set -e
echo "$RUNNER_RC" > "$OUT/runner-exit-code.txt"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv | tee "$OUT/gpu-memory-end.csv"
log "four_task_pilot_runner_exit=$RUNNER_RC summary=$OUT/summary.json"
(exit "$RUNNER_RC")
