from clone_trap.analysis.score import ScoreInputs, assign_verdict, compute_confidence
from clone_trap.models.enums import Verdict


def test_confirmed_trap_needs_two_sources():
    inputs = ScoreInputs(
        in_startup=True,
        missing_from_docs=True,
        missing_from_declaration=True,
        no_fallback=True,
        independent_source_kinds=2,
        has_undeclared_signal=True,
    )
    confidence = compute_confidence(inputs)
    assert confidence >= 0.80
    assert assign_verdict(confidence, inputs) == Verdict.CONFIRMED_TRAP


def test_single_source_cannot_confirm():
    inputs = ScoreInputs(
        in_startup=True,
        missing_from_docs=True,
        missing_from_declaration=True,
        no_fallback=True,
        independent_source_kinds=1,
        has_undeclared_signal=True,
    )
    confidence = compute_confidence(inputs)
    verdict = assign_verdict(confidence, inputs)
    assert verdict != Verdict.CONFIRMED_TRAP


def test_documented_and_declared_is_assumption_or_drop():
    inputs = ScoreInputs(
        in_startup=True,
        no_fallback=True,
        documented=True,
        declared=True,
        documented_external=True,
        independent_source_kinds=1,
        has_undeclared_signal=False,
    )
    confidence = compute_confidence(inputs)
    verdict = assign_verdict(confidence, inputs)
    assert verdict in {None, Verdict.ENVIRONMENT_ASSUMPTION}


def test_ambient_env_is_penalized():
    inputs = ScoreInputs(
        in_startup=True,
        ambient=True,
        missing_from_docs=True,
        missing_from_declaration=True,
        independent_source_kinds=2,
        has_undeclared_signal=True,
    )
    assert compute_confidence(inputs) < 0.80


def test_test_only_cannot_confirm():
    inputs = ScoreInputs(
        in_startup=True,
        missing_from_docs=True,
        missing_from_declaration=True,
        no_fallback=True,
        test_only=True,
        independent_source_kinds=2,
        has_undeclared_signal=True,
    )
    confidence = compute_confidence(inputs)
    assert assign_verdict(confidence, inputs) != Verdict.CONFIRMED_TRAP
