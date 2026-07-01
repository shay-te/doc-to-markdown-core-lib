import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.docx.docx2txt_extractor import (
    Docx2txtExtractor,
    _PLAIN_TEXT_CONFIDENCE_DISCOUNT,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType
from tests.patch_module import patch_module

_DOCX_BYTES = b'PK\x03\x04docx'


def _make_docx2txt(process_result):
    module = types.ModuleType('docx2txt')
    module.process = mock.Mock(return_value=process_result)
    return module


class TestDocx2txtExtractor(unittest.TestCase):
    def test_unavailable_without_docx2txt(self):
        with mock.patch.dict(sys.modules, {'docx2txt': None}):
            with self.assertRaises(ExtractorUnavailable):
                Docx2txtExtractor().extract(_DOCX_BYTES, FileType.DOCX)

    def test_happy_path_strips_text(self):
        module = _make_docx2txt('  docx body text  ')
        with patch_module('docx2txt', module):
            result = Docx2txtExtractor().extract(_DOCX_BYTES, FileType.DOCX)
        self.assertEqual(result.markdown, 'docx body text')
        self.assertGreater(result.confidence, 0.0)

    def test_none_result_yields_empty_zero_confidence(self):
        module = _make_docx2txt(None)
        with patch_module('docx2txt', module):
            result = Docx2txtExtractor().extract(_DOCX_BYTES, FileType.DOCX)
        self.assertEqual(result.markdown, '')
        self.assertEqual(result.confidence, 0.0)

    def test_full_length_text_caps_at_discounted_confidence(self):
        module = _make_docx2txt('word ' * 1000)
        with patch_module('docx2txt', module):
            result = Docx2txtExtractor().extract(_DOCX_BYTES, FileType.DOCX)
        self.assertAlmostEqual(result.confidence, _PLAIN_TEXT_CONFIDENCE_DISCOUNT)


if __name__ == '__main__':
    unittest.main()
