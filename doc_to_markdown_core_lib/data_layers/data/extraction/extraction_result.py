from dataclasses import dataclass, field
from typing import List

from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_report import (
    ExtractionReport,
)


@dataclass
class ExtractionResult:
    """``*_bytes`` are pre-UTF-8-asserted; persist as-is. ``report`` is the
    typed :class:`ExtractionReport`; ``report_bytes`` is its JSON form."""
    markdown: str
    markdown_bytes: bytes
    report: ExtractionReport
    report_bytes: bytes
    candidates: List[ExtractionCandidate] = field(default_factory=list)
