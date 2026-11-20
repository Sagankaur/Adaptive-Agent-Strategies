#!/usr/bin/env bash
# Serving-only gpt-oss-20b synthetic function-call smoke on RTX Pro 6000.
# Requires 01_gpt_oss_fetch.sbatch and the pinned llama.cpp SIF already in scratch.
# No task container, benchmark task, shell executor, or reference solution is run.
#SBATCH --job-name=aas-gptoss-tools
#SBATCH --partition=gpu
#SBATCH --qos=short
#SBATCH --gpus=rtxp6000:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --output=aas-gptoss-tools-%j.out
#SBATCH --error=aas-gptoss-tools-%j.err

set -eo pipefail
source /etc/profile
set -euo pipefail
log() { echo "[$(date -Is)] $*"; }

SCR=/scratch/$USER
MODEL_FILE=gpt-oss-20b-MXFP4.gguf
MODEL=$SCR/models/$MODEL_FILE
SIF=$SCR/images/llama-server-cuda12-b11515.sif
OUT=$SCR/jobs/gpt_oss_tool_smoke_${SLURM_JOB_ID:-manual}
PORT=$((24000 + ${SLURM_JOB_ID:-0} % 20000))
mkdir -p "$OUT"

[ -s "$MODEL" ] || { log "missing model file; submit 01_gpt_oss_fetch.sbatch first"; exit 1; }
[ -s "$SIF" ] || { log "missing pinned llama.cpp SIF"; exit 1; }

module load apptainer/apptainer
log "host=$(hostname) job=${SLURM_JOB_ID:-manual}"
log "starting localhost-only llama-server on port $PORT"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv | tee "$OUT/gpu.csv"

apptainer exec --nv --containall --bind "$SCR/models:/models:ro" "$SIF" \
  env LD_LIBRARY_PATH="/app:/usr/local/cuda/lib64:/.singularity.d/libs" \
  /app/llama-server -m "/models/$MODEL_FILE" --host 127.0.0.1 --port "$PORT" \
  -c 8192 -np 1 -ngl 999 --jinja --metrics \
  > "$OUT/server.log" 2>&1 &
SERVER_PID=$!
trap 'log "stopping server"; kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true' EXIT

UP=0
for i in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    UP=1
    log "server became healthy after about $((i * 5)) seconds"
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    log "server exited before becoming healthy"
    tail -60 "$OUT/server.log"
    exit 1
  fi
  sleep 5
done
[ "$UP" = 1 ] || { log "server health timeout"; tail -60 "$OUT/server.log"; exit 1; }
nvidia-smi --query-gpu=memory.used,memory.total --format=csv | tee "$OUT/gpu-memory.csv"

python3 - "$PORT" "$OUT" <<'PY'
import json
import sys
import time
import urllib.request

port, out = sys.argv[1:]
url = f"http://127.0.0.1:{port}/v1/chat/completions"
tool = {
    "type": "function",
    "function": {
        "name": "reverse_words",
        "description": "Reverse the order of words in the supplied text.",
        "parameters": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
}
payload = {
    "messages": [
        {"role": "system", "content": "Use the provided function when it can complete the request."},
        {"role": "user", "content": 'Call reverse_words on the exact string "red blue green".'},
    ],
    "tools": [tool],
    "temperature": 0.6,
    "top_p": 0.95,
    "seed": 20261116,
    "max_tokens": 256,
}
request = urllib.request.Request(
    url, json.dumps(payload).encode(), {"Content-Type": "application/json"}
)
started = time.monotonic()
with urllib.request.urlopen(request, timeout=180) as response:
    result = json.load(response)
wall_s = round(time.monotonic() - started, 3)
choice = result["choices"][0]
message = choice["message"]
calls = message.get("tool_calls") or []
name = calls[0].get("function", {}).get("name") if calls else None
arguments = calls[0].get("function", {}).get("arguments") if calls else None
if isinstance(arguments, str):
    try:
        arguments = json.loads(arguments)
    except json.JSONDecodeError:
        pass
usage = result.get("usage", {})
report = {
    "model": result.get("model"),
    "seed": payload["seed"],
    "temperature": payload["temperature"],
    "top_p": payload["top_p"],
    "max_tokens": payload["max_tokens"],
    "tool_choice": payload.get("tool_choice", "auto (server default)"),
    "tool_call_count": len(calls),
    "tool_name": name,
    "tool_arguments": arguments,
    "tool_call_correct": len(calls) == 1 and name == "reverse_words" and arguments == {"text": "red blue green"},
    "finish_reason": choice.get("finish_reason"),
    "wall_seconds": wall_s,
    "prompt_tokens": usage.get("prompt_tokens"),
    "completion_tokens": usage.get("completion_tokens"),
    "total_tokens": usage.get("total_tokens"),
    "task_or_benchmark_run": False,
    "tool_was_executed": False,
}
with open(f"{out}/tool_call.json", "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2)
print(json.dumps(report, indent=2), flush=True)
if not report["tool_call_correct"]:
    raise SystemExit("expected exactly one reverse_words call with the exact argument")
PY

log "serving-only tool-call smoke finished; raw record is $OUT/tool_call.json"
