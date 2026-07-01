from typing import List

from doc_to_markdown_core_lib.constants import (
    CONFIDENCE_DOCUMENT_CHARS_NORM,
    CONFIDENCE_SINGLE_IMAGE_CHARS_NORM,
)
from doc_to_markdown_core_lib.data_layers.data.extraction.extraction_candidate import (
    ExtractionCandidate,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.extractor import Extractor
from doc_to_markdown_core_lib.data_layers.service.extractors.image.pdf_rasterizer import (
    DEFAULT_RASTER_DPI,
    rasterize_pdf_pages,
)
from doc_to_markdown_core_lib.data_layers.data.file_type import FileType


class ImageOcrExtractor(Extractor):
    """Shared scaffold for OCR engines that read a single ``IMAGE`` or a
    rasterized ``PDF`` — the single source of the IMAGE/PDF branching,
    per-page ``<!-- page N -->`` markers (so `candidate_selection_service`
    can align pages), and length-based confidence (single-image vs
    whole-document norm). PDFs are rasterized via PyMuPDF.

    Subclasses supply ``name`` and two hooks: :meth:`_load_engine`, which
    imports the backend and builds a reusable engine (raising
    :class:`ExtractorUnavailable` when the library/model is missing — done
    once per call, then reused across pages), and :meth:`_read_image`,
    which OCRs one image's bytes to text. Override :meth:`_languages` when
    the engine is language-configured.
    """

    file_types = (FileType.PDF, FileType.IMAGE)

    def __init__(self, dpi: int = DEFAULT_RASTER_DPI):
        self._dpi = dpi

    def _load_engine(self):
        raise NotImplementedError

    def _read_image(self, engine, image_bytes: bytes) -> str:
        raise NotImplementedError

    def _languages(self) -> List[str]:
        return []

    def extract(self, content: bytes, file_type: FileType) -> ExtractionCandidate:
        engine = self._load_engine()

        if file_type == FileType.IMAGE:
            text = self._read_image(engine, content)
            confidence = min(
                1.0, max(0.0, len(text) / CONFIDENCE_SINGLE_IMAGE_CHARS_NORM)
            )
            return ExtractionCandidate(
                extractor=self.name,
                markdown=text,
                confidence=confidence,
                languages=self._languages(),
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
                1.0, max(0.0, len(markdown) / CONFIDENCE_DOCUMENT_CHARS_NORM)
            )
            return ExtractionCandidate(
                extractor=self.name,
                markdown=markdown,
                confidence=confidence,
                languages=self._languages(),
            )

        raise ValueError(f'{self.name} cannot handle file_type={file_type!r}')
