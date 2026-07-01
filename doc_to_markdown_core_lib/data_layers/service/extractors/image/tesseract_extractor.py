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


class TesseractExtractor(ImageOcrExtractor):
    """OCR fallback for scans/images. Wrong language pack → line noise, so
    configure ``ocr_languages`` (tesseract codes: 'eng'/'heb'/...) to match
    the corpora you receive."""

    name = 'tesseract'

    def __init__(
        self,
        languages: Optional[List[str]] = None,
        dpi: int = DEFAULT_RASTER_DPI,
    ):
        super().__init__(dpi)
        self._ocr_languages = list(languages or ['eng'])

    def _languages(self) -> List[str]:
        return list(self._ocr_languages)

    def _load_engine(self):
        try:
            import pytesseract
            from PIL import Image
        except ImportError as import_error:
            raise ExtractorUnavailable(
                'pytesseract / Pillow not installed'
            ) from import_error
        return (pytesseract, Image)

    def _read_image(self, engine, image_bytes: bytes) -> str:
        import io

        pytesseract, image_module = engine
        lang_arg = '+'.join(self._ocr_languages)
        image = image_module.open(io.BytesIO(image_bytes))
        return (pytesseract.image_to_string(image, lang=lang_arg) or '').strip()
