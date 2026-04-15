"""Tests for nobook.cli."""

import pytest

from nobook import cli


def test_default_command_passes_unknown_args_to_notebook(monkeypatch: pytest.MonkeyPatch):
    seen = {}

    def fake_default(args):
        seen["jupyter_args"] = args.jupyter_args

    monkeypatch.setattr(cli, "cmd_default", fake_default)
    cli.main(["--port=9999", "--no-browser"])
    assert seen["jupyter_args"] == ["--port=9999", "--no-browser"]


def test_run_subcommand_is_not_swallowed_by_default_dispatch(
    monkeypatch: pytest.MonkeyPatch,
):
    seen = {}

    def fake_run(args):
        seen["file"] = args.file
        seen["block"] = args.block

    monkeypatch.setattr(cli, "cmd_run", fake_run)
    cli.main(["run", "demo.py", "--block", "setup"])
    assert seen == {"file": "demo.py", "block": "setup"}


def test_help_exits_cleanly(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert "Plain .py files as notebooks" in out
