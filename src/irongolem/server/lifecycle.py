from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path
from queue import Empty, Queue

from irongolem.gradle.runner import gradle_executable


class ServerTimeoutError(TimeoutError):
    """Raised when the test server does not complete in time."""


def run_server(
    mod_dir: Path,
    task: str,
    timeout: int,
    extra_args: list[str] | None = None,
    idle_timeout: int = 30,
) -> dict[str, object]:
    cmd = gradle_executable(mod_dir) + [task, "--daemon", "--console=plain", "-Djava.awt.headless=true"]
    if extra_args:
        cmd.extend(extra_args)

    process = subprocess.Popen(
        cmd,
        cwd=mod_dir,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
    )

    queue: Queue[tuple[str, str]] = Queue()
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    last_output = time.monotonic()

    def reader(pipe, stream_name: str) -> None:
        if pipe is None:
            return
        for line in pipe:
            queue.put((stream_name, line))
        pipe.close()

    threads = [
        threading.Thread(target=reader, args=(process.stdout, "stdout"), daemon=True),
        threading.Thread(target=reader, args=(process.stderr, "stderr"), daemon=True),
    ]
    for thread in threads:
        thread.start()

    start = time.monotonic()
    while True:
        try:
            stream_name, line = queue.get(timeout=0.2)
            last_output = time.monotonic()
            if stream_name == "stdout":
                stdout_lines.append(line)
            else:
                stderr_lines.append(line)
        except Empty:
            pass

        if process.poll() is not None and queue.empty():
            break
        now = time.monotonic()
        if now - start > timeout:
            process.kill()
            raise ServerTimeoutError(f"Server did not complete tests within {timeout} seconds.")
        if stdout_lines and now - last_output > idle_timeout:
            process.kill()
            raise ServerTimeoutError(f"Server produced no output for {idle_timeout} seconds.")

    return {
        "returncode": process.returncode,
        "stdout": "".join(stdout_lines),
        "stderr": "".join(stderr_lines),
    }
