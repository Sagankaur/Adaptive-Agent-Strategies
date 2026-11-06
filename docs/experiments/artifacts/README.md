# Synthetic serving sweep artifacts - 2026-11

These directories contain raw outputs copied from Rohan scratch for the synthetic-only serving preflight documented in [serving-sweep-2026-11.md](../serving-sweep-2026-11.md).

| Job | GPU | Mode |
| --- | --- | --- |
| 4504954 | L40S | 12-configuration fit screen |
| 4504968 | L40S | 1 slot, q8_0, 65,536-token context measurement |
| 4504971 | L40S | 4 slots, q8_0, 65,536-token context measurement |
| 4505001 | L40S | 4 slots, f16, 65,536-token context measurement |
| 4505018 | RTX Pro 6000 Blackwell | 12-configuration fit screen |
| 4505019 | RTX Pro 6000 Blackwell | 4 slots, q8_0, 65,536-token context measurement |

Each run directory retains its JSONL records, metadata, GPU memory samples, server help output, and available server logs. The final three runs using the updated wrapper also include captured `slurm.out` and `slurm.err`; `sacct` results and the Slurm status discrepancy are recorded in the experiment note.

All prompts and token IDs were synthetic. No task benchmark or episode data is present. The copied files are useful for review and reproduction, but should also be backed up to the Research Data Store when an RDS collection is available.
