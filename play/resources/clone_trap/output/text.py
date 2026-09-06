"""Human-readable text output."""

from __future__ import annotations

from typing import TextIO

from clone_trap.models.enums import Verdict
from clone_trap.models.finding import Finding
from clone_trap.models.report import AnalysisReport

FOOTER = (
    "Portability evidence only — not a guarantee the clone will fail or succeed."
)

READINESS_LABELS = {
    "ready": "READY",
    "mostly_portable": "MOSTLY PORTABLE",
    "hidden_assumptions": "HAS HIDDEN ASSUMPTIONS",
    "high_risk": "HIGH RISK TO CLONE",
}

VERDICT_HEADINGS = {
    Verdict.CONFIRMED_TRAP: "Confirmed traps",
    Verdict.LIKELY_TRAP: "Likely traps",
    Verdict.ENVIRONMENT_ASSUMPTION: "Environment assumptions",
    Verdict.INFORMATIONAL: "Informational findings",
}


def render_text(report: AnalysisReport, stream: TextIO | None = None) -> str:
    lines = [
        "Clone Trap",
        "If a clean machine clones this repository, what hidden assumptions could prevent it from working?",
        "",
        f"Repository: {report.repository}",
        "",
        f"Readiness: {READINESS_LABELS.get(report.readiness, report.readiness.upper())}",
        report.readiness_reason,
    ]

    drift = report.documentation_drift
    lines.extend(["", "Documentation drift"])
    if drift.documented_setup:
        lines.append("  Documented setup:")
        for command in drift.documented_setup:
            lines.append(f"    {command}")
    else:
        lines.append("  No setup commands were extracted from documentation.")
    if drift.undocumented_requirements:
        lines.append("  Appears required but not documented:")
        for item in drift.undocumented_requirements:
            lines.append(f"    {item}")
    else:
        lines.append("  No undocumented requirements were confirmed.")
    if drift.documented_but_unused:
        lines.append("  Documented but unused in scanned source:")
        for item in drift.documented_but_unused:
            lines.append(f"    {item}")

    grouped: dict[Verdict, list[Finding]] = {verdict: [] for verdict in Verdict}
    for finding in report.findings:
        grouped[finding.verdict].append(finding)

    for verdict in (
        Verdict.CONFIRMED_TRAP,
        Verdict.LIKELY_TRAP,
        Verdict.ENVIRONMENT_ASSUMPTION,
        Verdict.INFORMATIONAL,
    ):
        items = grouped[verdict]
        if not items:
            continue
        lines.extend(["", VERDICT_HEADINGS[verdict]])
        for finding in items:
            lines.append("")
            lines.append(finding.title)
            lines.append(
                f"  {verdict.value} · {finding.severity.value} · confidence {finding.confidence:.2f}"
            )
            for evidence in finding.evidence[:4]:
                location = f"{evidence.path}: " if evidence.path else ""
                lines.append(f"  {location}{evidence.detail}")
            if finding.why_it_matters:
                lines.append(f"  Why this matters: {finding.why_it_matters}")
            if finding.verification:
                lines.append(f"  Verify: {finding.verification}")
            if finding.remediation:
                lines.append(f"  Consider: {finding.remediation}")

    if report.bootstrap_actions:
        lines.extend(["", "Suggested setup actions"])
        for action in report.bootstrap_actions:
            lines.append(
                f"  {action.action}: {action.requirement} (confidence {action.confidence:.2f})"
            )

    if report.clone_path:
        lines.extend(["", "Clone path"])
        for stage in report.clone_path:
            mark = "documented" if stage.documented else "not documented"
            extra = f" · {len(stage.finding_ids)} finding(s)" if stage.finding_ids else ""
            lines.append(f"  {stage.stage.value}: {mark}{extra}")

    if not report.findings:
        lines.extend(
            [
                "",
                "No high-confidence portability gaps were found.",
                "This is evidence from the working tree, not a safety guarantee.",
            ]
        )

    if report.truncated:
        lines.extend(["", "Output was capped; more candidates were scored than shown."])

    lines.extend(["", FOOTER])
    text = "\n".join(lines) + "\n"
    if stream is not None:
        stream.write(text)
    return text
