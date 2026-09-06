"""A scored portability finding."""

from __future__ import annotations

from dataclasses import dataclass, field

from clone_trap.models.enums import Category, CloneStage, Severity, Verdict
from clone_trap.models.evidence import EvidenceItem


@dataclass
class Finding:
    id: str
    category: Category
    verdict: Verdict
    severity: Severity
    confidence: float
    title: str
    evidence: list[EvidenceItem] = field(default_factory=list)
    counter_evidence: list[EvidenceItem] = field(default_factory=list)
    affected_files: list[str] = field(default_factory=list)
    why_it_matters: str = ""
    verification: str = ""
    remediation: str = ""
    clone_stage: CloneStage = CloneStage.RUN
    independent_source_kinds: int = 0
    has_undeclared_signal: bool = False
    test_only: bool = False
