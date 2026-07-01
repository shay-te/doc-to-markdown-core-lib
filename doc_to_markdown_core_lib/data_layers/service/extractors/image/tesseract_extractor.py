from typing import List, Optional

from doc_to_markdown_core_lib.constants import (
    CONFIDENCE_DOCUMENT_CHARS_NORM,
    CONFIDENCE_SINGLE_IMAGE_CHARS_NORM,
)
from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.extractor import Extractor
from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.pdf_rasterizer import (
    DEFAULT_RASTER_DPI,
    rasterize_pdf_pages,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType


class TesseractExtractor(Extractor):
    """OCR fallback for scans/images. Wrong language pack → line noise,
    so configure ``ocr_languages`` to match the corpora you receive.
    PDFs are rasterized via PyMuPDF; missing PyMuPDF → unavailable."""

    name = 'tesseract'
    file_types = (FileType.PDF, FileType.IMAGE)

    def __init__(
        self,
        languages: Optional[List[str]] = None,
        dpi: int = DEFAULT_RASTER_DPI,
    ):
        self._languages = list(languages or ['eng'])
        self._dpi = dpi

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        try:
            import io

            import pytesseract
            from PIL import Image
        except ImportError as import_error:
            raise ExtractorUnavailable(
                'pytesseract / Pillow not installed'
            ) from import_error

        lang_arg = '+'.join(self._languages)

        if file_type == FileType.IMAGE:
            img = Image.open(io.BytesIO(content))
            text = (pytesseract.image_to_string(img, lang=lang_arg) or '').strip()
            confidence = min(
                1.0,
                max(0.0, len(text) / CONFIDENCE_SINGLE_IMAGE_CHARS_NORM),
            )
            return ExtractionCandidate(
                extractor=self.name,
                markdown=text,
                confidence=confidence,
                languages=list(self._languages),
            )

        if file_type == FileType.PDF:
            parts = []
            for page_number, png_bytes in rasterize_pdf_pages(
                content, dpi=self._dpi
            ):
                img = Image.open(io.BytesIO(png_bytes))
                text = (pytesseract.image_to_string(img, lang=lang_arg) or '').strip()
                parts.append(f'<!-- page {page_number} -->\n\n{text}')

            markdown = '\n\n'.join(parts).strip()
            confidence = min(
                1.0,
                max(0.0, len(markdown) / CONFIDENCE_DOCUMENT_CHARS_NORM),
            )
            return ExtractionCandidate(
                extractor=self.name,
                markdown=markdown,
                confidence=confidence,
                languages=list(self._languages),
            )

        raise ValueError(f'tesseract cannot handle file_type={file_type!r}')
