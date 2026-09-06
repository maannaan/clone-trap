"""Cross-signal join: env, services, artifacts, toolchain, locality."""

from __future__ import annotations

import os
import re
from collections import defaultdict

from clone_trap.analysis.score import ScoreInputs, assign_verdict, compute_confidence, is_ambient_env
from clone_trap.extractors.compose import infer_service
from clone_trap.extractors.facts import ExtractedFacts
from clone_trap.extractors.toolchain import is_declared_binary
from clone_trap.git import is_ignored
from clone_trap.models.enums import Category, CloneStage, FileClass, Severity, Verdict
from clone_trap.models.evidence import EvidenceItem
from clone_trap.models.finding import Finding
from clone_trap.models.inventory import Inventory

SQLITE_RE = re.compile(r"sqlite", re.I)


def join_candidates(inventory: Inventory, facts: ExtractedFacts) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_join_env(facts))
    findings.extend(_join_services(facts))
    findings.extend(_join_artifacts(inventory, facts))
    findings.extend(_join_toolchain(facts))
    findings.extend(_join_locality(inventory, facts))
    return _dedupe([item for item in findings if item is not None])


def _dedupe(findings: list[Finding]) -> list[Finding]:
    seen: dict[str, Finding] = {}
    for finding in findings:
        current = seen.get(finding.id)
        if current is None or finding.confidence > current.confidence:
            seen[finding.id] = finding
    return list(seen.values())


def _join_env(facts: ExtractedFacts) -> list[Finding]:
    grouped: dict[str, list] = defaultdict(list)
    for usage in facts.env_usages:
        if is_ambient_env(usage.name):
            continue
        grouped[usage.name].append(usage)

    findings: list[Finding] = []
    for name, usages in grouped.items():
        files = sorted({item.path for item in usages})
        kinds = {item.file_class for item in usages}
        if FileClass.SOURCE in kinds or FileClass.CONFIG in kinds:
            kinds.add(FileClass.SOURCE)
        test_only = all(item.file_class == FileClass.TEST for item in usages)
        if test_only:
            continue
        in_startup = any(item.in_startup for item in usages)
        has_default = all(item.has_default for item in usages)
        documented = name in facts.doc_env_names
        declared = name in facts.env_example_names or any(
            name in service.env_names for service in facts.compose_services
        )
        if documented and declared:
            continue
        missing_docs = not documented
        missing_decl = not declared
        source_kinds = 1
        if FileClass.SOURCE in kinds or FileClass.CONFIG in kinds:
            source_kinds = 1
        undeclared = missing_decl or missing_docs
        if missing_decl:
            source_kinds += 1
        if missing_docs and not documented:
            source_kinds += 1 if missing_decl else 1
        # Independent kinds: source/config counts as one; missing declaration is a second kind.
        independent = 1
        if FileClass.SOURCE in kinds or FileClass.CONFIG in kinds or FileClass.SCRIPT in kinds:
            independent = 1
        if missing_decl:
            independent += 1
        if missing_docs and documented is False:
            # docs absence is a signal but not a second file kind unless we also lack example
            pass
        if len(files) > 1:
            independent = max(independent, 2 if (missing_decl or missing_docs) else 1)

        inputs = ScoreInputs(
            in_startup=in_startup,
            missing_from_docs=missing_docs,
            missing_from_declaration=missing_decl,
            no_fallback=not has_default,
            multiple_files=len(files) > 1,
            documented=documented,
            declared=declared,
            optional=has_default,
            test_only=test_only,
            ambient=is_ambient_env(name),
            independent_source_kinds=independent,
            has_undeclared_signal=undeclared and not test_only,
            documented_external=documented and declared,
        )
        confidence = compute_confidence(inputs)
        verdict = assign_verdict(confidence, inputs)
        if verdict is None:
            continue
        evidence = [
            EvidenceItem("source", usage.path, f"reads {name}")
            for usage in usages[:5]
        ]
        counter: list[EvidenceItem] = []
        if documented:
            counter.append(EvidenceItem("docs", facts.doc_files[0] if facts.doc_files else "", f"{name} is mentioned in documentation"))
        if declared and name in facts.env_example_names:
            counter.append(
                EvidenceItem(
                    "env_example",
                    facts.env_example_files[0] if facts.env_example_files else "",
                    f"{name} appears in an env example file",
                )
            )
        findings.append(
            Finding(
                id=f"env.{name.lower()}.undocumented" if undeclared else f"env.{name.lower()}",
                category=Category.ENVIRONMENT,
                verdict=verdict,
                severity=_severity(in_startup, has_default, test_only),
                confidence=confidence,
                title=f"Undocumented {name}" if undeclared and not documented else f"{name} environment assumption",
                evidence=evidence,
                counter_evidence=counter,
                affected_files=files,
                why_it_matters=(
                    f"A clean clone may start without {name} configured."
                    if undeclared
                    else f"This repository appears to read {name} from the environment."
                ),
                verification=f"Search the working tree for {name} and compare README / .env.example.",
                remediation=f"Consider documenting {name} in setup docs and an env example file."
                if undeclared
                else f"Confirm how a new machine should obtain {name}.",
                clone_stage=CloneStage.CONFIGURE,
                independent_source_kinds=independent,
                has_undeclared_signal=undeclared,
                test_only=test_only,
            )
        )
    return findings


