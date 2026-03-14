from __future__ import annotations

import json
from pathlib import Path

from irongolem.gradle.detector import detect_loader, detect_minecraft_version

STATIC_CAPABILITIES = {
    "actions": [
        {
            "name": "placeBlock",
            "signature": "placeBlock(int x, int y, int z, String blockId)",
            "description": "Place a block at the given coordinates in the test structure",
        },
        {
            "name": "breakBlock",
            "signature": "breakBlock(int x, int y, int z)",
            "description": "Break the block at the given coordinates",
        },
        {
            "name": "interactBlock",
            "signature": "interactBlock(int x, int y, int z)",
            "description": "Simulate a player right-click on the block",
        },
        {
            "name": "insertItem",
            "signature": "insertItem(int x, int y, int z, int slot, String itemStack)",
            "description": "Insert an item into a container block's inventory slot. itemStack uses Minecraft command syntax for NBT.",
        },
        {
            "name": "extractItem",
            "signature": "extractItem(int x, int y, int z, int slot)",
            "description": "Remove the item from a container block's inventory slot",
        },
        {
            "name": "tickFor",
            "signature": "tickFor(int ticks)",
            "description": "Advance the server by N ticks (20 ticks = 1 second)",
        },
        {
            "name": "sendRedstone",
            "signature": "sendRedstone(int x, int y, int z, int power)",
            "description": "Set redstone signal level (0-15) at a position",
        },
        {
            "name": "simulatePlayer",
            "signature": "simulatePlayer(String action, int x, int y, int z)",
            "description": "Simulate player actions: walk, sneak, jump, attack, useItem",
        },
    ],
    "assertions": [
        {
            "name": "assertBlockState",
            "signature": "assertBlockState(int x, int y, int z, String property, Object value)",
            "description": "Assert a block state property equals the expected value",
        },
        {
            "name": "assertNBT",
            "signature": "assertNBT(int x, int y, int z, String path, Matcher matcher)",
            "description": "Assert a value in the block entity's NBT data. Path uses dot notation. Matchers: equals(), contains(), greaterThan(), exists()",
        },
        {
            "name": "assertInventory",
            "signature": "assertInventory(int x, int y, int z, int slot, ItemMatcher matcher)",
            "description": "Assert an inventory slot contains a matching item. Matchers: item(), count(), enchantments(), nbt()",
        },
        {
            "name": "assertParticles",
            "signature": "assertParticles(String particleId, BlockPos near, int minCount)",
            "description": "Assert that a particle type was emitted near a position during the test",
        },
        {
            "name": "assertSound",
            "signature": "assertSound(String soundId, BlockPos near)",
            "description": "Assert that a sound event was triggered near a position during the test",
        },
        {
            "name": "assertGui",
            "signature": "assertGui(int x, int y, int z, GuiMatcher matcher)",
            "description": "Assert the block's menu/GUI state. Matchers: isOpen(), slotContains(), slotCount()",
        },
    ],
    "queries": [
        {
            "name": "queryNBT",
            "signature": "queryNBT(int x, int y, int z) -> JsonObject",
            "description": "Read the full NBT data of a block entity as a JSON object",
        },
        {
            "name": "queryInventory",
            "signature": "queryInventory(int x, int y, int z) -> List<ItemStack>",
            "description": "Read all inventory slots of a container block",
        },
        {
            "name": "queryBlockState",
            "signature": "queryBlockState(int x, int y, int z) -> Map<String, String>",
            "description": "Read all block state properties as key-value pairs",
        },
    ],
}


def discover_manifest(mod_dir: Path) -> dict[str, object]:
    mod_id = detect_mod_id(mod_dir)
    loader = detect_loader(mod_dir)
    minecraft_version = detect_minecraft_version(mod_dir)
    resources = mod_dir / "src" / "main" / "resources"

    blocks = block_entries(resources, mod_id)
    items = item_entries(resources, mod_id)
    sounds = sound_entries(resources, mod_id)
    particles = resource_ids(resources / "assets" / mod_id / "particles", f"{mod_id}:")
    recipes = recipe_entries(resources, mod_id)

    enrich_blocks(blocks, resources, mod_id, items)

    return {
        "mod_id": mod_id,
        "loader": loader,
        "minecraft_version": minecraft_version,
        "blocks": blocks,
        "items": items,
        "entities": [],
        "sounds": sounds,
        "particles": particles,
        "recipes": recipes,
        "capabilities": STATIC_CAPABILITIES,
    }


