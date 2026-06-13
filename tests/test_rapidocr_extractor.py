import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.rapidocr_extractor import (
    RapidOcrExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType
from tests.make_fitz_module import make_fitz_module
from tests.patch_module import patch_module


def _make_rapidocr(detections):
    rapidocr_module = types.ModuleType('rapidocr_onnxruntime')

    class FakeRapidOCR:
        def __call__(self, image_bytes):
            return detections, 0.01

    rapidocr_module.RapidOCR = FakeRapidOCR
    return rapidocr_module


class TestRapidOcrExtractor(unittest.TestCase):
    def test_unavailable_without_rapidocr(self):
        with mock.patch.dict(sys.modules, {'rapidocr_onnxruntime': None}):
            with self.assertRaises(ExtractorUnavailable):
                RapidOcrExtractor().extract(b'\x89PNG', FileType.IMAGE)

    def test_image_happy_path(self):
        detections = [
            [[[0, 0]], 'first line', 0.98],
            [[[0, 1]], 'second line', 0.91],
        ]
        with patch_module('rapidocr_onnxruntime', _make_rapidocr(detections)):
            result = RapidOcrExtractor().extract(b'\x89PNG', FileType.IMAGE)
        self.assertEqual(result.markdown, 'first line\nsecond line')
        self.assertGreater(result.confidence, 0.0)

    def test_no_detections_yields_empty_candidate(self):
        with patch_module('rapidocr_onnxruntime', _make_rapidocr(None)):
            result = RapidOcrExtractor().extract(b'\x89PNG', FileType.IMAGE)
        self.assertEqual(result.markdown, '')
        self.assertEqual(result.confidence, 0.0)

    def test_pdf_happy_path_rasterizes_via_fitz(self):
        detections = [[[[0, 0]], 'scanned text', 0.9]]
        with mock.patch.dict(
            sys.modules,
            {
                'rapidocr_onnxruntime': _make_rapidocr(detections),
                'fitz': make_fitz_module(pages_text=['']),
            },
        ):
            result = RapidOcrExtractor().extract(b'%PDF', FileType.PDF)
        self.assertIn('scanned text', result.markdown)
        self.assertIn('page 1', result.markdown)

    def test_unknown_file_type_raises_value_error(self):
        with patch_module('rapidocr_onnxruntime', _make_rapidocr([])):
            with self.assertRaises(ValueError):
                RapidOcrExtractor().extract(b'x', 'audio')


if __name__ == '__main__':
    unittest.main()
