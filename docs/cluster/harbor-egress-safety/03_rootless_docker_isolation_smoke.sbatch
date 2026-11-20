#!/usr/bin/env bash
# No-model check of Rohan's supplied rootless-Docker module.
# Submit from a CPU login node. This is a synthetic container only.
# It checks Docker control from the host while the container has no network.
#SBATCH --job-name=aas-rootless-net
#SBATCH --partition=cpu
#SBATCH --qos=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:15:00
#SBATCH --output=aas-rootless-net-%j.out
#SBATCH --error=aas-rootless-net-%j.err

set -eo pipefail
source /etc/profile
set -euo pipefail
log() { echo "[$(date -Is)] $*"; }

NAME=rootless-network-probe-${SLURM_JOB_ID:-manual}
DAEMON_STARTED=0
cleanup() {
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  if [ "$DAEMON_STARTED" = 1 ]; then
    stop_docker_rootless.sh || true
  fi
}
trap cleanup EXIT

module load rootless-docker/rootless-docker
case "${DOCKER_HOST:-}" in
  unix:///var/tmp/xdg_runtime_dir_*/docker.sock) ;;
  *) log "unexpected DOCKER_HOST=${DOCKER_HOST:-unset}"; exit 1 ;;
esac
DAEMON_STARTED=1
log "rootless Docker endpoint configured: $DOCKER_HOST"
start_docker_rootless.sh
docker info --format '{{json .SecurityOptions}}' | tee rootless-security-options.json
grep -qi rootless rootless-security-options.json || {
  log "Docker daemon did not report rootless mode"; exit 1;
}

# The host-side daemon may fetch the public test image. The task container below
# is explicitly attached to Docker's network=none network.
docker pull python:3.12-slim
docker image inspect --format '{{.Id}} {{index .RepoDigests 0}}' python:3.12-slim | tee image-pin.txt
docker run -d --name "$NAME" --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m python:3.12-slim sleep 300

NETWORK_MODE=$(docker inspect --format '{{.HostConfig.NetworkMode}}' "$NAME")
[ "$NETWORK_MODE" = none ] || { log "unexpected network mode: $NETWORK_MODE"; exit 1; }
log "container network mode: $NETWORK_MODE"
docker inspect --format '{{json .Mounts}}' "$NAME" | tee mounts.json
if grep -q 'docker.sock' mounts.json; then
  log "Docker API socket is mounted inside the test container"; exit 1
fi

docker exec -i "$NAME" python - <<'PY'
import socket

checks = [("1.1.1.1", 443, "external_ip"), ("169.254.169.254", 80, "metadata")]
for host, port, label in checks:
    try:
        socket.create_connection((host, port), timeout=3).close()
    except OSError as exc:
        print(f"{label}=blocked ({type(exc).__name__})", flush=True)
    else:
        raise SystemExit(f"{label}=UNEXPECTEDLY_REACHABLE")

try:
    socket.getaddrinfo("example.com", 443)
except OSError as exc:
    print(f"external_dns=blocked ({type(exc).__name__})", flush=True)
else:
    raise SystemExit("external_dns=UNEXPECTEDLY_REACHABLE")
PY

# Docker exec is the host-side control channel; it must work without a socket
# mount or network connection from inside the container.
docker exec "$NAME" python -c 'print("host_control_exec=ok")'
docker exec "$NAME" sh -c 'test ! -S /var/run/docker.sock'
log "synthetic rootless Docker isolation smoke passed"
