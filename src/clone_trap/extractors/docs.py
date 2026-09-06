"""Documentation index: claimed setup, env names, and services."""

from __future__ import annotations

import os
import re

from clone_trap.extractors.facts import ExtractedFacts
from clone_trap.extractors.readutil import read_text
from clone_trap.models.enums import FileClass
from clone_trap.models.inventory import Inventory

COMMAND_RE = re.compile(
    r"(?:"
    r"npm (?:install|ci|run \S+)|"
    r"pnpm (?:install|i|run \S+)|"
    r"yarn (?:install|[\w:-]+)|"
    r"pip(?:3)? install(?:\s+\S+)*|"
    r"python(?:3(?:\.\d+)?)? -m \S+(?: \S+)*|"
    r"poetry install|"
    r"uv sync|"
    r"docker compose(?: -f \S+)?(?: up(?: -d)?)?|"
    r"docker-compose(?: -f \S+)?(?: up(?: -d)?)?|"
    r"make [\w.-]+|"
    r"prisma generate|"
    r"npx [\w@/.-]+"
    r")",
    re.IGNORECASE,
)

ENV_NAME_RE = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\b")
GENERATE_RE = re.compile(
    r"(prisma generate|openapi-generator|graphql-codegen|npm run generate|make generate|alembic upgrade)",
    re.IGNORECASE,
)

SERVICE_WORDS = {
    "redis": "redis",
    "valkey": "redis",
    "postgres": "postgres",
    "postgresql": "postgres",
    "mysql": "mysql",
    "mariadb": "mysql",
    "mongodb": "mongodb",
    "mongo": "mongodb",
    "rabbitmq": "rabbitmq",
    "kafka": "kafka",
    "elasticsearch": "elasticsearch",
    "opensearch": "elasticsearch",
    "sqlite": "sqlite",
}

MAKE_STOPWORDS = frozenset(
    {
        "this",
        "the",
        "a",
        "an",
        "it",
        "to",
        "for",
        "of",
        "and",
        "or",
        "with",
        "your",
        "our",
        "their",
        "sure",
        "any",
        "all",
        "full",
    }
)

SETUP_DOC_NAMES = frozenset(
    {
        "readme.md",
        "readme.rst",
        "setup.md",
        "install.md",
        "getting-started.md",
        "contributing.md",
        "agents.md",
    }
)


def extract_docs(inventory: Inventory, facts: ExtractedFacts) -> None:
    for item in inventory.by_class(FileClass.DOCS):
        text = read_text(inventory.root, item.path)
        if not text:
            continue
        facts.doc_files.append(item.path)
        setup_primary = _is_setup_doc(item.path)
        for command in _commands_from_text(text):
            if command not in facts.doc_commands:
                facts.doc_commands.append(command)
        for match in GENERATE_RE.finditer(text):
            command = re.sub(r"\s+", " ", match.group(0).strip())
            if command not in facts.doc_generate_commands:
                facts.doc_generate_commands.append(command)
        for name in ENV_NAME_RE.findall(text):
            if _looks_like_env(name):
                facts.doc_env_names.add(name)
        if setup_primary:
            lowered = text.lower()
            for word, service in SERVICE_WORDS.items():
                if re.search(rf"\b{re.escape(word)}\b", lowered):
                    facts.doc_services.add(service)


def _is_setup_doc(path: str) -> bool:
    name = os.path.basename(path).lower()
    return name in SETUP_DOC_NAMES


def _commands_from_text(text: str) -> list[str]:
    found: list[str] = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        command_line = stripped.lstrip("$ ").strip()
        looks_like_command = (
            in_fence
            or stripped.startswith("$")
            or command_line.startswith(
                (
                    "npm ",
                    "pnpm ",
                    "yarn ",
                    "pip ",
                    "pip3 ",
                    "python",
                    "poetry ",
                    "uv ",
                    "docker ",
                    "npx ",
                    "make ",
                    "prisma ",
                )
            )
        )
        if not looks_like_command:
            continue
        for match in COMMAND_RE.finditer(command_line):
            command = re.sub(r"\s+", " ", match.group(0).strip())
            if command.lower().startswith("make "):
                target = command.split(None, 1)[-1].lower()
                if target in MAKE_STOPWORDS:
                    continue
            if command not in found:
                found.append(command)
    return found


def _looks_like_env(name: str) -> bool:
    if name in {"HTTP", "HTTPS", "JSON", "YAML", "TODO", "FIXME", "NOTE", "README", "MIT"}:
        return False
    return "_" in name or name.endswith(("_URL", "_KEY", "_TOKEN", "_SECRET", "_HOST", "_PORT"))
