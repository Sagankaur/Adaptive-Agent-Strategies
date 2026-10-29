# Reproduce the project client and toy-runner smoke

This repeats the one-task integration check recorded in [`REPORT.md`](REPORT.md). It needs access to the Deakin A2I2 cluster, the pinned model and Apptainer image on scratch, and the Python 3.11.7 smoke venv described in that report.

From the project root on the cluster login node, at the pinned project commit:

```bash
mkdir -p "$HOME/jobs/aas-client-smoke-src"
cp -r llm environments evaluation baselines strategy_schema "$HOME/jobs/aas-client-smoke-src/"
cp docs/cluster/l40s-client-smoke/project_client_toy_smoke.py "$HOME/jobs/project_client_toy_smoke.py"
sbatch docs/cluster/l40s-client-smoke/03_project_toy_smoke.sh
```

The Slurm script expects the files from the prior model-fetch step at `/scratch/$USER/models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf` and `/scratch/$USER/images/llama-server-cuda12-b11515.sif`, and the venv at `/scratch/$USER/venvs/aas-client-smoke`. Results are written to `$HOME/jobs/out/project_client_toy_<jobid>/`.

The job is intentionally limited to one toy task. A successful rerun still does not close G-INFRA; that requires the scripted Harbor CPU toy run and a five-task TB-Pro infrastructure smoke. The current adapter implementation is documented in [`../harbor-adapter/IMPLEMENTATION_2026-10-29.md`](../harbor-adapter/IMPLEMENTATION_2026-10-29.md).
