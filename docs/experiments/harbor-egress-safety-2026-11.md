# Harbor egress safety review — 2026-11-06

## Safety gate

No job that executes real-model commands may run until task-container egress is blocked and the block is verified together with Harbor's control channel. Serving-only model jobs remain allowed. No agent, model, Oracle or reference-solution job was run for this review.

## Audit of the two existing Harbor jobs

**Result: not audited; no clean-log conclusion is available.** The local repository contains the run summaries but not `aas_steps.jsonl`, Harbor `trial.log` files, or agent logs for either job. A key-only `ssh -o BatchMode=yes rohan ...` attempt failed before authentication because `login-f.ai.deakin.edu.au` did not resolve. No password authentication or password helper was used. Therefore zero log files were searched and there is no evidence from this attempt about whether either run issued a suspicious command.

When the key-only cluster connection is available, audit only those logs for each job with:

```bash
for job in 4410693 4433963; do
  root="/scratch/$USER/harbor-smoke/real-qwen/$job"
  printf '\n=== job %s ===\n' "$job"
  mapfile -d '' files < <(find "$root" -type f \
    \( -name 'aas_steps.jsonl' -o -name 'trial.log' -o -name 'agent.log' \) -print0)
  if ((${#files[@]} == 0)); then
    echo 'NO AUDIT LOG FILES FOUND'
    continue
  fi
  printf 'Searching: %s\n' "${files[@]}"
  if ! grep -nEi '169\.254|curl|wget|https?://|aliyuncs|oss-|unshare|nsenter|mount' "${files[@]}"; then
    echo 'No requested indicators matched in the listed files.'
  fi
done
```

Record the exact files searched and matching lines. If `grep` finds no matches, state that only for the files actually searched; it does not prove the container was isolated.

## Harbor 0.23.0 control-channel finding

The pinned [Harbor v0.23.0 Singularity provider](https://github.com/harbor-framework/harbor/blob/v0.23.0/src/harbor/environments/singularity/singularity.py) starts its execution server inside the task container and reaches it from the host through `http://localhost:<port>`. The pinned [server](https://github.com/harbor-framework/harbor/blob/v0.23.0/src/harbor/environments/singularity/server.py) listens on `127.0.0.1`. Adding `--net --network none` isolates that loopback namespace, so this current TCP control channel is not expected to work unchanged.

The viable design to test is a Harbor 0.23.0 provider patch that:

1. starts the task container with `--net --network none`;
2. places a per-trial Unix socket in a private, owner-only directory already bind-mounted into the container;
3. has the in-container Harbor execution server listen on that socket and has the host client use an HTTPX Unix-domain-socket transport;
4. keeps the mounted path limited to that one socket directory, with no Harbor state, host credentials, or Docker/Apptainer control sockets mounted into the task.

This requires a provider patch; there is no existing Harbor job-config option that turns the current localhost TCP server into a Unix socket. A socket exchange is not assumed to work until a scripted task demonstrates request/response with a unique nonce and ordinary `environment.exec` continues to work.

Apptainer's [1.3 networking guide](https://apptainer.org/docs/user/1.3/networking.html) documents `--network` together with `--net`; `none` is the no-external-network candidate. A2I2 module and Slurm policy still need an on-node check. The historical task-filesystem probe used both `--writable-tmpfs` and `--fakeroot`, so it does **not** show that fakeroot is needed or that writable tmpfs works alone. The scripted gate must test writable writes with `--writable-tmpfs` and no fakeroot first, then record the actual runtime argv.

## Required scripted isolation test

Run only a made-up scripted task, with no model client, agent, Oracle, benchmark task or reference solution. The test passes only when all of these are demonstrated in the same task-container configuration:

- the actual Apptainer argv includes `exec --net --network none --writable-tmpfs` and omits `--fakeroot` if the write probe succeeds without it;
- task writes under the expected working directory succeed;
- a unique-nonce request and response traverse the mounted Unix-socket control channel, and Harbor's ordinary `environment.exec` returns the expected result;
- `curl` is present in the image, then a request to a controlled external HTTPS host and a direct request to `169.254.169.254` both fail because of network reachability (not because `curl` is missing or the command is malformed);
- DNS/external lookup fails, only loopback exists inside the task network namespace, and host-side logs show no unexpected control request.

Save the job script, provider patch/hash, Harbor and Apptainer versions, full argv, socket probe output, `curl` exit codes/stderr, task and trial logs, and `sacct` result. Until this gate passes, the isolation status is **unverified** and the real-model job gate stays closed.

## Adapter tripwire

`HarborStrategyAgent` now scans proposed terminal commands and configured shell checks/probes for URLs, valid IPv4/IPv6 addresses, `unshare`, `nsenter`, and `mount`. Matching commands are refused before `environment.exec`, and `aas_steps.jsonl` records `tripwire_flags` on every step. This is command-text monitoring and filtering only. It is not a network boundary: obfuscated shell, Python or another executable can make network calls without matching these strings. Only the task-container network isolation test can close the egress gate.

## Harbor telemetry

Harbor 0.23.0 sends command-finished and job-finished usage events by default to PostHog. The events can include command path/flags, model/provider names, task/dataset references, resource settings, usage totals, and outcomes. The pinned [telemetry source](https://github.com/harbor-framework/harbor/blob/v0.23.0/src/harbor/telemetry.py) and [unit tests](https://github.com/harbor-framework/harbor/blob/v0.23.0/tests/unit/test_telemetry.py) define the supported opt-out: set `HARBOR_TELEMETRY=off` in the Harbor process environment before invoking any Harbor CLI/programmatic command. The original script revision used for jobs 4410693 and 4433963 did not set it explicitly; their inherited environments are unavailable here, so telemetry status for those two jobs is unknown. The current safety-disabled recipe sets the opt-out, and future Harbor job scripts must do so explicitly.

## Professor decision

See [DECISIONS.md, Q9](../DECISIONS.md#q9-model-choice-under-the-qwen-egress-advisory). No model choice is adopted here. The evidence and choice belong to the professor; the isolation gate applies whichever model is selected.

## Current status

| Item | Status |
|---|---|
| Logs for 4410693 and 4433963 | Not audited; raw logs inaccessible while key-only SSH name resolution fails |
| Egress isolation and Harbor control channel | Designed around a provider patch and Unix socket; not implemented or tested on Rohan |
| `--writable-tmpfs` without fakeroot | Not tested |
| Adapter tripwire | Implemented; local unit tests cover classification and pre-execution refusal |
| Harbor telemetry opt-out | Verified from pinned 0.23.0 source; set `HARBOR_TELEMETRY=off` for future jobs |
| Real-model command jobs | Paused until egress and control-channel checks pass |
