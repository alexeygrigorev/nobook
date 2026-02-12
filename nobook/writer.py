"""Write execution results back to .out.py files."""

from __future__ import annotations

from pathlib import Path

from .executor import BlockResult
from .formats import OUTPUT_PREFIX, ERROR_PREFIX
from .parser import ParsedFile


def format_output(parsed: ParsedFile, results: list[BlockResult]) -> str:
    """Produce the .out.py content: original source with output after each block."""
    result_map = {r.name: r for r in results}
    output_lines: list[str] = []

    # Preamble
    output_lines.extend(parsed.preamble)

    for i, block in enumerate(parsed.blocks):
        # Block header
        output_lines.append(f"# @block={block.name}")
        # Block body
        output_lines.extend(block.lines)

        # Append output if we have results for this block
        if block.name in result_map:
            result = result_map[block.name]
            _append_result_lines(output_lines, result)

    return "\n".join(output_lines) + "\n"


def _append_result_lines(output_lines: list[str], result: BlockResult) -> None:
    """Append stdout/error lines after a block."""
    if result.stdout:
        for out_line in result.stdout.rstrip("\n").splitlines():
            output_lines.append(f"{OUTPUT_PREFIX}{out_line}")
    elif result.error is None:
        output_lines.append(OUTPUT_PREFIX.rstrip())

    if result.error:
        for err_line in result.error.rstrip("\n").splitlines():
            output_lines.append(f"{ERROR_PREFIX}{err_line}")


def write_output(
    parsed: ParsedFile,
    results: list[BlockResult],
    output_path: str | Path,
) -> None:
    """Write the .out.py file."""
    content = format_output(parsed, results)
    Path(output_path).write_text(content, encoding="utf-8")
