# Nobook VS Code Extension

Edit plain `.py` files as notebooks in VS Code.

## Features

- Open `.py` files with `# @block=` markers as notebooks
- Block-based editing with VS Code's native notebook interface
- IPython kernel integration (uses VS Code's built-in Jupyter support)
- Block name metadata preserved in `.py` format

## Installation

### From VS Code Marketplace

Coming soon!

### Manual Development Install

```bash
# Install dependencies
npm install

# Build the extension
npm run build

# Install in VS Code
code --install-extension nobook-vscode-*.vsix
```

## File Format

```python
# @block=setup
import math
x = 42

# @block=compute
result = math.sqrt(x)
print(f"sqrt({x}) = {result:.4f}")
```

## Development

```bash
# Install dependencies
npm install

# Watch mode
npm run watch

# Press F5 in VS Code to launch Extension Development Host
```

## Architecture

The extension uses VS Code's Notebook API to provide:

1. **NotebookSerializer** - Converts between `.py` files and VS Code notebook format
2. **TypeScript Parser** - Parses `# @block=` markers (ported from `nobook/parser.py`)
3. **Commands** - "Open as Nobook" context menu, "Create New Notebook" command
4. **Status Bar** - Displays block names for each cell

## License

WTFPL
