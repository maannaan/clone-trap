"""Source-level local service signals."""

from __future__ import annotations

import re

from clone_trap.extractors.facts import ExtractedFacts, ServiceHit
from clone_trap.extractors.readutil import read_text
from clone_trap.models.enums import FileClass
from clone_trap.models.inventory import Inventory

SERVICE_PATTERNS: dict[str, list[tuple[str, re.Pattern[str]]]] = {
    "redis": [
        ("import", re.compile(r"""(?:import redis|from redis|ioredis|from ['"]redis['"]|require\(['"]ioredis['"]\))""")),
        ("port", re.compile(r"localhost:6379|127\.0\.0\.1:6379")),
        ("env", re.compile(r"\bREDIS_(?:URL|HOST|PORT|PASSWORD)\b")),
    ],
    "postgres": [
        ("import", re.compile(r"""(?:import psycopg|from psycopg|import asyncpg|from asyncpg|require\(['"]pg['"]\)|from ['"]pg['"])""")),
        ("port", re.compile(r"localhost:5432|127\.0\.0\.1:5432")),
        ("url", re.compile(r"postgres(?:ql)?://")),
        ("env", re.compile(r"\b(?:DATABASE_URL|POSTGRES_URL|POSTGRES_HOST|PGHOST|POSTGRES_PASSWORD)\b")),
    ],
    "mysql": [
        ("import", re.compile(r"""(?:import MySQLdb|mysql\.connector|require\(['"]mysql2['"]\))""")),
        ("port", re.compile(r"localhost:3306|127\.0\.0\.1:3306")),
    ],
    "mongodb": [
        ("import", re.compile(r"""(?:from pymongo|import pymongo|mongoose|require\(['"]mongodb['"]\))""")),
        ("port", re.compile(r"localhost:27017|127\.0\.0\.1:27017")),
        ("url", re.compile(r"mongodb(?:\+srv)?://")),
    ],
    "rabbitmq": [
        ("import", re.compile(r"""(?:import pika|from pika|amqplib|require\(['"]amqplib['"]\))""")),
        ("port", re.compile(r"localhost:5672|127\.0\.0\.1:5672")),
    ],
}


def extract_services(inventory: Inventory, facts: ExtractedFacts) -> None:
    for item in inventory.by_class(FileClass.SOURCE, FileClass.CONFIG, FileClass.TEST, FileClass.SCRIPT):
        if not item.path.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")):
            continue
        text = read_text(inventory.root, item.path)
        if not text:
            continue
        for service, patterns in SERVICE_PATTERNS.items():
            for kind, regex in patterns:
                if regex.search(text):
                    facts_hit = ServiceHit(
                        name=service,
                        kind=kind,
                        path=item.path,
                        file_class=item.file_class,
                        detail=kind,
                    )
                    if not _duplicate(facts, facts_hit):
                        facts.service_hits.append(facts_hit)


def _duplicate(facts: ExtractedFacts, hit: ServiceHit) -> bool:
    for existing in facts.service_hits:
        if existing.name == hit.name and existing.path == hit.path and existing.kind == hit.kind:
            return True
    return False
