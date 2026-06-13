import sys
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.tier_detector import detect_tier
from doc_to_markdown_core_lib.data_layers.service.types import FileType
from tests.fakes import make_fitz_module


class TestTierDetectorPdf(unittest.TestCase):
    def test_pdf_without_fitz_is_risky(self):
        with mock.patch.dict(sys.modules, {'fitz': None}):
            self.assertEqual(detect_tier(b'%PDF', FileType.PDF.value), 'risky')

    def test_pdf_with_dense_text_layer_is_clean(self):
        fitz_module = make_fitz_module(pages_text=['x' * 200, 'y' * 200])
        with mock.patch.dict(sys.modules, {'fitz': fitz_module}):
            self.assertEqual(detect_tier(b'%PDF', FileType.PDF.value), 'clean')

    def test_pdf_with_sparse_text_layer_is_risky(self):
        fitz_module = make_fitz_module(pages_text=['', ''])
        with mock.patch.dict(sys.modules, {'fitz': fitz_module}):
            self.assertEqual(detect_tier(b'%PDF', FileType.PDF.value), 'risky')

    def test_pdf_with_zero_pages_is_risky(self):
        fitz_module = make_fitz_module(pages_text=[])
        with mock.patch.dict(sys.modules, {'fitz': fitz_module}):
            self.assertEqual(detect_tier(b'%PDF', FileType.PDF.value), 'risky')

    def test_pdf_with_broken_fitz_open_is_risky(self):
        fitz_module = make_fitz_module(open_raises=RuntimeError('cannot open'))
        with mock.patch.dict(sys.modules, {'fitz': fitz_module}):
            self.assertEqual(
                detect_tier(b'not a pdf', FileType.PDF.value), 'risky'
            )


if __name__ == '__main__':
    unittest.main()
