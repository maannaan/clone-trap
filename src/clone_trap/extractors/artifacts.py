"""Referenced paths, generate scripts, and ignored artifacts."""

from __future__ import annotations

import os
import re

from clone_trap.extractors.facts import ExtractedFacts, PathReference
from clone_trap.extractors.readutil import read_text
from clone_trap.models.enums import FileClass
from clone_trap.models.inventory import Inventory

PATH_RE = re.compile(
    r"""(?:open|readFileSync|readFile|existsSync|Path)\(\s*['"]([^'"]+)['"]"""
)
RELATIVE_IMPORT_RE = re.compile(
    r"""(?:from|import|require)\(\s*['"](\./(?:generated|dist|build|prisma)[^'"]*)['"]"""
)
STRING_PATH_RE = re.compile(
    r"""['"]((?:\./)?(?:generated|dist|build)/[^'"]+)['"]"""
)

GENERATED_HINTS = ("generated", "codegen", "prisma", ".next/")
HARMLESS_IGNORED = {
    ".env",
    ".env.local",
    ".venv",
    "node_modules",
    ".ds_store",
    "__pycache__",
}


def extract_artifacts(inventory: Inventory, facts: ExtractedFacts) -> None:
    facts.gitignore_names = [
        os.path.basename(item.path) for item in inventory.by_class(FileClass.IGNORE)
    ]
    for item in inventory.by_class(FileClass.SOURCE, FileClass.CONFIG, FileClass.SCRIPT):
        text = read_text(inventory.root, item.path)
        if not text:
            continue
        for regex in (PATH_RE, RELATIVE_IMPORT_RE, STRING_PATH_RE):
            for match in regex.finditer(text):
                target = match.group(1).lstrip("./")
                if _skip_target(target):
                    continue
                facts.path_references.append(
                    PathReference(
                        path=target,
                        referenced_from=item.path,
                        file_class=item.file_class,
                        detail=match.group(0)[:120],
                    )
                )

    for item in inventory.by_class(FileClass.SCRIPT, FileClass.MANIFEST):
        text = read_text(inventory.root, item.path)
        if not text:
            continue
        if re.search(r"prisma generate|npm run generate|make generate", text, re.I):
            command = "prisma generate" if "prisma" in text.lower() else "generate"
            if command not in facts.generate_scripts:
                facts.generate_scripts.append(command)


def _skip_target(target: str) -> bool:
    lowered = target.lower()
    if lowered in HARMLESS_IGNORED or lowered.startswith(".env"):
        return True
    if lowered.startswith(("http://", "https://", "node_modules/", ".venv/")):
        return True
    return False
