import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractors.image.tesseract_extractor import (
    TesseractExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.types import (
    ExtractorUnavailable,
    FileType,
)
from tests.fakes import make_fitz_module, make_pil_modules


def _make_pytesseract(text='ocr text'):
    pytesseract_module = types.ModuleType('pytesseract')
    pytesseract_module.image_to_string = mock.Mock(return_value=text)
    return pytesseract_module


class TestTesseractExtractor(unittest.TestCase):
    def test_unavailable_without_pytesseract(self):
        with mock.patch.dict(sys.modules, {'pytesseract': None}):
            with self.assertRaises(ExtractorUnavailable):
                TesseractExtractor().extract(b'\x89PNG', FileType.IMAGE.value)

    def test_image_happy_path(self):
        pytesseract_module = _make_pytesseract(text='hello from ocr')
        pil_module, image_module = make_pil_modules()
        with mock.patch.dict(
            sys.modules,
            {
                'pytesseract': pytesseract_module,
                'PIL': pil_module,
                'PIL.Image': image_module,
            },
        ):
            result = TesseractExtractor(languages=['eng', 'heb']).extract(
                b'\x89PNG', FileType.IMAGE.value
            )
        self.assertEqual(result.markdown, 'hello from ocr')
        self.assertEqual(result.languages, ['eng', 'heb'])
        # ensure the lang arg threaded through
        pytesseract_module.image_to_string.assert_called_once()
        self.assertEqual(
            pytesseract_module.image_to_string.call_args.kwargs['lang'], 'eng+heb'
        )

    def test_pdf_happy_path_uses_fitz(self):
        pytesseract_module = _make_pytesseract(text='page-ocr')
        pil_module, image_module = make_pil_modules()
        fitz_module = make_fitz_module(pages_text=['', ''])
        with mock.patch.dict(
            sys.modules,
            {
                'pytesseract': pytesseract_module,
                'PIL': pil_module,
                'PIL.Image': image_module,
                'fitz': fitz_module,
            },
        ):
            result = TesseractExtractor().extract(b'%PDF', FileType.PDF.value)
        self.assertIn('page-ocr', result.markdown)
        self.assertIn('page 1', result.markdown)

    def test_pdf_requires_fitz(self):
        pytesseract_module = _make_pytesseract()
        pil_module, image_module = make_pil_modules()
        with mock.patch.dict(
            sys.modules,
            {
                'pytesseract': pytesseract_module,
                'PIL': pil_module,
                'PIL.Image': image_module,
                'fitz': None,
            },
        ):
            with self.assertRaises(ExtractorUnavailable):
                TesseractExtractor().extract(b'%PDF', FileType.PDF.value)

    def test_unknown_file_type_raises_value_error(self):
        pytesseract_module = _make_pytesseract()
        pil_module, image_module = make_pil_modules()
        with mock.patch.dict(
            sys.modules,
            {
                'pytesseract': pytesseract_module,
                'PIL': pil_module,
                'PIL.Image': image_module,
            },
        ):
            with self.assertRaises(ValueError):
                TesseractExtractor().extract(b'x', 'audio')


if __name__ == '__main__':
    unittest.main()
