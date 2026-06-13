import os
import tempfile

from doc_to_markdown_core_lib.data_layers.service.types import (
    CONFIDENCE_DOCUMENT_CHARS_NORM,
    ExtractionCandidate,
    Extractor,
    ExtractorUnavailable,
    FileType,
)

_SUFFIX_PER_TYPE = {
    FileType.PDF.value: '.pdf',
    FileType.DOCX.value: '.docx',
}


class MarkItDownExtractor(Extractor):
    """Microsoft ``markitdown`` — an independent whole-document →
    markdown converter covering both PDF and DOCX, adding a vendor-
    diverse opinion to the vote. Works on file paths only, so the
    bytes take a temp-file round trip."""

    name = 'markitdown'
    file_types = (FileType.PDF.value, FileType.DOCX.value)

    def extract(self, content: bytes, file_type: str) -> ExtractionCandidate:
        try:
            from markitdown import MarkItDown
        except ImportError as import_error:
            raise ExtractorUnavailable(
                'markitdown not installed'
            ) from import_error

        suffix = _SUFFIX_PER_TYPE.get(file_type)
        if suffix is None:
            raise ValueError(f'markitdown cannot handle file_type={file_type!r}')

        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        try:
            converted = MarkItDown().convert(temp_path)
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

        markdown = (getattr(converted, 'text_content', '') or '').strip()
        confidence = min(
            1.0, max(0.0, len(markdown) / CONFIDENCE_DOCUMENT_CHARS_NORM)
        )
        return ExtractionCandidate(
            extractor=self.name,
            markdown=markdown,
            confidence=confidence,
            languages=[],
        )
