import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pdfplumber_extractor import (
    PdfPlumberExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType


class TestPdfPlumberEmptyTableBranch(unittest.TestCase):
    def test_empty_table_does_not_emit_markdown(self):
        class _Page(object):
            def extract_text(self):
                return 'body'

            def extract_tables(self):
                return [[]]

        class _Pdf(object):
            pages = [_Page()]

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

        plumber_module = types.ModuleType('pdfplumber')
        plumber_module.open = lambda file_object: _Pdf()
        with mock.patch.dict(sys.modules, {'pdfplumber': plumber_module}):
            result = PdfPlumberExtractor().extract(b'%PDF', FileType.PDF)
        self.assertIn('body', result.markdown)
        self.assertNotIn('|', result.markdown)


if __name__ == '__main__':
    unittest.main()
