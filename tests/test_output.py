import json

from clone_trap.models.enums import Category, CloneStage, Severity, Verdict
from clone_trap.models.evidence import EvidenceItem
from clone_trap.models.finding import Finding
from clone_trap.models.report import AnalysisReport, DocumentationDrift
from clone_trap.output import render_json, render_text, report_to_dict


def _sample_report() -> AnalysisReport:
    finding = Finding(
        id="env.redis_url.undocumented",
        category=Category.ENVIRONMENT,
        verdict=Verdict.CONFIRMED_TRAP,
        severity=Severity.HIGH,
        confidence=0.91,
        title="Undocumented REDIS_URL",
        evidence=[EvidenceItem("source", "app.py", "reads REDIS_URL")],
        why_it_matters="A clean clone may start without REDIS_URL configured.",
        verification="Search for REDIS_URL",
        remediation="Consider documenting REDIS_URL.",
        clone_stage=CloneStage.CONFIGURE,
    )
    return AnalysisReport(
        repository="/tmp/repo",
        readiness="high_risk",
        readiness_reason="Undocumented REDIS_URL",
        findings=[finding],
        documentation_drift=DocumentationDrift(
            documented_setup=["npm install"],
            undocumented_requirements=["Undocumented REDIS_URL"],
        ),
    )


def test_json_schema_contract():
    payload = report_to_dict(_sample_report())
    assert payload["schema_version"] == 1
    assert payload["repository"] == "/tmp/repo"
    assert payload["readiness"] == "high_risk"
    assert payload["summary"]["confirmed_traps"] == 1
    assert payload["findings"][0]["id"] == "env.redis_url.undocumented"
    assert payload["findings"][0]["verdict"] == "confirmed_trap"
    assert "score" not in json.dumps(payload)
    text = render_json(_sample_report())
    json.loads(text)


def test_empty_report_is_honest():
    report = AnalysisReport(
        repository="/tmp/clean",
        readiness="ready",
        readiness_reason="No high-confidence portability gaps were found in the scanned working tree.",
    )
    payload = report_to_dict(report)
    assert payload["findings"] == []
    assert payload["bootstrap_actions"] == []
    assert payload["summary"]["confirmed_traps"] == 0
    text = render_text(report)
    assert "will definitely fail" not in text.lower()
    assert "the repository is incomplete" not in text.lower()
    assert "Portability evidence only" in text
