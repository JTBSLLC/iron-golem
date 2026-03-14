from __future__ import annotations

from pathlib import Path

from irongolem.commands import build as build_command
from irongolem.gradle.detector import detect_loader
from irongolem.server.lifecycle import ServerTimeoutError, run_server
from irongolem.server.log_parser import load_assertion_logs, parse_crash_report, parse_gametest_log


def run(args) -> dict[str, object]:
    mod_dir = Path(args.mod_dir).resolve()
    build_result = build_command.run(args)
    if build_result["status"] != "pass":
        return build_result

    loader = detect_loader(mod_dir)
    if loader == "fabric":
        task = "runGameTest"
    else:
        task = "runGameTestServer"

    extra_args: list[str] = []
    if args.test:
        extra_args.append(f"-Pirongolem.test={args.test}")

    try:
        proc = run_server(mod_dir, task, timeout=args.timeout, extra_args=extra_args)
    except ServerTimeoutError as exc:
        return {
            "status": "error",
            "phase": "runtime",
            "data": {},
            "errors": [
                {
                    "type": "timeout",
                    "message": str(exc),
                    "suggestion": "Check for infinite loops or increase --timeout.",
                }
            ],
        }

    log_output = f"{proc['stdout']}\n{proc['stderr']}"
    parsed = parse_gametest_log(log_output)
    assertion_data = collect_assertions(mod_dir)
    for test_entry in parsed["tests"]:
        name = str(test_entry["name"]).split(":")[-1]
        test_entry["assertions"] = assertion_data.get(name, assertion_data.get(str(test_entry["name"]), []))

    crash_report = newest_crash_report(mod_dir)
    if crash_report:
        return {
            "status": "error",
            "phase": "load",
            "data": {},
            "crash_report": crash_report,
            "errors": [],
        }

    if parsed["failed"]:
        return {
            "status": "fail",
            "phase": "test",
            "data": parsed,
            "crash_report": None,
            "errors": [],
        }
    if proc["returncode"] != 0 and not parsed["tests"]:
        return {
            "status": "error",
            "phase": "runtime",
            "data": {},
            "crash_report": None,
            "errors": [{"type": "runtime_error", "message": "GameTest server exited without reporting results"}],
        }
    return {
        "status": "pass",
        "phase": "test",
        "data": parsed,
        "crash_report": None,
        "errors": [],
    }


def collect_assertions(mod_dir: Path) -> dict[str, list[dict[str, object]]]:
    candidates = [
        mod_dir / "run" / "irongolem-results",
        mod_dir / "build" / "irongolem-results",
    ]
    merged: dict[str, list[dict[str, object]]] = {}
    for candidate in candidates:
        merged.update(load_assertion_logs(candidate))
    return merged


def newest_crash_report(mod_dir: Path) -> dict[str, object] | None:
    crash_dir = mod_dir / "run" / "crash-reports"
    if not crash_dir.exists():
        return None
    reports = sorted(crash_dir.glob("crash-*.txt"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not reports:
        return None
    return parse_crash_report(reports[0])
