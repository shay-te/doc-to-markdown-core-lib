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


class PyMuPdf4LlmExtractor(Extractor):
    """``pymupdf4llm`` renders PDFs as markdown natively (headings,
    lists, tables), so its candidate keeps structure the plain
    text-layer engines flatten."""

    name = 'pymupdf4llm'
    file_types = (FileType.PDF.value,)

    def extract(self, content: bytes, file_type: str) -> ExtractionCandidate:
        try:
            import fitz
            import pymupdf4llm
        except ImportError as import_error:
            raise ExtractorUnavailable(
                'pymupdf4llm (and PyMuPDF) not installed'
            ) from import_error

        doc = fitz.open(stream=content, filetype='pdf')
        try:
            markdown = (pymupdf4llm.to_markdown(doc) or '').strip()
        finally:
            doc.close()

        confidence = min(
            1.0, max(0.0, len(markdown) / CONFIDENCE_DOCUMENT_CHARS_NORM)
        )
        return ExtractionCandidate(
            extractor=self.name,
            markdown=markdown,
            confidence=confidence,
            languages=[],
        )
