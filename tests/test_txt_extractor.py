import unittest

from doc_to_markdown_core_lib.data_layers.service.extractors.txt.txt_extractor import (
    TxtExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType


class TestTxtExtractor(unittest.TestCase):
    def test_utf8(self):
        result = TxtExtractor().extract('مرحبا'.encode('utf-8'), FileType.TXT.value)
        self.assertEqual(result.markdown, 'مرحبا')
        self.assertEqual(result.confidence, 1.0)

    def test_utf16(self):
        result = TxtExtractor().extract('hello'.encode('utf-16'), FileType.TXT.value)
        self.assertEqual(result.markdown, 'hello')
        self.assertEqual(result.confidence, 1.0)

    def test_falls_back_to_latin1(self):
        # 0xa3 is invalid utf-8 and odd-length for utf-16 → latin-1 branch.
        result = TxtExtractor().extract(b'\xa3', FileType.TXT.value)
        self.assertEqual(result.confidence, 0.5)
        self.assertIn('£', result.markdown)


if __name__ == '__main__':
    unittest.main()
