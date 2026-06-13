from doc_to_markdown_core_lib.data_layers.service.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.service.extractor import Extractor
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType


class TxtExtractor(Extractor):
    """Plain-text source — try UTF variants, then fall back to latin-1."""

    name = 'plain-text'
    file_types = (FileType.TXT,)

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        last_error = None
        for encoding in ('utf-8-sig', 'utf-8', 'utf-16', 'latin-1'):
            try:
                text = content.decode(encoding)
                return ExtractionCandidate(
                    extractor=self.name,
                    markdown=text,
                    confidence=1.0 if encoding.startswith('utf') else 0.5,
                    languages=[],
                )
            except UnicodeDecodeError as decode_error:
                last_error = decode_error
        # latin-1 never fails — only reached if the fallback list shrinks.
        raise RuntimeError(f'could not decode text content: {last_error}')  # pragma: no cover
