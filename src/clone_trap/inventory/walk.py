"""Walk a repository and build an inventory."""

from __future__ import annotations

import os

from clone_trap.git import find_repository, is_ignored, list_submodules, list_tracked_files
from clone_trap.inventory.classify import (
    MAX_FILE_BYTES,
    MAX_FILES,
    classify_path,
    should_skip_dir,
)
from clone_trap.inventory.gitignore import load_gitignore
from clone_trap.models.enums import FileClass
from clone_trap.models.inventory import Inventory, InventoryItem


def build_inventory(start: str) -> Inventory:
    """Scan a Git working tree without executing project code."""
    root = find_repository(start)
    tracked = list_tracked_files(root)
    gitignore = load_gitignore(root)
    submodules = list_submodules(root)

    items: list[InventoryItem] = []
    skip_dirs_seen: list[str] = []
    ignored_existing: set[str] = set()
    truncated = False

    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        posix_dir = "" if rel_dir == "." else rel_dir.replace(os.sep, "/")

        kept: list[str] = []
        for name in dirnames:
            if should_skip_dir(name):
                skip_dirs_seen.append(
                    f"{posix_dir}/{name}".lstrip("/") if posix_dir else name
                )
                continue
            child = f"{posix_dir}/{name}".lstrip("/") if posix_dir else name
            if gitignore.matches(child, is_dir=True) and child not in tracked:
                skip_dirs_seen.append(child)
                continue
            kept.append(name)
        dirnames[:] = sorted(kept)

        for name in sorted(filenames):
            if len(items) >= MAX_FILES:
                truncated = True
                dirnames[:] = []
                break
            relative = f"{posix_dir}/{name}".lstrip("/") if posix_dir else name
            full = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            if size > MAX_FILE_BYTES:
                continue
            tracked_here = relative in tracked
            ignored = False
            if not tracked_here:
                ignored = gitignore.matches(relative, is_dir=False)
                if not ignored:
                    ignored = is_ignored(root, relative)
            if ignored:
                ignored_existing.add(relative)
            items.append(
                InventoryItem(
                    path=relative,
                    file_class=classify_path(relative),
                    size=size,
                    tracked=tracked_here,
                    ignored=ignored,
                )
            )

    # Always include .gitignore / .gitmodules if present even when walk skipped them.
    for special, file_class in ((".gitignore", FileClass.IGNORE), (".gitmodules", FileClass.GITMODULES)):
        full = os.path.join(root, special)
        if os.path.isfile(full) and not any(item.path == special for item in items):
            items.append(
                InventoryItem(
                    path=special,
                    file_class=file_class,
                    size=os.path.getsize(full),
                    tracked=special in tracked,
                    ignored=False,
                )
            )

    return Inventory(
        root=root,
        items=items,
        tracked_paths=tracked,
        ignored_existing=ignored_existing,
        skip_dirs_seen=skip_dirs_seen,
        submodules=submodules,
        truncated=truncated,
    )
