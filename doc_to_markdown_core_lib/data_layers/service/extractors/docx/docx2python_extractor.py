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


class Docx2pythonExtractor(Extractor):
    """``docx2python`` — pulls DOCX text while preserving body/header/footer/
    footnote structure, a different reading than python-docx / mammoth /
    docx2txt. Uses the documented context-manager API so its zip handle is
    closed."""

    name = 'docx2python'
    file_types = (FileType.DOCX,)

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        try:
            import io

            from docx2python import docx2python
        except ImportError as import_error:
            raise ExtractorUnavailable('docx2python not installed') from import_error

        with docx2python(io.BytesIO(content)) as docx_content:
            markdown = (docx_content.text or '').strip()
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
