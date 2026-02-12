"""Tests for nobook.executor."""

import pytest
from pathlib import Path

from nobook.parser import parse_file, parse_string
from nobook.executor import execute_all, execute_up_to, execute_blocks

FIXTURES = Path(__file__).parent / "fixtures"


def test_execute_all():
    parsed = parse_file(FIXTURES / "simple.py")
    results = execute_all(parsed)
    assert len(results) == 3
    assert results[0].name == "setup"
    assert results[0].stdout == ""
    assert results[0].error is None


def test_execute_output():
    parsed = parse_file(FIXTURES / "simple.py")
    results = execute_all(parsed)
    assert results[1].name == "compute"
    assert "result = 30" in results[1].stdout


def test_shared_globals():
    parsed = parse_file(FIXTURES / "simple.py")
    results = execute_all(parsed)
    assert results[1].error is None


def test_execute_up_to():
    parsed = parse_file(FIXTURES / "simple.py")
    results = execute_up_to(parsed, "compute")
    assert len(results) == 2
    assert results[0].name == "setup"
    assert results[1].name == "compute"


def test_execute_up_to_missing():
    parsed = parse_file(FIXTURES / "simple.py")
    with pytest.raises(KeyError, match="not found"):
        execute_up_to(parsed, "nonexistent")


def test_execute_error():
    text = "# @block=bad\n1/0\n"
    parsed = parse_string(text)
    results = execute_all(parsed)
    assert results[0].error is not None
    assert "ZeroDivisionError" in results[0].error


def test_error_stops_execution():
    text = "# @block=bad\n1/0\n# @block=after\nprint('hi')\n"
    parsed = parse_string(text)
    results = execute_all(parsed)
    assert len(results) == 1
    assert results[0].error is not None


def test_execute_specific_blocks():
    parsed = parse_file(FIXTURES / "simple.py")
    results = execute_blocks(parsed, block_names=["setup", "show"])
    assert len(results) == 2
    assert results[0].name == "setup"
    assert results[1].name == "show"
