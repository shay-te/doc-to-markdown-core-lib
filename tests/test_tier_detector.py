import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.tier_detector import detect_tier
from doc_to_markdown_core_lib.data_layers.service.types import FileType


def _fitz_module(pages_text=None, open_raises=None):
    mod = types.ModuleType('fitz')
    pages_text = pages_text if pages_text is not None else ['hello world']

    class FakePage:
        def __init__(self, text):
            self._text = text

        def get_text(self):
            return self._text

    class FakeDoc:
        def __init__(self):
            self._pages = [FakePage(text) for text in pages_text]

        def __iter__(self):
            return iter(self._pages)

        def __len__(self):
            return len(self._pages)

        def close(self):
            pass

    def fake_open(stream=None, filetype=None):
        if open_raises is not None:
            raise open_raises
        return FakeDoc()

    mod.open = fake_open
    return mod


class TestTierDetectorSimpleTypes(unittest.TestCase):
    def test_txt_md_docx_are_clean(self):
        # The uppercase variants are deliberately raw strings — they
        # probe the lower() normalization inside detect_tier.
        for file_type in (
            FileType.TXT.value,
            FileType.MD.value,
            FileType.DOCX.value,
            'TXT',
            'MD',
            'DocX',
        ):
            self.assertEqual(detect_tier(b'x', file_type), 'clean')

    def test_image_is_risky(self):
        self.assertEqual(
            detect_tier(b'\x89PNG\r\n\x1a\n', FileType.IMAGE.value), 'risky'
        )

    def test_unknown_type_is_risky(self):
        self.assertEqual(detect_tier(b'x', 'unknown'), 'risky')

    def test_empty_type_is_risky(self):
        self.assertEqual(detect_tier(b'x', ''), 'risky')

    def test_none_type_is_risky(self):
        self.assertEqual(detect_tier(b'x', None), 'risky')


class TestTierDetectorPdf(unittest.TestCase):
    def test_pdf_without_fitz_is_risky(self):
        with mock.patch.dict(sys.modules, {'fitz': None}):
            self.assertEqual(detect_tier(b'%PDF', FileType.PDF.value), 'risky')

    def test_pdf_with_dense_text_layer_is_clean(self):
        mod = _fitz_module(pages_text=['x' * 200, 'y' * 200])
        with mock.patch.dict(sys.modules, {'fitz': mod}):
            self.assertEqual(detect_tier(b'%PDF', FileType.PDF.value), 'clean')

    def test_pdf_with_sparse_text_layer_is_risky(self):
        mod = _fitz_module(pages_text=['', ''])
        with mock.patch.dict(sys.modules, {'fitz': mod}):
            self.assertEqual(detect_tier(b'%PDF', FileType.PDF.value), 'risky')

    def test_pdf_with_zero_pages_is_risky(self):
        mod = _fitz_module(pages_text=[])
        with mock.patch.dict(sys.modules, {'fitz': mod}):
            self.assertEqual(detect_tier(b'%PDF', FileType.PDF.value), 'risky')

    def test_pdf_with_broken_fitz_open_is_risky(self):
        mod = _fitz_module(open_raises=RuntimeError('cannot open'))
        with mock.patch.dict(sys.modules, {'fitz': mod}):
            self.assertEqual(detect_tier(b'not a pdf', FileType.PDF.value), 'risky')


if __name__ == '__main__':
    unittest.main()
