import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.doctr_extractor import (
    DocTrExtractor,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType


def _make_doctr(rendered, predictor_raises=None):
    doctr_module = types.ModuleType('doctr')
    models_module = types.ModuleType('doctr.models')
    io_module = types.ModuleType('doctr.io')

    class FakeResult:
        def render(self):
            return rendered

    def ocr_predictor(pretrained=True):
        if predictor_raises is not None:
            raise predictor_raises

        def model(document):
            return FakeResult()

        return model

    class FakeDocumentFile:
        @staticmethod
        def from_images(image_bytes):
            return ['document']

    models_module.ocr_predictor = ocr_predictor
    io_module.DocumentFile = FakeDocumentFile
    doctr_module.models = models_module
    doctr_module.io = io_module
    return {
        'doctr': doctr_module,
        'doctr.models': models_module,
        'doctr.io': io_module,
    }


class TestDocTrExtractor(unittest.TestCase):
    def test_unavailable_without_doctr(self):
        with mock.patch.dict(
            sys.modules, {'doctr': None, 'doctr.models': None}
        ):
            with self.assertRaises(ExtractorUnavailable):
                DocTrExtractor().extract(b'\x89PNG', FileType.IMAGE)

    def test_init_failure_raises_unavailable(self):
        modules = _make_doctr('', predictor_raises=RuntimeError('no weights'))
        with mock.patch.dict(sys.modules, modules):
            with self.assertRaises(ExtractorUnavailable):
                DocTrExtractor().extract(b'\x89PNG', FileType.IMAGE)

    def test_image_happy_path(self):
        with mock.patch.dict(sys.modules, _make_doctr('rendered doc text')):
            result = DocTrExtractor().extract(b'\x89PNG', FileType.IMAGE)
        self.assertEqual(result.markdown, 'rendered doc text')
        self.assertGreater(result.confidence, 0.0)

    def test_empty_render_yields_empty_candidate(self):
        with mock.patch.dict(sys.modules, _make_doctr(None)):
            result = DocTrExtractor().extract(b'\x89PNG', FileType.IMAGE)
        self.assertEqual(result.markdown, '')
        self.assertEqual(result.confidence, 0.0)


if __name__ == '__main__':
    unittest.main()
