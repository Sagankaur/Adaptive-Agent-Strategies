# Terminal-Bench 2.0 task list

`tb2_tasks.jsonl` lists the 89 tasks of Terminal-Bench 2.0 with the metadata used to stratify the splits.

- **Repository:** https://github.com/laude-institute/terminal-bench-2
- **Commit:** `2fd12b88aafdd04a52c298e3940bcb189f9766d6` (main, committed 2026-04-30 05:53 UTC, which is 2026-04-29 in US time zones; "Add task metadata to task manifests")
- **Extracted:** 2026-10-15
- **Method:** one task per top-level directory (89 directories; the other two root entries are `LICENSE` and `README.md`). The `task.toml` of each was parsed with Python's `tomllib`. No `task.yaml` exists at this commit. Nothing from the repository was executed.

## Fields

| JSONL field | Read from `task.toml` |
|---|---|
| `task_id` | the directory name (equal to the suffix of `[task] name = "terminal-bench/<id>"`) |
| `category` | `[metadata] category` |
| `difficulty` | `[metadata] difficulty` |
| `author_name` | `[metadata] author_name` |
| `tags` | `[metadata] tags` (empty for 3 tasks) |
| `source` | a fixed note giving the repository, commit and table |

`evaluation.splits` reads only `task_id`, `category` and `difficulty`; the other keys are ignored.

## Counts

Category (16):

- data-processing: 4
- data-querying: 1
- data-science: 8
- debugging: 5
- file-operations: 5
- games: 1
- machine-learning: 3
- mathematics: 4
- model-training: 4
- optimization: 1
- personal-assistant: 1
- scientific-computing: 8
- security: 8
- software-engineering: 26
- system-administration: 9
- video-processing: 1

Difficulty:

- easy: 4
- medium: 55
- hard: 30

Seed for the split: 20261015 (see `splits/terminal-bench-2.0.json`).
