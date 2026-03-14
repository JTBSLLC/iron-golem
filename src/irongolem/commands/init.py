from __future__ import annotations

import shutil
from importlib import resources
from pathlib import Path


def run(args) -> dict[str, object]:
    mod_dir = Path(args.mod_dir).resolve()
    template_root = resources.files("irongolem").joinpath("_resources", "templates", args.loader)
    if not template_root.is_dir():
        return {
            "status": "error",
            "phase": "setup",
            "data": {},
            "errors": [{"type": "template_error", "message": f"Template root not found: {template_root}"}],
        }

    mod_dir.mkdir(parents=True, exist_ok=True)
    replacements = {
        "{{MOD_ID}}": args.mod_id,
        "{{MC_VERSION}}": args.mc_version,
        "{{PACKAGE_NAME}}": package_name(args.mod_id),
        "{{CLASS_NAME}}": class_name(args.mod_id),
    }

    for path in template_root.rglob("*"):
        if path.is_dir():
            continue
        relative = path.relative_to(template_root)
        target = mod_dir / render_path(str(relative), replacements)
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".template":
            content = path.read_text(encoding="utf-8")
            for needle, value in replacements.items():
                content = content.replace(needle, value)
            target = target.with_suffix("")
            target.write_text(content, encoding="utf-8")
        else:
            shutil.copy2(path, target)

    run_dir = mod_dir / "run"
    run_dir.mkdir(exist_ok=True)
    (run_dir / "eula.txt").write_text("eula=true\n", encoding="utf-8")
    return {
        "status": "pass",
        "phase": "setup",
        "data": {
            "mod_dir": str(mod_dir),
            "loader": args.loader,
            "minecraft_version": args.mc_version,
            "mod_id": args.mod_id,
        },
        "errors": [],
    }


def render_path(value: str, replacements: dict[str, str]) -> str:
    rendered = value
    for needle, replacement in replacements.items():
        rendered = rendered.replace(needle, replacement)
    return rendered


def package_name(mod_id: str) -> str:
    return mod_id.replace("-", "_")


def class_name(mod_id: str) -> str:
    return "".join(chunk.capitalize() for chunk in mod_id.replace("-", "_").split("_")) + "Mod"
