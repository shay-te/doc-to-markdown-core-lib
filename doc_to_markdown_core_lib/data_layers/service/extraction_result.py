from dataclasses import dataclass, field
from typing import List

from doc_to_markdown_core_lib.data_layers.service.extraction_candidate import (
    ExtractionCandidate,
)


@dataclass
class ExtractionResult:
    """``*_bytes`` are pre-UTF-8-asserted; persist as-is."""
    markdown: str
    markdown_bytes: bytes
    report: dict
    report_bytes: bytes
    candidates: List[ExtractionCandidate] = field(default_factory=list)
