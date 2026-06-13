import sys
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pymupdf_extractor import (
    PyMuPdfExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType
from tests.make_fitz_module import make_fitz_module
from tests.patch_module import patch_module
from tests.read_fixture import read_fixture


class TestPyMuPdfExtractor(unittest.TestCase):
    def test_unavailable_without_fitz(self):
        with mock.patch.dict(sys.modules, {'fitz': None}):
            with self.assertRaises(ExtractorUnavailable):
                PyMuPdfExtractor().extract(
                    read_fixture('sample.pdf'), FileType.PDF
                )

    def test_happy_path(self):
        with patch_module('fitz', make_fitz_module(['page one text', 'page two text'])):
            result = PyMuPdfExtractor().extract(
                read_fixture('sample.pdf'), FileType.PDF
            )
        self.assertIn('page one text', result.markdown)
        self.assertIn('page two text', result.markdown)
        self.assertIn('page 1', result.markdown)
        self.assertIn('page 2', result.markdown)
        self.assertGreater(result.confidence, 0.0)

    def test_open_failure_raises_runtime_error(self):
        with patch_module('fitz', make_fitz_module(open_raises=Exception('broken'))):
            with self.assertRaises(RuntimeError):
                PyMuPdfExtractor().extract(
                    read_fixture('sample.pdf'), FileType.PDF
                )


if __name__ == '__main__':
    unittest.main()
