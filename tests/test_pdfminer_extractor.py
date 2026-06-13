import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pdfminer_extractor import (
    PdfMinerExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType


class TestPdfMinerExtractor(unittest.TestCase):
    def test_unavailable_without_pdfminer(self):
        with mock.patch.dict(
            sys.modules, {'pdfminer': None, 'pdfminer.high_level': None}
        ):
            with self.assertRaises(ExtractorUnavailable):
                PdfMinerExtractor().extract(b'%PDF', FileType.PDF.value)

    def test_happy_path(self):
        high_level_module = types.ModuleType('pdfminer.high_level')
        high_level_module.extract_text = lambda file_object: 'extracted text from pdf'
        pdfminer_module = types.ModuleType('pdfminer')
        pdfminer_module.high_level = high_level_module
        with mock.patch.dict(
            sys.modules,
            {'pdfminer': pdfminer_module, 'pdfminer.high_level': high_level_module},
        ):
            result = PdfMinerExtractor().extract(b'%PDF', FileType.PDF.value)
        self.assertEqual(result.markdown, 'extracted text from pdf')


if __name__ == '__main__':
    unittest.main()
