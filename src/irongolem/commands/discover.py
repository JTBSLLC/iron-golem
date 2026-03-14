from __future__ import annotations

from pathlib import Path

from irongolem.discovery.scanner import discover_manifest
from irongolem.gradle.parser import parse_gradle_errors
from irongolem.gradle.runner import GradleExecutionError, run_gradle


def run(args) -> dict[str, object]:
    mod_dir = Path(args.mod_dir).resolve()
    try:
        proc = run_gradle(mod_dir, ["classes"], timeout=1800)
    except GradleExecutionError as exc:
        return {
            "status": "error",
            "phase": "setup",
            "data": {},
            "errors": [{"type": "missing_dependency", "message": str(exc)}],
        }

    output = f"{proc.stdout}\n{proc.stderr}"
    if proc.returncode != 0:
        return {
            "status": "fail",
            "phase": "compile",
            "data": {},
            "errors": parse_gradle_errors(output, mod_dir) or [{"type": "build_error", "message": "Gradle classes task failed"}],
        }

    return {
        "status": "pass",
        "phase": "compile",
        "data": discover_manifest(mod_dir),
        "errors": [],
    }
