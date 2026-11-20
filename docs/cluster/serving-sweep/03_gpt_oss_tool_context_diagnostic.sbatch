#!/usr/bin/env bash
# No-task gpt-oss native tool-call/context diagnostic. Tool calls are never run.
# Raw model input/output is not printed or written by the client.
#SBATCH --job-name=aas-gptoss-contract
#SBATCH --partition=gpu
#SBATCH --qos=short
#SBATCH --gpus=rtxp6000:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch/%u/jobs/gpt_oss_tool_context_%j.out
#SBATCH --error=/scratch/%u/jobs/gpt_oss_tool_context_%j.err

set -eo pipefail
source /etc/profile
set -euo pipefail
log() { echo "[$(date -Is)] $*"; }

SCR=/scratch/$USER
MODEL=$SCR/models/gpt-oss-20b-MXFP4.gguf
SIF=$SCR/images/llama-server-cuda12-b11515.sif
RUNNER=$SCR/serving-sweep/03_gpt_oss_tool_context_diagnostic.py
PROTOCOL=$SCR/serving-sweep/gpt-oss-tool-context-diagnostic-2026-11-19.md
OUT=$SCR/jobs/gpt_oss_tool_context_${SLURM_JOB_ID}
mkdir -p "$OUT"
exec > >(tee "$OUT/slurm.log") 2>&1

module load apptainer/apptainer
log "job=$SLURM_JOB_ID host=$(hostname)"
log "apptainer=$(apptainer --version)"
log "cgroup_cpu_max=$(cat /sys/fs/cgroup/cpu.max 2>/dev/null || true)"
log "cgroup_memory_max=$(cat /sys/fs/cgroup/memory.max 2>/dev/null || true)"
log "cgroup_cpuset=$(cat /sys/fs/cgroup/cpuset.cpus.effective 2>/dev/null || true)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv | tee "$OUT/gpu.csv"

for required in "$MODEL" "$SIF" "$RUNNER" "$PROTOCOL"; do
  [ -s "$required" ] || { log "missing required input"; exit 2; }
done

python3 "$RUNNER" --output-dir "$OUT" --model "$MODEL" --server-sif "$SIF" \
  --protocol-file "$PROTOCOL" --job-id "$SLURM_JOB_ID"
log "synthetic tool-context diagnostic finished; only sanitized results.json is intended for archival"
