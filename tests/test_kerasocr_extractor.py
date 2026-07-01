import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.kerasocr_extractor import (
    KerasOcrExtractor,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType
from tests.make_pil_modules import make_pil_modules


def _fake_numpy():
    numpy_module = types.ModuleType('numpy')
    numpy_module.array = lambda image: image
    return numpy_module


def _make_keras_ocr(predictions, init_raises=None):
    module = types.ModuleType('keras_ocr')
    pipeline_module = types.ModuleType('keras_ocr.pipeline')

    class FakePipeline:
        def __init__(self):
            if init_raises is not None:
                raise init_raises

        def recognize(self, images):
            return predictions

    pipeline_module.Pipeline = FakePipeline
    module.pipeline = pipeline_module
    return {'keras_ocr': module, 'keras_ocr.pipeline': pipeline_module}


def _image_modules(keras_modules):
    pil_module, image_module = make_pil_modules(open_returns=mock.Mock())
    return {
        **keras_modules,
        'numpy': _fake_numpy(),
        'PIL': pil_module,
        'PIL.Image': image_module,
    }


class TestKerasOcrExtractor(unittest.TestCase):
    def test_unavailable_without_keras_ocr(self):
        with mock.patch.dict(sys.modules, {'keras_ocr': None}):
            with self.assertRaises(ExtractorUnavailable):
                KerasOcrExtractor().extract(b'\x89PNG', FileType.IMAGE)

    def test_init_failure_raises_unavailable(self):
        modules = _make_keras_ocr(None, init_raises=RuntimeError('no tf'))
        with mock.patch.dict(sys.modules, modules):
            with self.assertRaises(ExtractorUnavailable):
                KerasOcrExtractor().extract(b'\x89PNG', FileType.IMAGE)

    def test_image_happy_path(self):
        # recognize returns one (word, box) list per image; a blank word
        # exercises the empty-word filter.
        predictions = [[('Hello', [[0, 0]]), ('   ', [[0, 1]])]]
        with mock.patch.dict(
            sys.modules, _image_modules(_make_keras_ocr(predictions))
        ):
            result = KerasOcrExtractor().extract(b'\x89PNG', FileType.IMAGE)
        self.assertEqual(result.markdown, 'Hello')
        self.assertGreater(result.confidence, 0.0)

    def test_no_predictions_yields_empty_candidate(self):
        with mock.patch.dict(
            sys.modules, _image_modules(_make_keras_ocr(None))
        ):
            result = KerasOcrExtractor().extract(b'\x89PNG', FileType.IMAGE)
        self.assertEqual(result.markdown, '')
        self.assertEqual(result.confidence, 0.0)


if __name__ == '__main__':
    unittest.main()
