import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.docx.docx_extractor import (
    DocxExtractor,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType
from tests.patch_module import patch_module


def _make_docx(paragraphs, tables=None):
    docx_module = types.ModuleType('docx')

    class FakeStyle:
        def __init__(self, name):
            self.name = name

    class FakePara:
        def __init__(self, text, style_name=''):
            self.text = text
            self.style = FakeStyle(style_name) if style_name else FakeStyle('')

    class FakeCell:
        def __init__(self, text):
            self.text = text

    class FakeRow:
        def __init__(self, cells):
            self.cells = [FakeCell(text) for text in cells]

    class FakeTable:
        def __init__(self, rows):
            self.rows = [FakeRow(cells) for cells in rows]

    class FakeDoc:
        def __init__(self, *args, **kwargs):
            self.paragraphs = [
                FakePara(para_text, style_name)
                for para_text, style_name in paragraphs
            ]
            self.tables = [FakeTable(table_rows) for table_rows in (tables or [])]

    docx_module.Document = FakeDoc
    return docx_module


class TestDocxExtractor(unittest.TestCase):
    def test_unavailable_without_docx(self):
        with mock.patch.dict(sys.modules, {'docx': None}):
            with self.assertRaises(ExtractorUnavailable):
                DocxExtractor().extract(b'PK', FileType.DOCX)

    def test_headings_lists_paragraphs_and_tables(self):
        paragraphs = [
            ('Title', 'Heading 1'),
            ('Sub', 'Heading 2'),
            ('Subsub', 'Heading 3'),
            ('Detail', 'Heading 4'),
            ('Body text', ''),
            ('item', 'List Bullet'),
            ('', 'Normal'),  # empty — skipped
        ]
        tables = [[['A', 'B'], ['1', '2'], ['short']]]
        with patch_module('docx', _make_docx(paragraphs, tables)):
            result = DocxExtractor().extract(b'PK', FileType.DOCX)
        markdown_text = result.markdown
        self.assertIn('# Title', markdown_text)
        self.assertIn('## Sub', markdown_text)
        self.assertIn('### Subsub', markdown_text)
        self.assertIn('#### Detail', markdown_text)
        self.assertIn('Body text', markdown_text)
        self.assertIn('- item', markdown_text)
        self.assertIn('| A | B |', markdown_text)
        self.assertIn('| short |  |', markdown_text)

    def test_no_paragraphs_yields_zero_confidence(self):
        with patch_module('docx', _make_docx([], [])):
            result = DocxExtractor().extract(b'PK', FileType.DOCX)
        self.assertEqual(result.markdown, '')
        self.assertEqual(result.confidence, 0.0)


if __name__ == '__main__':
    unittest.main()
