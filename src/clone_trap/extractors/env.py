"""Language-aware environment variable extraction."""

from __future__ import annotations

import re

from clone_trap.extractors.facts import EnvUsage, ExtractedFacts
from clone_trap.extractors.readutil import read_text
from clone_trap.models.enums import FileClass
from clone_trap.models.inventory import Inventory

PYTHON_ENV_RE = re.compile(
    r"""os\.(?:environ(?:\.get)?|getenv)\(\s*['"]([A-Z][A-Z0-9_]{1,})['"](?P<default>\s*,)?""",
)
PYTHON_INDEX_RE = re.compile(
    r"""os\.environ\[\s*['"]([A-Z][A-Z0-9_]{1,})['"]\s*\]"""
)
NODE_DOT_RE = re.compile(r"""process\.env\.([A-Z][A-Z0-9_]{1,})\b""")
NODE_INDEX_RE = re.compile(r"""process\.env\[\s*['"]([A-Z][A-Z0-9_]{1,})['"]\s*\]""")
EXAMPLE_LINE_RE = re.compile(r"""^\s*(?:export\s+)?([A-Z][A-Z0-9_]{1,})\s*=""")
COMMENT_LINE_RE = re.compile(r"^\s*(#|//)")

STARTUP_NAMES = frozenset(
    {
        "settings.py",
        "config.py",
        "config.ts",
        "config.js",
        "configuration.py",
        "main.py",
        "app.py",
        "__main__.py",
        "wsgi.py",
        "asgi.py",
        "index.ts",
        "index.js",
        "server.ts",
        "server.js",
        "app.ts",
        "app.js",
    }
)
STARTUP_DIR_HINTS = ("/app/", "/src/", "/backend/", "/server/")


def extract_env(inventory: Inventory, facts: ExtractedFacts) -> None:
    for item in inventory.by_class(FileClass.ENV_EXAMPLE, FileClass.EXAMPLE):
        if item.file_class != FileClass.ENV_EXAMPLE and "env" not in item.path.lower():
            continue
        text = read_text(inventory.root, item.path)
        if not text:
            continue
        facts.env_example_files.append(item.path)
        for line in text.splitlines():
            if COMMENT_LINE_RE.match(line):
                continue
            match = EXAMPLE_LINE_RE.match(line)
            if match:
                facts.env_example_names.add(match.group(1))

    for item in inventory.by_class(FileClass.SOURCE, FileClass.CONFIG, FileClass.TEST, FileClass.SCRIPT):
        if not item.path.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")):
            continue
        text = read_text(inventory.root, item.path)
        if not text:
            continue
        startup = _is_startup(item.path, item.file_class)
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.lstrip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            for name, has_default in _scan_line(line):
                facts.env_usages.append(
                    EnvUsage(
                        name=name,
                        path=item.path,
                        file_class=item.file_class,
                        has_default=has_default,
                        in_startup=startup and item.file_class != FileClass.TEST,
                        line=line_no,
                    )
                )


def _scan_line(line: str) -> list[tuple[str, bool]]:
    found: list[tuple[str, bool]] = []
    for match in PYTHON_INDEX_RE.finditer(line):
        found.append((match.group(1), False))
    for match in PYTHON_ENV_RE.finditer(line):
        found.append((match.group(1), bool(match.group("default"))))
    for match in NODE_DOT_RE.finditer(line):
        name = match.group(1)
        tail = line[match.end() :]
        has_default = bool(re.match(r"\s*(?:\?\?|\|\|)", tail))
        found.append((name, has_default))
    for match in NODE_INDEX_RE.finditer(line):
        tail = line[match.end() :]
        has_default = bool(re.match(r"\s*(?:\?\?|\|\|)", tail))
        found.append((match.group(1), has_default))
    return found


def _is_startup(path: str, file_class: FileClass) -> bool:
    if file_class == FileClass.CONFIG:
        return True
    name = path.rsplit("/", 1)[-1].lower()
    if name in STARTUP_NAMES:
        return True
    lowered = path.replace("\\", "/").lower()
    return any(hint in lowered for hint in STARTUP_DIR_HINTS) and name in {
        "main.py",
        "app.py",
        "config.py",
        "settings.py",
        "index.ts",
        "server.ts",
    }