def _join_services(facts: ExtractedFacts) -> list[Finding]:
    grouped: dict[str, list] = defaultdict(list)
    for hit in facts.service_hits:
        grouped[hit.name].append(hit)

    compose_services = set()
    for service in facts.compose_services:
        inferred = infer_service(service.name, service.image)
        if inferred:
            compose_services.add(inferred)
        compose_services.add(service.name.lower())

    findings: list[Finding] = []
    for name, hits in grouped.items():
        if name == "sqlite":
            continue
        if name == "postgres" and _looks_like_sqlite(facts):
            continue
        files = sorted({hit.path for hit in hits})
        kinds = {hit.file_class for hit in hits}
        test_only = all(hit.file_class == FileClass.TEST for hit in hits)
        if test_only:
            continue
        in_startup = any(hit.file_class in {FileClass.SOURCE, FileClass.CONFIG} for hit in hits)
        documented = name in facts.doc_services
        declared = name in compose_services or name in facts.ci_services
        if declared:
            continue
        runtime_kinds = {hit.kind for hit in hits}
        strong = bool(runtime_kinds & {"import", "url", "env", "port"})
        independent = 1
        if len(runtime_kinds) >= 2:
            independent += 1
        if not declared:
            independent += 1
        undeclared = not declared and not documented
        inputs = ScoreInputs(
            in_startup=in_startup and not test_only,
            missing_from_docs=not documented,
            missing_from_declaration=not declared,
            no_fallback=True,
            multiple_files=len(files) > 1,
            documented=documented,
            declared=declared,
            optional=False,
            test_only=test_only,
            independent_source_kinds=independent,
            has_undeclared_signal=undeclared,
            documented_external=(documented or declared) and not undeclared,
        )
        confidence = compute_confidence(inputs)
        verdict = assign_verdict(confidence, inputs)
        if verdict is None:
            continue
        if not strong:
            continue
        evidence = [
            EvidenceItem("source", hit.path, f"{name} {hit.kind} signal")
            for hit in hits[:5]
        ]
        counter: list[EvidenceItem] = []
        if declared:
            path = facts.compose_files[0] if facts.compose_files else ""
            counter.append(EvidenceItem("compose", path, f"{name} appears in Compose or CI services"))
        if documented:
            counter.append(
                EvidenceItem("docs", facts.doc_files[0] if facts.doc_files else "", f"{name} is mentioned in documentation")
            )
        title = (
            f"Undocumented {name} dependency"
            if undeclared
            else f"Local {name} service assumption"
        )
        findings.append(
            Finding(
                id=f"service.{name}.{'undocumented' if undeclared else 'assumed'}",
                category=Category.SERVICES,
                verdict=verdict,
                severity=_severity(in_startup, False, test_only),
                confidence=confidence,
                title=title,
                evidence=evidence,
                counter_evidence=counter,
                affected_files=files,
                why_it_matters=(
                    f"A clean clone may start without the required {name} service."
                    if undeclared
                    else f"This repository appears to depend on {name} outside the repository tree."
                ),
                verification=f"Check docker-compose, CI services, and README for {name}.",
                remediation=(
                    f"Consider documenting {name} and providing a Compose service or hosted alternative."
                    if undeclared
                    else f"Confirm {name} is available before running the application."
                ),
                clone_stage=CloneStage.START_SERVICES,
                independent_source_kinds=independent,
                has_undeclared_signal=undeclared,
                test_only=test_only,
            )
        )
    return findings


