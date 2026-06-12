from doc_to_markdown_core_lib.data_layers.service.types import (
    ExtractionCandidate,
    Extractor,
    ExtractorUnavailable,
)


class TextractExtractor(Extractor):
    """``textract`` covers legacy ``.doc`` (and several other formats)
    via a Python wrapper around antiword / catdoc / wvText. Confidence
    is intentionally modest — textract strips structure to plain text,
    so it loses to format-aware extractors when they're available."""

    name = 'textract'
    file_types = ('doc', 'docx')

    def extract(self, content: bytes, file_type: str) -> ExtractionCandidate:
        try:
            import tempfile
            import os
            import textract
        except ImportError as import_error:
            raise ExtractorUnavailable('textract not installed') from import_error

        suffix = '.doc' if file_type == 'doc' else '.docx'
        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        try:
            text = textract.process(temp_path).decode('utf-8', errors='replace')
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

        markdown = (text or '').strip()
        confidence = min(1.0, max(0.0, len(markdown) / 2000)) * 0.7
        return ExtractionCandidate(
            extractor=self.name,
            markdown=markdown,
            confidence=confidence,
            languages=[],
        )
