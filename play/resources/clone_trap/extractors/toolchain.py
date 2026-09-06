"""Binaries used in repo scripts and toolchain declarations."""

from __future__ import annotations

import os
import re
import shlex

from clone_trap.extractors.facts import BinaryUse, ExtractedFacts
from clone_trap.extractors.readutil import read_text
from clone_trap.models.enums import FileClass
from clone_trap.models.inventory import Inventory

SHELL_KEYWORDS = frozenset(
    {
        "declare",
        "local",
        "return",
        "trap",
        "shift",
        "else",
        "elif",
        "then",
        "fi",
        "do",
        "done",
        "case",
        "esac",
        "function",
        "select",
        "break",
        "continue",
        "until",
        "in",
        "wait",
        "readonly",
        "typeset",
        "alias",
        "builtin",
        "caller",
        "enable",
        "help",
        "let",
        "read",
        "type",
        "ulimit",
        "umask",
        "hash",
        "eval",
        "exec",
        "kill",
        "jobs",
        "fg",
        "bg",
        "head",
        "tail",
        "wc",
        "sort",
        "uniq",
        "cut",
        "tr",
        "date",
        "basename",
        "dirname",
        "mktemp",
        "install",
        "seq",
        "yes",
        "await",
        "cannot",
        "approval",
        "eof",
        "const",
        "var",
        "export",
        "import",
        "typeof",
        "undefined",
        "cfg",
        "data",
        "require",
    }
)

SAFE_BINARIES = frozenset(
    {
        "node",
        "npm",
        "npx",
        "yarn",
        "pnpm",
        "python",
        "python3",
        "pip",
        "pip3",
        "git",
        "docker",
        "docker-compose",
        "compose",
        "make",
        "bash",
        "sh",
        "zsh",
        "rm",
        "mkdir",
        "cp",
        "mv",
        "cat",
        "echo",
        "cd",
        "ls",
        "chmod",
        "curl",
        "wget",
        "sleep",
        "true",
        "false",
        "env",
        "export",
        "set",
        "unset",
        "test",
        "[",
        "[[",
        ":",
        "exit",
        "printf",
        "tee",
        "xargs",
        "awk",
        "sed",
        "grep",
        "find",
        "which",
        "command",
        "sudo",
        "source",
        ".",
        "if",
        "then",
        "fi",
        "for",
        "do",
        "done",
        "while",
        "case",
        "esac",
        "uv",
        "poetry",
        "pytest",
        "coverage",
    }
    | SHELL_KEYWORDS
)

BIN_FROM_PACKAGE = {
    "tsc": "typescript",
    "eslint": "eslint",
    "prettier": "prettier",
    "prisma": "prisma",
    "vite": "vite",
    "next": "next",
    "tsx": "tsx",
    "ts-node": "ts-node",
    "webpack": "webpack",
    "nodemon": "nodemon",
    "jest": "jest",
    "vitest": "vitest",
    "turbo": "turbo",
    "playwright": "playwright",
}


FUNCTION_RE = re.compile(r"^(?:function\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)")
PYTHON_LINE_RE = re.compile(
    r"^(?:except|import|from|def|class|try|finally|raise|pass|yield|"
    r"lambda|with|assert|global|nonlocal|return|for|while|if|elif|else)\b"
    r"|^[A-Za-z_][A-Za-z0-9_]*\s*="
)
LOCAL_BIN_RE = re.compile(r"(?:^|[/'\"])(?:\.venv|venv|node_modules/\.bin)/")


