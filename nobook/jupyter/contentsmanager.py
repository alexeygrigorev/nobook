"""Custom ContentsManager that presents .py files with @block markers as notebooks."""

from __future__ import annotations

import nbformat
from jupyter_server.services.contents.largefilemanager import LargeFileManager

from ..formats import BLOCK_START_RE, OUTPUT_PREFIX, ERROR_PREFIX


def _has_block_markers(text: str) -> bool:
    """Check if text contains at least one @block marker."""
    for line in text.splitlines():
        if BLOCK_START_RE.match(line):
            return True
    return False


def _py_to_notebook(text: str) -> nbformat.NotebookNode:
    """Convert nobook-formatted .py text to a notebook node.

    Handles duplicate block names gracefully by appending suffixes.
    """
    nb = nbformat.v4.new_notebook()
    nb.metadata["nobook"] = True

    used_names: set[str] = set()
    preamble_lines: list[str] = []
    current_block: str | None = None
    current_lines: list[str] = []

    def flush_block() -> None:
        nonlocal current_block, current_lines
        if current_block is not None:
            name = _unique_block_name(current_block, used_names)
            used_names.add(name)
            cell = nbformat.v4.new_code_cell(source="\n".join(current_lines))
            cell.id = name
            cell.metadata["nobook"] = {"block": name}
            nb.cells.append(cell)
            current_block = None
            current_lines = []

    for line in text.splitlines():
        m = BLOCK_START_RE.match(line)
        if m:
            flush_block()
            current_block = m.group(1)
        elif current_block is not None:
            current_lines.append(line)
        else:
            preamble_lines.append(line)

    flush_block()

    # Insert preamble as a raw cell at the start
    preamble_text = "\n".join(preamble_lines)
    if preamble_text.strip():
        cell = nbformat.v4.new_raw_cell(source=preamble_text)
        cell.metadata["nobook"] = {"preamble": True}
        nb.cells.insert(0, cell)

    return nb


def _unique_block_name(base: str, used: set[str]) -> str:
    """Return a block name based on `base` that isn't in `used`."""
    if base not in used:
        return base
    i = 1
    while f"{base}-{i}" in used:
        i += 1
    return f"{base}-{i}"


def _notebook_to_py(nb: nbformat.NotebookNode) -> str:
    """Convert a notebook node back to nobook-formatted .py text."""
    lines: list[str] = []
    used_names: set[str] = set()
    cell_counter = 0

    for cell in nb.cells:
        nobook_meta = cell.metadata.get("nobook", {})

        if cell.cell_type == "raw" and nobook_meta.get("preamble"):
            lines.extend(cell.source.splitlines())
        elif cell.cell_type == "code":
            base = nobook_meta.get("block", f"cell-{cell_counter}")
            block_name = _unique_block_name(base, used_names)
            used_names.add(block_name)
            lines.append(f"# @block={block_name}")
            lines.extend(cell.source.splitlines())
        cell_counter += 1

    return "\n".join(lines) + "\n"


def _cell_outputs_to_lines(outputs: list) -> list[str]:
    """Extract stdout and error lines from notebook cell outputs."""
    lines: list[str] = []
    for output in outputs:
        output_type = output.get("output_type", "")
        if output_type == "stream":
            prefix = ERROR_PREFIX if output.get("name") == "stderr" else OUTPUT_PREFIX
            text = output.get("text", "")
            for line in text.rstrip("\n").splitlines():
                lines.append(f"{prefix}{line}")
        elif output_type == "execute_result":
            data = output.get("data", {})
            text = data.get("text/plain", "")
            if text:
                for line in text.rstrip("\n").splitlines():
                    lines.append(f"{OUTPUT_PREFIX}{line}")
        elif output_type == "error":
            tb = output.get("traceback", [])
            # Traceback entries may contain ANSI escape codes; strip them
            import re
            ansi_re = re.compile(r"\x1b\[[0-9;]*m")
            for entry in tb:
                clean = ansi_re.sub("", entry)
                for line in clean.splitlines():
                    lines.append(f"{ERROR_PREFIX}{line}")
    return lines


def _notebook_to_out_py(nb: nbformat.NotebookNode) -> str:
    """Convert a notebook with outputs to .out.py format."""
    lines: list[str] = []
    used_names: set[str] = set()
    cell_counter = 0
    has_any_output = False

    for cell in nb.cells:
        nobook_meta = cell.metadata.get("nobook", {})

        if cell.cell_type == "raw" and nobook_meta.get("preamble"):
            lines.extend(cell.source.splitlines())
        elif cell.cell_type == "code":
            base = nobook_meta.get("block", f"cell-{cell_counter}")
            block_name = _unique_block_name(base, used_names)
            used_names.add(block_name)
            lines.append(f"# @block={block_name}")
            lines.extend(cell.source.splitlines())

            # Append cell outputs
            cell_outputs = getattr(cell, "outputs", []) or []
            output_lines = _cell_outputs_to_lines(cell_outputs)
            if output_lines:
                has_any_output = True
                lines.extend(output_lines)
            elif cell_outputs == [] or cell_outputs is None:
                # Cell has been executed with no output — add empty marker
                pass
        cell_counter += 1

    if not has_any_output:
        return ""

    return "\n".join(lines) + "\n"


