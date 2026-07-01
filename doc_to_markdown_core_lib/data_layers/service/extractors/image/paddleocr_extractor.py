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


class PaddleOcrExtractor(ImageOcrExtractor):
    """PaddleOCR (``paddleocr``) — Baidu's full detect+recognize pipeline
    (``rapidocr`` is only its lite ONNX port), a strong high-accuracy
    opinion. ``languages`` uses paddle's own codes ('en'/'ch'/...), so it is
    NOT fed the tesseract config; paddle takes a single code, so the first
    is used."""

    name = 'paddleocr'

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
            from paddleocr import PaddleOCR
        except ImportError as import_error:
            raise ExtractorUnavailable('paddleocr not installed') from import_error
        try:
            return PaddleOCR(
                use_angle_cls=True, lang=self._ocr_languages[0], show_log=False
            )
        except Exception as init_error:
            raise ExtractorUnavailable(
                f'paddleocr init failed: {init_error}'
            ) from init_error

    def _read_image(self, engine, image_bytes: bytes) -> str:
        import io

        import numpy
        from PIL import Image

        image = numpy.array(Image.open(io.BytesIO(image_bytes)).convert('RGB'))
        pages = engine.ocr(image, cls=True) or []
        lines = [
            str(entry[1][0]).strip() for page in pages for entry in (page or [])
        ]
        return '\n'.join(line for line in lines if line).strip()
