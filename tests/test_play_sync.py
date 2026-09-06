"""Vendored Play package must stay in sync with src/clone_trap."""

from __future__ import annotations

from pathlib import Path


def test_play_package_matches_src():
    root = Path(__file__).resolve().parents[1]
    src = root / "src" / "clone_trap"
    vendored = root / "play" / "resources" / "clone_trap"
    src_files = {
        path.relative_to(src).as_posix()
        for path in src.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }
    vendored_files = {
        path.relative_to(vendored).as_posix()
        for path in vendored.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }
    assert src_files == vendored_files
    for relative in sorted(src_files):
        assert (src / relative).read_bytes() == (vendored / relative).read_bytes()
