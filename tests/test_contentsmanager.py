"""Tests for nobook.jupyter.contentsmanager conversion functions."""

import nbformat
import pytest

from nobook.jupyter.contentsmanager import (
    _attach_outputs,
    _cell_outputs_to_lines,
    _has_block_markers,
    _notebook_to_out_py,
    _notebook_to_py,
    _parse_out_py,
    _py_to_notebook,
    _unique_block_name,
)


# --- _has_block_markers ---

def test_has_markers_true():
    assert _has_block_markers("# @block=main\nprint(1)\n")

def test_has_markers_false():
    assert not _has_block_markers("print(1)\nx = 2\n")

def test_has_markers_empty():
    assert not _has_block_markers("")


# --- _unique_block_name ---

def test_unique_name_no_conflict():
    assert _unique_block_name("main", set()) == "main"

def test_unique_name_with_conflict():
    assert _unique_block_name("main", {"main"}) == "main-1"

def test_unique_name_multiple_conflicts():
    assert _unique_block_name("a", {"a", "a-1", "a-2"}) == "a-3"


# --- _py_to_notebook (round-trip: text -> notebook) ---

def test_py_to_notebook_simple():
    text = "# @block=main\nprint(1)\n"
    nb = _py_to_notebook(text)
    assert len(nb.cells) == 1
    assert nb.cells[0].cell_type == "code"
    assert nb.cells[0].source == "print(1)"
    assert nb.cells[0].metadata["nobook"]["block"] == "main"

def test_py_to_notebook_multiple_blocks():
    text = "# @block=a\nx = 1\n# @block=b\ny = 2\n"
    nb = _py_to_notebook(text)
    assert len(nb.cells) == 2
    assert nb.cells[0].metadata["nobook"]["block"] == "a"
    assert nb.cells[1].metadata["nobook"]["block"] == "b"

def test_py_to_notebook_with_preamble():
    text = "import os\n# @block=main\nprint(1)\n"
    nb = _py_to_notebook(text)
    assert len(nb.cells) == 2
    assert nb.cells[0].cell_type == "raw"
    assert nb.cells[0].metadata["nobook"]["preamble"] is True
    assert nb.cells[1].cell_type == "code"

def test_py_to_notebook_duplicate_names():
    """Duplicate block names should be auto-renamed, not crash."""
    text = "# @block=a\nx = 1\n# @block=a\ny = 2\n"
    nb = _py_to_notebook(text)
    assert len(nb.cells) == 2
    names = [c.metadata["nobook"]["block"] for c in nb.cells]
    assert names[0] == "a"
    assert names[1] == "a-1"

def test_py_to_notebook_empty_block():
    text = "# @block=main\n# @block=next\ncode\n"
    nb = _py_to_notebook(text)
    assert len(nb.cells) == 2
    assert nb.cells[0].source == ""
    assert nb.cells[1].source == "code"

def test_py_to_notebook_cell_id_equals_block_name():
    text = "# @block=setup\nx = 1\n"
    nb = _py_to_notebook(text)
    assert nb.cells[0].id == "setup"

def test_py_to_notebook_empty_text():
    nb = _py_to_notebook("")
    assert len(nb.cells) == 0


# --- _notebook_to_py (round-trip: notebook -> text) ---

def test_notebook_to_py_simple():
    nb = nbformat.v4.new_notebook()
    cell = nbformat.v4.new_code_cell(source="print(1)")
    cell.metadata["nobook"] = {"block": "main"}
    nb.cells.append(cell)

    text = _notebook_to_py(nb)
    assert text == "# @block=main\nprint(1)\n"

def test_notebook_to_py_multiple():
    nb = nbformat.v4.new_notebook()
    for name, src in [("a", "x = 1"), ("b", "y = 2")]:
        cell = nbformat.v4.new_code_cell(source=src)
        cell.metadata["nobook"] = {"block": name}
        nb.cells.append(cell)

    text = _notebook_to_py(nb)
    assert text == "# @block=a\nx = 1\n# @block=b\ny = 2\n"

def test_notebook_to_py_with_preamble():
    nb = nbformat.v4.new_notebook()
    raw = nbformat.v4.new_raw_cell(source="import os")
    raw.metadata["nobook"] = {"preamble": True}
    nb.cells.append(raw)
    code = nbformat.v4.new_code_cell(source="print(1)")
    code.metadata["nobook"] = {"block": "main"}
    nb.cells.append(code)

    text = _notebook_to_py(nb)
    assert text == "import os\n# @block=main\nprint(1)\n"

