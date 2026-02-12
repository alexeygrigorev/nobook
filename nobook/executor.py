"""Execute blocks from a parsed pybooks file."""

from __future__ import annotations

import contextlib
import io
import traceback
from dataclasses import dataclass

from .parser import ParsedFile


@dataclass
class BlockResult:
    name: str
    stdout: str
    error: str | None


def execute_blocks(
    parsed: ParsedFile,
    block_names: list[str] | None = None,
) -> list[BlockResult]:
    """Execute blocks, sharing a single globals dict.

    If block_names is None, executes all blocks in order.
    If block_names is provided, executes only those blocks (in file order).
    """
    shared_globals: dict = {"__name__": "__pybooks__"}
    results: list[BlockResult] = []

    if block_names is not None:
        # Validate all names exist
        for name in block_names:
            if name not in parsed.block_map:
                raise KeyError(f"Block '{name}' not found")
        targets = [b for b in parsed.blocks if b.name in block_names]
    else:
        targets = parsed.blocks

    for block in targets:
        code = "\n".join(block.lines)
        stdout_buf = io.StringIO()
        error = None

        try:
            with contextlib.redirect_stdout(stdout_buf):
                exec(compile(code, f"<block:{block.name}>", "exec"), shared_globals)
        except Exception:
            error = traceback.format_exc()

        results.append(BlockResult(
            name=block.name,
            stdout=stdout_buf.getvalue(),
            error=error,
        ))

        # Stop on error
        if error is not None:
            break

    return results


def execute_all(parsed: ParsedFile) -> list[BlockResult]:
    """Execute all blocks in order."""
    return execute_blocks(parsed)


def execute_up_to(parsed: ParsedFile, name: str) -> list[BlockResult]:
    """Execute all blocks up to and including the named block."""
    if name not in parsed.block_map:
        raise KeyError(f"Block '{name}' not found")
    names = []
    for block in parsed.blocks:
        names.append(block.name)
        if block.name == name:
            break
    return execute_blocks(parsed, block_names=names)
