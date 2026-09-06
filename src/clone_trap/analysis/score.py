"""Explainable additive scoring and verdict assignment."""

from __future__ import annotations

from dataclasses import dataclass

from clone_trap.models.enums import Verdict

CONFIRMED_MIN = 0.80
LIKELY_MIN = 0.60
INFORMATIONAL_MIN = 0.40
BOOTSTRAP_MIN = 0.70

AMBIENT_ENV = frozenset(
    {
        "NODE_ENV",
        "CI",
        "DEBUG",
        "PATH",
        "HOME",
        "USER",
        "USERNAME",
        "PWD",
        "OLDPWD",
        "SHELL",
        "TMPDIR",
        "TEMP",
        "TMP",
        "TERM",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TZ",
        "EDITOR",
        "VISUAL",
        "HOSTNAME",
        "HOST",
        "LOGNAME",
        "DISPLAY",
        "PYTHONPATH",
        "PYTHONUNBUFFERED",
        "PYTHONHASHSEED",
        "VIRTUAL_ENV",
        "CONDA_PREFIX",
        "CONDA_DEFAULT_ENV",
        "INIT_CWD",
        "SHLVL",
        "SSH_AUTH_SOCK",
        "FORCE_COLOR",
        "NO_COLOR",
        "TERM_PROGRAM",
        "DJANGO_SETTINGS_MODULE",
        "PYTEST_CURRENT_TEST",
        "PYTHONDONTWRITEBYTECODE",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
        "APPDATA",
        "LOCALAPPDATA",
    }
)


@dataclass
class ScoreInputs:
    in_startup: bool = False
    missing_from_docs: bool = False
    missing_from_declaration: bool = False
    no_fallback: bool = False
    multiple_files: bool = False
    ci_local_mismatch: bool = False
    documented: bool = False
    declared: bool = False
    optional: bool = False
    test_only: bool = False
    ambient: bool = False
    independent_source_kinds: int = 0
    has_undeclared_signal: bool = False
    documented_external: bool = False


def compute_confidence(inputs: ScoreInputs) -> float:
    score = 0.0
    if inputs.in_startup:
        score += 0.35
    elif not inputs.test_only:
        score += 0.20
    if inputs.missing_from_docs:
        score += 0.20
    if inputs.missing_from_declaration:
        score += 0.20
    if inputs.no_fallback:
        score += 0.15
    if inputs.multiple_files:
        score += 0.10
    if inputs.ci_local_mismatch:
        score += 0.10
    if inputs.documented:
        score -= 0.25
    if inputs.declared:
        score -= 0.25
    if inputs.optional:
        score -= 0.20
    if inputs.test_only:
        score -= 0.20
    if inputs.ambient:
        score -= 0.30
    return round(max(0.0, min(1.0, score)), 2)


def assign_verdict(confidence: float, inputs: ScoreInputs) -> Verdict | None:
    if inputs.ambient and confidence < LIKELY_MIN:
        return None
    if inputs.documented_external and not inputs.has_undeclared_signal:
        if confidence < INFORMATIONAL_MIN:
            return None
        return Verdict.ENVIRONMENT_ASSUMPTION
    two_sources = inputs.independent_source_kinds >= 2
    if (
        confidence >= CONFIRMED_MIN
        and two_sources
        and inputs.has_undeclared_signal
        and not inputs.test_only
    ):
        return Verdict.CONFIRMED_TRAP
    if LIKELY_MIN <= confidence < CONFIRMED_MIN or (
        two_sources and inputs.has_undeclared_signal and confidence >= LIKELY_MIN
    ):
        if inputs.documented_external and confidence < CONFIRMED_MIN:
            return Verdict.ENVIRONMENT_ASSUMPTION
        return Verdict.LIKELY_TRAP
    if inputs.documented_external:
        return Verdict.ENVIRONMENT_ASSUMPTION
    if INFORMATIONAL_MIN <= confidence < LIKELY_MIN:
        if inputs.independent_source_kinds <= 1 and not inputs.has_undeclared_signal:
            return Verdict.INFORMATIONAL
        if inputs.has_undeclared_signal and not inputs.test_only:
            return Verdict.ENVIRONMENT_ASSUMPTION
        return Verdict.INFORMATIONAL
    if confidence >= LIKELY_MIN and inputs.has_undeclared_signal and not two_sources:
        return Verdict.ENVIRONMENT_ASSUMPTION
    return None


def is_ambient_env(name: str) -> bool:
    if name in AMBIENT_ENV:
        return True
    return name.startswith("NPM_") or name.startswith("npm_")
