from __future__ import annotations

from pathlib import Path

from irongolem.gradle.detector import detect_loader
from irongolem.gradle.parser import find_built_artifact, parse_gradle_errors
from irongolem.gradle.runner import GradleExecutionError, run_gradle


def run(args) -> dict[str, object]:
    mod_dir = Path(args.mod_dir).resolve()
    loader = detect_loader(mod_dir)
    try:
        proc = run_gradle(mod_dir, ["build"], timeout=1800)
    except GradleExecutionError as exc:
        return error_result("setup", str(exc))

    output = f"{proc.stdout}\n{proc.stderr}"
    errors = parse_gradle_errors(output, mod_dir)
    artifact = find_built_artifact(mod_dir)

    if proc.returncode == 0:
        return {
            "status": "pass",
            "phase": "compile",
            "data": {"artifact": artifact, "loader": loader},
            "errors": [],
        }
    if errors:
        return {
            "status": "fail",
            "phase": "compile",
            "data": {"loader": loader},
            "errors": errors,
        }
    return error_result("compile", "Gradle build failed", {"output_excerpt": output[-4000:], "loader": loader})


def error_result(phase: str, message: str, data: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "status": "error",
        "phase": phase,
        "data": data or {},
        "errors": [{"type": "build_error", "message": message}],
    }
