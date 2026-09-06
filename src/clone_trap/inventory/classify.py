"""Classify repository paths into file classes."""

from __future__ import annotations

import os
import re

from clone_trap.models.enums import FileClass

SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
        "coverage",
        ".next",
        ".turbo",
        ".nuxt",
        ".output",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".eggs",
        "htmlcov",
        "vendor",
        "target",
        ".cache",
        ".parcel-cache",
        "playwright-report",
        "test-results",
    }
)

MAX_FILE_BYTES = 200_000
MAX_FILES = 4000

ENV_EXAMPLE_NAMES = frozenset(
    {
        ".env.example",
        ".env.template",
        ".env.sample",
        ".env.local.example",
        ".env.development.example",
    }
)

VERSION_NAMES = frozenset(
    {
        ".python-version",
        ".nvmrc",
        ".node-version",
        ".tool-versions",
        "runtime.txt",
        ".ruby-version",
        ".go-version",
    }
)

MANIFEST_NAMES = frozenset(
    {
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
        "pipfile",
        "setup.cfg",
        "setup.py",
        "poetry.toml",
        "go.mod",
        "cargo.toml",
        "gemfile",
        "composer.json",
    }
)

LOCKFILE_NAMES = frozenset(
    {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "pipfile.lock",
        "uv.lock",
        "cargo.lock",
        "composer.lock",
        "go.sum",
    }
)

CONFIG_NAMES = frozenset(
    {
        "settings.py",
        "config.py",
        "config.ts",
        "config.js",
        "configuration.py",
        "settings.ts",
        "settings.js",
        "next.config.js",
        "next.config.mjs",
        "next.config.ts",
        "vite.config.ts",
        "vite.config.js",
    }
)

TEST_DIR_NAMES = frozenset({"tests", "test", "__tests__", "spec", "e2e"})
DOC_DIR_NAMES = frozenset({"docs", "doc", "documentation"})
SCRIPT_DIR_NAMES = frozenset({"scripts", "bin", "script"})

TEST_FILE_RE = re.compile(
    r"(^test_|_test\.py$|\.test\.|\.spec\.|test\.py$)",
    re.IGNORECASE,
)
SOURCE_SUFFIXES = frozenset(
    {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rs", ".rb"}
)
SCRIPT_SUFFIXES = frozenset({".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd"})
DOC_SUFFIXES = frozenset({".md", ".rst", ".adoc"})


def should_skip_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES or name.startswith(".venv")


def classify_path(relative_path: str) -> FileClass:
    """Return a file class for a repository-relative path."""
    posix = relative_path.replace(os.sep, "/")
    name = os.path.basename(posix).lower()
    parts = [part.lower() for part in posix.split("/") if part]
    parent = parts[-2] if len(parts) > 1 else ""

    if name == ".gitignore":
        return FileClass.IGNORE
    if name == ".gitmodules":
        return FileClass.GITMODULES
    if name in ENV_EXAMPLE_NAMES or name.endswith(".env.example"):
        return FileClass.ENV_EXAMPLE
    if name.startswith(".env") and "example" in name:
        return FileClass.ENV_EXAMPLE
    if name in VERSION_NAMES:
        return FileClass.VERSION
    if name in LOCKFILE_NAMES:
        return FileClass.LOCKFILE
    if name in MANIFEST_NAMES:
        return FileClass.MANIFEST
    if name in {"makefile", "gnumakefile"} or name.endswith(".mk"):
        return FileClass.SCRIPT
    if _is_compose(name, posix):
        return FileClass.COMPOSE
    if _is_ci(posix, parts):
        return FileClass.CI
    if name.endswith((".example", ".sample", ".template")):
        return FileClass.EXAMPLE
    if (
        any(part in TEST_DIR_NAMES for part in parts[:-1])
        or TEST_FILE_RE.search(name)
        or name.startswith("playwright.config.")
        or name.endswith(".spec.ts")
        or name.endswith(".spec.js")
    ):
        return FileClass.TEST
    if name in CONFIG_NAMES or parent in {"config", "conf", "settings"}:
        if name.endswith(tuple(SOURCE_SUFFIXES)):
            return FileClass.CONFIG
    if any(part in DOC_DIR_NAMES for part in parts[:-1]) or name in {
        "readme.md",
        "readme.rst",
        "contributing.md",
        "setup.md",
        "install.md",
        "getting-started.md",
        "changelog.md",
        "agents.md",
    }:
        return FileClass.DOCS
    if name.endswith(tuple(DOC_SUFFIXES)) and len(parts) == 1:
        return FileClass.DOCS
    if name.endswith(tuple(SCRIPT_SUFFIXES)):
        return FileClass.SCRIPT
    if name.endswith(tuple(SOURCE_SUFFIXES)):
        return FileClass.SOURCE
    return FileClass.OTHER


def _is_compose(name: str, posix: str) -> bool:
    if "docker-compose" in name and name.endswith((".yml", ".yaml")):
        return True
    if name in {"compose.yml", "compose.yaml"}:
        return True
    if posix.startswith("docker/") and "compose" in name and name.endswith(
        (".yml", ".yaml")
    ):
        return True
    return False


def _is_ci(posix: str, parts: list[str]) -> bool:
    if posix.startswith(".github/workflows/") and posix.endswith((".yml", ".yaml")):
        return True
    if posix in {".gitlab-ci.yml", ".gitlab-ci.yaml"}:
        return True
    if ".circleci" in parts:
        return True
    return False
