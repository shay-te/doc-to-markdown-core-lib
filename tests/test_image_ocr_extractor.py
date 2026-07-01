import unittest

from doc_to_markdown_core_lib.data_layers.service.extractors.image.image_ocr_extractor import (
    ImageOcrExtractor,
)


class TestImageOcrExtractorBase(unittest.TestCase):
    """The base leaves the two engine hooks abstract; concrete engines
    override them. Exercise the defaults so the contract is pinned."""

    def test_load_engine_is_abstract(self):
        with self.assertRaises(NotImplementedError):
            ImageOcrExtractor()._load_engine()

    def test_read_image_is_abstract(self):
        with self.assertRaises(NotImplementedError):
            ImageOcrExtractor()._read_image(None, b'')


if __name__ == '__main__':
    unittest.main()
