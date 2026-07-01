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


class Docx2txtExtractor(Extractor):
    """``docx2txt`` — a lightweight DOCX text pull (paragraphs + tab-joined
    table cells). A plain-text opinion distinct from the structure-aware
    python-docx / mammoth walks."""

    name = 'docx2txt'
    file_types = (FileType.DOCX,)

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        try:
            import io

            import docx2txt
        except ImportError as import_error:
            raise ExtractorUnavailable('docx2txt not installed') from import_error

        markdown = (docx2txt.process(io.BytesIO(content)) or '').strip()
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
