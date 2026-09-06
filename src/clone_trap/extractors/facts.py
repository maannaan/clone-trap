"""Structured facts extracted from a repository."""

from __future__ import annotations

from dataclasses import dataclass, field

from clone_trap.models.enums import FileClass


@dataclass
class EnvUsage:
    name: str
    path: str
    file_class: FileClass
    has_default: bool
    in_startup: bool
    line: int = 0


@dataclass
class ServiceHit:
    name: str
    kind: str
    path: str
    file_class: FileClass
    detail: str


@dataclass
class ComposeService:
    name: str
    image: str
    ports: list[str]
    env_names: list[str]
    path: str


@dataclass
class PathReference:
    path: str
    referenced_from: str
    file_class: FileClass
    detail: str


@dataclass
class BinaryUse:
    name: str
    path: str
    detail: str


@dataclass
class VersionPin:
    family: str
    value: str
    path: str
    source: str


@dataclass
class ExtractedFacts:
    env_usages: list[EnvUsage] = field(default_factory=list)
    env_example_names: set[str] = field(default_factory=set)
    env_example_files: list[str] = field(default_factory=list)
    doc_commands: list[str] = field(default_factory=list)
    doc_env_names: set[str] = field(default_factory=set)
    doc_services: set[str] = field(default_factory=set)
    doc_generate_commands: list[str] = field(default_factory=list)
    doc_files: list[str] = field(default_factory=list)
    compose_services: list[ComposeService] = field(default_factory=list)
    compose_files: list[str] = field(default_factory=list)
    ci_services: list[str] = field(default_factory=list)
    ci_versions: list[VersionPin] = field(default_factory=list)
    package_scripts: dict[str, str] = field(default_factory=dict)
    package_deps: set[str] = field(default_factory=set)
    package_engines: dict[str, str] = field(default_factory=dict)
    python_requires: str = ""
    version_pins: list[VersionPin] = field(default_factory=list)
    lockfiles: list[str] = field(default_factory=list)
    manifests: list[str] = field(default_factory=list)
    generate_scripts: list[str] = field(default_factory=list)
    path_references: list[PathReference] = field(default_factory=list)
    binaries: list[BinaryUse] = field(default_factory=list)
    absolute_paths: list[PathReference] = field(default_factory=list)
    home_paths: list[PathReference] = field(default_factory=list)
    os_specific_scripts: list[str] = field(default_factory=list)
    sibling_refs: list[PathReference] = field(default_factory=list)
    private_registries: list[str] = field(default_factory=list)
    gitignore_names: list[str] = field(default_factory=list)
    service_hits: list[ServiceHit] = field(default_factory=list)
