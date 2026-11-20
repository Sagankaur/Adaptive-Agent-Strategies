#!/usr/bin/env bash
set -uo pipefail
mkdir -p /logs/verifier
python3 -m pytest -q /tests/test_gpt_oss_smoke.py > /logs/verifier/pytest.log 2>&1
rc=$?
cat /logs/verifier/pytest.log
if [ "$rc" -eq 0 ]; then
  printf '1\n' > /logs/verifier/reward.txt
else
  printf '0\n' > /logs/verifier/reward.txt
fi
exit 0
