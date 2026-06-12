"""Orchestrator. Knows which extractors to run for each file_type and
which to skip in the clean PDF tier. Delegates the choose-a-winner
work to :class:`CandidateSelectionService`."""
import logging
from typing import List, Optional, Tuple

from core_lib.data_layers.service.service import Service

from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import (
    CandidateSelectionService,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.docx.docx_extractor import (
    DocxExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.docx.mammoth_extractor import (
    MammothExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.md.md_extractor import (
    MdExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pdfminer_extractor import (
    PdfMinerExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pdfplumber_extractor import (
    PdfPlumberExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.pdf.pymupdf_extractor import (
    PyMuPdfExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.doc.soffice_extractor import (
    SofficeExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.image.tesseract_extractor import (
    TesseractExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.doc.textract_extractor import (
    TextractExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.extractors.txt.txt_extractor import (
    TxtExtractor,
)
from doc_to_markdown_core_lib.data_layers.service.tier_detector import detect_tier
from doc_to_markdown_core_lib.data_layers.service.types import (
    ExtractionCandidate,
    ExtractionResult,
    Extractor,
    ExtractorUnavailable,
)

logger = logging.getLogger(__name__)


_PRIMARY_PER_TYPE = {
    'pdf': 'pymupdf',
    'docx': 'python-docx',
    'doc': 'soffice',
    'txt': 'plain-text',
    'md': 'md-passthrough',
}


class MarkdownService(Service):
    """Runs the per-file_type extractor set, hands the candidates to
    the selection service."""

    DEFAULT_OCR_LANGUAGES = ('eng', 'heb', 'ara', 'chi_sim')

    def __init__(
        self,
        selection_service: CandidateSelectionService,
        ocr_languages: Optional[Tuple[str, ...]] = None,
        extractors: Optional[List[Extractor]] = None,
    ):
        self._selection_service = selection_service
        if extractors is not None:
            self._extractors: List[Extractor] = list(extractors)
        else:
            self._extractors = self._build_default_extractors(
                tuple(ocr_languages or self.DEFAULT_OCR_LANGUAGES),
            )

    @staticmethod
    def _build_default_extractors(
        ocr_languages: Tuple[str, ...],
    ) -> List[Extractor]:
        return [
            MdExtractor(),
            TxtExtractor(),
            DocxExtractor(),
            MammothExtractor(),
            TextractExtractor(),
            SofficeExtractor(),
            PyMuPdfExtractor(),
            PdfPlumberExtractor(),
            PdfMinerExtractor(),
            TesseractExtractor(languages=list(ocr_languages)),
        ]

    def register(self, extractor: Extractor) -> None:
        self._extractors.append(extractor)

    def extract(
        self,
        content: bytes,
        file_type: str,
        *,
        filename: Optional[str] = None,
    ) -> ExtractionResult:
        normalized_file_type = (file_type or '').lower()
        tier = detect_tier(content, normalized_file_type)

        selected = self._select(normalized_file_type, tier)
        candidates: List[ExtractionCandidate] = []
        used: List[str] = []
        skipped: List[dict] = []

        for extractor in selected:
            try:
                candidate = extractor.extract(content, normalized_file_type)
            except ExtractorUnavailable as unavailable_error:
                logger.info(
                    'extractor `%s` unavailable: %s',
                    extractor.name, unavailable_error,
                )
                skipped.append(
                    {
                        'extractor': extractor.name,
                        'reason': f'unavailable: {unavailable_error}',
                    }
                )
                continue
            except Exception as engine_error:  # noqa: BLE001
                logger.warning(
                    'extractor `%s` failed: %s', extractor.name, engine_error
                )
                skipped.append(
                    {
                        'extractor': extractor.name,
                        'reason': f'error: {engine_error}',
                    }
                )
                continue

            if candidate and (candidate.markdown or '').strip():
                candidates.append(candidate)
                used.append(extractor.name)
            else:
                skipped.append(
                    {'extractor': extractor.name, 'reason': 'empty result'}
                )

        return self._selection_service.select(
            candidates,
            tier=tier,
            used=used,
            skipped=skipped,
            filename=filename,
        )

    def _select(self, file_type: str, tier: str) -> List[Extractor]:
        matches = [
            extractor for extractor in self._extractors
            if file_type in extractor.file_types
        ]
        if not matches:
            return []
        if tier == 'clean':
            primary = _PRIMARY_PER_TYPE.get(file_type)
            if primary:
                primary_matches = [
                    extractor for extractor in matches
                    if extractor.name == primary
                ]
                if primary_matches:
                    return primary_matches
            return matches[:1]
        return matches
