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


class PypdfExtractor(Extractor):
    """Fourth diverse-class text-layer engine (pure-Python ``pypdf``).
    Its tokenizer disagrees with pdfminer/pymupdf on hyphenation and
    whitespace, which is exactly the diversity the vote wants."""

    name = 'pypdf'
    file_types = (FileType.PDF.value,)

    def extract(self, content: bytes, file_type: str) -> ExtractionCandidate:
        try:
            import io

            from pypdf import PdfReader
        except ImportError as import_error:
            raise ExtractorUnavailable(
                'pypdf not installed'
            ) from import_error

        reader = PdfReader(io.BytesIO(content))
        parts = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or '').strip()
            parts.append(f'<!-- page {page_number} -->\n\n{text}')

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
