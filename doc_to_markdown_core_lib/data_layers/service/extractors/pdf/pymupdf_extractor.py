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


class PyMuPdfExtractor(Extractor):
    """Text-layer extractor (PyMuPDF/fitz). Mostly empty on scans —
    OCR engines pick up the slack."""

    name = 'pymupdf'
    file_types = (FileType.PDF,)

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        try:
            import fitz
        except ImportError as import_error:
            raise ExtractorUnavailable(
                'PyMuPDF (fitz) not installed'
            ) from import_error

        try:
            doc = fitz.open(stream=content, filetype=FileType.PDF)
        except Exception as open_error:
            raise RuntimeError(
                f'pymupdf failed to open document: {open_error}'
            ) from open_error

        parts = []
        try:
            for page_number, page in enumerate(doc, start=1):
                text = (page.get_text('text') or '').strip()
                parts.append(f'<!-- page {page_number} -->\n\n{text}')
        finally:
            doc.close()

        markdown = '\n\n'.join(parts).strip()
        confidence = min(
            1.0, max(0.0, len(markdown) / CONFIDENCE_DOCUMENT_CHARS_NORM)
        )
        return ExtractionCandidate(
            extractor=self.name,
            markdown=markdown,
            confidence=confidence,
            languages=[],
        )
