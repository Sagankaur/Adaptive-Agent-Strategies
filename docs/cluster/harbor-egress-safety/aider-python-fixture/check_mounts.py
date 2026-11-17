import os
import re
from pathlib import Path


mountpoints = set()
for line in Path("/proc/self/mountinfo").read_text().splitlines():
    fields = line.split()
    if len(fields) >= 5:
        mountpoints.add(fields[4].replace("\\040", " "))

required = {"/app", "/harbor-control", "/runtime-deps", "/wheels", "/probe"}
missing = required - mountpoints
forbidden = {
    path
    for path in mountpoints
    if path
    in {
        "/home",
        "/root/.ssh",
        "/root/.aws",
        "/run/docker.sock",
        "/var/run/docker.sock",
        "/run/secrets",
        "/var/run/secrets",
        "/.env",
    }
    or path.startswith("/home/")
    or path.startswith("/root/.ssh/")
    or path.startswith("/root/.aws/")
    or path.startswith("/run/secrets/")
    or path.startswith("/var/run/secrets/")
    or path.startswith("/var/tmp/xdg_runtime_dir_")
    or path.endswith("/docker.sock")
}
secret_env = re.compile(r"(API_KEY|ACCESS_KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL|AUTH)", re.I)
credential_names = sorted(
    name
    for name in os.environ
    if secret_env.search(name)
    or name in {"DOCKER_CONFIG", "PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL", "SSH_AUTH_SOCK"}
)
has_docker_host = "DOCKER_HOST" in os.environ

if missing or forbidden or credential_names or has_docker_host:
    raise SystemExit(
        "mounts=FAIL "
        f"missing_expected={sorted(missing)} forbidden={sorted(forbidden)} "
        f"credential_env_names={credential_names} docker_host_env={has_docker_host}"
    )

print("mounts=PASS")
print("credential_env_vars=absent")
print("docker_host_env=absent")
print("rootless_docker_socket_mount=absent")
