#!/usr/bin/env python3
"""Run Clone Trap against a real repository and store the JSON payload."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--max-findings", default="20")
    args = parser.parse_args()

    command = [
        sys.executable,
        "-m",
        "clone_trap",
        "--repo",
        args.repo,
        "--json",
        "--max-findings",
        str(args.max_findings),
    ]
    env = dict(**__import__("os").environ)
    env["PYTHONPATH"] = str(ROOT / "src") + (
        (__import__("os").pathsep + env["PYTHONPATH"]) if env.get("PYTHONPATH") else ""
    )
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    results = ROOT / "validation" / "results"
    results.mkdir(parents=True, exist_ok=True)
    payload = {
        "label": args.label,
        "repo": args.repo,
        "exit_code": completed.returncode,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "stderr": completed.stderr,
        "payload": None,
    }
    if completed.stdout.strip():
        try:
            payload["payload"] = json.loads(completed.stdout)
        except json.JSONDecodeError:
            payload["stdout"] = completed.stdout
    path = results / f"{args.label}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(path)
    return 0 if completed.returncode == 0 else completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
