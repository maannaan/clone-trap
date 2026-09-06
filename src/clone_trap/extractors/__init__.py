"""Run all structured extractors."""

from clone_trap.extractors.artifacts import extract_artifacts
from clone_trap.extractors.compose import extract_compose_and_ci
from clone_trap.extractors.docs import extract_docs
from clone_trap.extractors.env import extract_env
from clone_trap.extractors.facts import ExtractedFacts
from clone_trap.extractors.locality import extract_locality
from clone_trap.extractors.manifests import extract_manifests
from clone_trap.extractors.services import extract_services
from clone_trap.extractors.toolchain import extract_toolchain
from clone_trap.models.inventory import Inventory


def extract_facts(inventory: Inventory) -> ExtractedFacts:
    facts = ExtractedFacts()
    extract_docs(inventory, facts)
    extract_env(inventory, facts)
    extract_compose_and_ci(inventory, facts)
    extract_manifests(inventory, facts)
    extract_services(inventory, facts)
    extract_artifacts(inventory, facts)
    extract_toolchain(inventory, facts)
    extract_locality(inventory, facts)
    return facts