def test_notebook_to_py_duplicate_names():
    """Duplicate block names in metadata should be deduplicated on save."""
    nb = nbformat.v4.new_notebook()
    for src in ["x = 1", "y = 2"]:
        cell = nbformat.v4.new_code_cell(source=src)
        cell.metadata["nobook"] = {"block": "dupe"}
        nb.cells.append(cell)

    text = _notebook_to_py(nb)
    assert "# @block=dupe\n" in text
    assert "# @block=dupe-1\n" in text

def test_notebook_to_py_new_cell_no_metadata():
    """New cells without nobook metadata get auto-assigned names."""
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_code_cell(source="x = 1"))
    nb.cells.append(nbformat.v4.new_code_cell(source="y = 2"))

    text = _notebook_to_py(nb)
    assert "# @block=cell-0\n" in text
    assert "# @block=cell-1\n" in text


# --- Round-trip: text -> notebook -> text ---

def test_roundtrip_simple():
    original = "# @block=main\nprint(1)\n"
    nb = _py_to_notebook(original)
    result = _notebook_to_py(nb)
    assert result == original

def test_roundtrip_multiple_blocks():
    original = "# @block=setup\nx = 1\n# @block=run\nprint(x)\n# @block=done\npass\n"
    nb = _py_to_notebook(original)
    result = _notebook_to_py(nb)
    assert result == original

def test_roundtrip_with_preamble():
    original = "import os\n# @block=main\nprint(1)\n"
    nb = _py_to_notebook(original)
    result = _notebook_to_py(nb)
    assert result == original

def test_roundtrip_empty_blocks():
    original = "# @block=a\n# @block=b\ncode\n"
    nb = _py_to_notebook(original)
    result = _notebook_to_py(nb)
    assert result == original

def test_roundtrip_duplicate_names_fixed():
    """Duplicates in source get renamed, and the renamed version round-trips."""
    text = "# @block=x\na\n# @block=x\nb\n"
    nb = _py_to_notebook(text)
    result = _notebook_to_py(nb)
    # Second 'x' became 'x-1'
    assert result == "# @block=x\na\n# @block=x-1\nb\n"
    # And that round-trips cleanly
    nb2 = _py_to_notebook(result)
    assert _notebook_to_py(nb2) == result


# --- _cell_outputs_to_lines ---

def test_cell_outputs_stream_stdout():
    outputs = [{"output_type": "stream", "name": "stdout", "text": "hello\nworld\n"}]
    lines = _cell_outputs_to_lines(outputs)
    assert lines == ["# >>> hello", "# >>> world"]

def test_cell_outputs_stream_stderr():
    outputs = [{"output_type": "stream", "name": "stderr", "text": "warning\n"}]
    lines = _cell_outputs_to_lines(outputs)
    assert lines == ["# !!! warning"]

def test_cell_outputs_execute_result():
    outputs = [{"output_type": "execute_result", "data": {"text/plain": "42"}}]
    lines = _cell_outputs_to_lines(outputs)
    assert lines == ["# >>> 42"]

def test_cell_outputs_error():
    outputs = [{"output_type": "error", "ename": "ValueError", "evalue": "bad",
                "traceback": ["Traceback:", "ValueError: bad"]}]
    lines = _cell_outputs_to_lines(outputs)
    assert lines == ["# !!! Traceback:", "# !!! ValueError: bad"]

def test_cell_outputs_empty():
    assert _cell_outputs_to_lines([]) == []


# --- _notebook_to_out_py ---

def test_out_py_with_outputs():
    nb = nbformat.v4.new_notebook()
    cell = nbformat.v4.new_code_cell(source="print(1)")
    cell.metadata["nobook"] = {"block": "main"}
    cell.outputs = [{"output_type": "stream", "name": "stdout", "text": "1\n"}]
    nb.cells.append(cell)

    result = _notebook_to_out_py(nb)
    assert result == "# @block=main\nprint(1)\n# >>> 1\n"

def test_out_py_no_outputs_returns_empty():
    """If no cells have been executed, return empty string (skip .out.py)."""
    nb = nbformat.v4.new_notebook()
    cell = nbformat.v4.new_code_cell(source="x = 1")
    cell.metadata["nobook"] = {"block": "main"}
    cell.outputs = []
    nb.cells.append(cell)

    assert _notebook_to_out_py(nb) == ""