def _join_artifacts(inventory: Inventory, facts: ExtractedFacts) -> list[Finding]:
    findings: list[Finding] = []
    generate_blob = " ".join(facts.generate_scripts + facts.doc_generate_commands).lower()
    documented_generate = bool(generate_blob)

    for ref in facts.path_references:
        target = ref.path
        basename = os.path.basename(target)
        if basename.lower() in {".env", ".env.local"}:
            continue
        if not re.search(r"\.[A-Za-z0-9]{1,12}$", target) and not any(
            token in target.lower() for token in ("generated", "codegen")
        ):
            continue
        tracked = target in inventory.tracked_paths
        exists_ignored = target in inventory.ignored_existing or is_ignored(
            inventory.root, target
        )
        on_disk = os.path.isfile(os.path.join(inventory.root, target))
        generated_hint = any(token in target.lower() for token in ("generated", "codegen", "prisma"))
        if tracked:
            continue
        if documented_generate and generated_hint:
            continue
        if on_disk and not exists_ignored and not generated_hint:
            continue
        if not exists_ignored and not generated_hint:
            continue
        test_only = ref.file_class == FileClass.TEST
        undeclared = not documented_generate
        independent = 2 if (exists_ignored or generated_hint) and undeclared else 1
        inputs = ScoreInputs(
            in_startup=ref.file_class in {FileClass.SOURCE, FileClass.CONFIG},
            missing_from_docs=undeclared,
            missing_from_declaration=True,
            no_fallback=True,
            documented=documented_generate,
            declared=documented_generate,
            test_only=test_only,
            independent_source_kinds=independent,
            has_undeclared_signal=undeclared,
        )
        confidence = compute_confidence(inputs)
        verdict = assign_verdict(confidence, inputs)
        if verdict is None:
            continue
        findings.append(
            Finding(
                id=f"artifact.{_slug(target)}",
                category=Category.ARTIFACTS,
                verdict=verdict,
                severity=Severity.MEDIUM if generated_hint else Severity.LOW,
                confidence=confidence,
                title=f"Referenced file may be missing after a clean clone: {target}",
                evidence=[
                    EvidenceItem("source", ref.referenced_from, ref.detail),
                    EvidenceItem(
                        "gitignore" if exists_ignored else "filesystem",
                        target,
                        "ignored or absent from the tracked tree",
                    ),
                ],
                counter_evidence=[],
                affected_files=[ref.referenced_from, target],
                why_it_matters="A clean clone may lack a generated or ignored file the author has locally.",
                verification=f"Confirm whether {target} is tracked, generated, or gitignored.",
                remediation="Consider documenting the generate step or committing a placeholder.",
                clone_stage=CloneStage.GENERATE,
                independent_source_kinds=independent,
                has_undeclared_signal=undeclared,
                test_only=test_only,
            )
        )

    for submodule in inventory.submodules:
        if submodule.get("state") != "uninitialized":
            continue
        path = submodule.get("path", "")
        inputs = ScoreInputs(
            in_startup=True,
            missing_from_docs="submodule" not in " ".join(facts.doc_commands).lower(),
            missing_from_declaration=False,
            no_fallback=True,
            independent_source_kinds=2,
            has_undeclared_signal=True,
        )
        confidence = compute_confidence(inputs)
        verdict = assign_verdict(confidence, inputs)
        if verdict is None:
            verdict = Verdict.LIKELY_TRAP
        findings.append(
            Finding(
                id=f"artifact.submodule.{_slug(path)}",
                category=Category.ARTIFACTS,
                verdict=verdict,
                severity=Severity.HIGH,
                confidence=max(confidence, 0.8),
                title=f"Git submodule is uninitialized: {path}",
                evidence=[
                    EvidenceItem("git", ".gitmodules", f"submodule {path} is uninitialized"),
                ],
                counter_evidence=[],
                affected_files=[path, ".gitmodules"],
                why_it_matters="A plain git clone does not fetch submodule contents unless initialized.",
                verification="Run a read-only `git submodule status` and inspect `.gitmodules`.",
                remediation="Consider documenting `git submodule update --init`.",
                clone_stage=CloneStage.CLONE,
                independent_source_kinds=2,
                has_undeclared_signal=True,
            )
        )
    return findings