def extract_toolchain(inventory: Inventory, facts: ExtractedFacts) -> None:
    defined: set[str] = {
        os.path.splitext(os.path.basename(item.path))[0]
        for item in inventory.items
    }
    defined.update(os.path.basename(item.path) for item in inventory.items)
    shell_texts: list[tuple[str, str]] = []
    for item in inventory.by_class(FileClass.SCRIPT):
        name = os.path.basename(item.path).lower()
        if not name.endswith((".sh", ".bash", ".zsh")) and name not in {
            "makefile",
            "gnumakefile",
        } and not name.endswith(".mk"):
            continue
        text = read_text(inventory.root, item.path)
        if not text:
            continue
        shell_texts.append((item.path, text))
        for line in text.splitlines():
            match = FUNCTION_RE.match(line.strip())
            if match:
                defined.add(match.group(1))

    for script in facts.package_scripts.values():
        for binary, detail in _binaries_from_command(script):
            if binary not in defined:
                facts.binaries.append(BinaryUse(binary, "package.json", detail))

    for path, text in shell_texts:
        name = os.path.basename(path).lower()
        if name in {"makefile", "gnumakefile"} or name.endswith(".mk"):
            for line in text.splitlines():
                stripped = line.lstrip()
                if not stripped or stripped.startswith("#") or stripped.startswith("."):
                    continue
                if line.startswith("\t") or line.startswith("        "):
                    for binary, detail in _binaries_from_command(stripped):
                        if binary not in defined:
                            facts.binaries.append(BinaryUse(binary, path, detail))
            continue
        if not name.endswith((".sh", ".bash", ".zsh")):
            continue
        in_heredoc = None
        in_python_c = False
        for line in text.splitlines():
            stripped = line.strip()
            if in_heredoc:
                if stripped == in_heredoc:
                    in_heredoc = None
                continue
            if in_python_c:
                if stripped.endswith('"') or stripped == '"' or stripped.endswith("'''") or stripped.endswith('"""'):
                    in_python_c = False
                continue
            heredoc = re.search(r"<<[-]?['\"]?(\w+)['\"]?", stripped)
            if heredoc:
                in_heredoc = heredoc.group(1)
            if re.search(r"""python3?\s+-c\s+["']""", stripped):
                opens = stripped.count('"') + stripped.count("'")
                in_python_c = opens % 2 == 1
                continue
            if not stripped or stripped.startswith("#"):
                continue
            if FUNCTION_RE.match(stripped) or stripped.startswith(("const ", "let ", "var ", "export ", "import ")):
                continue
            if PYTHON_LINE_RE.match(stripped):
                continue
            if "=" in stripped.split()[0] and not stripped.split()[0].startswith(("http", "./")):
                continue
            for binary, detail in _binaries_from_command(stripped):
                if binary not in defined:
                    facts.binaries.append(BinaryUse(binary, path, detail))


def is_declared_binary(name: str, facts: ExtractedFacts) -> bool:
    if name in SAFE_BINARIES:
        return True
    if name.startswith("python3."):
        return True
    declared = _normalized_deps(facts.package_deps)
    package = BIN_FROM_PACKAGE.get(name, name)
    return package.lower() in declared or name.lower() in declared


def _normalized_deps(deps: set[str]) -> set[str]:
    names: set[str] = set()
    for dep in deps:
        base = dep.split("[", 1)[0].lower()
        names.add(base)
        if "/" in base:
            names.add(base.split("/", 1)[0].lstrip("@"))
            names.add(base.rsplit("/", 1)[-1])
    return names


REDIRECT_RE = re.compile(r"(?:\d*)(?:>>|&>|>)\s*\S+|\d*>&\d+")


def _binaries_from_command(command: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    command = _strip_redirections(command)
    for piece in _split_shell_commands(command):
        piece = piece.strip()
        if not piece or piece.startswith("#"):
            continue
        if piece.startswith("npx "):
            continue
        try:
            tokens = shlex.split(piece, posix=True)
        except ValueError:
            tokens = piece.split()
        if not tokens:
            continue
        tokens = list(tokens)
        while tokens and "=" in tokens[0] and not tokens[0].startswith("-"):
            tokens = tokens[1:]
        if not tokens:
            continue
        first = tokens[0]
        if first in {"env", "command", "exec"} and len(tokens) > 1:
            first = tokens[1]
        if first in {"echo", "printf"}:
            continue
        if LOCAL_BIN_RE.search(first.replace("\\", "/")):
            continue
        binary = os.path.basename(first)
        if binary.startswith("-") or binary in SAFE_BINARIES:
            continue
        if len(binary) < 3 or binary[0].isdigit():
            continue
        if not re.match(r"^[A-Za-z][A-Za-z0-9_+-]*$", binary):
            continue
        found.append((binary, piece[:160]))
    return found


def _strip_redirections(command: str) -> str:
    """Remove shell redirections so `/dev/null` is not parsed as a binary."""
    out: list[str] = []
    quote = None
    i = 0
    while i < len(command):
        ch = command[i]
        if quote:
            out.append(ch)
            if ch == quote and (i == 0 or command[i - 1] != "\\"):
                quote = None
            i += 1
            continue
        if ch in {'"', "'"}:
            quote = ch
            out.append(ch)
            i += 1
            continue
        match = REDIRECT_RE.match(command, i)
        if match:
            i = match.end()
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _split_shell_commands(command: str) -> list[str]:
    """Split on shell operators without breaking quoted strings."""
    pieces: list[str] = []
    buf: list[str] = []
    quote = None
    i = 0
    while i < len(command):
        ch = command[i]
        if quote:
            buf.append(ch)
            if ch == quote and (i == 0 or command[i - 1] != "\\"):
                quote = None
            i += 1
            continue
        if ch in {'"', "'"}:
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if command.startswith("&&", i) or command.startswith("||", i):
            piece = "".join(buf).strip()
            if piece:
                pieces.append(piece)
            buf = []
            i += 2
            continue
        if ch in {";", "|", "\n"}:
            piece = "".join(buf).strip()
            if piece:
                pieces.append(piece)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    piece = "".join(buf).strip()
    if piece:
        pieces.append(piece)
    return pieces or [command]
