import json

from irongolem.cli import main


def test_cli_doctor_emits_json(capsys) -> None:
    code = main(["doctor", "--mod-dir", ".", "--accept-eula"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert code in {0, 1}
    assert payload["command"] == "doctor"
    assert "status" in payload