def _join_toolchain(facts: ExtractedFacts) -> list[Finding]:
    findings: list[Finding] = []
    seen_bins: set[str] = set()
    for binary in facts.binaries:
        if binary.name in seen_bins or is_declared_binary(binary.name, facts):
            continue
        seen_bins.add(binary.name)
        inputs = ScoreInputs(
            in_startup=False,
            missing_from_docs=binary.name.lower() not in " ".join(facts.doc_commands).lower(),
            missing_from_declaration=True,
            no_fallback=True,
            independent_source_kinds=1,
            has_undeclared_signal=True,
        )
        confidence = compute_confidence(inputs)
        verdict = assign_verdict(confidence, inputs)
        if verdict is None:
            continue
        findings.append(
            Finding(
                id=f"toolchain.binary.{_slug(binary.name)}",
                category=Category.TOOLCHAIN,
                verdict=verdict,
                severity=Severity.MEDIUM,
                confidence=confidence,
                title=f"Undeclared tool used in scripts: {binary.name}",
                evidence=[
                    EvidenceItem("script", binary.path, binary.detail),
                    EvidenceItem("manifest", facts.manifests[0] if facts.manifests else "", f"{binary.name} is not a declared dependency"),
                ],
                counter_evidence=[],
                affected_files=[binary.path],
                why_it_matters=f"A clean machine may lack `{binary.name}` if it was only installed globally on the author's machine.",
                verification=f"Check package manifests and setup docs for {binary.name}.",
                remediation=f"Consider declaring {binary.name} as a project dependency or documenting how to install it.",
                clone_stage=CloneStage.INSTALL,
                independent_source_kinds=1,
                has_undeclared_signal=True,
            )
        )

    findings.extend(_version_mismatches(facts))

    for host in facts.private_registries:
        findings.append(
            Finding(
                id=f"toolchain.registry.{_slug(host)}",
                category=Category.TOOLCHAIN,
                verdict=Verdict.ENVIRONMENT_ASSUMPTION,
                severity=Severity.MEDIUM,
                confidence=0.7,
                title=f"Private package registry assumption: {host}",
                evidence=[EvidenceItem("manifest", "", f"registry host {host} is not a public default")],
                counter_evidence=[],
                affected_files=[],
                why_it_matters="A clean clone may be unable to install packages without registry credentials.",
                verification="Inspect .npmrc and package.json publishConfig.",
                remediation="Document how a new machine authenticates to this registry.",
                clone_stage=CloneStage.INSTALL,
                independent_source_kinds=1,
                has_undeclared_signal=True,
            )
        )
    return findings


