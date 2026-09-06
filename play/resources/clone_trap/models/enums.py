"""Shared enumerations."""

from __future__ import annotations

from enum import Enum


class FileClass(str, Enum):
    SOURCE = "source"
    TEST = "test"
    DOCS = "docs"
    EXAMPLE = "example"
    ENV_EXAMPLE = "env_example"
    COMPOSE = "compose"
    CI = "ci"
    MANIFEST = "manifest"
    LOCKFILE = "lockfile"
    VERSION = "version"
    SCRIPT = "script"
    IGNORE = "ignore"
    GITMODULES = "gitmodules"
    CONFIG = "config"
    OTHER = "other"


class Category(str, Enum):
    ENVIRONMENT = "environment"
    SERVICES = "services"
    ARTIFACTS = "artifacts"
    TOOLCHAIN = "toolchain"
    LOCALITY = "locality"


class Verdict(str, Enum):
    CONFIRMED_TRAP = "confirmed_trap"
    LIKELY_TRAP = "likely_trap"
    ENVIRONMENT_ASSUMPTION = "environment_assumption"
    INFORMATIONAL = "informational"


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CloneStage(str, Enum):
    CLONE = "clone"
    INSTALL = "install"
    GENERATE = "generate"
    CONFIGURE = "configure"
    START_SERVICES = "start_services"
    RUN = "run"
