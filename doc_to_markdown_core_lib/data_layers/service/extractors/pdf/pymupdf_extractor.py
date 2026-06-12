from doc_to_markdown_core_lib.data_layers.service.types import (
    ExtractionCandidate,
    Extractor,
    ExtractorUnavailable,
)


class PyMuPdfExtractor(Extractor):
    """Text-layer extractor (PyMuPDF/fitz). Mostly empty on scans —
    OCR engines pick up the slack."""

    name = 'pymupdf'
    file_types = ('pdf',)

    def extract(self, content: bytes, file_type: str) -> ExtractionCandidate:
        try:
            import fitz
        except ImportError as e:
            raise ExtractorUnavailable('PyMuPDF (fitz) not installed') from e

        try:
            doc = fitz.open(stream=content, filetype='pdf')
        except Exception as e:
            raise RuntimeError(f'pymupdf failed to open document: {e}') from e

        parts = []
        try:
            for i, page in enumerate(doc, start=1):
                text = (page.get_text('text') or '').strip()
                parts.append(f'<!-- page {i} -->\n\n{text}')
        finally:
            doc.close()

        markdown = '\n\n'.join(parts).strip()
        confidence = min(1.0, max(0.0, len(markdown) / 2000))
        return ExtractionCandidate(
            extractor=self.name,
            markdown=markdown,
            confidence=confidence,
            languages=[],
        )
