from pathlib import Path

from irongolem.server.log_parser import load_assertion_logs, parse_crash_report, parse_gametest_log


def test_parse_gametest_log_summarizes_results() -> None:
    text = "\n".join(
        [
            "[Server thread/INFO]: Running test: mymod:test_block",
            "[Server thread/INFO]: Test mymod:test_block passed",
            "[Server thread/INFO]: Running test: mymod:test_fail",
            "[Server thread/ERROR]: Test mymod:test_fail failed: Expected block but found air",
            "[Server thread/INFO]: GameTest completed. 1 passed, 1 failed.",
        ]
    )

    parsed = parse_gametest_log(text)

    assert parsed["total"] == 2
    assert parsed["passed"] == 1
    assert parsed["failed"] == 1


def test_load_assertion_logs_reads_jsonl(tmp_path: Path) -> None:
    results = tmp_path / "irongolem-results"
    results.mkdir()
    (results / "test_block.json").write_text(
        '{"test":"test_block","assertion":"assertInventory","pass":true}\n',
        encoding="utf-8",
    )

    data = load_assertion_logs(results)

    assert data["test_block"][0]["assertion"] == "assertInventory"


def test_parse_crash_report_extracts_exception(tmp_path: Path) -> None:
    crash = tmp_path / "crash-2026-03-14.txt"
    crash.write_text(
        "\n".join(
            [
                "---- Minecraft Crash Report ----",
                "Description: Exception in server tick loop",
                "java.lang.NullPointerException: boom",
                "at com.example.Block.onPlace(Block.java:67)",
                "at net.minecraft.world.level.Level.tick(Level.java:99)",
            ]
        ),
        encoding="utf-8",
    )

    parsed = parse_crash_report(crash)

    assert parsed is not None
    assert parsed["description"] == "Exception in server tick loop"
    assert parsed["line"] == 67
