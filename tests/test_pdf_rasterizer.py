import sys
import unittest
from unittest import mock

from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.pdf_rasterizer import (
    DEFAULT_RASTER_DPI,
    rasterize_pdf_pages,
)
from tests.make_fitz_module import make_fitz_module
from tests.read_fixture import read_fixture


class TestPdfRasterizer(unittest.TestCase):
    def test_without_fitz_raises_unavailable(self):
        with mock.patch.dict(sys.modules, {'fitz': None}):
            with self.assertRaises(ExtractorUnavailable):
                list(rasterize_pdf_pages(read_fixture('sample.pdf')))

    def test_yields_one_png_per_page_one_based(self):
        png_bytes = read_fixture('sample.png')
        fitz_module = make_fitz_module(pages_text=['', ''], pixmap_bytes=png_bytes)
        with mock.patch.dict(sys.modules, {'fitz': fitz_module}):
            pages = list(rasterize_pdf_pages(
                read_fixture('sample.pdf'), dpi=DEFAULT_RASTER_DPI
            ))
        self.assertEqual(pages, [(1, png_bytes), (2, png_bytes)])


if __name__ == '__main__':
    unittest.main()
