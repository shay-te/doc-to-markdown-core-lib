import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pdfplumber_extractor import (
    PdfPlumberExtractor,
    _table_to_markdown as _plumber_table_to_md,
)
from doc_to_markdown_core_lib.data_layers.service.types import (
    ExtractorUnavailable,
    FileType,
)
from tests.patch_module import patch_module


class _FakePdfPlumberPage:
    def __init__(self, text, tables=None):
        self._text = text
        self._tables = tables or []

    def extract_text(self):
        return self._text

    def extract_tables(self):
        return self._tables


class _FakePdfPlumberPdf:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass


def _make_pdfplumber(pages):
    plumber_module = types.ModuleType('pdfplumber')
    plumber_module.open = lambda file_object: _FakePdfPlumberPdf(pages)
    return plumber_module


class TestPdfPlumberExtractor(unittest.TestCase):
    def test_unavailable_without_pdfplumber(self):
        with mock.patch.dict(sys.modules, {'pdfplumber': None}):
            with self.assertRaises(ExtractorUnavailable):
                PdfPlumberExtractor().extract(b'%PDF', FileType.PDF.value)

    def test_happy_path_with_tables(self):
        pages = [
            _FakePdfPlumberPage(
                'p1 body',
                tables=[[['A', 'B'], ['1', '2'], ['3', '4', 'extra']]],
            ),
            _FakePdfPlumberPage('p2 body'),
        ]
        with patch_module('pdfplumber', _make_pdfplumber(pages)):
            result = PdfPlumberExtractor().extract(b'%PDF', FileType.PDF.value)
        self.assertIn('p1 body', result.markdown)
        self.assertIn('p2 body', result.markdown)
        self.assertIn('| A | B |', result.markdown)

    def test_table_helper_empty_returns_empty_string(self):
        self.assertEqual(_plumber_table_to_md([]), '')
        self.assertEqual(_plumber_table_to_md([[]]), '')

    def test_table_helper_pads_short_rows(self):
        rendered = _plumber_table_to_md([['A', 'B', 'C'], ['1']])
        self.assertIn('| 1 |  |  |', rendered)


if __name__ == '__main__':
    unittest.main()
