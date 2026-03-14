# irongolem

Use `irongolem` when developing, testing, or debugging Minecraft mods.

## Protocol

1. Run `irongolem doctor --mod-dir <path>`
2. Run `irongolem discover --mod-dir <path>`
3. Write or update GameTests in `src/test/java/`
4. Run `irongolem build --mod-dir <path>`
5. Run `irongolem test --mod-dir <path>`
6. Fix failures and repeat

## Result handling

- `status=pass`: command succeeded
- `status=fail`: the tool ran and found compile or test failures
- `status=error`: setup, loader, timeout, or crash problem
- `phase=compile|load|runtime|test`: focus the fix on that stage
