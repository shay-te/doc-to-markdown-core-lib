import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pypdf_extractor import (
    PypdfExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType
from tests.patch_module import patch_module


def _make_pypdf(pages_text):
    pypdf_module = types.ModuleType('pypdf')

    class FakePage:
        def __init__(self, text):
            self._text = text

        def extract_text(self):
            return self._text

    class FakeReader:
        def __init__(self, stream):
            self.pages = [FakePage(text) for text in pages_text]

    pypdf_module.PdfReader = FakeReader
    return pypdf_module


class TestPypdfExtractor(unittest.TestCase):
    def test_unavailable_without_pypdf(self):
        with mock.patch.dict(sys.modules, {'pypdf': None}):
            with self.assertRaises(ExtractorUnavailable):
                PypdfExtractor().extract(b'%PDF', FileType.PDF)

    def test_happy_path(self):
        with patch_module('pypdf', _make_pypdf(['first page', 'second page'])):
            result = PypdfExtractor().extract(b'%PDF', FileType.PDF)
        self.assertIn('first page', result.markdown)
        self.assertIn('second page', result.markdown)
        self.assertIn('page 1', result.markdown)
        self.assertIn('page 2', result.markdown)
        self.assertGreater(result.confidence, 0.0)


if __name__ == '__main__':
    unittest.main()