def _version_mismatches(facts: ExtractedFacts) -> list[Finding]:
    findings: list[Finding] = []
    by_family: dict[str, list] = defaultdict(list)
    for pin in facts.version_pins + facts.ci_versions:
        by_family[pin.family].append(pin)
    for family, pins in by_family.items():
        if len(pins) < 2:
            continue
        numbers = []
        for pin in pins:
            match = re.search(r"(\d+)(?:\.(\d+))?", pin.value)
            if match:
                numbers.append((int(match.group(1)), int(match.group(2) or 0), pin))
        if len(numbers) < 2:
            continue
        majors = {item[0] for item in numbers}
        minors = {(item[0], item[1]) for item in numbers}
        conflict = False
        if family == "python" and facts.python_requires.startswith(">="):
            required = _parse_tuple(facts.python_requires)
            for major, minor, pin in numbers:
                if pin.source == "version_file" and (major, minor) < required:
                    conflict = True
        if len(majors) > 1:
            conflict = True
        if not conflict and family == "node" and len(minors) > 1 and max(m[0] for m in minors) - min(m[0] for m in minors) >= 2:
            conflict = True
        if not conflict:
            continue
        files = sorted({pin.path for pin in pins})
        inputs = ScoreInputs(
            in_startup=True,
            missing_from_docs=False,
            missing_from_declaration=False,
            ci_local_mismatch=any(pin.source == "ci" for pin in pins),
            no_fallback=True,
            multiple_files=True,
            independent_source_kinds=2,
            has_undeclared_signal=True,
        )
        confidence = compute_confidence(inputs)
        verdict = assign_verdict(confidence, inputs) or Verdict.LIKELY_TRAP
        findings.append(
            Finding(
                id=f"toolchain.version.{family}",
                category=Category.TOOLCHAIN,
                verdict=verdict,
                severity=Severity.MEDIUM,
                confidence=max(confidence, 0.7),
                title=f"{family} version pins appear to disagree",
                evidence=[
                    EvidenceItem("version", pin.path, f"{pin.source}: {pin.value}")
                    for pin in pins
                ],
                counter_evidence=[],
                affected_files=files,
                why_it_matters="A clean clone may install a different runtime than CI or the lockfile expects.",
                verification=f"Compare {family} version files, manifests, and CI configuration.",
                remediation=f"Consider aligning {family} version declarations.",
                clone_stage=CloneStage.INSTALL,
                independent_source_kinds=2,
                has_undeclared_signal=True,
            )
        )
    return findings


