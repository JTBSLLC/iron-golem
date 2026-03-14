from pathlib import Path

from irongolem.gradle.parser import parse_gradle_errors


def test_parse_gradle_errors_extracts_context(tmp_path: Path) -> None:
    source = tmp_path / "src/main/java/com/example/Example.java"
    source.parent.mkdir(parents=True)
    source.write_text(
        "\n".join(
            [
                "package com.example;",
                "public class Example {",
                "    void run() {",
                "        var enchants = stack.getEnchantments();",
                "    }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    output = "\n".join(
        [
            "src/main/java/com/example/Example.java:4: error: cannot find symbol: method getEnchantments()",
            "        var enchants = stack.getEnchantments();",
            "                           ^",
        ]
    )

    errors = parse_gradle_errors(output, tmp_path)

    assert len(errors) == 1
    assert errors[0]["file"] == "src/main/java/com/example/Example.java"
    assert errors[0]["line"] == 4
    assert "getAllEnchantments()" in str(errors[0]["suggestion"])
    assert "void run()" in str(errors[0]["context"])
