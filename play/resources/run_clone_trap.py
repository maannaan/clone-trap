#!/usr/bin/env python3
"""Play wrapper: run the vendored stdlib Clone Trap engine.

Rote copies Play resources into a temporary workspace. This wrapper adds the
sibling ``clone_trap`` package to ``sys.path`` and does not require engine_root.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="Absolute path to a Git repository")
    parser.add_argument("--max-findings", default="20")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    from clone_trap.cli import main as cli_main

    return cli_main(
        [
            "--repo",
            args.repo,
            "--json",
            "--max-findings",
            str(args.max_findings),
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
