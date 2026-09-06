"""Lightweight .gitignore matching for inventory."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class GitignoreRule:
    pattern: str
    negated: bool
    directory_only: bool
    anchored: bool


@dataclass
class GitignoreSet:
    rules: list[GitignoreRule] = field(default_factory=list)

    def matches(self, relative_path: str, is_dir: bool = False) -> bool:
        posix = relative_path.replace(os.sep, "/").lstrip("./")
        ignored = False
        for rule in self.rules:
            if rule.directory_only and not is_dir and "/" not in posix:
                # directory-only rules still match files under that directory
                if not _path_under_dir(posix, rule):
                    continue
            if _rule_matches(rule, posix, is_dir):
                ignored = not rule.negated
        return ignored


def parse_gitignore(text: str) -> GitignoreSet:
    rules: list[GitignoreRule] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        negated = line.startswith("!")
        if negated:
            line = line[1:]
        directory_only = line.endswith("/")
        if directory_only:
            line = line[:-1]
        anchored = line.startswith("/")
        if anchored:
            line = line[1:]
        rules.append(
            GitignoreRule(
                pattern=line,
                negated=negated,
                directory_only=directory_only,
                anchored=anchored,
            )
        )
    return GitignoreSet(rules)


def load_gitignore(root: str) -> GitignoreSet:
    path = os.path.join(root, ".gitignore")
    if not os.path.isfile(path):
        return GitignoreSet()
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return parse_gitignore(handle.read())
    except OSError:
        return GitignoreSet()


def _path_under_dir(posix: str, rule: GitignoreRule) -> bool:
    name = rule.pattern.rstrip("/")
    return posix == name or posix.startswith(name + "/")


def _rule_matches(rule: GitignoreRule, posix: str, is_dir: bool) -> bool:
    pattern = rule.pattern
    if rule.directory_only and is_dir and posix.rstrip("/") == pattern.rstrip("/"):
        return True
    if "**" in pattern:
        return _glob_match(pattern, posix)
    if "/" in pattern or rule.anchored:
        return _glob_match(pattern, posix) or posix.startswith(pattern.rstrip("/") + "/")
    basename = posix.rsplit("/", 1)[-1]
    if _glob_match(pattern, basename):
        return True
    if rule.directory_only and (posix == pattern or posix.startswith(pattern + "/")):
        return True
    return posix.startswith(pattern + "/") if pattern.endswith("*") is False and "*" not in pattern else False


def _glob_match(pattern: str, value: str) -> bool:
    return _recursive_match(pattern, value)


def _recursive_match(pattern: str, value: str) -> bool:
    if pattern == "**":
        return True
    if pattern == value:
        return True
    if "**/" in pattern:
        head, tail = pattern.split("**/", 1)
        if head and not value.startswith(head):
            return False
        rest = value[len(head) :] if head else value
        parts = rest.split("/") if rest else [""]
        acc = []
        for index in range(len(parts) + 1):
            candidate = "/".join(parts[index:])
            if _recursive_match(tail, candidate):
                return True
            if index < len(parts):
                acc.append(parts[index])
        return False
    return _simple_glob(pattern, value)


def _simple_glob(pattern: str, value: str) -> bool:
    regex = ""
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "*":
            regex += "[^/]*"
        elif char == "?":
            regex += "[^/]"
        else:
            if char in r".^$+{}[]|()\\":
                regex += "\\" + char
            else:
                regex += char
        i += 1
    import re

    return re.fullmatch(regex, value) is not None
