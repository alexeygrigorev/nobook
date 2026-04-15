"""Execute blocks from a parsed pybooks file."""

import ast
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

    preamble_error = _execute_snippet(
        "\n".join(parsed.preamble),
        "<preamble>",
        shared_globals,
    )
    if preamble_error is not None:
        return [
            BlockResult(
                name="<preamble>",
                stdout="",
                error=preamble_error,
            )
        ]

    for block in targets:
        code = "\n".join(block.lines)
        stdout_buf = io.StringIO()
        error = None

        try:
            with contextlib.redirect_stdout(stdout_buf):
                exec_cell_like(code, f"<block:{block.name}>", shared_globals)
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


def _execute_snippet(code: str, filename: str, shared_globals: dict) -> str | None:
    """Execute plain setup code and return traceback text on error."""
    if not code.strip():
        return None

    try:
        exec(compile(code, filename, "exec"), shared_globals)
    except Exception:
        return traceback.format_exc()

    return None


def exec_cell_like(code: str, filename: str, shared_globals: dict) -> None:
    """Execute code using notebook semantics for the final bare expression."""
    tree = ast.parse(code, filename=filename, mode="exec")
    if not tree.body:
        return

    last_stmt = tree.body[-1]
    if not isinstance(last_stmt, ast.Expr):
        exec(compile(tree, filename, "exec"), shared_globals)
        return

    body = ast.Module(body=tree.body[:-1], type_ignores=[])
    if body.body:
        ast.fix_missing_locations(body)
        exec(compile(body, filename, "exec"), shared_globals)

    expr = ast.Expression(last_stmt.value)
    ast.fix_missing_locations(expr)
    result = eval(compile(expr, filename, "eval"), shared_globals)
    if result is not None:
        print(repr(result))
