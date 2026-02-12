"""Parse .py files with @block markers into structured blocks.

Format: A block starts at `# @block=name` and continues until
the next `# @block=...` line or end of file. No `# @end` needed.
Lines before the first block are the preamble (preserved but not executed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .formats import BLOCK_START_RE


@dataclass
class Block:
    name: str
    lines: list[str]
    start_line: int  # 0-indexed line of # @block=...


@dataclass
class ParsedFile:
    preamble: list[str]  # lines before the first block
    blocks: list[Block]
    raw_lines: list[str]
    block_map: dict[str, Block] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.block_map = {b.name: b for b in self.blocks}


class ParseError(Exception):
    pass


def parse_string(text: str) -> ParsedFile:
    """Parse a string containing pybooks-formatted Python code."""
    raw_lines = text.splitlines()
    blocks: list[Block] = []
    seen_names: set[str] = set()
    preamble: list[str] = []

    current_name: str | None = None
    current_lines: list[str] = []
    current_start: int = -1

    for i, line in enumerate(raw_lines):
        start_match = BLOCK_START_RE.match(line)

        if start_match:
            # Close previous block if any
            if current_name is not None:
                blocks.append(Block(
                    name=current_name,
                    lines=current_lines,
                    start_line=current_start,
                ))

            name = start_match.group(1)
            if name in seen_names:
                raise ParseError(
                    f"Line {i + 1}: duplicate block name '{name}'"
                )
            seen_names.add(name)
            current_name = name
            current_lines = []
            current_start = i

        elif current_name is not None:
            current_lines.append(line)
        else:
            preamble.append(line)

    # Close final block
    if current_name is not None:
        blocks.append(Block(
            name=current_name,
            lines=current_lines,
            start_line=current_start,
        ))

    return ParsedFile(preamble=preamble, blocks=blocks, raw_lines=raw_lines)


def parse_file(path: str | Path) -> ParsedFile:
    """Parse a .py file with @block markers."""
    text = Path(path).read_text(encoding="utf-8")
    return parse_string(text)
