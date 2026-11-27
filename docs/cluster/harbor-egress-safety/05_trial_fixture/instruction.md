# Synthetic container preflight

This is an infrastructure-only fixture. It asks no coding question and is
paired with Harbor's built-in no-op agent. The verifier checks that Harbor can
run a scripted Python check in the task container while the container has no
external network route. No benchmark data or model is involved.
