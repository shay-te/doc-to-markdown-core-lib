import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.paddleocr_extractor import (
    PaddleOcrExtractor,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType
from tests.make_pil_modules import make_pil_modules


def _fake_numpy():
    numpy_module = types.ModuleType('numpy')
    numpy_module.array = lambda image: image
    return numpy_module


def _make_paddleocr(pages, init_raises=None):
    module = types.ModuleType('paddleocr')

    class FakePaddleOCR:
        def __init__(self, use_angle_cls=None, lang=None, show_log=None):
            if init_raises is not None:
                raise init_raises

        def ocr(self, image, cls=True):
            return pages

    module.PaddleOCR = FakePaddleOCR
    return module


def _image_modules(paddle_module):
    pil_module, image_module = make_pil_modules(open_returns=mock.Mock())
    return {
        'paddleocr': paddle_module,
        'numpy': _fake_numpy(),
        'PIL': pil_module,
        'PIL.Image': image_module,
    }


class TestPaddleOcrExtractor(unittest.TestCase):
    def test_unavailable_without_paddleocr(self):
        with mock.patch.dict(sys.modules, {'paddleocr': None}):
            with self.assertRaises(ExtractorUnavailable):
                PaddleOcrExtractor().extract(b'\x89PNG', FileType.IMAGE)

    def test_init_failure_raises_unavailable(self):
        module = _make_paddleocr([], init_raises=RuntimeError('no model'))
        with mock.patch.dict(sys.modules, {'paddleocr': module}):
            with self.assertRaises(ExtractorUnavailable):
                PaddleOcrExtractor().extract(b'\x89PNG', FileType.IMAGE)

    def test_image_happy_path(self):
        # A None page (paddle's "no text on page") plus a real page with one
        # blank line, to exercise every branch of the result walk.
        pages = [
            None,
            [
                [[[0, 0]], ('Hello world', 0.99)],
                [[[0, 1]], ('   ', 0.10)],
            ],
        ]
        with mock.patch.dict(sys.modules, _image_modules(_make_paddleocr(pages))):
            result = PaddleOcrExtractor(languages=['en']).extract(
                b'\x89PNG', FileType.IMAGE
            )
        self.assertEqual(result.markdown, 'Hello world')
        self.assertEqual(result.languages, ['en'])
        self.assertGreater(result.confidence, 0.0)

    def test_no_detections_yields_empty_candidate(self):
        with mock.patch.dict(sys.modules, _image_modules(_make_paddleocr(None))):
            result = PaddleOcrExtractor().extract(b'\x89PNG', FileType.IMAGE)
        self.assertEqual(result.markdown, '')
        self.assertEqual(result.confidence, 0.0)


if __name__ == '__main__':
    unittest.main()
