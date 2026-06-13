from doc_to_markdown_core_lib.data_layers.service.confidence_norms import (
    CONFIDENCE_DOCUMENT_CHARS_NORM,
)
from doc_to_markdown_core_lib.data_layers.service.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.service.extractor import Extractor
from doc_to_markdown_core_lib.data_layers.service.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType

# Structure is lost in the plain-text dump, so a full-length document
# still only earns a discounted score versus format-aware extractors.
_PLAIN_TEXT_CONFIDENCE_DISCOUNT = 0.7


class TextractExtractor(Extractor):
    """``textract`` covers legacy ``.doc`` (and several other formats)
    via a Python wrapper around antiword / catdoc / wvText. Confidence
    is intentionally modest — textract strips structure to plain text,
    so it loses to format-aware extractors when they're available."""

    name = 'textract'
    file_types = (FileType.DOC.value, FileType.DOCX.value)

    def extract(self, content: bytes, file_type: str) -> ExtractionCandidate:
        try:
            import tempfile
            import os
            import textract
        except ImportError as import_error:
            raise ExtractorUnavailable('textract not installed') from import_error

        suffix = f'.{file_type}'
        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        try:
            text = textract.process(temp_path).decode('utf-8', errors='replace')
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

        markdown = (text or '').strip()
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
