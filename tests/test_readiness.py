from clone_trap.analysis.readiness import build_bootstrap, derive_readiness
from clone_trap.models.enums import Category, CloneStage, Severity, Verdict
from clone_trap.models.finding import Finding


def _finding(verdict: Verdict, confidence: float = 0.9, title: str = "Undocumented REDIS_URL") -> Finding:
    return Finding(
        id="env.redis_url.undocumented",
        category=Category.ENVIRONMENT,
        verdict=verdict,
        severity=Severity.HIGH,
        confidence=confidence,
        title=title,
        clone_stage=CloneStage.CONFIGURE,
    )


def test_readiness_buckets():
    assert derive_readiness([])[0] == "ready"
    assert derive_readiness([_finding(Verdict.INFORMATIONAL, 0.45)])[0] == "mostly_portable"
    assert derive_readiness([_finding(Verdict.ENVIRONMENT_ASSUMPTION, 0.5)])[0] == "mostly_portable"
    assert derive_readiness([_finding(Verdict.LIKELY_TRAP, 0.7)])[0] == "hidden_assumptions"
    assert derive_readiness([_finding(Verdict.CONFIRMED_TRAP, 0.91)])[0] == "high_risk"


def test_toolchain_confirmed_is_not_high_risk():
    finding = Finding(
        id="toolchain.binary.afconvert",
        category=Category.TOOLCHAIN,
        verdict=Verdict.CONFIRMED_TRAP,
        severity=Severity.MEDIUM,
        confidence=0.9,
        title="Undeclared tool used in scripts: afconvert",
        clone_stage=CloneStage.INSTALL,
    )
    assert derive_readiness([finding])[0] == "hidden_assumptions"


def test_bootstrap_only_high_confidence():
    actions = build_bootstrap(
        [
            _finding(Verdict.CONFIRMED_TRAP, 0.91),
            _finding(Verdict.LIKELY_TRAP, 0.61, "Maybe tool"),
            _finding(Verdict.INFORMATIONAL, 0.4, "Note"),
        ]
    )
    assert len(actions) == 1
    assert actions[0].action == "configure"
    assert "REDIS_URL" in actions[0].requirement
