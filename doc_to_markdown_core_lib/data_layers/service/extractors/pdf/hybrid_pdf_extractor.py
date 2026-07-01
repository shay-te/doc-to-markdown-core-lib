from doc_to_markdown_core_lib.constants import CONFIDENCE_DOCUMENT_CHARS_NORM
from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.extractor import Extractor
from doc_to_markdown_core_lib.data_layers.service.extractors.image.pdf_rasterizer import (
    DEFAULT_RASTER_DPI,
)
from doc_to_markdown_core_lib.error_handling.extractor_unavailable import (
    ExtractorUnavailable,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType

# A page with fewer than this many text-layer chars is treated as image-only
# (scanned figure, newspaper clipping) and sent to OCR.
TEXT_LAYER_PAGE_FLOOR = 200


class HybridPdfExtractor(Extractor):
    """Most-complete PDF path: native text where a page has a text layer, OCR
    only for image-only pages. Delegates per-page OCR to any image extractor
    (via its ``FileType.IMAGE`` path); unavailable if PyMuPDF or — once a
    sparse page is hit — the OCR backend is unavailable.
    """

    name = 'pymupdf_ocr_hybrid'
    file_types = (FileType.PDF,)

    def __init__(
        self,
        ocr_extractor: Extractor,
        dpi: int = DEFAULT_RASTER_DPI,
        text_layer_floor: int = TEXT_LAYER_PAGE_FLOOR,
    ):
        self._ocr_extractor = ocr_extractor
        self._dpi = dpi
        self._text_layer_floor = text_layer_floor

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        try:
            import fitz
        except ImportError as import_error:
            raise ExtractorUnavailable(
                'PyMuPDF (fitz) not installed'
            ) from import_error

        parts = []
        languages = []
        # Conditional per-page rasterization off the already-open doc — the
        # shared rasterize_pdf_pages renders *every* page, which this avoids.
        doc = fitz.open(stream=content, filetype=FileType.PDF)
        try:
            for page_number, page in enumerate(doc, start=1):
                text = (page.get_text('text') or '').strip()
                if len(text) < self._text_layer_floor:
                    png_bytes = page.get_pixmap(dpi=self._dpi).tobytes('png')
                    ocr = self._ocr_extractor.extract(png_bytes, FileType.IMAGE)
                    text = (ocr.markdown or '').strip()
                    for lang in ocr.languages or []:
                        if lang and lang not in languages:
                            languages.append(lang)
                parts.append(f'<!-- page {page_number} -->\n\n{text}')
        finally:
            doc.close()

        markdown = '\n\n'.join(parts).strip()
        confidence = min(
            1.0, max(0.0, len(markdown) / CONFIDENCE_DOCUMENT_CHARS_NORM)
        )
        return ExtractionCandidate(
            extractor=self.name,
            markdown=markdown,
            confidence=confidence,
            languages=languages,
        )
