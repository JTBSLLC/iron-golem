from __future__ import annotations

from pathlib import Path


def read_build_text(mod_dir: Path) -> str:
    for name in ("build.gradle", "build.gradle.kts"):
        path = mod_dir / name
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


def detect_loader(mod_dir: Path) -> str:
    build_text = read_build_text(mod_dir).lower()
    if "architectury" in build_text:
        return "architectury"
    if "net.neoforged" in build_text or "neoforge" in build_text:
        return "neoforge"
    if "fabric-loom" in build_text or "net.fabricmc" in build_text or "fabric" in build_text:
        return "fabric"
    if (mod_dir / "src/main/resources/META-INF/neoforge.mods.toml").exists():
        return "neoforge"
    if (mod_dir / "src/main/resources/fabric.mod.json").exists():
        return "fabric"
    return "unknown"


def detect_minecraft_version(mod_dir: Path) -> str | None:
    gradle_properties = mod_dir / "gradle.properties"
    if gradle_properties.exists():
        for line in gradle_properties.read_text(encoding="utf-8").splitlines():
            if "=" not in line:
                continue
            key, value = [part.strip() for part in line.split("=", 1)]
            if key in {"minecraft_version", "minecraftVersion", "mc_version"}:
                return value
    build_text = read_build_text(mod_dir)
    for quote in ('"', "'"):
        token = f"{quote}1."
        if token in build_text:
            start = build_text.index(token) + 1
            end = build_text.find(quote, start)
            if end > start:
                return build_text[start:end]
    return None