def _join_locality(inventory: Inventory, facts: ExtractedFacts) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[str] = set()
    for ref in facts.absolute_paths:
        key = f"abs:{ref.referenced_from}:{ref.path}"
        if key in seen:
            continue
        seen.add(key)
        if ref.file_class == FileClass.DOCS:
            continue
        inputs = ScoreInputs(
            in_startup=ref.file_class in {FileClass.SOURCE, FileClass.CONFIG},
            missing_from_docs=True,
            missing_from_declaration=True,
            no_fallback=True,
            independent_source_kinds=2,
            has_undeclared_signal=True,
            test_only=ref.file_class == FileClass.TEST,
        )
        confidence = compute_confidence(inputs)
        verdict = assign_verdict(confidence, inputs) or Verdict.LIKELY_TRAP
        findings.append(
            Finding(
                id=f"locality.abs.{_slug(ref.referenced_from)}",
                category=Category.LOCALITY,
                verdict=verdict,
                severity=Severity.HIGH if ref.file_class in {FileClass.SOURCE, FileClass.CONFIG} else Severity.MEDIUM,
                confidence=confidence,
                title="Machine-specific absolute path",
                evidence=[EvidenceItem("source", ref.referenced_from, ref.detail)],
                counter_evidence=[],
                affected_files=[ref.referenced_from],
                why_it_matters="A clean clone on another machine will not have this path.",
                verification=f"Inspect {ref.referenced_from} for absolute filesystem paths.",
                remediation="Consider replacing the absolute path with a repository-relative path.",
                clone_stage=CloneStage.RUN,
                independent_source_kinds=2,
                has_undeclared_signal=True,
            )
        )

    for ref in facts.home_paths:
        findings.append(
            Finding(
                id=f"locality.home.{_slug(ref.referenced_from)}",
                category=Category.LOCALITY,
                verdict=Verdict.ENVIRONMENT_ASSUMPTION,
                severity=Severity.LOW,
                confidence=0.55,
                title="Home-directory path assumption",
                evidence=[EvidenceItem("source", ref.referenced_from, ref.detail)],
                counter_evidence=[],
                affected_files=[ref.referenced_from],
                why_it_matters="The repository appears to assume a home-directory layout.",
                verification=f"Inspect {ref.referenced_from} for $HOME or ~ paths.",
                remediation="Consider documenting the expected home-directory files.",
                clone_stage=CloneStage.CONFIGURE,
                independent_source_kinds=1,
            )
        )

    if facts.os_specific_scripts:
        findings.append(
            Finding(
                id="locality.os.powershell",
                category=Category.LOCALITY,
                verdict=Verdict.LIKELY_TRAP,
                severity=Severity.MEDIUM,
                confidence=0.72,
                title="Bootstrap scripts appear OS-specific",
                evidence=[
                    EvidenceItem("script", path, "PowerShell script without a Unix counterpart")
                    for path in facts.os_specific_scripts[:4]
                ],
                counter_evidence=[],
                affected_files=list(facts.os_specific_scripts),
                why_it_matters="A clean clone on another OS may lack the documented bootstrap path.",
                verification="Compare .ps1 scripts with Makefile or .sh equivalents.",
                remediation="Consider documenting a Unix bootstrap path or adding a portable script.",
                clone_stage=CloneStage.INSTALL,
                independent_source_kinds=2,
                has_undeclared_signal=True,
            )
        )

    for ref in facts.sibling_refs:
        from_dir = os.path.dirname(ref.referenced_from)
        resolved = os.path.normpath(os.path.join(from_dir, ref.path))
        if not resolved.startswith(".."):
            continue
        findings.append(
            Finding(
                id=f"locality.sibling.{_slug(ref.path)}",
                category=Category.LOCALITY,
                verdict=Verdict.LIKELY_TRAP,
                severity=Severity.HIGH,
                confidence=0.78,
                title=f"Sibling repository path: {ref.path}",
                evidence=[EvidenceItem("source", ref.referenced_from, ref.detail)],
                counter_evidence=[],
                affected_files=[ref.referenced_from],
                why_it_matters="A clean clone of this repository alone will not include the sibling checkout.",
                verification=f"Inspect {ref.referenced_from} for relative paths that leave the repository.",
                remediation="Consider documenting the extra checkout or vendoring the dependency.",
                clone_stage=CloneStage.CLONE,
                independent_source_kinds=2,
                has_undeclared_signal=True,
            )
        )
    return findings


def _looks_like_sqlite(facts: ExtractedFacts) -> bool:
    for path in facts.env_example_files:
        # values are not stored; treat sqlite mention in docs as enough
        pass
    return "sqlite" in facts.doc_services and "postgres" not in {
        infer_service(item.name, item.image) for item in facts.compose_services
    }


def _severity(in_startup: bool, has_default: bool, test_only: bool) -> Severity:
    if test_only:
        return Severity.LOW
    if in_startup and not has_default:
        return Severity.HIGH
    if in_startup:
        return Severity.MEDIUM
    return Severity.MEDIUM if not has_default else Severity.LOW


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", ".", value.lower()).strip(".")
    return slug[:48] or "item"


def _parse_tuple(spec: str) -> tuple[int, int]:
    match = re.search(r"(\d+)(?:\.(\d+))?", spec)
    if not match:
        return (0, 0)
    return (int(match.group(1)), int(match.group(2) or 0))
