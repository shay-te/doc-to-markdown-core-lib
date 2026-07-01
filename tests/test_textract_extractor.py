import os
import sys
import types
import unittest
from unittest import mock

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.doc.textract_extractor import (
    TextractExtractor,
    _PLAIN_TEXT_CONFIDENCE_DISCOUNT,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType
from tests.patch_module import patch_module
from tests.read_fixture import read_fixture


def _make_textract(process_result: bytes):
    textract_module = types.ModuleType('textract')
    textract_module.process = mock.Mock(return_value=process_result)
    return textract_module


class TestTextractExtractor(unittest.TestCase):
    def test_unavailable_without_textract(self):
        with mock.patch.dict(sys.modules, {'textract': None}):
            with self.assertRaises(ExtractorUnavailable):
                TextractExtractor().extract(b'\xd0\xcf', FileType.DOC)

    def test_doc_happy_path_uses_doc_suffix(self):
        textract_module = _make_textract(b'legacy doc body')
        with patch_module('textract', textract_module):
            result = TextractExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertEqual(result.markdown, 'legacy doc body')
        self.assertGreater(result.confidence, 0.0)
        processed_path = textract_module.process.call_args.args[0]
        self.assertTrue(processed_path.endswith(f'.{FileType.DOC.value}'))
        # the temp file must be cleaned up after processing
        self.assertFalse(os.path.exists(processed_path))

    def test_docx_uses_docx_suffix(self):
        textract_module = _make_textract(b'docx body')
        with patch_module('textract', textract_module):
            TextractExtractor().extract(
                read_fixture('sample.docx'), FileType.DOCX
            )
        processed_path = textract_module.process.call_args.args[0]
        self.assertTrue(processed_path.endswith(f'.{FileType.DOCX.value}'))

    def test_full_length_text_caps_at_discounted_confidence(self):
        long_text = ('word ' * 1000).encode('utf-8')
        with patch_module('textract', _make_textract(long_text)):
            result = TextractExtractor().extract(b'\xd0\xcf', FileType.DOC)
        self.assertAlmostEqual(
            result.confidence, _PLAIN_TEXT_CONFIDENCE_DISCOUNT
        )

    def test_unlink_oserror_is_swallowed(self):
        # The temp-file cleanup is best-effort: a locked /tmp must not
        # mask a successful extraction. ``os`` is imported lazily
        # inside ``extract`` so we patch the global symbol instead of a
        # module-level attribute.
        textract_module = _make_textract(b'still ok')
        with patch_module('textract', textract_module):
            with mock.patch('os.unlink', side_effect=OSError('locked')):
                result = TextractExtractor().extract(
                    b'\xd0\xcf', FileType.DOC
                )
        self.assertEqual(result.markdown, 'still ok')


if __name__ == '__main__':
    unittest.main()
