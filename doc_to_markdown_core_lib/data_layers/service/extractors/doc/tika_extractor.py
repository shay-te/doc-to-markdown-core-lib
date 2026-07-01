from doc_to_markdown_core_lib.constants import CONFIDENCE_DOCUMENT_CHARS_NORM
from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.extractor import Extractor
from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType

# Plain-text dump loses structure, so it scores below format-aware extractors.
_PLAIN_TEXT_CONFIDENCE_DISCOUNT = 0.7


class TikaExtractor(Extractor):
    """Apache Tika (``tika``) — a battle-tested cross-format parser that reads
    both legacy ``.doc`` and ``.docx`` through its Java backend, giving a
    robust independent opinion on either. Needs the ``tika`` package (which
    manages its own Tika server). Plain text → discounted score."""

    name = 'tika'
    file_types = (FileType.DOC, FileType.DOCX)

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        try:
            from tika import parser
        except ImportError as import_error:
            raise ExtractorUnavailable('tika not installed') from import_error

        parsed = parser.from_buffer(content)
        markdown = ((parsed or {}).get('content') or '').strip()
        confidence = (
            min(1.0, max(0.0, len(markdown) / CONFIDENCE_DOCUMENT_CHARS_NORM))
            * _PLAIN_TEXT_CONFIDENCE_DISCOUNT
        )
        return ExtractionCandidate(
            extractor=self.name,
            markdown=markdown,
            confidence=confidence,
            languages=[],
        )
