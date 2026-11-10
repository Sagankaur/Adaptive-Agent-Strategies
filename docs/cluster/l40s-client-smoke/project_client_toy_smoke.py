"""One-task integration spike for the real model client and toy runner."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from baselines.baselines import FixedStrategy
from environments.toy_text import ToyTextEnvironment, make_toy_tasks
from evaluation.runner import RunBudget, evaluate, summarise
from evaluation.splits import TaskInfo, make_split
from llm import Message, OpenAICompatibleModel
from strategy_schema.defaults import s0
from strategy_schema.model import Budget


def main() -> None:
    port, out_arg = int(sys.argv[1]), Path(sys.argv[2])
    out_arg.mkdir(parents=True, exist_ok=True)
    client = OpenAICompatibleModel(
        base_url=f"http://127.0.0.1:{port}/v1",
        model="/models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf",
        name="qwen3.6-35b-a3b-q4_k_m",
        timeout_s=180,
        temperature=0.0,
        max_tokens=512,
    )

    direct = client.complete(
        [
            Message("system", "Reply with the single word PASS and no explanation."),
            Message("user", "Output PASS only."),
        ]
    )
    if not isinstance(direct.text, str) or not direct.text.strip():
        raise RuntimeError("real client returned empty/non-text content")
    if direct.input_tokens <= 0 or direct.output_tokens <= 0:
        raise RuntimeError(f"real client returned invalid usage counts: {direct!r}")
    print(
        json.dumps(
            {
                "direct_text": direct.text[:120],
                "input_tokens": direct.input_tokens,
                "output_tokens": direct.output_tokens,
                "elapsed_s": round(direct.elapsed_s, 3),
            }
        ),
        flush=True,
    )

    tasks = make_toy_tasks(1, seed=0)
    task = tasks[0]
    split = make_split(
        [TaskInfo(task_id=task.task_id, category=task.category, difficulty=task.difficulty)],
        {"A": 1},
        seed=20261028,
        benchmark="toy-text",
    )
    strategy = s0().model_copy(update={"budget": Budget(max_steps=8, max_tokens=4096, max_wall_s=300)})
    run_path = out_arg / "toy_run.jsonl"
    outcomes, records = evaluate(
        run_id="real-model-toy-smoke-2026-10-28",
        baseline=FixedStrategy(),
        strategy=strategy,
        model=client,
        env=ToyTextEnvironment(),
        tasks={task.task_id: task},
        split=split,
        split_name="A",
        out_path=run_path,
        budget=RunBudget(max_calls=10, max_tokens=4096),
    )
    if len(records) != 1 or records[0].status != "completed":
        raise RuntimeError(f"runner did not write one completed result: {records!r}")
    if records[0].cost is None or records[0].cost["calls"] <= 0 or records[0].cost["input_tokens"] <= 0:
        raise RuntimeError(f"runner record did not capture model usage: {records[0]!r}")
    if len(run_path.read_text(encoding="utf-8").splitlines()) != 1:
        raise RuntimeError(f"expected one JSONL result at {run_path}")

    summary = {
        "task_id": task.task_id,
        "task_category": task.category,
        "success": outcomes[0].success,
        "stop_reason": outcomes[0].attempts[0].stop_reason,
        "calls": records[0].cost["calls"],
        "input_tokens": records[0].cost["input_tokens"],
        "output_tokens": records[0].cost["output_tokens"],
        "model_usage_total": client.usage.to_dict(),
        "runner_summary": summarise(records).__dict__,
        "result_path": str(run_path),
    }
    (out_arg / "client_smoke_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
