# Synthetic serving and Harbor preflight artifacts - 2026-11

These directories contain selected, sanitized outputs copied from Rohan scratch for synthetic-only serving and Harbor preflight measurements. The Harbor run records are documented in [the Harbor CLI egress preflight](../harbor-cli-egress-preflight-2026-11-17.md).

| Job | GPU | Mode |
| --- | --- | --- |
| 4504954 | L40S | 12-configuration fit screen |
| 4504968 | L40S | 1 slot, q8_0, 65,536-token context measurement |
| 4504971 | L40S | 4 slots, q8_0, 65,536-token context measurement |
| 4505001 | L40S | 4 slots, f16, 65,536-token context measurement |
| 4505018 | RTX Pro 6000 Blackwell | 12-configuration fit screen |
| 4505019 | RTX Pro 6000 Blackwell | 4 slots, q8_0, 65,536-token context measurement |
| 4801507 | CPU | Initial Harbor CLI synthetic trial; read-only dependency mounts were not verified |
| 4801512 | CPU | Corrected Harbor CLI synthetic trial; verified read-only binds and egress probes |

The serving-sweep directories retain their JSONL records, metadata, GPU memory samples, server help output, and available server logs. The final three runs using the updated wrapper also include captured `slurm.out` and `slurm.err`; `sacct` results and the Slurm status discrepancy are recorded in the experiment note. The Harbor entries contain only compact, sanitized result JSON.

All prompts and token IDs were synthetic. No task benchmark or episode data is present. Raw Harbor logs remain on scratch; only compact sanitized JSON is checked in. The copied files are useful for review and reproduction, but should also be backed up to the Research Data Store when an RDS collection is available.
