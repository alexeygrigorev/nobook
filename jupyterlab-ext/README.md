# Nobook JupyterLab Extension

JupyterLab extension for [nobook](https://github.com/alexeidation/nobook).

## Features

- **Launcher card** - Click "Nobook" in the JupyterLab launcher to create a new `.py` notebook
- **Context menu** - Right-click any `.py` file and select "Open as Nobook"
- **Block name labels** - Editable labels on each cell showing the `@block` name

## Development

### Setup

```bash
# From the repository root
cd jupyterlab-ext
jlpm install
```

### Build

```bash
# Development build
jlpm run build:lib

# Production build
jlpm run build:prod
```

### Watch mode

```bash
jlpm run watch
```

### Install in development

```bash
# From repository root
jupyter labextension develop jupyterlab-ext/ --overwrite
```

### Clean

```bash
jlpm run clean
```

## Architecture

The extension consists of two plugins:

1. **Launcher plugin** (`launcherPlugin`):
   - Registers "Create new Nobook" command
   - Adds launcher card
   - Adds "Open as Nobook" context menu

2. **Cell labels plugin** (`cellLabelPlugin`):
   - Attaches to notebook opening
   - Renders editable block name labels on cells
   - Handles block name metadata

## Distribution

This extension is bundled with the `nobook` Python package and installed automatically via:

```bash
pip install nobook
```

## License

WTFPL
