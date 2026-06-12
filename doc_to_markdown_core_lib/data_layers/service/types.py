"""Extraction pipeline shared types."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class ExtractorUnavailable(RuntimeError):
    """Raised when an extractor's backing library is missing. The
    pipeline records the reason and continues."""


@dataclass
class ExtractionCandidate:
    """One engine's verdict. ``confidence`` is the engine's 0..1
    self-assessment."""
    extractor: str
    markdown: str
    confidence: float = 0.0
    languages: List[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    """``*_bytes`` are pre-UTF-8-asserted; persist as-is."""
    markdown: str
    markdown_bytes: bytes
    report: dict
    report_bytes: bytes
    candidates: List[ExtractionCandidate] = field(default_factory=list)


class Extractor(ABC):
    """Engines raise ``ExtractorUnavailable`` from ``extract`` (not
    ``__init__``) so the registry can be built eagerly."""

    name: str = ''
    file_types: Tuple[str, ...] = ()

    @abstractmethod
    def extract(self, content: bytes, file_type: str) -> ExtractionCandidate:
        ...  # pragma: no cover
