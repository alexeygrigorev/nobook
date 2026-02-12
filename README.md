# nobook

Plain `.py` files as notebooks. No `.ipynb` files ever.

Write Python with `# @block=name` markers. Each block becomes a Jupyter cell. The `.py` file **is** the notebook.

## File format

```python
# @block=setup
import math
x = 42

# @block=compute
result = math.sqrt(x)
print(f"sqrt({x}) = {result:.4f}")
```

A block starts at `# @block=name` and runs until the next `# @block=` or end of file. That's it.

## Quick start

### CLI (no Jupyter needed)

```
uv add -e path/to/nobook
uv run nobook run example.py        # executes all blocks, writes example.out.py
uv run nobook run example.py --block=setup   # runs up to and including "setup"
uv run nobook list example.py       # prints block names
```

Output goes to `.out.py` with results inlined as comments:

```python
# @block=setup
import math
x = 42
# >>>

# @block=compute
result = math.sqrt(x)
print(f"sqrt({x}) = {result:.4f}")
# >>> sqrt(42) = 6.4807
```

Errors show as `# !!! ...` lines.

### Jupyter

Install with the jupyter extra:

```
uv add -e "path/to/nobook[jupyter]"
```

Then launch Jupyter with the nobook ContentsManager:

```
uv run nobook jupyter
```

This runs `jupyter notebook` with the right `--ContentsManager` flag. Navigate to any `.py` file containing `# @block=` markers and it opens as a notebook. Run cells, edit, save -- it writes back to the same `.py` file.

#### Manual launch (without the CLI wrapper)

```
uv run jupyter notebook --ContentsManager.default_cm_class=nobook.jupyter.contentsmanager.NobookContentsManager
```

## Minimal reproducible example

```bash
# 1. Start a new project
uv init myproject && cd myproject

# 2. Add nobook with jupyter support
uv add -e "path/to/nobook[jupyter]"

# 3. Create a nobook file
cat > demo.py << 'EOF'
# @block=hello
print("hello from nobook")

# @block=math
import math
print(f"pi = {math.pi:.4f}")
EOF

# 4. Launch
uv run nobook jupyter
```

Jupyter opens. Click `demo.py` in the file browser. It renders as a notebook with two cells (`hello` and `math`). Run them, edit them, save -- the file stays `.py`.

## How it works

```
Jupyter UI (standard, unmodified)
        |
IPython Kernel (standard, unmodified)
        |
NobookContentsManager          <-- intercepts file I/O
        |
.py files with # @block markers
```

The `NobookContentsManager` subclasses Jupyter's `LargeFileManager`. On `get()`, it parses `# @block=` markers and returns a notebook model (blocks as code cells). On `save()`, it converts the notebook model back to `.py` format. The kernel and UI are completely stock.

`.py` files without `# @block=` markers are served normally (as plain text files).
