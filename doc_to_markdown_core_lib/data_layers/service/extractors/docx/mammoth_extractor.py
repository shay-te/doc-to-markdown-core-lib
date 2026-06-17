from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.extractor import Extractor
from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType


class MammothExtractor(Extractor):
    """DOCX → Markdown. Second opinion alongside python-docx; tends to
    keep inline formatting better."""

    name = 'mammoth'
    file_types = (FileType.DOCX,)

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        try:
            import io

            import mammoth
        except ImportError as import_error:
            raise ExtractorUnavailable(
                'mammoth not installed'
            ) from import_error

        result = mammoth.convert_to_markdown(io.BytesIO(content))
        markdown = (result.value or '').strip()
        return ExtractionCandidate(
            extractor=self.name,
            markdown=markdown,
            confidence=0.9 if markdown else 0.0,
            languages=[],
        )
