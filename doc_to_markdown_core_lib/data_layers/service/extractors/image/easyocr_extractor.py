from typing import List, Optional

from doc_to_markdown_core_lib.data_layers.service.extractors.image.image_ocr_extractor import (
    ImageOcrExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.pdf_rasterizer import (
    DEFAULT_RASTER_DPI,
)
from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)


class EasyOcrExtractor(ImageOcrExtractor):
    """Deep-learning OCR (``easyocr``) — a second OCR opinion next to
    tesseract, stronger on photos/low-contrast scans. ``languages`` uses
    easyocr's own codes ('en', 'he', ...) and must respect easyocr's
    combination rules, so it is NOT fed from the tesseract language config
    (an incompatible combo surfaces as ExtractorUnavailable, not a crash)."""

    name = 'easyocr'

    def __init__(
        self,
        languages: Optional[List[str]] = None,
        dpi: int = DEFAULT_RASTER_DPI,
    ):
        super().__init__(dpi)
        self._ocr_languages = list(languages or ['en'])

    def _languages(self) -> List[str]:
        return list(self._ocr_languages)

    def _load_engine(self):
        try:
            import easyocr
        except ImportError as import_error:
            raise ExtractorUnavailable('easyocr not installed') from import_error
        try:
            return easyocr.Reader(self._ocr_languages, verbose=False)
        except Exception as reader_error:
            raise ExtractorUnavailable(
                f'easyocr reader init failed: {reader_error}'
            ) from reader_error

    def _read_image(self, engine, image_bytes: bytes) -> str:
        lines = engine.readtext(image_bytes, detail=0, paragraph=True) or []
        return '\n'.join(line.strip() for line in lines if line).strip()
