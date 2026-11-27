#!/usr/bin/env bash
set -uo pipefail

mkdir -p /logs/verifier
PIP_NO_INDEX=1 python3 -m pip install \
  --disable-pip-version-check --no-cache-dir --no-index \
  --find-links=/wheels --target=/tmp/aas-pytest 'pytest==8.3.4' \
  > /logs/verifier/pip-install.log 2>&1
install_rc=$?
if [ "$install_rc" -ne 0 ]; then
  printf '0\n' > /logs/verifier/reward.txt
  printf '{"gate":"FAIL","reason":"offline pytest installation failed"}\n' \
    > /logs/verifier/isolation.json
  exit 0
fi

PYTHONPATH=/tmp/aas-pytest python3 -m pytest -q /tests/test_isolation.py \
  > /logs/verifier/pytest.log 2>&1
pytest_rc=$?
cat /logs/verifier/pytest.log
if [ "$pytest_rc" -eq 0 ]; then
  printf '1\n' > /logs/verifier/reward.txt
else
  printf '0\n' > /logs/verifier/reward.txt
fi
exit 0
