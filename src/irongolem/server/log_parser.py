from __future__ import annotations

import json
import re
from pathlib import Path

RUNNING_RE = re.compile(r"Running test: (?P<name>[\w:./-]+)")
PASS_RE = re.compile(r"Test (?P<name>[\w:./-]+) passed")
FAIL_RE = re.compile(r"Test (?P<name>[\w:./-]+) failed: (?P<reason>.+)")
SUMMARY_RE = re.compile(r"GameTest completed\. (?P<passed>\d+) passed, (?P<failed>\d+) failed\.")


def parse_gametest_log(text: str) -> dict[str, object]:
    tests: dict[str, dict[str, object]] = {}
    summary: dict[str, int] = {"passed": 0, "failed": 0}
    for line in text.splitlines():
        running = RUNNING_RE.search(line)
        if running:
            name = running.group("name")
            tests.setdefault(name, {"name": name, "status": "running", "assertions": [], "error": None, "duration_ms": None})
            continue
        passed = PASS_RE.search(line)
        if passed:
            name = passed.group("name")
            entry = tests.setdefault(name, {"name": name, "assertions": [], "duration_ms": None})
            entry["status"] = "pass"
            entry.setdefault("error", None)
            continue
        failed = FAIL_RE.search(line)
        if failed:
            name = failed.group("name")
            entry = tests.setdefault(name, {"name": name, "assertions": [], "duration_ms": None})
            entry["status"] = "fail"
            entry["error"] = failed.group("reason").strip()
            continue
        summary_match = SUMMARY_RE.search(line)
        if summary_match:
            summary["passed"] = int(summary_match.group("passed"))
            summary["failed"] = int(summary_match.group("failed"))
    ordered = list(tests.values())
    if summary["passed"] == 0 and summary["failed"] == 0:
        summary["passed"] = len([test for test in ordered if test.get("status") == "pass"])
        summary["failed"] = len([test for test in ordered if test.get("status") == "fail"])
    return {
        "total": len(ordered),
        "passed": summary["passed"],
        "failed": summary["failed"],
        "tests": ordered,
    }


def load_assertion_logs(results_dir: Path) -> dict[str, list[dict[str, object]]]:
    if not results_dir.exists():
        return {}
    data: dict[str, list[dict[str, object]]] = {}
    for path in sorted(results_dir.glob("*.json")):
        assertions: list[dict[str, object]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            assertions.append(json.loads(line))
        data[path.stem] = assertions
    return data


def parse_crash_report(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    description = ""
    exception = ""
    stacktrace: list[str] = []
    source_file = None
    source_line = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("Description:"):
            description = stripped.split(":", 1)[1].strip()
        elif not exception and (stripped.startswith("java.") or stripped.startswith("net.") or "Exception" in stripped):
            exception = stripped
        elif stripped.startswith("at "):
            stacktrace.append(stripped)
            if source_file is None and ".java:" in stripped:
                source_file = stripped.split("(")[-1].rstrip(")")
                file_bits = source_file.split(":")
                if len(file_bits) == 2 and file_bits[1].isdigit():
                    source_line = int(file_bits[1])
    return {
        "description": description,
        "exception": exception,
        "stacktrace": stacktrace[:20],
        "file": source_file.split(":")[0] if source_file else None,
        "line": source_line,
    }
