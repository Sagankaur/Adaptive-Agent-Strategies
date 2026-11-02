#!/bin/bash -l
# Synthetic llama.cpp fit screen or serving measurement; no Harbor tasks or episodes.
#SBATCH --job-name=aas-serving-sweep
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err
#SBATCH --partition=gpu
#SBATCH --qos=short
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --signal=B:TERM@120
set -euo pipefail

log() { echo "[$(date -Is)] $*"; }
SCR=/scratch/$USER
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
MODEL_FILE=Qwen3.6-35B-A3B-UD-Q4_K_M.gguf
MODEL=$SCR/models/$MODEL_FILE
SERVER_IMAGE=$SCR/images/llama-server-cuda12-b11515.sif
OUT=${SWEEP_OUT:-$SCR/jobs/out/serving_sweep_${SLURM_JOB_ID}}
MODE=${SWEEP_MODE:-screen}
GPU_LABEL=${SWEEP_GPU_LABEL:?Set SWEEP_GPU_LABEL to the exact GPU type requested from Slurm}

mkdir -p "$OUT"
for required in "$MODEL" "$SERVER_IMAGE" "$SCRIPT_DIR/02_model_sweep.py"; do
  [ -f "$required" ] || { log "required file missing: $required"; exit 2; }
done
command -v python3 >/dev/null || { log "python3 is unavailable"; exit 2; }
module load apptainer
command -v apptainer >/dev/null || { log "Apptainer module did not provide apptainer"; exit 2; }

log "job=$SLURM_JOB_ID host=$(hostname) mode=$MODE requested_gpu=$GPU_LABEL"
log "runtime=$(apptainer --version) python=$(python3 --version 2>&1)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
log "model=$MODEL"
log "server_image=$SERVER_IMAGE"
log "outputs=$OUT"

ARGS=(
  --mode "$MODE"
  --server-image "$SERVER_IMAGE"
  --model "$MODEL"
  --output-dir "$OUT"
  --gpu-label "$GPU_LABEL"
  --run-budget-s "$((55 * 60))"
)
if [ "$MODE" = measure ]; then
  : "${SWEEP_SLOTS:?Set SWEEP_SLOTS to 1, 2, or 4 in measure mode}"
  : "${SWEEP_KV:?Set SWEEP_KV to f16 or q8_0 in measure mode}"
  : "${SWEEP_CONTEXT_PER_SLOT:?Set SWEEP_CONTEXT_PER_SLOT to 65536 or 98304 in measure mode}"
  ARGS+=(
    --slots "$SWEEP_SLOTS"
    --kv-type "$SWEEP_KV"
    --context-per-slot "$SWEEP_CONTEXT_PER_SLOT"
  )
elif [ "$MODE" != screen ]; then
  log "SWEEP_MODE must be screen or measure"
  exit 2
fi

PY_PID=
on_signal() {
  log "received shutdown signal; asking the Python runner to stop its current server"
  if [ -n "${PY_PID:-}" ]; then
    kill -TERM "$PY_PID" 2>/dev/null || true
    wait "$PY_PID" 2>/dev/null || true
  fi
  exit 143
}
trap on_signal TERM INT
python3 "$SCRIPT_DIR/02_model_sweep.py" "${ARGS[@]}" &
PY_PID=$!
set +e
wait "$PY_PID"
STATUS=$?
set -e
PY_PID=
exit "$STATUS"
