from doc_to_markdown_core_lib.data_layers.service.confidence_norms import (
    CONFIDENCE_DOCUMENT_CHARS_NORM,
    CONFIDENCE_SINGLE_IMAGE_CHARS_NORM,
)
from doc_to_markdown_core_lib.data_layers.service.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.service.extractor import Extractor
from doc_to_markdown_core_lib.data_layers.service.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.pdf_rasterizer import (
    DEFAULT_RASTER_DPI,
    rasterize_pdf_pages,
)
from doc_to_markdown_core_lib.data_layers.service.file_type import FileType


class RapidOcrExtractor(Extractor):
    """Lightweight ONNX OCR (``rapidocr-onnxruntime``) — third OCR
    opinion; ships its own latin+chinese models, no language config.
    PDFs are rasterized via PyMuPDF."""

    name = 'rapidocr'
    file_types = (FileType.PDF, FileType.IMAGE)

    def __init__(self, dpi: int = DEFAULT_RASTER_DPI):
        self._dpi = dpi

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as import_error:
            raise ExtractorUnavailable(
                'rapidocr-onnxruntime not installed'
            ) from import_error

        engine = RapidOCR()

        if file_type == FileType.IMAGE:
            text = self._read_image(engine, content)
            confidence = min(
                1.0,
                max(0.0, len(text) / CONFIDENCE_SINGLE_IMAGE_CHARS_NORM),
            )
            return ExtractionCandidate(
                extractor=self.name,
                markdown=text,
                confidence=confidence,
                languages=[],
            )

        if file_type == FileType.PDF:
            parts = []
            for page_number, png_bytes in rasterize_pdf_pages(
                content, dpi=self._dpi
            ):
                text = self._read_image(engine, png_bytes)
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
                languages=[],
            )

        raise ValueError(f'rapidocr cannot handle file_type={file_type!r}')

    @staticmethod
    def _read_image(engine, image_bytes: bytes) -> str:
        detections, _elapsed = engine(image_bytes)
        if not detections:
            return ''
        return '\n'.join(
            (detection[1] or '').strip()
            for detection in detections
            if len(detection) > 1
        ).strip()
