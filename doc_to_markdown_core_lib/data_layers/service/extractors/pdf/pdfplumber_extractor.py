from doc_to_markdown_core_lib.data_layers.service.types import (
    ExtractionCandidate,
    Extractor,
    ExtractorUnavailable,
)


class PdfPlumberExtractor(Extractor):
    """Strong text-layer engine for table-heavy PDFs."""

    name = 'pdfplumber'
    file_types = ('pdf',)

    def extract(self, content: bytes, file_type: str) -> ExtractionCandidate:
        try:
            import io

            import pdfplumber
        except ImportError as e:
            raise ExtractorUnavailable('pdfplumber not installed') from e

        parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = (page.extract_text() or '').strip()
                parts.append(f'<!-- page {i} -->\n\n{text}')
                for table in page.extract_tables() or []:
                    rendered = _table_to_markdown(table)
                    if rendered:
                        parts.append(rendered)

        markdown = '\n\n'.join(parts).strip()
        confidence = min(1.0, max(0.0, len(markdown) / 2000))
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
