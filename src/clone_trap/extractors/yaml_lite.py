"""Purpose-built YAML subset reader for compose and GitHub Actions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class YamlLine:
    indent: int
    key: str
    value: str
    is_list: bool
    raw: str


def parse_lines(text: str) -> list[YamlLine]:
    """Parse simple key/value YAML without anchors, tags, or multiline blocks."""
    parsed: list[YamlLine] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        body = raw.strip()
        is_list = body.startswith("- ")
        if is_list:
            body = body[2:].strip()
        key = ""
        value = body
        if not is_list and ":" in body:
            key, rest = body.split(":", 1)
            key = key.strip().strip("'\"")
            value = rest.strip().strip("'\"")
        elif is_list and ":" in body and not body.startswith("{"):
            key, rest = body.split(":", 1)
            key = key.strip().strip("'\"")
            value = rest.strip().strip("'\"")
        parsed.append(
            YamlLine(
                indent=indent,
                key=key,
                value=value,
                is_list=is_list,
                raw=raw,
            )
        )
    return parsed


def mapping_under(lines: list[YamlLine], header_key: str) -> list[tuple[str, list[YamlLine]]]:
    """Return named child mappings under a top-level or nested header key."""
    results: list[tuple[str, list[YamlLine]]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.key == header_key and not line.value:
            header_indent = line.indent
            i += 1
            while i < len(lines) and lines[i].indent > header_indent:
                child = lines[i]
                if child.indent == header_indent + 2 and child.key and not child.is_list:
                    name = child.key
                    child_indent = child.indent
                    block: list[YamlLine] = []
                    i += 1
                    while i < len(lines) and lines[i].indent > child_indent:
                        block.append(lines[i])
                        i += 1
                    results.append((name, block))
                    continue
                i += 1
            continue
        i += 1
    return results


def values_for(block: list[YamlLine], key: str) -> list[str]:
    found: list[str] = []
    for index, line in enumerate(block):
        if line.key != key:
            continue
        if line.value:
            found.append(line.value)
            continue
        indent = line.indent
        for child in block[index + 1 :]:
            if child.indent <= indent:
                break
            if child.is_list:
                token = child.value or child.key
                if token:
                    found.append(token)
            elif child.key:
                found.append(child.key if not child.value else f"{child.key}={child.value}")
    return found
