import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.ocrmac_extractor import (
    OcrMacExtractor,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType
from tests.make_pil_modules import make_pil_modules


def _make_ocrmac(annotations):
    package = types.ModuleType('ocrmac')
    inner = types.ModuleType('ocrmac.ocrmac')

    class FakeOCR:
        def __init__(self, image):
            self._image = image

        def recognize(self):
            return annotations

    inner.OCR = FakeOCR
    package.ocrmac = inner
    return package, inner


def _image_modules(ocrmac_package, ocrmac_inner):
    pil_module, image_module = make_pil_modules(open_returns=mock.Mock())
    return {
        'ocrmac': ocrmac_package,
        'ocrmac.ocrmac': ocrmac_inner,
        'PIL': pil_module,
        'PIL.Image': image_module,
    }


class TestOcrMacExtractor(unittest.TestCase):
    def test_unavailable_without_ocrmac(self):
        with mock.patch.dict(sys.modules, {'ocrmac': None}):
            with self.assertRaises(ExtractorUnavailable):
                OcrMacExtractor().extract(b'\x89PNG', FileType.IMAGE)

    def test_image_happy_path(self):
        # Apple Vision returns (text, confidence, bbox); one blank line
        # exercises the empty-line filter.
        annotations = [
            ('Hello from Vision', 0.98, [0, 0, 1, 1]),
            ('   ', 0.20, [0, 1, 1, 1]),
        ]
        package, inner = _make_ocrmac(annotations)
        with mock.patch.dict(sys.modules, _image_modules(package, inner)):
            result = OcrMacExtractor().extract(b'\x89PNG', FileType.IMAGE)
        self.assertEqual(result.markdown, 'Hello from Vision')
        self.assertGreater(result.confidence, 0.0)

    def test_no_detections_yields_empty_candidate(self):
        package, inner = _make_ocrmac(None)
        with mock.patch.dict(sys.modules, _image_modules(package, inner)):
            result = OcrMacExtractor().extract(b'\x89PNG', FileType.IMAGE)
        self.assertEqual(result.markdown, '')
        self.assertEqual(result.confidence, 0.0)


if __name__ == '__main__':
    unittest.main()
