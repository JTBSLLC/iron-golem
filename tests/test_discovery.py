from pathlib import Path

from irongolem.discovery.scanner import discover_manifest


def test_discover_manifest_scans_resources(tmp_path: Path) -> None:
    resources = tmp_path / "src/main/resources"
    (resources / "assets/mymod/blockstates").mkdir(parents=True)
    (resources / "assets/mymod/models/block").mkdir(parents=True)
    (resources / "assets/mymod/models/item").mkdir(parents=True)
    (resources / "assets/mymod/particles").mkdir(parents=True)
    (resources / "data/mymod/loot_tables/blocks").mkdir(parents=True)
    (resources / "data/mymod/recipes").mkdir(parents=True)
    (resources / "META-INF").mkdir(parents=True)

    (resources / "assets/mymod/blockstates/test_block.json").write_text(
        '{"variants":{"facing=north,powered=true":{"model":"mymod:block/test_block"}}}',
        encoding="utf-8",
    )
    (resources / "assets/mymod/models/block/test_block.json").write_text("{}", encoding="utf-8")
    (resources / "assets/mymod/models/item/test_item.json").write_text("{}", encoding="utf-8")
    (resources / "assets/mymod/particles/sparkle.json").write_text("{}", encoding="utf-8")
    (resources / "assets/mymod/sounds.json").write_text('{"complete": {"sounds": ["complete"]}}', encoding="utf-8")
    (resources / "data/mymod/loot_tables/blocks/test_block.json").write_text(
        '{"pools":[{"entries":[{"name":"mymod:test_block"}]}]}',
        encoding="utf-8",
    )
    (resources / "data/mymod/recipes/test_block.json").write_text(
        '{"type":"minecraft:crafting_shaped"}',
        encoding="utf-8",
    )
    (resources / "META-INF/neoforge.mods.toml").write_text('modId="mymod"\n', encoding="utf-8")
    (tmp_path / "build.gradle").write_text('plugins { id "net.neoforged.moddev" }', encoding="utf-8")
    (tmp_path / "gradle.properties").write_text("minecraft_version=1.21.1\n", encoding="utf-8")

    manifest = discover_manifest(tmp_path)

    assert manifest["mod_id"] == "mymod"
    assert manifest["loader"] == "neoforge"
    assert manifest["minecraft_version"] == "1.21.1"
    assert manifest["blocks"][0]["block_states"] == ["facing", "powered"]
    assert manifest["sounds"] == ["mymod:complete"]
    assert manifest["particles"] == ["mymod:sparkle"]
