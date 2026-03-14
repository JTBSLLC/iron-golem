from __future__ import annotations

import argparse
import time
from typing import Any, Callable

from irongolem.commands import build, discover, doctor, init, test
from irongolem.output import Envelope, emit_json

CommandHandler = Callable[[argparse.Namespace], dict[str, Any]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="irongolem")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor", help="Verify Java, Gradle, disk, and EULA state")
    doctor_parser.add_argument("--mod-dir", default=".", help="Path to the mod project")
    doctor_parser.add_argument("--accept-eula", action="store_true", help="Write eula=true into run/eula.txt")
    doctor_parser.set_defaults(handler=doctor.run)

    discover_parser = subparsers.add_parser("discover", help="Scan a mod and return its manifest")
    discover_parser.add_argument("--mod-dir", required=True, help="Path to the mod project")
    discover_parser.set_defaults(handler=discover.run)

    build_parser_ = subparsers.add_parser("build", help="Compile the mod and parse build errors")
    build_parser_.add_argument("--mod-dir", required=True, help="Path to the mod project")
    build_parser_.set_defaults(handler=build.run)

    test_parser = subparsers.add_parser("test", help="Run GameTests headlessly")
    test_parser.add_argument("--mod-dir", required=True, help="Path to the mod project")
    test_parser.add_argument("--test", help="Optional GameTest name filter")
    test_parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds")
    test_parser.set_defaults(handler=test.run)

    init_parser = subparsers.add_parser("init", help="Scaffold a new mod project")
    init_parser.add_argument("--mod-dir", required=True, help="Where to create the mod project")
    init_parser.add_argument("--loader", required=True, choices=["neoforge", "fabric"], help="Mod loader")
    init_parser.add_argument("--mc-version", required=True, help="Minecraft version")
    init_parser.add_argument("--mod-id", required=True, help="Mod identifier")
    init_parser.set_defaults(handler=init.run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler: CommandHandler = args.handler
    start = time.monotonic()
    try:
        result = handler(args)
        duration_ms = int((time.monotonic() - start) * 1000)
        envelope = Envelope(
            command=args.command,
            status=result.get("status", "error"),
            phase=result.get("phase", "setup"),
            duration_ms=duration_ms,
            data=result.get("data", {}),
            errors=result.get("errors", []),
            extra={k: v for k, v in result.items() if k not in {"status", "phase", "data", "errors"}},
        ).to_dict()
        emit_json(envelope, pretty=args.pretty)
        return 0 if envelope["status"] == "pass" else 1
    except Exception as exc:  # pragma: no cover - last-resort envelope path
        duration_ms = int((time.monotonic() - start) * 1000)
        envelope = Envelope(
            command=args.command,
            status="error",
            phase="setup",
            duration_ms=duration_ms,
            data={},
            errors=[{"type": "exception", "message": str(exc)}],
        ).to_dict()
        emit_json(envelope, pretty=args.pretty)
        return 1
