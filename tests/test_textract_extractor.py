import os
import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractors.doc.textract_extractor import (
    TextractExtractor,
    _PLAIN_TEXT_CONFIDENCE_DISCOUNT,
)
from doc_to_markdown_core_lib.data_layers.service.types import (
    ExtractorUnavailable,
    FileType,
)
from tests.patch_module import patch_module


def _make_textract(process_result: bytes):
    textract_module = types.ModuleType('textract')
    textract_module.process = mock.Mock(return_value=process_result)
    return textract_module


class TestTextractExtractor(unittest.TestCase):
    def test_unavailable_without_textract(self):
        with mock.patch.dict(sys.modules, {'textract': None}):
            with self.assertRaises(ExtractorUnavailable):
                TextractExtractor().extract(b'\xd0\xcf', FileType.DOC.value)

    def test_doc_happy_path_uses_doc_suffix(self):
        textract_module = _make_textract(b'legacy doc body')
        with patch_module('textract', textract_module):
            result = TextractExtractor().extract(b'\xd0\xcf', FileType.DOC.value)
        self.assertEqual(result.markdown, 'legacy doc body')
        self.assertGreater(result.confidence, 0.0)
        processed_path = textract_module.process.call_args.args[0]
        self.assertTrue(processed_path.endswith('.doc'))
        # the temp file must be cleaned up after processing
        self.assertFalse(os.path.exists(processed_path))

    def test_docx_uses_docx_suffix(self):
        textract_module = _make_textract(b'docx body')
        with patch_module('textract', textract_module):
            TextractExtractor().extract(b'PK', FileType.DOCX.value)
        processed_path = textract_module.process.call_args.args[0]
        self.assertTrue(processed_path.endswith('.docx'))

    def test_full_length_text_caps_at_discounted_confidence(self):
        long_text = ('word ' * 1000).encode('utf-8')
        with patch_module('textract', _make_textract(long_text)):
            result = TextractExtractor().extract(b'\xd0\xcf', FileType.DOC.value)
        self.assertAlmostEqual(
            result.confidence, _PLAIN_TEXT_CONFIDENCE_DISCOUNT
        )


if __name__ == '__main__':
    unittest.main()
