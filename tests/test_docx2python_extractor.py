import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.docx.docx2python_extractor import (
    Docx2pythonExtractor,
    _PLAIN_TEXT_CONFIDENCE_DISCOUNT,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType
from tests.patch_module import patch_module

_DOCX_BYTES = b'PK\x03\x04docx'


def _make_docx2python(text):
    module = types.ModuleType('docx2python')
    context = mock.MagicMock()
    context.__enter__.return_value = types.SimpleNamespace(text=text)
    context.__exit__.return_value = False
    module.docx2python = mock.Mock(return_value=context)
    return module


class TestDocx2pythonExtractor(unittest.TestCase):
    def test_unavailable_without_docx2python(self):
        with mock.patch.dict(sys.modules, {'docx2python': None}):
            with self.assertRaises(ExtractorUnavailable):
                Docx2pythonExtractor().extract(_DOCX_BYTES, FileType.DOCX)

    def test_happy_path_strips_text(self):
        with patch_module('docx2python', _make_docx2python('  body text  ')):
            result = Docx2pythonExtractor().extract(_DOCX_BYTES, FileType.DOCX)
        self.assertEqual(result.markdown, 'body text')
        self.assertGreater(result.confidence, 0.0)

    def test_none_text_yields_empty_zero_confidence(self):
        with patch_module('docx2python', _make_docx2python(None)):
            result = Docx2pythonExtractor().extract(_DOCX_BYTES, FileType.DOCX)
        self.assertEqual(result.markdown, '')
        self.assertEqual(result.confidence, 0.0)

    def test_full_length_text_caps_at_discounted_confidence(self):
        with patch_module('docx2python', _make_docx2python('word ' * 1000)):
            result = Docx2pythonExtractor().extract(_DOCX_BYTES, FileType.DOCX)
        self.assertAlmostEqual(result.confidence, _PLAIN_TEXT_CONFIDENCE_DISCOUNT)


if __name__ == '__main__':
    unittest.main()
