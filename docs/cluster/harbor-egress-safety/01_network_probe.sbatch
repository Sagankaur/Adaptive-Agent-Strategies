#!/bin/bash
# Scripted Apptainer network probe. No model, agent, benchmark task, or reference solution.
# Submit on Rohan after confirming the image path below exists.
#SBATCH --job-name=aas-egress-probe
#SBATCH --output=/scratch/%u/harbor-smoke/egress-probe/%j.out
#SBATCH --error=/scratch/%u/harbor-smoke/egress-probe/%j.err
#SBATCH --partition=cpu
#SBATCH --qos=short
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:05:00
set -uo pipefail

APPTAINER=/sw/software/apptainer/apptainer-1.3.3/apptainer/apptainer
IMAGE=/scratch/$USER/harbor-smoke/images/harbor-smoke-python312.sif
OUT=/scratch/$USER/harbor-smoke/egress-probe/$SLURM_JOB_ID
HOST_CURL=$(command -v curl || true)
mkdir -p "$OUT"
exec > >(tee "$OUT/probe.log") 2>&1

echo "job=$SLURM_JOB_ID host=$(hostname) date=$(date -Is)"
"$APPTAINER" --version
if [ -z "$HOST_CURL" ]; then
  echo "FAIL: curl is not installed on the compute host"
  exit 23
fi
echo "host_curl=$HOST_CURL"
echo "argv: $APPTAINER exec --net --network none --writable-tmpfs --containall --bind $HOST_CURL:/usr/local/bin/curl:ro --bind /lib/x86_64-linux-gnu:/host-libs:ro --bind /lib/x86_64-linux-gnu/ld-linux-x86-64.so.2:/host-loader:ro --pwd /app $IMAGE /bin/sh -c <probe>"

"$APPTAINER" exec --net --network none --writable-tmpfs --containall \
  --bind "$HOST_CURL:/usr/local/bin/curl:ro" \
  --bind /lib/x86_64-linux-gnu:/host-libs:ro \
  --bind /lib/x86_64-linux-gnu/ld-linux-x86-64.so.2:/host-loader:ro \
  --pwd /app "$IMAGE" \
  /bin/sh -c '
    set +e
    echo "task_uid=$(id -u)"
    echo "interfaces:"
    cat /proc/net/dev
    echo "routes:"
    cat /proc/net/route
    if ! command -v curl >/dev/null 2>&1; then
      echo "FAIL: curl missing"
      exit 20
    fi
    echo "curl=$(command -v curl)"
    printf writable-tmpfs-ok > /app/.egress-probe
    test -s /app/.egress-probe || { echo "FAIL: /app write"; exit 21; }
    echo "write_probe=PASS"
    /host-loader --library-path /host-libs /usr/local/bin/curl --noproxy "*" -k -sS -o /dev/null --connect-timeout 3 --max-time 5 \
      -w "external_http=%{http_code}\n" https://1.1.1.1/
    ext_rc=$?
    echo "external_curl_rc=$ext_rc"
    /host-loader --library-path /host-libs /usr/local/bin/curl --noproxy "*" -sS -o /dev/null --connect-timeout 3 --max-time 5 \
      -w "metadata_http=%{http_code}\n" http://169.254.169.254/latest/meta-data/
    meta_rc=$?
    echo "metadata_curl_rc=$meta_rc"
    case "$ext_rc:$meta_rc" in
      7:7|7:28|28:7|28:28) echo "network_probe=PASS (both endpoints unreachable)"; exit 0 ;;
      *) echo "network_probe=FAIL (inspect curl stderr and exit codes)"; exit 22 ;;
    esac
  '
rc=$?
echo "apptainer_task_rc=$rc"
exit "$rc"
