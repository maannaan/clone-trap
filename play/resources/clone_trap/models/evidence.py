"""Evidence records attached to a finding."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceItem:
    source: str
    path: str
    detail: str
