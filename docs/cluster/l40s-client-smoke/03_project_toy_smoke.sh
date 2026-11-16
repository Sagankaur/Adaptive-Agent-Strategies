#!/bin/bash -l
# Run the project's real OpenAI-compatible client and toy runner in the same
# short Slurm allocation as llama-server. No Harbor task image is used.
# Submit from ~/jobs: sbatch 03_project_toy_smoke.sh
#SBATCH --job-name=aas-client-toy
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err
#SBATCH --partition=gpu
#SBATCH --qos=short
#SBATCH --gpus=l40s:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=00:20:00
set -euo pipefail
log() { echo "[$(date -Is)] $*"; }

SCR=/scratch/$USER
MODEL_FILE=Qwen3.6-35B-A3B-UD-Q4_K_M.gguf
SIF=$SCR/images/llama-server-cuda12-b11515.sif
MODEL=$SCR/models/$MODEL_FILE
PY=$SCR/venvs/aas-client-smoke/bin/python
SRC=$HOME/jobs/aas-client-smoke-src
DRIVER=$HOME/jobs/project_client_toy_smoke.py
PORT=$((20000 + ${SLURM_JOB_ID:-0} % 20000))
OUT=$HOME/jobs/out/project_client_toy_${SLURM_JOB_ID:-manual}
mkdir -p "$OUT"

log "start host=$(hostname) job=${SLURM_JOB_ID:-none}"
[ -f "$MODEL" ] || { log "model missing: $MODEL"; exit 1; }
[ -f "$SIF" ] || { log "server image missing: $SIF"; exit 1; }
[ -x "$PY" ] || { log "smoke venv missing: $PY"; exit 1; }
[ -f "$DRIVER" ] || { log "client smoke driver missing: $DRIVER"; exit 1; }
[ -d "$SRC/llm" ] || { log "staged project source missing: $SRC"; exit 1; }
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv

module load apptainer 2>/dev/null || module load singularity 2>/dev/null || true
C=$(command -v apptainer || command -v singularity)
log "container tool=$C python=$PY"
log "starting llama-server on 127.0.0.1:$PORT"
"$C" exec --nv --containall --bind "$SCR/models:/models:ro" "$SIF" \
  env LD_LIBRARY_PATH="/app:/usr/local/cuda/lib64:/.singularity.d/libs" \
  /app/llama-server -m "/models/$MODEL_FILE" --host 127.0.0.1 --port "$PORT" \
  -c 16384 -np 1 -ngl 999 --jinja --metrics > "$OUT/server.log" 2>&1 &
SRV=$!
trap 'log "stopping server"; kill "$SRV" 2>/dev/null || true; wait "$SRV" 2>/dev/null || true' EXIT

up=0
for i in $(seq 1 90); do
  if curl -sf "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then up=1; log "server up after about $((i * 2)) s"; break; fi
  if ! kill -0 "$SRV" 2>/dev/null; then log "server exited early"; tail -40 "$OUT/server.log"; exit 1; fi
  sleep 2
done
[ "$up" = 1 ] || { log "server not healthy after 180 s"; tail -40 "$OUT/server.log"; exit 1; }

log "running direct client and one toy-runner task"
PYTHONPATH="$SRC" "$PY" -u "$DRIVER" "$PORT" "$OUT"
log "integration smoke completed; results in $OUT"
