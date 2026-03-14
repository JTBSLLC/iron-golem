# Iron Golem

`irongolem` is a headless Minecraft mod testing harness for AI coding agents. It wraps Gradle, loader detection, resource discovery, and GameTest log parsing behind a JSON-only CLI so an agent can compile and test mods without Minecraft-specific prompt engineering.

## Status

This repository contains an initial, installable implementation:

- Python CLI with `doctor`, `discover`, `build`, `test`, and `init`
- Resource-based discovery for NeoForge and Fabric projects
- Gradle and GameTest output parsing with structured JSON envelopes
- Scaffold templates and agent skill files
- A starter `irongolem-lib` Java API stub for test authors

The Python CLI is usable today. The Java library and generated templates are intentionally lightweight starting points rather than a complete production-ready Minecraft integration.

## Install

```bash
pip install .
```

Or after publishing:

```bash
pip install irongolem
```

## Commands

```bash
irongolem doctor --mod-dir ./my-mod
irongolem discover --mod-dir ./my-mod
irongolem build --mod-dir ./my-mod
irongolem test --mod-dir ./my-mod --timeout 120
irongolem init --mod-dir ./my-mod --loader neoforge --mc-version 1.21.1 --mod-id mymod
```

Every command emits one JSON object to stdout. Human-readable progress and diagnostics go to stderr.

## Development

```bash
python -m pytest
python -m irongolem doctor
```
