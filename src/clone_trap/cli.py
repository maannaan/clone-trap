"""Command-line interface."""

from __future__ import annotations

import argparse
import sys

from clone_trap.analysis import analyze_repository
from clone_trap.errors import CloneTrapError
from clone_trap.output import render_json, render_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="clone-trap",
        description=(
            "Find hidden local dependencies and assumptions that may prevent "
            "a repository from working after a clean clone."
        ),
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Absolute or relative path to a Git working tree.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write machine-readable JSON to stdout.",
    )
    parser.add_argument(
        "--max-findings",
        type=int,
        default=20,
        help="Maximum findings to display after ranking (default 20).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        if args.max_findings < 1:
            raise CloneTrapError("--max-findings must be at least 1.")
        report = analyze_repository(args.repo, max_findings=args.max_findings)
    except CloneTrapError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        render_json(report, sys.stdout)
    else:
        render_text(report, sys.stdout)
    return 0
