"""Tests for nobook.parser."""

import pytest
from pathlib import Path

from nobook.parser import parse_string, parse_file, ParseError

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_simple():
    parsed = parse_file(FIXTURES / "simple.py")
    assert len(parsed.blocks) == 3
    assert [b.name for b in parsed.blocks] == ["setup", "compute", "show"]


def test_block_contents():
    parsed = parse_file(FIXTURES / "simple.py")
    setup = parsed.block_map["setup"]
    assert setup.lines == ["x = 10", "y = 20", ""]


def test_block_start_line():
    parsed = parse_file(FIXTURES / "simple.py")
    assert parsed.block_map["setup"].start_line == 0
    assert parsed.block_map["compute"].start_line == 4


def test_preamble():
    text = "# preamble comment\nimport os\n# @block=a\ncode\n"
    parsed = parse_string(text)
    assert parsed.preamble == ["# preamble comment", "import os"]
    assert len(parsed.blocks) == 1


def test_no_preamble():
    text = "# @block=a\ncode\n"
    parsed = parse_string(text)
    assert parsed.preamble == []


def test_duplicate_name():
    text = "# @block=a\nx=1\n# @block=a\nx=2\n"
    with pytest.raises(ParseError, match="duplicate block name 'a'"):
        parse_string(text)


def test_empty_file():
    parsed = parse_string("")
    assert parsed.blocks == []
    assert parsed.preamble == []


def test_no_blocks():
    parsed = parse_string("x = 1\ny = 2\n")
    assert parsed.blocks == []
    assert parsed.preamble == ["x = 1", "y = 2"]


def test_single_block_to_eof():
    text = "# @block=only\nline1\nline2"
    parsed = parse_string(text)
    assert len(parsed.blocks) == 1
    assert parsed.blocks[0].lines == ["line1", "line2"]


def test_block_ends_at_next_block():
    text = "# @block=a\nfirst\n# @block=b\nsecond\n"
    parsed = parse_string(text)
    assert parsed.blocks[0].lines == ["first"]
    assert parsed.blocks[1].lines == ["second"]
