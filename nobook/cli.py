"""CLI entry point for nobook."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .executor import execute_all, execute_up_to
from .parser import parse_file
from .writer import write_output


def cmd_run(args: argparse.Namespace) -> None:
    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    parsed = parse_file(path)

    if args.block:
        results = execute_up_to(parsed, args.block)
    else:
        results = execute_all(parsed)

    out_path = path.with_suffix(".out.py")
    write_output(parsed, results, out_path)
    print(f"Output written to {out_path}")

    # Exit with error if any block failed
    if any(r.error for r in results):
        sys.exit(1)


def cmd_list(args: argparse.Namespace) -> None:
    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    parsed = parse_file(path)
    for block in parsed.blocks:
        print(block.name)


def _launch_jupyter(module: str, extra_args: list[str]) -> None:
    jupyter_args = [
        sys.executable, "-m", module,
        "--ServerApp.contents_manager_class=nobook.jupyter.contentsmanager.NobookContentsManager",
        *extra_args,
    ]
    try:
        sys.exit(subprocess.call(jupyter_args))
    except KeyboardInterrupt:
        sys.exit(0)


def cmd_default(args: argparse.Namespace) -> None:
    _launch_jupyter("notebook", args.jupyter_args)


def cmd_lab(args: argparse.Namespace) -> None:
    _launch_jupyter("jupyterlab", args.jupyter_args)


def cmd_jupyter(args: argparse.Namespace) -> None:
    _launch_jupyter("notebook", args.jupyter_args)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="nobook", description="Plain .py files as notebooks")
    parser.add_argument("jupyter_args", nargs="*", help="Extra args for notebook")
    sub = parser.add_subparsers(dest="command")

    # run
    run_parser = sub.add_parser("run", help="Execute blocks and write .out.py")
    run_parser.add_argument("file", help="Path to .py file")
    run_parser.add_argument("--block", help="Run up to and including this block")

    # list
    list_parser = sub.add_parser("list", help="List block names")
    list_parser.add_argument("file", help="Path to .py file")

    # lab
    lab_parser = sub.add_parser("lab", help="Launch JupyterLab with nobook")
    lab_parser.add_argument("jupyter_args", nargs="*", help="Extra args for jupyterlab")

    # jupyter (kept for backwards compat)
    jupyter_parser = sub.add_parser("jupyter", help="Launch Jupyter Notebook with nobook")
    jupyter_parser.add_argument("jupyter_args", nargs="*", help="Extra args for notebook")

    args = parser.parse_args(argv)
    if args.command is None:
        cmd_default(args)
        return

    {"run": cmd_run, "list": cmd_list, "lab": cmd_lab, "jupyter": cmd_jupyter}[args.command](args)
