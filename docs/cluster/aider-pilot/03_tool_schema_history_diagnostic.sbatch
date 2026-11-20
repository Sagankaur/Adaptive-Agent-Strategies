#!/bin/bash
# Task-free, synthetic tool-protocol diagnostic. No tool executor is started.
# Output artifact contains only aggregate categories, timings and hashes.
#SBATCH --job-name=aas-agent-protocol
#SBATCH --output=/scratch/%u/aider-protocol-diagnostic/slurm-%j.out
#SBATCH --error=/scratch/%u/aider-protocol-diagnostic/slurm-%j.err
#SBATCH --partition=gpu
#SBATCH --qos=short
#SBATCH --gpus=rtxp6000:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00

set -eo pipefail
source /etc/profile
set -euo pipefail
module load apptainer/apptainer

SCR=/scratch/$USER
ROOT=$SCR/aider-protocol-diagnostic
SOURCE=$ROOT/source
MODEL=$SCR/models/gpt-oss-20b-MXFP4.gguf
SERVER_IMAGE=$SCR/images/llama-server-cuda12-b11515.sif
OUT=$ROOT/results/${SLURM_JOB_ID}
PORT=$((30000 + SLURM_JOB_ID % 20000))
SERVER_PID=
MONITOR_PID=

mkdir -p "$OUT"
exec > >(tee "$OUT/job.log") 2>&1
export HARBOR_TELEMETRY=off

cleanup() {
  if [ -n "${MONITOR_PID:-}" ]; then kill "$MONITOR_PID" 2>/dev/null || true; fi
  if [ -n "${SERVER_PID:-}" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

for required in "$MODEL" "$SERVER_IMAGE" "$SOURCE/docs/cluster/aider-pilot/03_agent_protocol_diagnostic.py" \
  "$SOURCE/environments/harbor_agent.py" "$SOURCE/llm/async_openai_compatible.py" \
  "$SOURCE/strategy_schema/defaults.py"; do
  [ -e "$required" ] || { echo "missing required input: $required"; exit 2; }
done

EXPECTED_MODEL=27cd6c432c7672cb812a92f611cf3ba7bbc35928262bb1e1253ff4ee6ae35901
EXPECTED_SERVER=dd8110164788b9deb354e06cb984214b2ef8b6b0598c2ef73dd0ab9828957d56
MODEL_HASH=$(sha256sum "$MODEL" | awk '{print $1}')
SERVER_HASH=$(sha256sum "$SERVER_IMAGE" | awk '{print $1}')
[ "$MODEL_HASH" = "$EXPECTED_MODEL" ] || { echo "model_hash_mismatch"; exit 3; }
[ "$SERVER_HASH" = "$EXPECTED_SERVER" ] || { echo "server_sif_hash_mismatch"; exit 3; }

if [ ! -x /scratch/$USER/venvs/harbor-0.23.0/bin/python ]; then
  echo "pinned_harbor_python_unavailable"
  exit 4
fi
PYTHON=/scratch/$USER/venvs/harbor-0.23.0/bin/python
SOURCE_COMMIT=$(git -C "$SOURCE" rev-parse HEAD)
EXPECTED_SOURCE_COMMIT=${AAS_EXPECTED_SOURCE_COMMIT:?set AAS_EXPECTED_SOURCE_COMMIT to the reviewed commit}
[ "$SOURCE_COMMIT" = "$EXPECTED_SOURCE_COMMIT" ] || { echo "source_commit_mismatch"; exit 3; }
export PYTHONPATH="$SOURCE"
export PYTHONDONTWRITEBYTECODE=1

echo "job=$SLURM_JOB_ID host=$(hostname) source_commit=$SOURCE_COMMIT"
echo "apptainer=$(apptainer --version)"
echo "model_sha256=$MODEL_HASH server_sif_sha256=$SERVER_HASH"
echo "cgroup_cpu_max=$(cat /sys/fs/cgroup/cpu.max 2>/dev/null || true)"
echo "cgroup_memory_max=$(cat /sys/fs/cgroup/memory.max 2>/dev/null || true)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv

apptainer exec --nv --containall --bind "$SCR/models:/models:ro" "$SERVER_IMAGE" \
  env LD_LIBRARY_PATH="/app:/usr/local/cuda/lib64:/.singularity.d/libs" \
  /app/llama-server -m /models/gpt-oss-20b-MXFP4.gguf \
  --host 127.0.0.1 --port "$PORT" -c 8192 -np 1 -ngl 999 -t 8 -tb 8 \
  --jinja --metrics --log-disable >/dev/null 2>&1 &
SERVER_PID=$!

READY=0
for _ in $(seq 1 90); do
  if curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then READY=1; break; fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then echo "server_exited_before_health"; exit 5; fi
  sleep 2
done
[ "$READY" = 1 ] || { echo "server_health_timeout"; exit 5; }

export AAS_DIAGNOSTIC_OUT="$OUT/protocol-results.json"
set +e
"$PYTHON" "$SOURCE/docs/cluster/aider-pilot/03_tool_schema_history_diagnostic.py" \
  --base-url "http://127.0.0.1:$PORT" \
  --output "$AAS_DIAGNOSTIC_OUT" \
  --model-sha256 "$MODEL_HASH" \
  --server-sif-sha256 "$SERVER_HASH" \
  --source-commit "$SOURCE_COMMIT" \
  --server-pid "$SERVER_PID"
RUN_RC=$?
set -e
echo "diagnostic_exit_code=$RUN_RC"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
(exit "$RUN_RC")
