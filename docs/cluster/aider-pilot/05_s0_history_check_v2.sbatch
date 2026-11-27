#!/bin/bash
# AMENDED (v2) task-free S0 agent-loop history check; see docs/experiments/s0-history-check-v2-protocol-2026-11.md.
# Server context 32768 (was 8192). Command-discarding mock environment.
# No Harbor trial, benchmark, verifier, or shell executor is created.
#SBATCH --job-name=aas-s0-history-v2
#SBATCH --output=/scratch/%u/aider-protocol-diagnostic/slurm-%j.out
#SBATCH --error=/scratch/%u/aider-protocol-diagnostic/slurm-%j.err
#SBATCH --partition=gpu
#SBATCH --qos=short
#SBATCH --gpus=l40s:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00

set -eo pipefail
source /etc/profile
set -euo pipefail
module load apptainer/apptainer

SCR=/scratch/$USER
ROOT=$SCR/aider-protocol-diagnostic
SOURCE=$ROOT/source
MODEL=$SCR/models/gpt-oss-20b-MXFP4.gguf
SERVER_IMAGE=$SCR/images/llama-server-cuda12-b11515.sif
OUT=$ROOT/results/${SLURM_JOB_ID}-s0-history-v2
PORT=$((30000 + SLURM_JOB_ID % 20000))
SERVER_PID=
VRAM_GUARD_PID=
GPU_ID=${CUDA_VISIBLE_DEVICES%%,*}
VRAM_CSV=$ROOT/results/${SLURM_JOB_ID}-s0-history-v2-vram.csv

mkdir -p "$OUT"
exec > >(tee "$OUT/job.log") 2>&1
export HARBOR_TELEMETRY=off
export PYTHONDONTWRITEBYTECODE=1

