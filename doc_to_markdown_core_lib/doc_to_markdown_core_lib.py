from omegaconf import DictConfig

from core_lib.core_lib import CoreLib

from doc_to_markdown_core_lib.data_layers.service.candidate_selection_service import (
    CandidateSelectionService,
)
from doc_to_markdown_core_lib.data_layers.service.document_service import (
    DocumentService,
)


class DocToMarkdownCoreLib(CoreLib):
    """Stateless document-to-markdown conversion lib.

    The single public service is :attr:`document` — a
    :class:`DocumentService`. Call :meth:`DocumentService.extract` with
    the document bytes and its :class:`FileType`; the service fans the
    bytes out across every applicable extractor (e.g. a PDF goes to
    PyMuPDF + pdfplumber + pdfminer + pypdf + pymupdf4llm + markitdown
    + OCR engines), hands the candidates to an internal
    :class:`CandidateSelectionService` for voting, and returns the
    winning markdown plus the report explaining the choice.

    Config knobs (under ``core_lib`` in the supplied :class:`DictConfig`):

    - ``extraction.ocr_languages``: tuple of tesseract language codes.
    - ``extraction.confidence_threshold``: float, gates ``needs_review``.
    """

    def __init__(self, conf: DictConfig):
        super().__init__()
        self.config = conf

        core_cfg = conf.get('core_lib', {}) if conf else {}
        extraction_cfg = core_cfg.get('extraction', {}) or {}
        ocr_languages_raw = extraction_cfg.get('ocr_languages')
        confidence_threshold = float(
            extraction_cfg.get('confidence_threshold', 0.8)
        )

        ocr_languages = (
            tuple(ocr_languages_raw)
            if ocr_languages_raw is not None
            else None
        )

        # Selection service is constructed here and handed to
        # ``DocumentService`` as a constructor parameter — callers
        # interact only with the document service.
        selection_service = CandidateSelectionService(
            confidence_threshold=confidence_threshold,
        )
        self.document = DocumentService(
            selection_service=selection_service,
            ocr_languages=ocr_languages,
        )
