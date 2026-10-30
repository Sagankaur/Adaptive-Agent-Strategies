#!/bin/bash -l
# Real Qwen + Harbor smoke on one L40S allocation; synthetic task only.
# Stage the source snapshot at /scratch/$USER/harbor-smoke/aas-source-639ba1d.
# Submit with: sbatch docs/cluster/harbor-real-model-smoke/01_qwen_harbor_smoke.sbatch
#SBATCH --job-name=aas-qwen-harbor
#SBATCH --output=/scratch/kasag/harbor-smoke/real-qwen-%j.out
#SBATCH --error=/scratch/kasag/harbor-smoke/real-qwen-%j.err
#SBATCH --partition=gpu
#SBATCH --qos=short
#SBATCH --gpus=l40s:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=00:30:00
set -euo pipefail

log() { echo "[$(date -Is)] $*"; }
SCR=/scratch/$USER
ROOT=$SCR/harbor-smoke
SOURCE=$ROOT/aas-source-639ba1d
TASK=$ROOT/task_apptainer
TASK_IMAGE=$ROOT/images/harbor-smoke-python312.sif
SERVER_IMAGE=$SCR/images/llama-server-cuda12-b11515.sif
MODEL_FILE=Qwen3.6-35B-A3B-UD-Q4_K_M.gguf
MODEL=$SCR/models/$MODEL_FILE
HARBOR_PY=$SCR/venvs/harbor-0.23.0/bin/harbor
JOB_NAME=aas_qwen_harbor_${SLURM_JOB_ID}
OUT=$ROOT/real-qwen/$SLURM_JOB_ID
PORT=$((22000 + SLURM_JOB_ID % 20000))
MODEL_ID=/models/$MODEL_FILE

mkdir -p "$OUT" "$ROOT/cache_apptainer"
for required in "$SOURCE/environments/harbor_agent.py" "$TASK/task.toml" "$TASK_IMAGE" "$SERVER_IMAGE" "$MODEL" "$HARBOR_PY"; do
  [ -e "$required" ] || { log "missing required artifact: $required"; exit 2; }
done

