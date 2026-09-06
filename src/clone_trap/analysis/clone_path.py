"""Place findings on a non-executing clone lifecycle."""

from __future__ import annotations

from clone_trap.extractors.facts import ExtractedFacts
from clone_trap.models.enums import CloneStage
from clone_trap.models.finding import Finding
from clone_trap.models.report import ClonePathStage

STAGE_HINTS = {
    CloneStage.CLONE: ("clone", "submodule"),
    CloneStage.INSTALL: ("npm install", "pip install", "pnpm", "yarn", "poetry"),
    CloneStage.GENERATE: ("generate", "prisma"),
    CloneStage.CONFIGURE: (".env", "config"),
    CloneStage.START_SERVICES: ("docker compose", "docker-compose", "postgres", "redis"),
    CloneStage.RUN: ("npm run", "uvicorn", "python -m", "pytest"),
}


def build_clone_path(facts: ExtractedFacts, findings: list[Finding]) -> list[ClonePathStage]:
    blob = " ".join(facts.doc_commands + facts.doc_generate_commands).lower()
    stages: list[ClonePathStage] = []
    for stage in CloneStage:
        documented = any(hint in blob for hint in STAGE_HINTS[stage])
        if stage == CloneStage.CLONE:
            documented = True
        if stage == CloneStage.CONFIGURE and facts.env_example_files:
            documented = True
        if stage == CloneStage.START_SERVICES and facts.compose_files:
            documented = True or documented
        ids = [finding.id for finding in findings if finding.clone_stage == stage]
        stages.append(ClonePathStage(stage=stage, documented=documented, finding_ids=ids))
    return stages
