"""Repository inventory models."""

from __future__ import annotations

from dataclasses import dataclass, field

from clone_trap.models.enums import FileClass


@dataclass(frozen=True)
class InventoryItem:
    path: str
    file_class: FileClass
    size: int
    tracked: bool
    ignored: bool


@dataclass
class Inventory:
    root: str
    items: list[InventoryItem] = field(default_factory=list)
    tracked_paths: set[str] = field(default_factory=set)
    ignored_existing: set[str] = field(default_factory=set)
    skip_dirs_seen: list[str] = field(default_factory=list)
    submodules: list[dict[str, str]] = field(default_factory=list)
    truncated: bool = False

    def by_class(self, *classes: FileClass) -> list[InventoryItem]:
        wanted = set(classes)
        return [item for item in self.items if item.file_class in wanted]