def test_out_py_mixed_outputs():
    nb = nbformat.v4.new_notebook()
    c1 = nbformat.v4.new_code_cell(source="x = 1")
    c1.metadata["nobook"] = {"block": "setup"}
    c1.outputs = []
    nb.cells.append(c1)

    c2 = nbformat.v4.new_code_cell(source="print(x)")
    c2.metadata["nobook"] = {"block": "run"}
    c2.outputs = [{"output_type": "stream", "name": "stdout", "text": "1\n"}]
    nb.cells.append(c2)

    result = _notebook_to_out_py(nb)
    assert "# @block=setup\nx = 1\n" in result
    assert "# @block=run\nprint(x)\n# >>> 1\n" in result


# --- _parse_out_py ---

def test_parse_out_py_stdout():
    text = "# @block=main\nprint(1)\n# >>> 1\n"
    outputs = _parse_out_py(text)
    assert "main" in outputs
    assert len(outputs["main"]) == 1
    assert outputs["main"][0]["output_type"] == "stream"
    assert outputs["main"][0]["name"] == "stdout"
    assert outputs["main"][0]["text"] == "1\n"

def test_parse_out_py_stderr():
    text = "# @block=main\nprint(1)\n# !!! warning\n"
    outputs = _parse_out_py(text)
    assert outputs["main"][0]["name"] == "stderr"
    assert outputs["main"][0]["text"] == "warning\n"

def test_parse_out_py_mixed():
    text = "# @block=main\nprint(1)\n# >>> 1\n# !!! oops\n"
    outputs = _parse_out_py(text)
    assert len(outputs["main"]) == 2
    assert outputs["main"][0]["name"] == "stdout"
    assert outputs["main"][1]["name"] == "stderr"

def test_parse_out_py_multiple_blocks():
    text = "# @block=a\nx = 1\n# @block=b\nprint(x)\n# >>> 1\n"
    outputs = _parse_out_py(text)
    assert "a" not in outputs  # no output for block a
    assert "b" in outputs
    assert outputs["b"][0]["text"] == "1\n"

def test_parse_out_py_no_outputs():
    text = "# @block=main\nx = 1\n"
    outputs = _parse_out_py(text)
    assert outputs == {}

def test_parse_out_py_multiline_stdout():
    text = "# @block=main\nprint('a\\nb')\n# >>> a\n# >>> b\n"
    outputs = _parse_out_py(text)
    assert outputs["main"][0]["text"] == "a\nb\n"


# --- _attach_outputs ---

def test_attach_outputs():
    nb = _py_to_notebook("# @block=main\nprint(1)\n")
    block_outputs = {
        "main": [{"output_type": "stream", "name": "stdout", "text": "1\n"}]
    }
    _attach_outputs(nb, block_outputs)
    assert len(nb.cells[0].outputs) == 1
    assert nb.cells[0].outputs[0]["text"] == "1\n"

def test_attach_outputs_missing_block():
    """Outputs for non-existent blocks are silently ignored."""
    nb = _py_to_notebook("# @block=main\nprint(1)\n")
    block_outputs = {
        "other": [{"output_type": "stream", "name": "stdout", "text": "1\n"}]
    }
    _attach_outputs(nb, block_outputs)
    assert nb.cells[0].outputs == []


# --- Round-trip: notebook with outputs -> .out.py -> parse -> attach ---

def test_out_py_roundtrip():
    """Outputs survive a save/load cycle through .out.py."""
    nb = nbformat.v4.new_notebook()
    cell = nbformat.v4.new_code_cell(source="print('hello')")
    cell.metadata["nobook"] = {"block": "main"}
    cell.outputs = [{"output_type": "stream", "name": "stdout", "text": "hello\n"}]
    nb.cells.append(cell)

    # Save to .out.py format
    out_text = _notebook_to_out_py(nb)
    assert out_text

    # Load back
    block_outputs = _parse_out_py(out_text)
    nb2 = _py_to_notebook("# @block=main\nprint('hello')\n")
    _attach_outputs(nb2, block_outputs)

    assert len(nb2.cells[0].outputs) == 1
    assert nb2.cells[0].outputs[0]["text"] == "hello\n"
