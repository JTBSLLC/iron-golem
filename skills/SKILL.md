---
name: irongolem
description: "Use this skill when developing, testing, or debugging Minecraft mods. Triggers on Minecraft modding, NeoForge, Fabric, GameTest, or when you need to compile or test a mod headlessly."
---

# irongolem

You have access to `irongolem`, a CLI for compiling and testing Minecraft mods headlessly.

## Protocol

1. Run `irongolem doctor --mod-dir <path>`
2. Run `irongolem discover --mod-dir <path>`
3. Write or update GameTests in `src/test/java/`
4. Run `irongolem build --mod-dir <path>`
5. Run `irongolem test --mod-dir <path>`
6. Fix failures and repeat

## Rules

- Always read the full JSON payload.
- Check `phase` before changing code.
- Treat `discover` output as the source of truth for block, item, sound, and capability names.
- Write focused tests: one behavior per test method.
- Use `tickFor()` generously when behavior is asynchronous.
