import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.easyocr_extractor import (
    EasyOcrExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType
from tests.make_fitz_module import make_fitz_module
from tests.patch_module import patch_module


def _make_easyocr(lines, reader_init_raises=None):
    easyocr_module = types.ModuleType('easyocr')

    class FakeReader:
        def __init__(self, languages, verbose=False):
            if reader_init_raises:
                raise reader_init_raises
            self.languages = languages

        def readtext(self, image_bytes, detail=0, paragraph=True):
            return lines

    easyocr_module.Reader = FakeReader
    return easyocr_module


class TestEasyOcrExtractor(unittest.TestCase):
    def test_unavailable_without_easyocr(self):
        with mock.patch.dict(sys.modules, {'easyocr': None}):
            with self.assertRaises(ExtractorUnavailable):
                EasyOcrExtractor().extract(b'\x89PNG', FileType.IMAGE)

    def test_reader_init_failure_is_unavailable(self):
        broken_module = _make_easyocr(
            [], reader_init_raises=ValueError('bad lang combo')
        )
        with patch_module('easyocr', broken_module):
            with self.assertRaises(ExtractorUnavailable):
                EasyOcrExtractor(languages=['he', 'ch_sim']).extract(
                    b'\x89PNG', FileType.IMAGE
                )

    def test_image_happy_path(self):
        with patch_module('easyocr', _make_easyocr(['hello', 'world'])):
            result = EasyOcrExtractor(languages=['en']).extract(
                b'\x89PNG', FileType.IMAGE
            )
        self.assertEqual(result.markdown, 'hello\nworld')
        self.assertEqual(result.languages, ['en'])
        self.assertGreater(result.confidence, 0.0)

    def test_pdf_happy_path_rasterizes_via_fitz(self):
        with mock.patch.dict(
            sys.modules,
            {
                'easyocr': _make_easyocr(['page-ocr']),
                'fitz': make_fitz_module(pages_text=['', '']),
            },
        ):
            result = EasyOcrExtractor().extract(b'%PDF', FileType.PDF)
        self.assertIn('page-ocr', result.markdown)
        self.assertIn('page 1', result.markdown)
        self.assertIn('page 2', result.markdown)

    def test_pdf_requires_fitz(self):
        with mock.patch.dict(
            sys.modules, {'easyocr': _make_easyocr(['x']), 'fitz': None}
        ):
            with self.assertRaises(ExtractorUnavailable):
                EasyOcrExtractor().extract(b'%PDF', FileType.PDF)

    def test_unknown_file_type_raises_value_error(self):
        with patch_module('easyocr', _make_easyocr(['x'])):
            with self.assertRaises(ValueError):
                EasyOcrExtractor().extract(b'x', 'audio')


if __name__ == '__main__':
    unittest.main()
