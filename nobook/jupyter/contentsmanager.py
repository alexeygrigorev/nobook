"""Custom ContentsManager that presents .py files with @block markers as notebooks."""

from __future__ import annotations

import nbformat
from jupyter_server.services.contents.largefilemanager import LargeFileManager

from ..formats import BLOCK_START_RE
from ..parser import parse_string


def _has_block_markers(text: str) -> bool:
    """Check if text contains at least one @block marker."""
    for line in text.splitlines():
        if BLOCK_START_RE.match(line):
            return True
    return False


def _py_to_notebook(text: str) -> nbformat.NotebookNode:
    """Convert nobook-formatted .py text to a notebook node."""
    parsed = parse_string(text)
    nb = nbformat.v4.new_notebook()
    nb.metadata["nobook"] = True

    # Preamble as a raw cell (if non-empty)
    preamble_text = "\n".join(parsed.preamble)
    if preamble_text.strip():
        cell = nbformat.v4.new_raw_cell(source=preamble_text)
        cell.metadata["nobook"] = {"preamble": True}
        nb.cells.append(cell)

    # Each block becomes a code cell
    for block in parsed.blocks:
        cell = nbformat.v4.new_code_cell(source="\n".join(block.lines))
        cell.metadata["nobook"] = {"block": block.name}
        nb.cells.append(cell)

    return nb


def _notebook_to_py(nb: nbformat.NotebookNode) -> str:
    """Convert a notebook node back to nobook-formatted .py text."""
    lines: list[str] = []

    for cell in nb.cells:
        nobook_meta = cell.metadata.get("nobook", {})

        if cell.cell_type == "raw" and nobook_meta.get("preamble"):
            lines.extend(cell.source.splitlines())
        elif cell.cell_type == "code" and "block" in nobook_meta:
            block_name = nobook_meta["block"]
            lines.append(f"# @block={block_name}")
            lines.extend(cell.source.splitlines())
        elif cell.cell_type == "code":
            # New code cell without block name — assign one
            block_name = f"cell-{len(lines)}"
            lines.append(f"# @block={block_name}")
            lines.extend(cell.source.splitlines())

    return "\n".join(lines) + "\n"


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

        nb = _py_to_notebook(text)
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
        # Return a notebook-typed model
        return self.get(path, content=False)