def detect_mod_id(mod_dir: Path) -> str:
    resources = mod_dir / "src" / "main" / "resources"
    fabric_mod = resources / "fabric.mod.json"
    if fabric_mod.exists():
        data = json.loads(fabric_mod.read_text(encoding="utf-8"))
        if data.get("id"):
            return str(data["id"])
    mods_toml = resources / "META-INF" / "neoforge.mods.toml"
    if mods_toml.exists():
        for line in mods_toml.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("modId"):
                _, value = line.split("=", 1)
                return value.strip().strip('"')
    data_root = resources / "data"
    if data_root.exists():
        for child in data_root.iterdir():
            if child.is_dir():
                return child.name
    assets_root = resources / "assets"
    if assets_root.exists():
        for child in assets_root.iterdir():
            if child.is_dir():
                return child.name
    return mod_dir.name.replace("-", "_")


def block_entries(resources: Path, mod_id: str) -> list[dict[str, object]]:
    blockstates_dir = resources / "assets" / mod_id / "blockstates"
    loot_dir = resources / "data" / mod_id / "loot_tables" / "blocks"
    entries: list[dict[str, object]] = []
    for path in sorted(blockstates_dir.glob("*.json")):
        block_id = f"{mod_id}:{path.stem}"
        entries.append(
            {
                "id": block_id,
                "has_block_entity": False,
                "has_container": False,
                "container_slots": 0,
                "block_states": extract_variant_keys(path),
                "drops": infer_drops(loot_dir / f"{path.stem}.json"),
                "loot_table": (loot_dir / f"{path.stem}.json").exists(),
                "model": False,
            }
        )
    return entries


def item_entries(resources: Path, mod_id: str) -> list[dict[str, object]]:
    models_dir = resources / "assets" / mod_id / "models" / "item"
    return [{"id": f"{mod_id}:{path.stem}", "max_stack": 64} for path in sorted(models_dir.glob("*.json"))]


def sound_entries(resources: Path, mod_id: str) -> list[str]:
    sounds_path = resources / "assets" / mod_id / "sounds.json"
    if not sounds_path.exists():
        return []
    data = json.loads(sounds_path.read_text(encoding="utf-8"))
    return [f"{mod_id}:{key}" for key in sorted(data.keys())]


def recipe_entries(resources: Path, mod_id: str) -> list[dict[str, str]]:
    recipe_dir = resources / "data" / mod_id / "recipes"
    entries: list[dict[str, str]] = []
    for path in sorted(recipe_dir.glob("*.json")):
        recipe_type = "unknown"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            recipe_type = str(data.get("type", "unknown")).split(":")[-1]
        except json.JSONDecodeError:
            pass
        entries.append({"id": f"{mod_id}:{path.stem}", "type": recipe_type})
    return entries


def resource_ids(directory: Path, prefix: str) -> list[str]:
    if not directory.exists():
        return []
    return [f"{prefix}{path.stem}" for path in sorted(directory.glob("*.json"))]


def extract_variant_keys(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    variants = data.get("variants", {})
    keys: set[str] = set()
    for variant_key in variants:
        if not variant_key:
            continue
        for chunk in variant_key.split(","):
            key = chunk.split("=", 1)[0].strip()
            if key:
                keys.add(key)
    return sorted(keys)


def infer_drops(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    pools = data.get("pools", [])
    drops: list[str] = []
    for pool in pools:
        for entry in pool.get("entries", []):
            name = entry.get("name")
            if isinstance(name, str):
                drops.append(name)
    return drops


def enrich_blocks(
    blocks: list[dict[str, object]],
    resources: Path,
    mod_id: str,
    items: list[dict[str, object]],
) -> None:
    model_dir = resources / "assets" / mod_id / "models" / "block"
    item_ids = {entry["id"] for entry in items}
    for block in blocks:
        stem = str(block["id"]).split(":")[-1]
        block["model"] = (model_dir / f"{stem}.json").exists()
        if f"{mod_id}:{stem}" not in item_ids:
            block["drops"] = block["drops"] or [block["id"]]
