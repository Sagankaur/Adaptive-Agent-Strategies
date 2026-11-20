# TB2 one-task feasibility route on Rohan

## Current status

The first one-task attempt stopped before model execution at job `4869467`; Harbor's default bootstrap required `/usr/bin/python3` and attempted installation while the task network was disabled. A separate model-free runtime preflight now passed (jobs `4870172` and `4870175`). The report and sanitized artifact for the earlier attempt remain unchanged. Do not resume that job or submit `02_one_task_pilot.sbatch`.

The current follow-up is model-free. The dependency setup job passed, while the first exact-image driver stopped before starting Harbor because it selected the cluster's system Python without `tomllib`. A single corrected driver run is allowed; it will use Harbor's Python 3.12 virtual environment. Full rationale and stop rules are in [`TB2-HARBOR-PYTHON313-RUNTIME-PREFLIGHT-2026-11-20.md`](../../experiments/TB2-HARBOR-PYTHON313-RUNTIME-PREFLIGHT-2026-11-20.md).

## Stage committed source on Rohan

Run from the repository root in PowerShell after committing the scripts and documentation:

```powershell
$commit = (git rev-parse HEAD).Trim()
$archive = Join-Path $env:TEMP "aas-tb2-runtime-$commit.tar"
git archive --format=tar --output=$archive HEAD
$archiveHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLower()
scp $archive rohan:tb2-runtime-source.tar
ssh rohan "mkdir -p /scratch/`$USER/tb2-pilot/source-$commit && mv ~/tb2-runtime-source.tar /scratch/`$USER/tb2-pilot/source.tar && tar -xf /scratch/`$USER/tb2-pilot/source.tar -C /scratch/`$USER/tb2-pilot/source-$commit && printf '%s\n' '$commit' > /scratch/`$USER/tb2-pilot/expected-source-commit.txt && printf '%s\n' '$archiveHash' > /scratch/`$USER/tb2-pilot/source-archive.sha256"
Remove-Item -LiteralPath $archive
```

This archive contains tracked project files only. It does not include `.env`, models, task data, or credentials.

## Run the model-free gate

1. Submit the binary-wheel preparation job:

   ```bash
   sbatch /scratch/$USER/tb2-pilot/source-<commit>/docs/cluster/tb2-pilot/04_prepare_harbor_runtime.sbatch
   ```

   It uses network access only to download Python wheels into a dedicated wheelhouse. Installation runs offline, with hashes, inside the pinned task SIF. No task setup or task command runs.

2. Wait for `sacct -X -j <prep-job-id>` to report `COMPLETED`. Check that `/scratch/$USER/tb2-pilot/runtime-manifest-<prep-job-id>.json` exists and the output reports `RUNTIME_PREP_STATUS=PASS`.

3. Submit the exact-image Harbor check using that setup job ID:

   ```bash
   sbatch --export=ALL,AAS_RUNTIME_PREP_JOB_ID=<prep-job-id> /scratch/$USER/tb2-pilot/source-<commit>/docs/cluster/tb2-pilot/05_exact_runtime_preflight.sbatch
   ```

4. Continue only if Slurm reports `COMPLETED` and `/scratch/$USER/tb2-pilot/exact-runtime-<job-id>.txt` says `status=PASS`. The record must confirm pinned dependencies and tree hash, UDS health and `environment.exec`, blocked external/DNS/metadata connections, a read-only dependency mount, expected Apptainer arguments, and no fakeroot. This gate passed on job `4870175`.

Any failed or missing check after the exact task container starts ends this route. The driver failure before container startup is recorded in the experiment report. Do not relax isolation or switch tasks. The current TB2 task scope prohibits model or agent runs on TB2, so this successful result remains infrastructure evidence only. No Oracle, reference solution, verifier, benchmark task setup, task command, or model ran in these jobs.

Raw logs, wheel files, and runtimes remain on scratch. Copy only reviewed, sanitized records and hashes into Git.
