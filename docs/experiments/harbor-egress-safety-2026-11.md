# Harbor egress safety review - 2026-11-06

## Safety gate

No job that executes real-model commands may run until task-container egress is blocked and the block is verified together with Harbor's control channel. Serving-only model jobs remain allowed. No agent, model, Oracle or reference-solution job was run for this review.

## Audit of the two existing Harbor jobs

**Result: searched four logs per job using key-only SSH on 2026-11-06.** For each job, the searched files were Harbor `job.log`, agent `aas_steps.jsonl`, Harbor `trial.log`, and `server.log` under `/scratch/kasag/harbor-smoke/real-qwen/<job>/harbor_jobs/aas_qwen_harbor_<job>/`. The `aas_steps.jsonl` files had no matches for any requested indicator. Across all four files per job, there were no matches for `169.254`, `curl`, `wget`, `aliyuncs`, `oss-`, `unshare`, or `nsenter`. The `mount` matches were Apptainer warnings that `squashfuse` and `fuse2fs` are unavailable. URL matches were Harbor's localhost execution-server and llama.cpp listener URLs, plus a GitHub pull-request link embedded in a llama.cpp warning about its local server configuration. These are not evidence of agent-issued outbound commands. The audit applies only to these eight files; it does not prove network isolation or establish what happened in unsearched files.

The raw logs remain on Rohan under the paths above. The scan does not prove the container was isolated; both historical jobs ran with task internet available. `server.log` also records that llama.cpp ran without an API key and allowed permissive CORS while listening on loopback. Treat that as a separate local-service hardening issue for any future model job.

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

The search was limited to the requested indicators in these eight files. The exact match categories are summarized above.

## Harbor 0.23.0 control-channel finding

The pinned [Harbor v0.23.0 Singularity provider](https://github.com/harbor-framework/harbor/blob/v0.23.0/src/harbor/environments/singularity/singularity.py) starts its execution server inside the task container and reaches it from the host through `http://localhost:<port>`. The pinned [server](https://github.com/harbor-framework/harbor/blob/v0.23.0/src/harbor/environments/singularity/server.py) listens on `127.0.0.1`. Adding `--net --network none` isolates that loopback namespace, so this current TCP control channel is not expected to work unchanged.

The viable design to test is a Harbor 0.23.0 provider patch that:

1. starts the task container with `--net --network none`;
2. places a per-trial Unix socket in a private, owner-only directory already bind-mounted into the container;
3. has the in-container Harbor execution server listen on that socket and has the host client use an HTTPX Unix-domain-socket transport;
4. keeps the mounted path limited to that one socket directory, with no Harbor state, host credentials, or Docker/Apptainer control sockets mounted into the task.

This requires a provider patch; there is no existing Harbor job-config option that turns the current localhost TCP server into a Unix socket. A socket exchange is not assumed to work until a scripted task demonstrates request/response with a unique nonce and ordinary `environment.exec` continues to work.

Apptainer's [1.3 networking guide](https://apptainer.org/docs/user/1.3/networking.html) documents `--network` together with `--net`. The on-node probe used this configuration on Rohan CPU node `cpu-f-01`, without `--fakeroot`. The image's `/app` write succeeded, `/proc/net/dev` showed only `lo`, `/proc/net/route` had no routes, and curl requests to `https://1.1.1.1/` and `http://169.254.169.254/latest/meta-data/` both failed with curl exit 7 (could not connect). The successful probe was job **4626138**, exit `0:0`; its complete log and Slurm output are under `/scratch/kasag/harbor-smoke/egress-probe/4626138/`. The first attempt failed because the image lacked curl. A second attempt using the host curl with the container dynamic loader segfaulted; the passing attempt explicitly used the host loader and libraries mounted read-only. This proves the tested Apptainer invocation blocked the two requested endpoints and that writable tmpfs works without fakeroot. It does not yet prove Harbor can communicate with the task under the same network configuration. A2I2 policy approval for the flags remains to be confirmed.

## Required scripted isolation test

The initial network and filesystem probe is recorded above. The complete Harbor integration test remains open. Run only a made-up scripted task, with no model client, Oracle, benchmark task or reference solution. The integration test passes only when all of these are demonstrated in the same task-container configuration:

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
| Logs for 4410693 and 4433963 | Eight logs searched; no suspicious-command indicators in `aas_steps.jsonl`; benign runtime/local-URL matches described above |
| Apptainer egress isolation | Scripted probe job 4626138 passed on Rohan CPU node; no task routes; external and metadata curl attempts failed with exit 7 |
| `--writable-tmpfs` without fakeroot | `/app` write passed in job 4626138 |
| Harbor control channel under network isolation | Not implemented or tested; Unix-socket provider patch still required |
| Adapter tripwire | Implemented; local unit tests cover classification and pre-execution refusal |
| Harbor telemetry opt-out | Verified from pinned 0.23.0 source; set `HARBOR_TELEMETRY=off` for future jobs |
| Real-model command jobs | Paused until egress and control-channel checks pass |
