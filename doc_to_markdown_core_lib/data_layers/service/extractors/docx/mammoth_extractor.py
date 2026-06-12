from doc_to_markdown_core_lib.data_layers.service.types import (
    ExtractionCandidate,
    Extractor,
    ExtractorUnavailable,
)


class MammothExtractor(Extractor):
    """DOCX → Markdown. Second opinion alongside python-docx; tends to
    keep inline formatting better."""

    name = 'mammoth'
    file_types = ('docx',)

    def extract(self, content: bytes, file_type: str) -> ExtractionCandidate:
        try:
            import io

            import mammoth
        except ImportError as e:
            raise ExtractorUnavailable('mammoth not installed') from e

        result = mammoth.convert_to_markdown(io.BytesIO(content))
        markdown = (result.value or '').strip()
        return ExtractionCandidate(
            extractor=self.name,
            markdown=markdown,
            confidence=0.9 if markdown else 0.0,
            languages=[],
        )
