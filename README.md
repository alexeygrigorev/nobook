# nobook

Plain `.py` files as notebooks. No `.ipynb` files ever.

Write Python with `# @block=name` markers. Each block becomes a Jupyter cell. The `.py` file is the notebook.

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

### JupyterLab / Jupyter Notebook

```bash
# 1. Create a .py file with block markers
cat > demo.py << 'EOF'
# @block=hello
print("hello from nobook")

# @block=math
import math
print(f"pi = {math.pi:.4f}")
EOF

# 2. Launch Jupyter (no install needed)
uvx nobook
```

Jupyter opens. Right-click `demo.py` in the file browser and select Open as Nobook. It renders as a notebook with two cells (`hello` and `math`). Run them, edit them, save -- the file stays `.py`.

### VS Code

Install the [Nobook VS Code extension](https://marketplace.visualstudio.com/items?itemName=nobook.nobook-vscode) (coming soon).

Then:
1. Open any `.py` file with `# @block=` markers
2. Right-click and select "Open as Nobook"
3. Or use the command palette: "Nobook: Create New Notebook"

### As a project dependency

```bash
uv add nobook
uv run nobook
```

## Opening .py files as notebooks

In JupyterLab / Jupyter Notebook, right-click any `.py` file and select Open as Nobook:

![Right-click a .py file and select "Open as Nobook"](docs/open-as-nobook.png)

`.py` files containing `# @block=` markers will also auto-open as notebooks when double-clicked.

## CLI commands

### Launch Jupyter

```bash
uv run nobook           # launches Jupyter Notebook (default)
uv run nobook lab       # launches JupyterLab
uv run nobook jupyter   # same as default, launches Jupyter Notebook
```

All launch commands accept extra arguments that are passed through to Jupyter:

```bash
uv run nobook --port=9999 --no-browser
uv run nobook lab --port=9999
```

### Run blocks without Jupyter

```bash
uv run nobook run example.py                 # execute all blocks, write example.out.py
uv run nobook run example.py --block=setup   # run up to and including "setup"
uv run nobook list example.py                # print block names
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

Errors show as `# !!! ...` lines. Since output and errors are plain comments, `.out.py` files are valid Python -- you can run them directly with `python example.out.py`.

See `examples/` for sample input and output files.

## Manual launch (without the CLI wrapper)

```bash
uv run jupyter notebook --ServerApp.contents_manager_class=nobook.jupyter.contentsmanager.NobookContentsManager
```

Or for JupyterLab:

```bash
uv run jupyter lab --ServerApp.contents_manager_class=nobook.jupyter.contentsmanager.NobookContentsManager
```

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

## JupyterLab extension

Nobook includes a JupyterLab extension that adds:

- Launcher card -- click "Nobook" in the launcher to create a new `.py` notebook
- "Open as Nobook" context menu -- right-click any `.py` file to open it as a notebook
- Block name labels -- editable labels on each cell showing the `@block` name

The extension is bundled with the package and installs automatically.

## VS Code extension

The VS Code extension provides:

- Open `.py` files with `# @block=` markers as notebooks
- Block name display on each cell
- "Open as Nobook" context menu
- "Create New Notebook" command

Install from [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=nobook.nobook-vscode) (coming soon).

## Development

To test nobook from any project without installing it:

```bash
uv run --project <path-to-nobook> python -m nobook
```

### Full development install

```bash
git clone <repo-url> && cd nobook
uv sync
make setup-all      # Set up both JupyterLab and VS Code extensions
make build-all      # Build both extensions
```

### JupyterLab extension development

```bash
cd jupyterlab-ext
jlpm install
jlpm run watch
```

### VS Code extension development

```bash
cd vscode-ext
npm install
npm run watch
# Press F5 in VS Code to launch Extension Development Host
```

### Project structure

```
nobook/
├── nobook/              # Python package
├── jupyterlab-ext/      # JupyterLab extension (TypeScript)
├── vscode-ext/          # VS Code extension (TypeScript)
├── tests/               # Python tests
└── examples/            # Example notebooks
```
