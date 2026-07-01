import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.doc.tika_extractor import (
    TikaExtractor,
    _PLAIN_TEXT_CONFIDENCE_DISCOUNT,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType
from tests.patch_module import patch_module


def _make_tika(from_buffer_result):
    module = types.ModuleType('tika')
    module.parser = types.SimpleNamespace(
        from_buffer=mock.Mock(return_value=from_buffer_result)
    )
    return module


class TestTikaExtractor(unittest.TestCase):
    def test_unavailable_without_tika(self):
        with mock.patch.dict(sys.modules, {'tika': None}):
            with self.assertRaises(ExtractorUnavailable):
                TikaExtractor().extract(b'\xd0\xcf', FileType.DOC)

    def test_doc_happy_path_reads_content(self):
        with patch_module('tika', _make_tika({'content': '  doc body  '})):
            result = TikaExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertEqual(result.markdown, 'doc body')
        self.assertGreater(result.confidence, 0.0)

    def test_docx_is_supported_too(self):
        with patch_module('tika', _make_tika({'content': 'docx body'})):
            result = TikaExtractor().extract(b'PK\x03\x04', FileType.DOCX)
        self.assertEqual(result.markdown, 'docx body')

    def test_none_content_yields_empty(self):
        with patch_module('tika', _make_tika({'content': None})):
            result = TikaExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertEqual(result.markdown, '')
        self.assertEqual(result.confidence, 0.0)

    def test_none_parsed_yields_empty(self):
        with patch_module('tika', _make_tika(None)):
            result = TikaExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertEqual(result.markdown, '')

    def test_full_length_text_caps_at_discounted_confidence(self):
        with patch_module('tika', _make_tika({'content': 'word ' * 1000})):
            result = TikaExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertAlmostEqual(result.confidence, _PLAIN_TEXT_CONFIDENCE_DISCOUNT)


if __name__ == '__main__':
    unittest.main()
