"""Machine-readable JSON output."""

from __future__ import annotations

import json
from typing import Any, TextIO

from clone_trap.models.evidence import EvidenceItem
from clone_trap.models.finding import Finding
from clone_trap.models.report import AnalysisReport, BootstrapAction, ClonePathStage


def report_to_dict(report: AnalysisReport) -> dict[str, Any]:
    """Serialize the full report. No truncation here beyond report.truncated."""
    return {
        "schema_version": 1,
        "repository": report.repository,
        "readiness": report.readiness,
        "readiness_reason": report.readiness_reason,
        "summary": report.summary(),
        "documentation_drift": {
            "documented_setup": list(report.documentation_drift.documented_setup),
            "undocumented_requirements": list(
                report.documentation_drift.undocumented_requirements
            ),
            "documented_but_unused": list(
                report.documentation_drift.documented_but_unused
            ),
        },
        "clone_path": [_path_to_dict(stage) for stage in report.clone_path],
        "bootstrap_actions": [
            _action_to_dict(action) for action in report.bootstrap_actions
        ],
        "findings": [_finding_to_dict(finding) for finding in report.findings],
        "truncated": report.truncated,
    }


def render_json(report: AnalysisReport, stream: TextIO | None = None) -> str:
    """Serialize the report and optionally write it."""
    text = json.dumps(report_to_dict(report), indent=2, ensure_ascii=False)
    if stream is not None:
        stream.write(text)
        if not text.endswith("\n"):
            stream.write("\n")
    return text


def _finding_to_dict(finding: Finding) -> dict[str, Any]:
    return {
        "id": finding.id,
        "category": finding.category.value,
        "verdict": finding.verdict.value,
        "severity": finding.severity.value,
        "confidence": finding.confidence,
        "title": finding.title,
        "evidence": [_evidence_to_dict(item) for item in finding.evidence],
        "counter_evidence": [
            _evidence_to_dict(item) for item in finding.counter_evidence
        ],
        "affected_files": list(finding.affected_files),
        "why_it_matters": finding.why_it_matters,
        "verification": finding.verification,
        "remediation": finding.remediation,
        "clone_stage": finding.clone_stage.value,
    }


def _evidence_to_dict(item: EvidenceItem) -> dict[str, Any]:
    return {
        "source": item.source,
        "path": item.path,
        "detail": item.detail,
    }


def _path_to_dict(stage: ClonePathStage) -> dict[str, Any]:
    return {
        "stage": stage.stage.value,
        "documented": stage.documented,
        "finding_ids": list(stage.finding_ids),
    }


def _action_to_dict(action: BootstrapAction) -> dict[str, Any]:
    return {
        "action": action.action,
        "requirement": action.requirement,
        "confidence": action.confidence,
        "finding_ids": list(action.finding_ids),
    }
