from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.extractor import Extractor
from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType


class DocxExtractor(Extractor):
    """python-docx structure walk. Pairs with :class:`MammothExtractor`
    for diverse interpretations of the same DOCX."""

    name = 'python-docx'
    file_types = (FileType.DOCX,)

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        try:
            import io

            from docx import Document as DocxDocument
        except ImportError as import_error:
            raise ExtractorUnavailable(
                'python-docx not installed'
            ) from import_error

        doc = DocxDocument(io.BytesIO(content))
        parts = []
        for para in doc.paragraphs:
            text = (para.text or '').strip()
            if not text:
                continue
            style = (para.style.name or '').lower() if para.style else ''
            if 'heading 1' in style:
                parts.append('# ' + text)
            elif 'heading 2' in style:
                parts.append('## ' + text)
            elif 'heading 3' in style:
                parts.append('### ' + text)
            elif 'heading 4' in style:
                parts.append('#### ' + text)
            elif 'list' in style or 'bullet' in style:
                parts.append('- ' + text)
            else:
                parts.append(text)

        for table in doc.tables:
            rendered = _docx_table_to_markdown(table)
            if rendered:
                parts.append(rendered)

        markdown = '\n\n'.join(parts).strip()
        return ExtractionCandidate(
            extractor=self.name,
            markdown=markdown,
            confidence=0.9 if markdown else 0.0,
            languages=[],
        )


def _docx_table_to_markdown(table) -> str:
    rows = []
    for row in table.rows:
        rows.append([(cell.text or '').strip().replace('|', '\\|') for cell in row.cells])
    if not rows or not rows[0]:
        return ''
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
