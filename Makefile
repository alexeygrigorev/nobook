.PHONY: test setup shell coverage publish-build publish-test publish publish-clean
.PHONY: build-jl dev-jl clean-jl build-vscode dev-vscode clean-vscode

test:
	uv run pytest

setup:
	uv sync --dev

setup-jl:
	cd jupyterlab-ext && jlpm install

setup-vscode:
	cd vscode-ext && npm install

setup-all: setup setup-jl setup-vscode

shell:
	uv shell

coverage:
	uv run pytest --cov=nobook --cov-report=term-missing

# JupyterLab extension
build-jl:
	cd jupyterlab-ext && jlpm run build:prod

dev-jl:
	cd jupyterlab-ext && jlpm run watch

clean-jl:
	cd jupyterlab-ext && jlpm run clean

# VS Code extension
build-vscode:
	cd vscode-ext && npm run build

dev-vscode:
	cd vscode-ext && npm run watch

clean-vscode:
	rm -rf vscode-ext/out

package-vscode:
	cd vscode-ext && npx vsce package

# Build all extensions
build-all: build-jl build-vscode

# Publishing
publish-build:
	uv run hatch build

publish-test:
	uv run hatch publish --repo test

publish:
	uv run hatch publish

publish-clean:
	rm -r dist/
