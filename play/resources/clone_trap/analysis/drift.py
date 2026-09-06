"""Documentation drift synthesis."""

from __future__ import annotations

from clone_trap.extractors.facts import ExtractedFacts
from clone_trap.models.enums import Verdict
from clone_trap.models.finding import Finding
from clone_trap.models.report import DocumentationDrift

TRAP_VERDICTS = {Verdict.CONFIRMED_TRAP, Verdict.LIKELY_TRAP}


def build_drift(facts: ExtractedFacts, findings: list[Finding]) -> DocumentationDrift:
    documented_setup = list(facts.doc_commands[:12])
    undocumented: list[str] = []
    for finding in findings:
        if finding.verdict in TRAP_VERDICTS:
            label = finding.title
            if label not in undocumented:
                undocumented.append(label)
    unused: list[str] = []
    used_services = {hit.name for hit in facts.service_hits}
    for service in facts.doc_services:
        if service == "sqlite":
            continue
        if service not in used_services and not any(
            infer == service
            for infer in (
                item.name.lower() for item in facts.compose_services
            )
        ):
            unused.append(service)
    return DocumentationDrift(
        documented_setup=documented_setup,
        undocumented_requirements=undocumented[:12],
        documented_but_unused=unused[:6],
    )
