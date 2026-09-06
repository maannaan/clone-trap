"""Display caps applied after scoring."""

from __future__ import annotations

from clone_trap.models.enums import Verdict
from clone_trap.models.finding import Finding

BAND_CAPS = {
    Verdict.CONFIRMED_TRAP: 8,
    Verdict.LIKELY_TRAP: 8,
    Verdict.ENVIRONMENT_ASSUMPTION: 8,
    Verdict.INFORMATIONAL: 5,
}

VERDICT_ORDER = {
    Verdict.CONFIRMED_TRAP: 0,
    Verdict.LIKELY_TRAP: 1,
    Verdict.ENVIRONMENT_ASSUMPTION: 2,
    Verdict.INFORMATIONAL: 3,
}


def rank_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(
        findings,
        key=lambda item: (VERDICT_ORDER[item.verdict], -item.confidence, item.id),
    )


def apply_caps(findings: list[Finding], max_findings: int) -> tuple[list[Finding], bool]:
    ranked = rank_findings(findings)
    kept: list[Finding] = []
    counts = {verdict: 0 for verdict in Verdict}
    truncated = False
    for finding in ranked:
        if counts[finding.verdict] >= BAND_CAPS[finding.verdict]:
            truncated = True
            continue
        if len(kept) >= max_findings:
            truncated = True
            break
        kept.append(finding)
        counts[finding.verdict] += 1
    if len(ranked) > len(kept):
        truncated = True
    return kept, truncated
