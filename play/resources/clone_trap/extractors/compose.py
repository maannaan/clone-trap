"""Docker Compose and CI service extractors."""

from __future__ import annotations

import re

from clone_trap.extractors.facts import ComposeService, ExtractedFacts, VersionPin
from clone_trap.extractors.readutil import read_text
from clone_trap.extractors.yaml_lite import mapping_under, parse_lines, values_for
from clone_trap.models.enums import FileClass
from clone_trap.models.inventory import Inventory

IMAGE_SERVICE_HINTS = {
    "redis": "redis",
    "valkey": "redis",
    "postgres": "postgres",
    "postgresql": "postgres",
    "mysql": "mysql",
    "mariadb": "mysql",
    "mongo": "mongodb",
    "rabbitmq": "rabbitmq",
    "kafka": "kafka",
    "elasticsearch": "elasticsearch",
    "opensearch": "elasticsearch",
}


def extract_compose_and_ci(inventory: Inventory, facts: ExtractedFacts) -> None:
    for item in inventory.by_class(FileClass.COMPOSE):
        text = read_text(inventory.root, item.path)
        if not text:
            continue
        facts.compose_files.append(item.path)
        lines = parse_lines(text)
        for name, block in mapping_under(lines, "services"):
            images = values_for(block, "image")
            ports = values_for(block, "ports")
            env_entries = values_for(block, "environment")
            env_names = [_env_name(entry) for entry in env_entries if _env_name(entry)]
            image = images[0] if images else ""
            facts.compose_services.append(
                ComposeService(
                    name=name,
                    image=image,
                    ports=_normalize_ports(ports),
                    env_names=env_names,
                    path=item.path,
                )
            )

    for item in inventory.by_class(FileClass.CI):
        text = read_text(inventory.root, item.path)
        if not text:
            continue
        lines = parse_lines(text)
        for name, block in mapping_under(lines, "services"):
            images = values_for(block, "image")
            image = images[0] if images else name
            service = infer_service(name, image)
            if service:
                facts.ci_services.append(service)
        facts.ci_versions.extend(_ci_versions(text, item.path))


def infer_service(name: str, image: str) -> str | None:
    blob = f"{name} {image}".lower()
    for token, service in IMAGE_SERVICE_HINTS.items():
        if token in blob:
            return service
    return None


def _env_name(entry: str) -> str:
    match = re.match(r"([A-Z][A-Z0-9_]{1,})", entry)
    return match.group(1) if match else ""


def _normalize_ports(ports: list[str]) -> list[str]:
    found: list[str] = []
    for item in ports:
        match = re.search(r"(\d{2,5})", item)
        if match:
            found.append(match.group(1))
    return found


def _ci_versions(text: str, path: str) -> list[VersionPin]:
    pins: list[VersionPin] = []
    python = re.search(r"python-version:\s*['\"]?([0-9.]+)", text)
    if python:
        pins.append(
            VersionPin(
                family="python",
                value=python.group(1),
                path=path,
                source="ci",
            )
        )
    node = re.search(r"node-version:\s*['\"]?([0-9.]+)", text)
    if node:
        pins.append(
            VersionPin(
                family="node",
                value=node.group(1),
                path=path,
                source="ci",
            )
        )
    return pins