module load apptainer
SHIM_DIR=$OUT/bin
mkdir -p "$SHIM_DIR"
cat > "$SHIM_DIR/singularity" <<'SHIM'
#!/bin/bash
exec /sw/software/apptainer/apptainer-1.3.3/apptainer/apptainer "$@"
SHIM
chmod 700 "$SHIM_DIR/singularity"
export PATH="$SHIM_DIR:$PATH"
export APPTAINER_CACHEDIR=$ROOT/cache_apptainer
TRIAL_TMP=$(mktemp -d "/tmp/aas-qwen-harbor-${SLURM_JOB_ID}.XXXXXX")
export APPTAINER_TMPDIR=$TRIAL_TMP
SERVER_PID=
cleanup() {
  if [ -n "${SERVER_PID:-}" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$TRIAL_TMP"
}
trap cleanup EXIT

cd "$ROOT"
source "$SCR/venvs/harbor-0.23.0/bin/activate"
export PYTHONPATH="$SOURCE"
export PYTHONDONTWRITEBYTECODE=1

log "job=$SLURM_JOB_ID host=$(hostname) source_commit=639ba1d"
log "runtime=$(command -v apptainer)"
apptainer --version
harbor --version
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv

# Check the exact task runtime primitives on the allocated GPU node.
singularity exec --containall --writable-tmpfs --fakeroot --pwd /app "$TASK_IMAGE" \
  /bin/sh -c 'test -w /app && python3 --version && printf runtime-ok > /app/.runtime-probe && test -f /app/.runtime-probe'
log "task SIF writable-tmpfs and /app probe passed"

log "starting llama.cpp on 127.0.0.1:$PORT"
apptainer exec --nv --containall --bind "$SCR/models:/models:ro" "$SERVER_IMAGE" \
  env LD_LIBRARY_PATH="/app:/usr/local/cuda/lib64:/.singularity.d/libs" \
  /app/llama-server -m "$MODEL_ID" --host 127.0.0.1 --port "$PORT" \
  -c 16384 -np 1 -ngl 999 --jinja --metrics > "$OUT/server.log" 2>&1 &
SERVER_PID=$!

ready=0
for i in $(seq 1 120); do
  if curl -sf "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    ready=1
    log "model server healthy after about $((i * 2)) seconds"
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    log "model server exited before becoming healthy"
    tail -80 "$OUT/server.log"
    exit 3
  fi
  sleep 2
done
[ "$ready" = 1 ] || { log "model server health timeout"; tail -80 "$OUT/server.log"; exit 3; }

# Confirm the real Qwen endpoint returns a parseable terminal tool call before Harbor starts.
export AAS_PREFLIGHT_URL="http://127.0.0.1:$PORT/v1"
export AAS_PREFLIGHT_MODEL="$MODEL_ID"
export AAS_PREFLIGHT_SEED=20261030
python - <<'PY' | tee "$OUT/tool-call-preflight.json"
import asyncio
import json
import os
import sys

from environments.harbor_agent import _TOOLS, _json_object
from llm.async_openai_compatible import AsyncOpenAICompatibleModel

async def main():
    model = AsyncOpenAICompatibleModel(
        base_url=os.environ["AAS_PREFLIGHT_URL"],
        model=os.environ["AAS_PREFLIGHT_MODEL"],
        timeout_s=180,
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        seed=int(os.environ["AAS_PREFLIGHT_SEED"]),
        max_tokens=256,
    )
    response = await model.complete(
        [
            {"role": "system", "content": "Use the terminal tool to create /app/output.txt with exactly this line: harbor smoke passed. Then call submit."},
            {"role": "user", "content": "Create /app/output.txt with exactly one line: harbor smoke passed. Then submit."},
        ],
        tools=_TOOLS,
    )
    calls = [{"name": call.name, "arguments": call.arguments} for call in response.tool_calls]
    result = {
        "model": os.environ["AAS_PREFLIGHT_MODEL"],
        "seed": response.seed,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "elapsed_s": response.elapsed_s,
        "tool_calls": calls,
    }
    if not response.tool_calls:
        result["failure"] = "Qwen returned no native tool_calls"
        print(json.dumps(result, sort_keys=True))
        raise SystemExit(4)
    first = response.tool_calls[0]
    if first.name != "terminal":
        result["failure"] = f"expected terminal as first call, got {first.name}"
        print(json.dumps(result, sort_keys=True))
        raise SystemExit(4)
    _json_object(first.arguments, call_id=first.id)
    print(json.dumps(result, sort_keys=True))

asyncio.run(main())
PY

STRATEGY=$ROOT/strategy.json
cat > "$OUT/job.yaml" <<EOF
job_name: $JOB_NAME
jobs_dir: $OUT/harbor_jobs
n_attempts: 1
n_concurrent_trials: 1
agent_timeout_multiplier: 2.0
quiet: true
environment:
  type: singularity
agents:
  - import_path: environments.harbor_agent:HarborStrategyAgent
    model_name: "$MODEL_ID"
    env:
      AAS_STRATEGY_PATH: $STRATEGY
      AAS_MODEL_BASE_URL: http://127.0.0.1:$PORT/v1
      AAS_MODEL_TIMEOUT_S: "90"
      AAS_RUN_ID: qwen-harbor-smoke-$SLURM_JOB_ID
      AAS_PROVENANCE_TAG: qwen3.6-real-model-harbor-smoke-639ba1d
      AAS_SEED_ROOT: "20261030"
tasks:
  - path: $TASK
EOF

log "starting one Harbor trial with the project's real async client"
harbor run --config "$OUT/job.yaml" --jobs-dir "$OUT/harbor_jobs" --n-concurrent 1 --quiet

JOB_DIR=$OUT/harbor_jobs/$JOB_NAME
export AAS_HARBOR_JOB_DIR=$JOB_DIR
export AAS_HARBOR_EPISODE_OUT=$OUT/episode.jsonl
python - <<'PY' | tee "$OUT/harbor-evaluation.json"
import glob
import json
import os
import sys
from pathlib import Path

from evaluation.harbor_results import append_completed_trial

job_dir = Path(os.environ["AAS_HARBOR_JOB_DIR"])
summary_path = job_dir / "result.json"
summary = json.loads(summary_path.read_text(encoding="utf-8"))
stats = summary.get("stats", {})
if summary.get("n_total_trials") != 1 or stats.get("n_completed_trials") != 1 or stats.get("n_errored_trials") != 0 or stats.get("n_retries") != 0:
    raise SystemExit(f"Harbor job did not produce exactly one clean trial: {json.dumps(summary, sort_keys=True)}")

trial_results = []
for result_path in job_dir.glob("*/result.json"):
    candidate = json.loads(result_path.read_text(encoding="utf-8"))
    if isinstance(candidate, dict) and "verifier_result" in candidate:
        trial_results.append((result_path, candidate))
if len(trial_results) != 1:
    raise SystemExit(f"expected exactly one persisted Harbor trial result, found {len(trial_results)}")
trial_path, trial = trial_results[0]
step_logs = list(trial_path.parent.rglob("aas_steps.jsonl"))
if len(step_logs) != 1:
    raise SystemExit(f"expected exactly one adapter step log, found {len(step_logs)}")
record = append_completed_trial(trial, step_log_path=step_logs[0], output_path=Path(os.environ["AAS_HARBOR_EPISODE_OUT"]))
if record["step_count"] < 2 or not any(step.get("action") == "terminal" for step in record["steps"]) or not any(step.get("action") == "submit" for step in record["steps"]):
    raise SystemExit("trial completed without the expected terminal and submit actions")
print(json.dumps({
    "harbor_trial_id": record["harbor_trial_id"],
    "task_id": record["task_id"],
    "reward": record["reward"],
    "success": record["success"],
    "step_count": record["step_count"],
    "input_tokens": record["input_tokens"],
    "cached_tokens": record["cached_tokens"],
    "output_tokens": record["output_tokens"],
    "actions": [step.get("action") for step in record["steps"]],
}, sort_keys=True))
PY

log "REAL_MODEL_HARBOR_SMOKE_STATUS=PASS output_dir=$OUT"
