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

        # Read config directly — no `.get(...)` defaults, no fallbacks. A
        # missing/malformed extraction section must fail loudly here at
        # construction; silently defaulting would hide misconfiguration.
        # (`float`/`tuple` are type coercions, not fallbacks: env-sourced
        # values arrive as strings / OmegaConf list nodes.)
        selection_service = CandidateSelectionService(
            confidence_threshold=float(conf.core_lib.extraction.confidence_threshold),
        )
        self.document = DocumentService(
            selection_service=selection_service,
            ocr_languages=tuple(conf.core_lib.extraction.ocr_languages),
        )
