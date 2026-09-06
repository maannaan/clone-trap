"""Top-level analysis report."""

from __future__ import annotations

from dataclasses import dataclass, field

from clone_trap.models.enums import CloneStage, Verdict
from clone_trap.models.finding import Finding


@dataclass
class DocumentationDrift:
    documented_setup: list[str] = field(default_factory=list)
    undocumented_requirements: list[str] = field(default_factory=list)
    documented_but_unused: list[str] = field(default_factory=list)


@dataclass
class ClonePathStage:
    stage: CloneStage
    documented: bool
    finding_ids: list[str] = field(default_factory=list)


@dataclass
class BootstrapAction:
    action: str
    requirement: str
    confidence: float
    finding_ids: list[str] = field(default_factory=list)


@dataclass
class AnalysisReport:
    repository: str
    readiness: str
    readiness_reason: str
    findings: list[Finding] = field(default_factory=list)
    documentation_drift: DocumentationDrift = field(default_factory=DocumentationDrift)
    clone_path: list[ClonePathStage] = field(default_factory=list)
    bootstrap_actions: list[BootstrapAction] = field(default_factory=list)
    truncated: bool = False

    def summary(self) -> dict[str, int]:
        counts = {
            "confirmed_traps": 0,
            "likely_traps": 0,
            "environment_assumptions": 0,
            "informational": 0,
        }
        mapping = {
            Verdict.CONFIRMED_TRAP: "confirmed_traps",
            Verdict.LIKELY_TRAP: "likely_traps",
            Verdict.ENVIRONMENT_ASSUMPTION: "environment_assumptions",
            Verdict.INFORMATIONAL: "informational",
        }
        for finding in self.findings:
            counts[mapping[finding.verdict]] += 1
        return counts
