from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Sequence


class GradleExecutionError(RuntimeError):
    """Raised when no Gradle executable can be found."""


def gradle_executable(mod_dir: Path) -> list[str]:
    wrapper = mod_dir / ("gradlew.bat" if shutil.which("cmd.exe") and (mod_dir / "gradlew.bat").exists() else "gradlew")
    if wrapper.exists():
        return [str(wrapper)]
    system_gradle = shutil.which("gradle")
    if system_gradle:
        return [system_gradle]
    raise GradleExecutionError("No Gradle wrapper or system Gradle installation found")


def run_gradle(
    mod_dir: Path,
    tasks: Sequence[str],
    extra_args: Sequence[str] | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = gradle_executable(mod_dir) + list(tasks) + ["--daemon", "--console=plain"]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(
        cmd,
        cwd=mod_dir,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def gradle_version(mod_dir: Path) -> str | None:
    try:
        proc = run_gradle(mod_dir, ["--version"], timeout=30)
    except (GradleExecutionError, subprocess.TimeoutExpired):
        return None
    output = f"{proc.stdout}\n{proc.stderr}"
    for line in output.splitlines():
        if line.lower().startswith("gradle "):
            return line.split(maxsplit=1)[1].strip()
    return None
