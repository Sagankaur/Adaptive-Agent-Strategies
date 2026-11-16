#!/usr/bin/env bash
# Fetch the pinned gpt-oss-20b GGUF artifact to Rohan scratch.
# Submit from a CPU login node: sbatch 01_gpt_oss_fetch.sbatch
# This is a model-file transfer only; it runs no model or benchmark task.
#SBATCH --job-name=aas-gptoss-fetch
#SBATCH --partition=cpu
#SBATCH --qos=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=aas-gptoss-fetch-%j.out
#SBATCH --error=aas-gptoss-fetch-%j.err

set -euo pipefail
log() { echo "[$(date -Is)] $*"; }

SCR=/scratch/$USER
MODEL_REPO=ggml-org/gpt-oss-20b-GGUF
MODEL_REV=41e8a94d15d62070b36cf4553a0250717ecf46b8
MODEL_FILE=gpt-oss-20b-MXFP4.gguf
MODEL_BYTES=12109566624
MODEL_SHA256=27cd6c432c7672cb812a92f611cf3ba7bbc35928262bb1e1253ff4ee6ae35901
DEST=$SCR/models/$MODEL_FILE
TMP=$DEST.part

mkdir -p "$SCR/models" "$SCR/jobs"
read -r size_kb avail_kb < <(df -Pk /scratch | awk 'NR==2 {print $2, $4}')
after=$(( (size_kb - avail_kb + 13 * 1024 * 1024) * 100 / size_kb ))
log "projected scratch use after download: ${after}%"
if [ "$after" -ge 80 ]; then
  log "STOP: scratch would reach 80%; consult A2I2 support before downloading."
  exit 1
fi

if [ -f "$DEST" ] && [ "$(stat -c %s "$DEST")" = "$MODEL_BYTES" ]; then
  log "model file already present; verifying checksum"
else
  URL="https://huggingface.co/$MODEL_REPO/resolve/$MODEL_REV/$MODEL_FILE"
  log "downloading pinned $MODEL_REPO@$MODEL_REV/$MODEL_FILE"
  curl -sS -L --fail --retry 5 --retry-delay 15 -C - -o "$TMP" "$URL"
  [ "$(stat -c %s "$TMP")" = "$MODEL_BYTES" ] || {
    log "download size mismatch; retaining partial file for a resumable retry"
    exit 1
  }
  mv "$TMP" "$DEST"
fi

echo "$MODEL_SHA256  $DEST" | sha256sum -c -
PIN="$MODEL_REPO@$MODEL_REV/$MODEL_FILE sha256=$MODEL_SHA256 size=$MODEL_BYTES"
if ! grep -Fqx "$PIN" "$SCR/models/PINS.txt" 2>/dev/null; then
  printf '%s\n' "$PIN" >> "$SCR/models/PINS.txt"
fi
log "verified gpt-oss-20b model file"
