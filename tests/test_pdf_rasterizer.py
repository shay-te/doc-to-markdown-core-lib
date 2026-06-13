import sys
import unittest
from unittest import mock

from doc_to_markdown_core_lib.data_layers.service.extractors.image.pdf_rasterizer import (
    DEFAULT_RASTER_DPI,
    rasterize_pdf_pages,
)
from doc_to_markdown_core_lib.data_layers.service.types import ExtractorUnavailable
from tests.make_fitz_module import make_fitz_module


class TestPdfRasterizer(unittest.TestCase):
    def test_without_fitz_raises_unavailable(self):
        with mock.patch.dict(sys.modules, {'fitz': None}):
            with self.assertRaises(ExtractorUnavailable):
                list(rasterize_pdf_pages(b'%PDF'))

    def test_yields_one_png_per_page_one_based(self):
        png_bytes = b'\x89PNG\r\n\x1a\nfake'
        fitz_module = make_fitz_module(pages_text=['', ''], pixmap_bytes=png_bytes)
        with mock.patch.dict(sys.modules, {'fitz': fitz_module}):
            pages = list(rasterize_pdf_pages(b'%PDF', dpi=DEFAULT_RASTER_DPI))
        self.assertEqual(pages, [(1, png_bytes), (2, png_bytes)])


if __name__ == '__main__':
    unittest.main()
