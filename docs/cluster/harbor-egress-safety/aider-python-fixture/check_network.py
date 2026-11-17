import socket


blocked = []
interfaces = {
    line.split(":", 1)[0].strip()
    for line in open("/proc/net/dev", encoding="utf-8").read().splitlines()[2:]
    if ":" in line
}
routes = open("/proc/net/route", encoding="utf-8").read().splitlines()[1:]
if interfaces - {"lo"}:
    blocked.append("unexpected_interface")
if routes:
    blocked.append("unexpected_route")
print(f"interfaces={','.join(sorted(interfaces))}")
print(f"non_loopback_routes={len(routes)}")
targets = [
    ("1.1.1.1", 443, "external_ip"),
    ("169.254.169.254", 80, "metadata"),
]

for host, port, label in targets:
    try:
        socket.create_connection((host, port), timeout=3).close()
    except OSError as exc:
        print(f"{label}=blocked:{type(exc).__name__}")
    else:
        blocked.append(label)

try:
    socket.getaddrinfo("example.com", 443)
except OSError as exc:
    print(f"external_dns=blocked:{type(exc).__name__}")
else:
    blocked.append("external_dns")

if blocked:
    raise SystemExit(f"network=FAIL:{','.join(blocked)}")

print("network=PASS")
