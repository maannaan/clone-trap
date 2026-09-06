"""Safe file reads for extractors."""

from __future__ import annotations

import os

from clone_trap.inventory.classify import MAX_FILE_BYTES


def read_text(root: str, relative: str, limit: int = MAX_FILE_BYTES) -> str:
    full = os.path.join(root, relative)
    try:
        with open(full, "rb") as handle:
            data = handle.read(limit + 1)
    except OSError:
        return ""
    if not data or b"\0" in data[:1024]:
        return ""
    return data[:limit].decode("utf-8", errors="replace")
