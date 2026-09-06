"""Derived readiness bucket and bootstrap actions."""

from __future__ import annotations

from clone_trap.analysis.score import BOOTSTRAP_MIN
from clone_trap.models.enums import Category, Severity, Verdict
from clone_trap.models.finding import Finding
from clone_trap.models.report import BootstrapAction

BLOCKING_CATEGORIES = {
    Category.ENVIRONMENT,
    Category.SERVICES,
    Category.ARTIFACTS,
}

STAGE_TO_ACTION = {
    "clone": "clone",
    "install": "install",
    "generate": "generate",
    "configure": "configure",
    "start_services": "start",
    "run": "run",
}


def derive_readiness(findings: list[Finding]) -> tuple[str, str]:
    confirmed = [item for item in findings if item.verdict == Verdict.CONFIRMED_TRAP]
    likely = [item for item in findings if item.verdict == Verdict.LIKELY_TRAP]
    assumptions = [
        item for item in findings if item.verdict == Verdict.ENVIRONMENT_ASSUMPTION
    ]
    blocking = [
        item
        for item in confirmed
        if item.category in BLOCKING_CATEGORIES
        or (item.category == Category.LOCALITY and item.severity == Severity.HIGH)
    ]
    if blocking:
        top = blocking[0]
        return (
            "high_risk",
            f"{top.title} — this repository appears to require something a clean clone may not have.",
        )
    if confirmed:
        top = confirmed[0]
        return (
            "hidden_assumptions",
            f"{top.title} Multiple signals suggest an undocumented dependency.",
        )
    if likely:
        top = likely[0]
        return (
            "hidden_assumptions",
            f"{top.title} Multiple signals suggest an undocumented dependency.",
        )
    if assumptions or findings:
        top = (assumptions or findings)[0]
        return (
            "mostly_portable",
            f"{top.title} Documented or weak signals only; still worth knowing.",
        )
    return (
        "ready",
        "No high-confidence portability gaps were found in the scanned working tree.",
    )


def build_bootstrap(findings: list[Finding]) -> list[BootstrapAction]:
    actions: list[BootstrapAction] = []
    for finding in findings:
        if finding.verdict == Verdict.CONFIRMED_TRAP or (
            finding.verdict == Verdict.LIKELY_TRAP and finding.confidence >= BOOTSTRAP_MIN
        ):
            requirement = finding.title
            if requirement.lower().startswith("undocumented "):
                requirement = requirement.split(" ", 1)[1]
            actions.append(
                BootstrapAction(
                    action=STAGE_TO_ACTION.get(finding.clone_stage.value, finding.clone_stage.value),
                    requirement=requirement,
                    confidence=finding.confidence,
                    finding_ids=[finding.id],
                )
            )
    return actions[:8]
