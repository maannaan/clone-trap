"""Machine-specific paths, OS-only scripts, and sibling checkouts."""

from __future__ import annotations

import os
import re

from clone_trap.extractors.facts import ExtractedFacts, PathReference
from clone_trap.extractors.readutil import read_text
from clone_trap.models.enums import FileClass
from clone_trap.models.inventory import Inventory

ABS_PATH_RE = re.compile(
    r"""['"](/Users/[^'"]+|/home/[^'"]+|/opt/[^'"]+|C:\\\\[^'"]+|C:/[^'"]+)['"]"""
)
HOME_RE = re.compile(
    r"""(?:os\.path\.expanduser\(\s*['"]~[^'"]*['"]|['"]~/[^'"]+['"]|\$HOME/[^'"]+)"""
)
SIBLING_RE = re.compile(r"""['"](\.\./[A-Za-z0-9._/-]+)['"]""")


def extract_locality(inventory: Inventory, facts: ExtractedFacts) -> None:
    script_paths = [item.path for item in inventory.by_class(FileClass.SCRIPT)]
    has_sh = any(path.endswith((".sh", ".bash")) for path in script_paths)
    has_ps1 = any(path.endswith(".ps1") for path in script_paths)
    if has_ps1 and not has_sh:
        facts.os_specific_scripts.extend(
            path for path in script_paths if path.endswith(".ps1")
        )

    for item in inventory.by_class(FileClass.SOURCE, FileClass.CONFIG, FileClass.SCRIPT, FileClass.MANIFEST):
        if item.file_class == FileClass.MANIFEST and not item.path.endswith(".json"):
            # data manifests sometimes embed author machine paths
            pass
        text = read_text(inventory.root, item.path)
        if not text:
            continue
        for match in ABS_PATH_RE.finditer(text):
            if "/absolute/path/to/" in match.group(1):
                continue
            facts.absolute_paths.append(
                PathReference(
                    path=match.group(1),
                    referenced_from=item.path,
                    file_class=item.file_class,
                    detail=match.group(0)[:160],
                )
            )
        for match in HOME_RE.finditer(text):
            facts.home_paths.append(
                PathReference(
                    path=match.group(0),
                    referenced_from=item.path,
                    file_class=item.file_class,
                    detail=match.group(0)[:160],
                )
            )
        if item.file_class in {FileClass.SOURCE, FileClass.CONFIG, FileClass.SCRIPT}:
            for match in SIBLING_RE.finditer(text):
                target = match.group(1)
                if target.startswith("../"):
                    facts.sibling_refs.append(
                        PathReference(
                            path=target,
                            referenced_from=item.path,
                            file_class=item.file_class,
                            detail=match.group(0)[:160],
                        )
                    )
