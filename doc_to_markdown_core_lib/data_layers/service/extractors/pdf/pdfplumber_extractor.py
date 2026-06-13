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


class PdfPlumberExtractor(Extractor):
    """Strong text-layer engine for table-heavy PDFs."""

    name = 'pdfplumber'
    file_types = (FileType.PDF,)

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        try:
            import io

            import pdfplumber
        except ImportError as import_error:
            raise ExtractorUnavailable(
                'pdfplumber not installed'
            ) from import_error

        parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                text = (page.extract_text() or '').strip()
                parts.append(f'<!-- page {page_number} -->\n\n{text}')
                for table in page.extract_tables() or []:
                    rendered = _table_to_markdown(table)
                    if rendered:
                        parts.append(rendered)

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


def _table_to_markdown(table) -> str:
    if not table or not table[0]:
        return ''
    rows = [
        [(cell or '').strip().replace('|', '\\|') for cell in row]
        for row in table
    ]
    header = rows[0]
    sep = ['---'] * len(header)
    out = ['| ' + ' | '.join(header) + ' |', '| ' + ' | '.join(sep) + ' |']
    for row in rows[1:]:
        if len(row) < len(header):
            row = row + [''] * (len(header) - len(row))
        elif len(row) > len(header):
            row = row[: len(header)]
        out.append('| ' + ' | '.join(row) + ' |')
    return '\n'.join(out)
