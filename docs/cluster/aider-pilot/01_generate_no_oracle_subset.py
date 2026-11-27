"""Generate the four pre-run eligible frozen Aider tasks without Oracle files.

The script imports the adapter at its pinned Harbor commit. It bypasses the
adapter constructor because that constructor discovers every Python exercise
and reads all task instructions. It instantiates only the explicitly frozen,
eligible IDs. It does not read reference example files or solution-script
templates, and it does not copy `.meta` recursively.

Task test files and starter source files are copied into the generated Harbor
task for ordinary model editing and official verification. Their contents are
not read by this generator. All generated task material must stay outside the
public repository.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import stat
import sys
from pathlib import Path


HARBOR_COMMIT = "1e5c5c6db929a10a140d05e606882c671ae20729"
POLYGLOT_COMMIT = "7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f"
ELIGIBLE_TASKS = ("hangman", "poker", "rest-api", "variable-length-quantity")
SAFE_META_FILES = ("config.json", "tests.toml")


def git_head(path: Path) -> str:
    import subprocess

    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()


def safe_setup_test_files(adapter: object, task: object, tests_dir: Path) -> None:
    """Copy verifier inputs while excluding reference/example metadata."""
    exercise_path = Path(task.exercise_path)
    metadata_source = exercise_path / ".meta"
    if metadata_source.is_dir():
        metadata_dest = tests_dir / ".meta"
        metadata_dest.mkdir(parents=True, exist_ok=True)
        for name in SAFE_META_FILES:
            source = metadata_source / name
            if source.is_file():
                shutil.copy2(source, metadata_dest / name)

    for relative in task.test_files:
        adapter_module_copy_relative(adapter, exercise_path, relative, tests_dir)
    for relative in getattr(task, "editor_files", []) or []:
        adapter_module_copy_relative(adapter, exercise_path, relative, tests_dir)


def adapter_module_copy_relative(
    adapter: object, source_root: Path, relative: str, destination_root: Path
) -> None:
    """Use the pinned adapter's ordinary path copier for declared files only."""
    module = sys.modules[type(adapter).__module__]
    module.copy_relative(source_root, relative, destination_root)


def set_toml_section_values(text: str, section: str, values: dict[str, str]) -> str:
    """Set a small allowlisted set of scalar task fields without reading task code."""
    header = f"[{section}]"
    matches = list(re.finditer(rf"(?m)^\[{re.escape(section)}\]\s*$", text))
    if len(matches) != 1:
        raise SystemExit(f"expected one {header} section")
    start = matches[0].end()
    next_section = re.search(r"(?m)^\[[^\]]+\]\s*$", text[start:])
    end = start + next_section.start() if next_section else len(text)
    body = text[start:end]
    for key, value in values.items():
        line = f'{key} = "{value}"'
        pattern = re.compile(rf"(?m)^[ \t]*{re.escape(key)}[ \t]*=.*$")
        if pattern.search(body):
            body = pattern.sub(line, body, count=1)
        else:
            body = "\n" + line + body
    return text[:start] + body + text[end:]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--polyglot-root", type=Path, required=True)
    parser.add_argument("--harbor-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--task-image", required=True)
    args = parser.parse_args()

    polyglot_root = args.polyglot_root.resolve()
    harbor_root = args.harbor_root.resolve()
    output_dir = args.output_dir.resolve()
    if git_head(polyglot_root) != POLYGLOT_COMMIT:
        raise SystemExit("Polyglot checkout is not at the frozen commit")
    if git_head(harbor_root) != HARBOR_COMMIT:
        raise SystemExit("Harbor checkout is not at the pinned adapter commit")
    if output_dir.exists():
        raise SystemExit(f"refusing to overwrite existing output: {output_dir}")

    adapter_source = harbor_root / "adapters" / "aider_polyglot" / "src"
    template_dir = (
        harbor_root
        / "adapters"
        / "aider_polyglot"
        / "src"
        / "aider_polyglot"
        / "task-template"
    )
    sys.path.insert(0, str(adapter_source))
    from aider_polyglot.adapter import AiderPolyglotAdapter, AiderPolyglotTask

    adapter = AiderPolyglotAdapter.__new__(AiderPolyglotAdapter)
    adapter.task_dir = output_dir
    adapter.polyglot_repo_path = polyglot_root
    adapter.templates_dir = template_dir
    adapter.target_languages = ["python"]
    adapter.tasks = {}

    for task_id in ELIGIBLE_TASKS:
        exercise_path = (
            polyglot_root / "python" / "exercises" / "practice" / task_id
        )
        if not exercise_path.is_dir():
            raise SystemExit(f"frozen task directory missing: {task_id}")
        adapter.tasks[f"python_{task_id}"] = AiderPolyglotTask(
            exercise_path, "python", task_id
        )

    adapter._setup_test_files = lambda task, tests_dir: safe_setup_test_files(
        adapter, task, tests_dir
    )
    # Assignment to the instance replaces the bound method with a no-op. The
    # pinned implementation's omitted method would create a solve.sh and read
    # .meta example/reference files to encrypt an Oracle payload.
    adapter._create_solution_script = lambda *_args, **_kwargs: None

    output_dir.mkdir(parents=True)
    for task_id in ELIGIBLE_TASKS:
        full_id = f"python_{task_id}"
        adapter.generate_task(full_id, f"polyglot_{full_id}")
        task_output = output_dir / f"polyglot_{full_id}"
        # Harbor 0.23.0 executes verifier shell scripts directly. Keep the
        # executable bit in the staged task tree so it does not depend on a
        # privileged chmod inside a rootless Apptainer container.
        for script in (task_output / "tests").rglob("*.sh"):
            script.chmod(stat.S_IMODE(script.stat().st_mode) | stat.S_IXUSR)
        task_config = task_output / "task.toml"
        task_text = task_config.read_text(encoding="utf-8")
        escaped_image = args.task_image.replace('"', '\\"')
        task_text = set_toml_section_values(
            task_text,
            "environment",
            {"docker_image": escaped_image, "network_mode": "no-network"},
        )
        task_text = set_toml_section_values(task_text, "agent", {"network_mode": "no-network"})
        task_text = set_toml_section_values(task_text, "verifier", {"network_mode": "no-network"})
        task_config.write_text(task_text, encoding="utf-8")
        empty_solution_dir = task_output / "solution"
        if empty_solution_dir.is_dir():
            empty_solution_dir.rmdir()

        relative_paths = [
            path.relative_to(task_output).as_posix()
            for path in task_output.rglob("*")
        ]
        forbidden = [
            path
            for path in relative_paths
            if ".oracle" in path.casefold()
            or path.startswith("solution/")
            or "/.meta/example" in path.casefold()
            or "/reference/" in path.casefold()
        ]
        if forbidden:
            raise SystemExit(
                f"forbidden Oracle/reference artifact path in {full_id}: {forbidden}"
            )

    manifest = {
        "harbor_commit": HARBOR_COMMIT,
        "polyglot_commit": POLYGLOT_COMMIT,
        "generated_task_ids": [f"polyglot_python_{name}" for name in ELIGIBLE_TASKS],
        "oracle_artifacts_generated": False,
        "reference_example_files_copied": False,
        "task_image": args.task_image,
        "environment_network_mode": "no-network",
        "agent_network_mode": "no-network",
        "verifier_network_mode": "no-network",
        "model_episodes_run": False,
    }
    (output_dir / "generation-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
