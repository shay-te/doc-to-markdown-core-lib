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


class EasyOcrExtractor(Extractor):
    """Deep-learning OCR (``easyocr``) — a second OCR opinion next to
    tesseract, stronger on photos/low-contrast scans. ``languages``
    uses easyocr's own codes ('en', 'he', ...) and must respect
    easyocr's combination rules, so it is NOT fed from the tesseract
    language config. PDFs are rasterized via PyMuPDF."""

    name = 'easyocr'
    file_types = (FileType.PDF, FileType.IMAGE)

    def __init__(
        self,
        languages: Optional[List[str]] = None,
        dpi: int = DEFAULT_RASTER_DPI,
    ):
        self._languages = list(languages or ['en'])
        self._dpi = dpi

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        try:
            import easyocr
        except ImportError as import_error:
            raise ExtractorUnavailable(
                'easyocr not installed'
            ) from import_error

        try:
            reader = easyocr.Reader(self._languages, verbose=False)
        except Exception as reader_error:
            raise ExtractorUnavailable(
                f'easyocr reader init failed: {reader_error}'
            ) from reader_error

        if file_type == FileType.IMAGE:
            text = self._read_image(reader, content)
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
                text = self._read_image(reader, png_bytes)
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

        raise ValueError(f'easyocr cannot handle file_type={file_type!r}')

    @staticmethod
    def _read_image(reader, image_bytes: bytes) -> str:
        lines = reader.readtext(image_bytes, detail=0, paragraph=True) or []
        return '\n'.join(line.strip() for line in lines if line).strip()
