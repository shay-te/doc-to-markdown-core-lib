import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pymupdf4llm_extractor import (
    PyMuPdf4LlmExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType
from tests.make_fitz_module import make_fitz_module


class TestPyMuPdf4LlmExtractor(unittest.TestCase):
    def test_unavailable_without_pymupdf4llm(self):
        with mock.patch.dict(
            sys.modules, {'fitz': make_fitz_module(), 'pymupdf4llm': None}
        ):
            with self.assertRaises(ExtractorUnavailable):
                PyMuPdf4LlmExtractor().extract(b'%PDF', FileType.PDF.value)

    def test_happy_path_returns_native_markdown(self):
        pymupdf4llm_module = types.ModuleType('pymupdf4llm')
        pymupdf4llm_module.to_markdown = mock.Mock(return_value='# Native\n\nbody')
        with mock.patch.dict(
            sys.modules,
            {'fitz': make_fitz_module(), 'pymupdf4llm': pymupdf4llm_module},
        ):
            result = PyMuPdf4LlmExtractor().extract(b'%PDF', FileType.PDF.value)
        self.assertIn('# Native', result.markdown)
        self.assertGreater(result.confidence, 0.0)
        pymupdf4llm_module.to_markdown.assert_called_once()


if __name__ == '__main__':
    unittest.main()
