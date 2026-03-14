from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from irongolem.gradle.runner import GradleExecutionError, gradle_version


def run(args) -> dict[str, object]:
    mod_dir = Path(args.mod_dir).resolve()
    checks: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []

    java_version, java_home = detect_java()
    if java_version:
        checks.append({"name": "java", "status": "pass", "detail": f"Java {java_version} found"})
    else:
        checks.append({"name": "java", "status": "fail", "detail": "Java not found on PATH"})
        errors.append({"type": "missing_dependency", "message": "Java 17+ is required"})

    try:
        gradle = gradle_version(mod_dir)
    except GradleExecutionError:
        gradle = None
    if gradle:
        checks.append({"name": "gradle", "status": "pass", "detail": f"Gradle {gradle} available"})
    else:
        checks.append({"name": "gradle", "status": "fail", "detail": "No Gradle wrapper or system Gradle found"})
        errors.append({"type": "missing_dependency", "message": "Gradle wrapper or system Gradle is required"})

    total, used, free = shutil.disk_usage(mod_dir)
    free_gb = round(free / (1024 ** 3), 1)
    disk_status = "pass" if free_gb >= 2 else "fail"
    checks.append({"name": "disk", "status": disk_status, "detail": f"{free_gb} GB free"})
    if disk_status == "fail":
        errors.append({"type": "disk_space", "message": "At least 2 GB of free disk space is recommended"})

    eula_path = mod_dir / "run" / "eula.txt"
    if args.accept_eula:
        eula_path.parent.mkdir(parents=True, exist_ok=True)
        eula_path.write_text("eula=true\n", encoding="utf-8")
    eula_accepted = eula_path.exists() and "eula=true" in eula_path.read_text(encoding="utf-8").lower()
    eula_status = "pass" if eula_accepted else "fail"
    checks.append({"name": "eula", "status": eula_status, "detail": "eula.txt accepted" if eula_accepted else "eula.txt missing or false"})
    if not eula_accepted:
        errors.append(
            {
                "type": "eula",
                "message": "Minecraft EULA has not been accepted",
                "suggestion": "Re-run with --accept-eula to create run/eula.txt with eula=true",
            }
        )

    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    return {
        "status": status,
        "phase": "setup",
        "data": {
            "java_version": java_version,
            "java_home": java_home,
            "gradle_version": gradle,
            "disk_free_gb": free_gb,
            "eula_accepted": eula_accepted,
            "irongolem_lib_version": "0.1.0",
            "checks": checks,
        },
        "checks": checks,
        "errors": errors,
    }


def detect_java() -> tuple[str | None, str | None]:
    java_home = None
    try:
        proc = subprocess.run(["java", "-version"], text=True, capture_output=True, check=False, timeout=15)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None, java_home
    output = f"{proc.stdout}\n{proc.stderr}"
    for line in output.splitlines():
        if "version" in line.lower():
            parts = line.split('"')
            if len(parts) >= 2:
                return parts[1], str(Path(shutil.which("java") or "").resolve().parent.parent)
    return None, java_home
