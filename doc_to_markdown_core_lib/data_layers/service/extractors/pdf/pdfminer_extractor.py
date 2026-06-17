from doc_to_markdown_core_lib.constants import (
    CONFIDENCE_DOCUMENT_CHARS_NORM,
)
from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.extractor import Extractor
from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType


class PdfMinerExtractor(Extractor):
    """Third diverse-class text-layer engine. Handles encoding
    quirks (custom CMaps, non-standard glyphs) the others mis-parse."""

    name = 'pdfminer'
    file_types = (FileType.PDF,)

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        try:
            import io

            from pdfminer.high_level import extract_text
        except ImportError as import_error:
            raise ExtractorUnavailable(
                'pdfminer.six not installed'
            ) from import_error

        text = (extract_text(io.BytesIO(content)) or '').strip()
        confidence = min(
            1.0, max(0.0, len(text) / CONFIDENCE_DOCUMENT_CHARS_NORM)
        )
        return ExtractionCandidate(
            extractor=self.name,
            markdown=text,
            confidence=confidence,
            languages=[],
        )
