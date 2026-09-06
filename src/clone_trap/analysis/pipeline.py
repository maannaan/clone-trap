"""End-to-end analysis pipeline."""

from __future__ import annotations

from clone_trap.analysis.caps import apply_caps
from clone_trap.analysis.clone_path import build_clone_path
from clone_trap.analysis.drift import build_drift
from clone_trap.analysis.join import join_candidates
from clone_trap.analysis.readiness import build_bootstrap, derive_readiness
from clone_trap.extractors import extract_facts
from clone_trap.inventory import build_inventory
from clone_trap.models.report import AnalysisReport


def analyze_repository(repo_path: str, max_findings: int = 20) -> AnalysisReport:
    inventory = build_inventory(repo_path)
    facts = extract_facts(inventory)
    raw = join_candidates(inventory, facts)
    findings, truncated = apply_caps(raw, max_findings)
    readiness, reason = derive_readiness(findings)
    return AnalysisReport(
        repository=inventory.root,
        readiness=readiness,
        readiness_reason=reason,
        findings=findings,
        documentation_drift=build_drift(facts, findings),
        clone_path=build_clone_path(facts, findings),
        bootstrap_actions=build_bootstrap(findings),
        truncated=truncated or inventory.truncated,
    )
