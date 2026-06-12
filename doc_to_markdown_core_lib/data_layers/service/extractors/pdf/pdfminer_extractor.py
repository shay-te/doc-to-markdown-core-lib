from doc_to_markdown_core_lib.data_layers.service.types import (
    ExtractionCandidate,
    Extractor,
    ExtractorUnavailable,
)


class PdfMinerExtractor(Extractor):
    """Third diverse-class text-layer engine. Handles encoding
    quirks (custom CMaps, non-standard glyphs) the others mis-parse."""

    name = 'pdfminer'
    file_types = ('pdf',)

    def extract(self, content: bytes, file_type: str) -> ExtractionCandidate:
        try:
            import io

            from pdfminer.high_level import extract_text
        except ImportError as e:
            raise ExtractorUnavailable('pdfminer.six not installed') from e

        text = (extract_text(io.BytesIO(content)) or '').strip()
        confidence = min(1.0, max(0.0, len(text) / 2000))
        return ExtractionCandidate(
            extractor=self.name,
            markdown=text,
            confidence=confidence,
            languages=[],
        )
