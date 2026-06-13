import sys
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractors.docx.mammoth_extractor import (
    MammothExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.types import (
    ExtractorUnavailable,
    FileType,
)
from tests.fakes import make_mammoth_module, patch_module


class TestMammothExtractor(unittest.TestCase):
    def test_unavailable_without_mammoth(self):
        with mock.patch.dict(sys.modules, {'mammoth': None}):
            with self.assertRaises(ExtractorUnavailable):
                MammothExtractor().extract(b'PK', FileType.DOCX.value)

    def test_happy_path(self):
        with patch_module('mammoth', make_mammoth_module('# heading\n\nbody')):
            result = MammothExtractor().extract(b'PK', FileType.DOCX.value)
        self.assertIn('# heading', result.markdown)
        self.assertGreater(result.confidence, 0.0)

    def test_empty_value_gives_zero_confidence(self):
        with patch_module('mammoth', make_mammoth_module('')):
            result = MammothExtractor().extract(b'PK', FileType.DOCX.value)
        self.assertEqual(result.confidence, 0.0)


if __name__ == '__main__':
    unittest.main()
