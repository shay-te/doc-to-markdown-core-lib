import unittest

from doc_to_markdown_core_lib.data_layers.service.extractors.md.md_extractor import (
    MdExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.types import FileType


class TestMdExtractor(unittest.TestCase):
    def test_pass_through_utf8(self):
        result = MdExtractor().extract(
            'שלום\nworld'.encode('utf-8'), FileType.MD.value
        )
        self.assertEqual(result.markdown, 'שלום\nworld')
        self.assertEqual(result.confidence, 1.0)

    def test_strips_bom(self):
        result = MdExtractor().extract('﻿hello'.encode('utf-8'), FileType.MD.value)
        self.assertEqual(result.markdown, 'hello')


if __name__ == '__main__':
    unittest.main()
