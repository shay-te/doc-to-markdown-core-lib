import os
import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.markitdown_extractor import (
    MarkItDownExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType
from tests.patch_module import patch_module


def _make_markitdown(text_content):
    markitdown_module = types.ModuleType('markitdown')

    class FakeConversion:
        def __init__(self, text):
            self.text_content = text

    class FakeMarkItDown:
        last_converted_path = None

        def convert(self, path):
            FakeMarkItDown.last_converted_path = path
            return FakeConversion(text_content)

    markitdown_module.MarkItDown = FakeMarkItDown
    return markitdown_module


class TestMarkItDownExtractor(unittest.TestCase):
    def test_unavailable_without_markitdown(self):
        with mock.patch.dict(sys.modules, {'markitdown': None}):
            with self.assertRaises(ExtractorUnavailable):
                MarkItDownExtractor().extract(b'%PDF', FileType.PDF.value)

    def test_pdf_happy_path_and_temp_cleanup(self):
        markitdown_module = _make_markitdown('# converted')
        with patch_module('markitdown', markitdown_module):
            result = MarkItDownExtractor().extract(b'%PDF', FileType.PDF.value)
        self.assertIn('# converted', result.markdown)
        converted_path = markitdown_module.MarkItDown.last_converted_path
        self.assertTrue(converted_path.endswith(f'.{FileType.PDF.value}'))
        self.assertFalse(os.path.exists(converted_path))

    def test_docx_uses_docx_suffix(self):
        markitdown_module = _make_markitdown('docx body')
        with patch_module('markitdown', markitdown_module):
            MarkItDownExtractor().extract(b'PK', FileType.DOCX.value)
        converted_path = markitdown_module.MarkItDown.last_converted_path
        self.assertTrue(converted_path.endswith(f'.{FileType.DOCX.value}'))

    def test_unknown_file_type_raises_value_error(self):
        with patch_module('markitdown', _make_markitdown('x')):
            with self.assertRaises(ValueError):
                MarkItDownExtractor().extract(b'x', 'audio')


if __name__ == '__main__':
    unittest.main()
