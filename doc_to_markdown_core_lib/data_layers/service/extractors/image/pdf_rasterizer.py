"""Shared PDF → page-PNG rasterization for the OCR extractors."""
from typing import Iterator, Tuple

from doc_to_markdown_core_lib.data_layers.service.extractor_unavailable import (
    ExtractorUnavailable,
)

DEFAULT_RASTER_DPI = 200


def rasterize_pdf_pages(
    content: bytes, dpi: int = DEFAULT_RASTER_DPI
) -> Iterator[Tuple[int, bytes]]:
    """Yields ``(page_number, png_bytes)`` per page, 1-based."""
    try:
        import fitz
    except ImportError as import_error:
        raise ExtractorUnavailable(
            'PyMuPDF (fitz) required to rasterize PDF pages for OCR'
        ) from import_error

    doc = fitz.open(stream=content, filetype='pdf')
    try:
        for page_number, page in enumerate(doc, start=1):
            pix = page.get_pixmap(dpi=dpi)
            yield page_number, pix.tobytes('png')
    finally:
        doc.close()
