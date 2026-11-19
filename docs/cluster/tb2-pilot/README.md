# TB2 one-task pilot on Rohan

This is one exploratory feasibility attempt, not a benchmark estimate. It uses the local gpt-oss-20b model on `cobol-modernization`, an A-split task not listed in Decision 21's prior instruction exposure. The result is excluded from future confirmatory analysis by `evaluation/data/tb2_pilot_exclusions.json`.

## Frozen inputs and stop conditions

- Task snapshot: `harborframework/terminal-bench-2.0`, revision `f2e8c75e23add71613117eecc9498f53bcd7e04e`.
- Docker Registry source image: `alexgshaw/cobol-modernization:20251031`, resolved to manifest digest `sha256:593ab9df3d83f771e927888b2d9436b380cdf7ec4d0af2a9f0802d541edebba0`.
- Model: `/scratch/$USER/models/gpt-oss-20b-MXFP4.gguf`.
- Harbor: 0.23.0; Apptainer: 1.3.3; UDS patch: `docs/cluster/harbor-egress-safety/harbor-0.23.0-uds.patch`.
- Stop if the exact-image network/UDS preflight fails, the SIF or UDS patch hash changes, the task metadata image tag differs, local NVMe is unavailable, or required inputs are missing. Do not retry or select another task.

## Stage the committed source snapshot

From the repository root in PowerShell, after committing the preregistration and scripts:

```powershell
$archive = Join-Path $env:TEMP 'aas-tb2-pilot-source.tar'
$commit = (git rev-parse HEAD).Trim()
git archive --format=tar --output=$archive HEAD
$archiveHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLower()
scp $archive rohan:tb2-pilot-source.tar
ssh rohan "mkdir -p /scratch/`$USER/tb2-pilot/source-$commit && mv ~/tb2-pilot-source.tar /scratch/`$USER/tb2-pilot/source.tar && tar -xf /scratch/`$USER/tb2-pilot/source.tar -C /scratch/`$USER/tb2-pilot/source-$commit && printf '%s\\n' '$commit' > /scratch/`$USER/tb2-pilot/expected-source-commit.txt && printf '%s\\n' '$archiveHash' > /scratch/`$USER/tb2-pilot/source-archive.sha256"
Remove-Item -LiteralPath $archive
```

This archives tracked files only; `.env`, model weights, benchmark data, and local secrets are not included. The dataset and model remain on cluster scratch.

## Run order

In the commands below, replace `<commit>` with the value of `$commit` printed by `git rev-parse HEAD` above.

1. Submit only the model-free exact-image preflight:

   ```bash
   sbatch /scratch/$USER/tb2-pilot/source-<commit>/docs/cluster/tb2-pilot/01_task_image_preflight.sbatch
   ```

2. Inspect only `/scratch/$USER/tb2-pilot/preflight-<job-id>.txt` and `sacct -X -j <job-id>`. Continue only when that exact record says `status=PASS` and Slurm says `COMPLETED`; keep the full probe log on scratch. The preflight verifies the snapshot content against the pinned Hugging Face revision, model/server hashes, exact task SIF, UDS control, blocked DNS/external-IP/metadata access, `--writable-tmpfs`, `--containall`, absence of `--fakeroot`, and path-only absence of verifier/reference-like artifacts in the agent work directory.

3. If and only if preflight passes, submit the single GPU episode:

   ```bash
   sbatch --export=ALL,AAS_PREFLIGHT_JOB_ID=<preflight-job-id> /scratch/$USER/tb2-pilot/source-<commit>/docs/cluster/tb2-pilot/02_one_task_pilot.sbatch
   ```

4. Do not submit a replacement job after any model, Harbor, or verifier failure. Keep raw model, Harbor, task, and verifier logs on scratch. Copy only the sanitized summary and hashes to the repository after review.

Slurm scripts use the account-specific Rohan partitions/QoS. This pilot does not use Oracle or reference solutions, does not grant general permission for other TB2 tasks, and does not clear the TB-Pro route/licence gate.