def _parse_out_py(text: str) -> dict[str, list[dict]]:
    """Parse .out.py text and return a map of block name -> notebook outputs.

    Each block's output lines (# >>> ... and # !!! ...) are converted to
    notebook-format output objects (stream/error).
    """
    block_outputs: dict[str, list[dict]] = {}
    current_block: str | None = None
    stdout_lines: list[str] = []
    error_lines: list[str] = []

    def flush_outputs() -> None:
        nonlocal current_block, stdout_lines, error_lines
        if current_block is None:
            return
        outputs: list[dict] = []
        if stdout_lines:
            outputs.append({
                "output_type": "stream",
                "name": "stdout",
                "text": "\n".join(stdout_lines) + "\n",
            })
        if error_lines:
            outputs.append({
                "output_type": "stream",
                "name": "stderr",
                "text": "\n".join(error_lines) + "\n",
            })
        if outputs:
            block_outputs[current_block] = outputs
        current_block = None
        stdout_lines = []
        error_lines = []

    for line in text.splitlines():
        m = BLOCK_START_RE.match(line)
        if m:
            flush_outputs()
            current_block = m.group(1)
        elif line.startswith(OUTPUT_PREFIX):
            stdout_lines.append(line[len(OUTPUT_PREFIX):])
        elif line.startswith(ERROR_PREFIX):
            error_lines.append(line[len(ERROR_PREFIX):])
        # Source lines are ignored — we only care about outputs

    flush_outputs()
    return block_outputs


def _attach_outputs(nb: nbformat.NotebookNode, block_outputs: dict[str, list[dict]]) -> None:
    """Attach parsed outputs to matching notebook cells."""
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        block_name = cell.metadata.get("nobook", {}).get("block")
        if block_name and block_name in block_outputs:
            cell.outputs = block_outputs[block_name]


class NobookContentsManager(LargeFileManager):
    """ContentsManager that opens .py files with @block markers as notebooks."""

    def new_untitled(self, path="", type="", ext=""):
        if type == "notebook" or ext == ".ipynb":
            # Create a .py file with a block marker instead of .ipynb
            name = self.increment_filename(self.untitled_notebook + ".py", path)
            full_path = f"{path.strip('/')}/{name}"
            # Write the file to disk as plain text
            file_model = {
                "type": "file",
                "format": "text",
                "content": "# @block=main\n",
            }
            super().save(file_model, full_path)
            # Return a notebook model so the frontend opens the notebook editor
            return self.get(full_path, content=False)
        return super().new_untitled(path=path, type=type, ext=ext)

    def get(self, path, content=True, type=None, format=None, **kwargs):
        if path.endswith(".py") and type in (None, "notebook"):
            return self._get_nobook(path, content, type, format, **kwargs)
        return super().get(path, content=content, type=type, format=format, **kwargs)

    def _get_nobook(self, path, content, type, format, **kwargs):
        model = super().get(path, content=True, type="file", format="text", **kwargs)

        text = model.get("content", "")
        if not isinstance(text, str) or not _has_block_markers(text):
            if type == "notebook":
                return super().get(path, content=content, type=type, format=format, **kwargs)
            return super().get(path, content=content, type="file", format=format, **kwargs)

        try:
            nb = _py_to_notebook(text)
        except Exception:
            # Fall back to plain file if parsing fails
            return super().get(path, content=content, type="file", format=format, **kwargs)

        # Try to load outputs from .out.py
        if content:
            try:
                out_path = path.removesuffix(".py") + ".out.py"
                out_model = super().get(out_path, content=True, type="file", format="text")
                out_text = out_model.get("content", "")
                if isinstance(out_text, str):
                    block_outputs = _parse_out_py(out_text)
                    _attach_outputs(nb, block_outputs)
            except Exception:
                pass  # No .out.py or failed to parse — that's fine

        model["type"] = "notebook"
        if content:
            model["format"] = "json"
            model["content"] = nb
        else:
            model["format"] = None
            model["content"] = None
        return model

    def save(self, model, path=""):
        if path.endswith(".py") and model.get("type") == "notebook":
            return self._save_nobook(model, path)
        return super().save(model, path)

    def _save_nobook(self, model, path):
        nb = model["content"]
        if isinstance(nb, dict):
            nb = nbformat.from_dict(nb)

        py_content = _notebook_to_py(nb)

        file_model = {
            "type": "file",
            "format": "text",
            "content": py_content,
        }
        super().save(file_model, path)

        # Also write .out.py with cell outputs (if any cells have been executed)
        out_content = _notebook_to_out_py(nb)
        if out_content:
            out_path = path.removesuffix(".py") + ".out.py"
            out_model = {
                "type": "file",
                "format": "text",
                "content": out_content,
            }
            super().save(out_model, out_path)

        # Return a notebook-typed model
        return self.get(path, content=False)
