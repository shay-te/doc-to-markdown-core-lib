"""Extraction pipeline shared types."""
import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class FileType(str, enum.Enum):
    """Canonical pipeline file types — ``Extractor.file_types``,
    ``MarkdownService.extract`` and ``detect_tier`` all speak these
    values."""
    MD = 'md'
    TXT = 'txt'
    PDF = 'pdf'
    DOC = 'doc'
    DOCX = 'docx'
    IMAGE = 'image'


class ExtractorUnavailable(RuntimeError):
    """Raised when an extractor's backing library is missing. The
    pipeline records the reason and continues."""


# Length-based confidence heuristic shared by the extractors: the
# extracted text length is divided by the norm and clamped to 0..1,
# so output at or above the norm contributes full confidence.
CONFIDENCE_DOCUMENT_CHARS_NORM = 2000
CONFIDENCE_SINGLE_IMAGE_CHARS_NORM = 1500


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
