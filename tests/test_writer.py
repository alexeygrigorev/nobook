"""Tests for nobook.writer."""

from pathlib import Path

from nobook.parser import parse_file, parse_string
from nobook.executor import execute_all
from nobook.writer import format_output

FIXTURES = Path(__file__).parent / "fixtures"


def test_format_output_basic():
    parsed = parse_file(FIXTURES / "simple.py")
    results = execute_all(parsed)
    output = format_output(parsed, results)

    assert "# @block=setup" in output
    assert "# >>> result = 30" in output
    assert "# >>> done" in output


def test_output_with_error():
    text = "# @block=bad\nraise ValueError('oops')\n"
    parsed = parse_string(text)
    results = execute_all(parsed)
    output = format_output(parsed, results)
    assert "# !!! " in output
    assert "ValueError" in output


def test_empty_output_block():
    text = "# @block=quiet\nx = 1\n"
    parsed = parse_string(text)
    results = execute_all(parsed)
    output = format_output(parsed, results)
    assert "# >>>" in output


def test_preamble_preserved():
    text = "# preamble\n# @block=a\nprint('hi')\n"
    parsed = parse_string(text)
    results = execute_all(parsed)
    output = format_output(parsed, results)
    assert output.startswith("# preamble\n")
    assert "# >>> hi" in output