cleanup() {
  touch "$OUT/stop-vram-guard" 2>/dev/null || true
  if [ -n "${VRAM_GUARD_PID:-}" ]; then
    kill "$VRAM_GUARD_PID" 2>/dev/null || true
    wait "$VRAM_GUARD_PID" 2>/dev/null || true
  fi
  if [ -n "${SERVER_PID:-}" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

for required in "$MODEL" "$SERVER_IMAGE" \
  "$SOURCE/docs/cluster/aider-pilot/05_s0_history_check_v2.py"   "$SOURCE/docs/cluster/aider-pilot/04_harbor_s0_history_check.py" \
  "$SOURCE/docs/cluster/aider-pilot/03_tool_schema_history_diagnostic.py" \
  "$SOURCE/environments/harbor_agent.py" "$SOURCE/llm/async_openai_compatible.py" \
  "$SOURCE/strategy_schema/defaults.py"; do
  [ -e "$required" ] || { echo "missing_required_input"; exit 2; }
done

EXPECTED_MODEL=27cd6c432c7672cb812a92f611cf3ba7bbc35928262bb1e1253ff4ee6ae35901
EXPECTED_SERVER=dd8110164788b9deb354e06cb984214b2ef8b6b0598c2ef73dd0ab9828957d56
MODEL_HASH=$(sha256sum "$MODEL" | awk '{print $1}')
SERVER_HASH=$(sha256sum "$SERVER_IMAGE" | awk '{print $1}')
[ "$MODEL_HASH" = "$EXPECTED_MODEL" ] || { echo "model_hash_mismatch"; exit 3; }
[ "$SERVER_HASH" = "$EXPECTED_SERVER" ] || { echo "server_hash_mismatch"; exit 3; }

PYTHON=/scratch/$USER/venvs/harbor-0.23.0/bin/python
[ -x "$PYTHON" ] || { echo "pinned_python_unavailable"; exit 4; }
SOURCE_COMMIT=$(git -C "$SOURCE" rev-parse HEAD)
EXPECTED_SOURCE_COMMIT=${AAS_EXPECTED_SOURCE_COMMIT:?set reviewed source commit}
[ "$SOURCE_COMMIT" = "$EXPECTED_SOURCE_COMMIT" ] || { echo "source_commit_mismatch"; exit 3; }
SOURCE_STATUS=$(git -C "$SOURCE" status --porcelain=v1)
[ -z "$SOURCE_STATUS" ] || { echo "source_tree_dirty"; exit 3; }
RUNNER_HASH=$(sha256sum "$SOURCE/docs/cluster/aider-pilot/05_s0_history_check_v2.py" | awk '{print $1}')
V1_RUNNER_HASH=$(sha256sum "$SOURCE/docs/cluster/aider-pilot/04_harbor_s0_history_check.py" | awk '{print $1}')
export PYTHONPATH="$SOURCE"

echo "job=$SLURM_JOB_ID host=$(hostname) source_commit=$SOURCE_COMMIT runner_sha256=$RUNNER_HASH v1_runner_sha256=$V1_RUNNER_HASH"
echo "apptainer=$(apptainer --version)"
echo "model_sha256=$MODEL_HASH server_sif_sha256=$SERVER_HASH"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv

[ -n "$GPU_ID" ] || { echo "allocated_gpu_id_unavailable"; exit 6; }
echo "sample_utc,gpu_uuid,used_mib,total_mib,free_mib" > "$VRAM_CSV"
cat > "$OUT/vram_guard.sh" <<'SH'
#!/bin/bash
set -Eeuo pipefail
guard_failure() {
  if [ -s "$OUT/server.pid" ]; then
    kill "$(cat "$OUT/server.pid")" 2>/dev/null || true
  fi
  touch "$OUT/vram-guard-failed" 2>/dev/null || true
}
trap guard_failure ERR
while [ ! -e "$OUT/stop-vram-guard" ]; do
  if ! row=$(nvidia-smi --id="$GPU_ID" --query-gpu=uuid,memory.used,memory.total \
      --format=csv,noheader,nounits 2>/dev/null); then
    [ ! -s "$OUT/server.pid" ] || kill "$(cat "$OUT/server.pid")" 2>/dev/null || true
    touch "$OUT/vram-guard-failed" 2>/dev/null || true
    exit 1
  fi
  IFS=, read -r uuid used total <<< "$row"
  uuid=${uuid//[[:space:]]/}
  used=${used//[[:space:]]/}
  total=${total//[[:space:]]/}
  if [[ ! "$used" =~ ^[0-9]+$ || ! "$total" =~ ^[0-9]+$ ]]; then
    [ ! -s "$OUT/server.pid" ] || kill "$(cat "$OUT/server.pid")" 2>/dev/null || true
    touch "$OUT/vram-guard-failed" 2>/dev/null || true
    exit 1
  fi
  free=$((total - used))
  printf '%s,%s,%s,%s,%s\n' "$(date -u +%FT%TZ)" "$uuid" "$used" "$total" "$free" >> "$VRAM_CSV"
  if [ "$free" -lt 1024 ]; then
    [ ! -s "$OUT/server.pid" ] || kill "$(cat "$OUT/server.pid")" 2>/dev/null || true
    touch "$OUT/vram-guard-failed" 2>/dev/null || true
    exit 1
  fi
  sleep 1
done
SH
chmod 700 "$OUT/vram_guard.sh"
export OUT GPU_ID VRAM_CSV
"$OUT/vram_guard.sh" &
VRAM_GUARD_PID=$!
sleep 2
[ ! -e "$OUT/vram-guard-failed" ] || { echo "vram_guard_failed_before_server"; exit 6; }
kill -0 "$VRAM_GUARD_PID" 2>/dev/null || { echo "vram_guard_not_running_before_server"; exit 6; }
[ "$(wc -l < "$VRAM_CSV")" -ge 2 ] || { echo "vram_guard_no_valid_startup_sample"; exit 6; }

apptainer exec --nv --containall --bind "$SCR/models:/models:ro" "$SERVER_IMAGE" \
  env LD_LIBRARY_PATH="/app:/usr/local/cuda/lib64:/.singularity.d/libs" \
  /app/llama-server -m /models/gpt-oss-20b-MXFP4.gguf \
  --host 127.0.0.1 --port "$PORT" -c 32768 -np 1 -ngl 999 -t 8 -tb 8 \
  --jinja --metrics --log-disable >/dev/null 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > "$OUT/server.pid"

READY=0
for _ in $(seq 1 90); do
  [ ! -e "$OUT/vram-guard-failed" ] || { echo "vram_headroom_guard_stopped_server"; exit 6; }
  kill -0 "$VRAM_GUARD_PID" 2>/dev/null || { echo "vram_guard_died_during_startup"; exit 6; }
  if curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then READY=1; break; fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then echo "server_exited_before_health"; exit 5; fi
  sleep 2
done
[ "$READY" = 1 ] || { echo "server_health_timeout"; exit 5; }

# Fail closed unless the server reports the frozen effective context (32768, one slot).
EFFECTIVE_CTX=$(curl -fsS "http://127.0.0.1:$PORT/props" | "$PYTHON" -c   'import json,sys; d=json.load(sys.stdin); print(d["default_generation_settings"]["n_ctx"])' 2>/dev/null || true)
echo "effective_n_ctx=$EFFECTIVE_CTX"
[ "$EFFECTIVE_CTX" = "32768" ] || { echo "effective_context_mismatch"; exit 5; }

cd "$OUT"
set +e
"$PYTHON" "$SOURCE/docs/cluster/aider-pilot/05_s0_history_check_v2.py" \
  --base-url "http://127.0.0.1:$PORT" \
  --output "$OUT/s0-history-v2-results.json" \
  --server-pid "$SERVER_PID" \
  --model-sha256 "$MODEL_HASH" \
  --server-sif-sha256 "$SERVER_HASH" \
  --source-commit "$SOURCE_COMMIT"
RUN_RC=$?
set -e
echo "experiment_exit_code=$RUN_RC"
kill -0 "$VRAM_GUARD_PID" 2>/dev/null || { echo "vram_guard_died_during_experiment"; RUN_RC=6; }
touch "$OUT/stop-vram-guard"
wait "$VRAM_GUARD_PID" || true
VRAM_GUARD_PID=
if [ -e "$OUT/vram-guard-failed" ]; then
  echo "vram_guard_failed_during_experiment"
  RUN_RC=6
fi
[ "$(wc -l < "$VRAM_CSV")" -ge 2 ] || { echo "vram_guard_samples_missing"; RUN_RC=6; }
if [ -s "$OUT/s0-history-v2-results.json" ]; then
  "$PYTHON" - "$OUT/s0-history-v2-results.json" "$VRAM_CSV" "$OUT/vram-guard-failed" <<'PY'
import csv
import json
import sys
from pathlib import Path

result_path, csv_path, guard_failure_path = map(Path, sys.argv[1:])
result = json.loads(result_path.read_text(encoding="utf-8"))
with csv_path.open(newline="", encoding="utf-8") as source:
    rows = list(csv.DictReader(source))
used = [int(row["used_mib"]) for row in rows]
free = [int(row["free_mib"]) for row in rows]
monitor = result["gpu_monitor"]
if used:
    monitor["peak_used_mib"] = max([monitor["peak_used_mib"], *used])
    monitor["minimum_free_mib"] = min(
        [value for value in [monitor["minimum_free_mib"], *free] if value is not None]
    )
    monitor["gpu_uuid"] = monitor["gpu_uuid"] or rows[0]["gpu_uuid"]
monitor["samples"] += len(rows)
monitor["startup_and_job_guard_samples"] = len(rows)
monitor["vram_guard_failed"] = guard_failure_path.exists()
result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
fi
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
(exit "$RUN_RC")
