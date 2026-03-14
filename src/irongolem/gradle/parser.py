from __future__ import annotations

import re
from pathlib import Path

ERROR_RE = re.compile(r"^(?P<file>.+?):(?P<line>\d+): (?:(?P<kind>warning|error): )(?P<message>.+)$")

SUGGESTIONS: tuple[tuple[str, str], ...] = (
    ("getEnchantments()", "ItemStack method may have been renamed to getAllEnchantments() in newer Minecraft mappings."),
    ("RegistryObject", "Check whether the loader or mappings changed registry holder types."),
    ("MenuProvider", "Confirm your menu provider imports and constructor signatures for the target Minecraft version."),
)


def parse_gradle_errors(output: str, root_dir: Path) -> list[dict[str, object]]:
    lines = output.splitlines()
    errors: list[dict[str, object]] = []
    for index, line in enumerate(lines):
        match = ERROR_RE.match(line.strip())
        if not match or match.group("kind") != "error":
            continue
        file_path = match.group("file")
        line_number = int(match.group("line"))
        context = source_context(root_dir / file_path, line_number)
        message = match.group("message").strip()
        suggestion = suggest_fix(message)
        errors.append(
            {
                "type": "compile_error",
                "file": file_path,
                "line": line_number,
                "column": extract_column(lines, index),
                "message": message,
                "suggestion": suggestion,
                "context": context,
            }
        )
    return errors


def extract_column(lines: list[str], error_index: int) -> int | None:
    if error_index + 2 >= len(lines):
        return None
    caret_line = lines[error_index + 2]
    caret = caret_line.find("^")
    return caret + 1 if caret >= 0 else None


def source_context(path: Path, line_number: int, radius: int = 1) -> str:
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = max(line_number - radius - 1, 0)
    end = min(line_number + radius, len(lines))
    return "\n".join(lines[start:end])


def suggest_fix(message: str) -> str | None:
    for needle, suggestion in SUGGESTIONS:
        if needle in message:
            return suggestion
    return None


def find_built_artifact(mod_dir: Path) -> str | None:
    libs_dir = mod_dir / "build" / "libs"
    if not libs_dir.exists():
        return None
    jars = sorted(
        (path for path in libs_dir.glob("*.jar") if not path.name.endswith(("-sources.jar", "-dev.jar"))),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not jars:
        return None
    return str(jars[0].relative_to(mod_dir))
