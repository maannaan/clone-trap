"""Package manifests, lockfiles, and version pins."""

from __future__ import annotations

import json
import os
import re

from clone_trap.extractors.facts import ExtractedFacts, VersionPin
from clone_trap.extractors.readutil import read_text
from clone_trap.models.enums import FileClass
from clone_trap.models.inventory import Inventory

REQUIRES_PYTHON_RE = re.compile(r"""requires-python\s*=\s*['"]([^'"]+)['"]""")
DEP_NAME_RE = re.compile(r"""['"]([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?""")
PRIVATE_HOST_RE = re.compile(
    r"https?://(?!registry\.npmjs\.org|npmjs\.org|pypi\.org|files\.pythonhosted\.org|pypi\.python\.org)([A-Za-z0-9.-]+)"
)


def extract_manifests(inventory: Inventory, facts: ExtractedFacts) -> None:
    for item in inventory.by_class(FileClass.MANIFEST):
        facts.manifests.append(item.path)
        text = read_text(inventory.root, item.path)
        if not text:
            continue
        name = os.path.basename(item.path).lower()
        if name == "package.json":
            _package_json(text, item.path, facts)
        elif name == "pyproject.toml":
            _pyproject(text, item.path, facts)
        elif name.startswith("requirements"):
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                pkg = re.split(r"[<>=!~;\s]", line, maxsplit=1)[0]
                pkg = pkg.split("[", 1)[0].strip()
                if pkg:
                    facts.package_deps.add(pkg.lower())

    for item in inventory.by_class(FileClass.LOCKFILE):
        facts.lockfiles.append(item.path)

    for item in inventory.by_class(FileClass.VERSION):
        text = read_text(inventory.root, item.path).strip()
        if not text:
            continue
        name = os.path.basename(item.path).lower()
        if name in {".python-version", "runtime.txt"}:
            facts.version_pins.append(
                VersionPin("python", _first_version(text), item.path, "version_file")
            )
        elif name in {".nvmrc", ".node-version"}:
            facts.version_pins.append(
                VersionPin("node", _first_version(text), item.path, "version_file")
            )
        elif name == ".tool-versions":
            for line in text.splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[0] in {"python", "nodejs", "node"}:
                    family = "node" if parts[0] in {"nodejs", "node"} else "python"
                    facts.version_pins.append(
                        VersionPin(family, parts[1], item.path, "version_file")
                    )

    npmrc = os.path.join(inventory.root, ".npmrc")
    if os.path.isfile(npmrc):
        text = read_text(inventory.root, ".npmrc")
        for match in PRIVATE_HOST_RE.finditer(text):
            facts.private_registries.append(match.group(1))


def _package_json(text: str, path: str, facts: ExtractedFacts) -> None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return
    if not isinstance(data, dict):
        return
    scripts = data.get("scripts") or {}
    if isinstance(scripts, dict):
        for key, value in scripts.items():
            if isinstance(value, str):
                facts.package_scripts[key] = value
                if "generate" in key.lower() or "prisma generate" in value.lower():
                    facts.generate_scripts.append(value)
    for bucket in ("dependencies", "devDependencies", "optionalDependencies"):
        deps = data.get(bucket) or {}
        if isinstance(deps, dict):
            facts.package_deps.update(str(name).lower() for name in deps)
    engines = data.get("engines") or {}
    if isinstance(engines, dict):
        for key, value in engines.items():
            if isinstance(value, str):
                facts.package_engines[str(key)] = value
                if key in {"node", "python"}:
                    facts.version_pins.append(
                        VersionPin(key, value, path, "engines")
                    )
    registry = ""
    publish = data.get("publishConfig") or {}
    if isinstance(publish, dict):
        registry = str(publish.get("registry") or "")
    if registry:
        match = PRIVATE_HOST_RE.search(registry)
        if match:
            facts.private_registries.append(match.group(1))


def _pyproject(text: str, path: str, facts: ExtractedFacts) -> None:
    match = REQUIRES_PYTHON_RE.search(text)
    if match:
        facts.python_requires = match.group(1)
        facts.version_pins.append(
            VersionPin("python", match.group(1), path, "requires-python")
        )
    for match in DEP_NAME_RE.finditer(text):
        name = match.group(1).lower()
        if name in {"dependencies", "dev", "test", "optional-dependencies"}:
            continue
        if re.match(r"^[a-z][a-z0-9_.-]+$", name):
            facts.package_deps.add(name)


def _first_version(text: str) -> str:
    match = re.search(r"(\d+(?:\.\d+)*)", text)
    return match.group(1) if match else text.split()[0]
